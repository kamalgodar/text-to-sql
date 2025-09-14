from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages.utils import count_tokens_approximately
from langmem.short_term import SummarizationNode

from src.configs.settings import settings
from src.agent.tools.sql_toolkit import SQLDatabaseToolkit
from src.agent.tools.graph_parser import recommend_graph_object
from src.schemas.chat_response import (
    StructuredResponseSchema, 
    ResponseSchemaMod
)
from src.db.db import fetch_data_from_db 
from typing import Any, Optional
import re
import pandas as pd
from src.agent.compose_csv import stream_csv
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
# Configuration constants
TOP_K = settings.TOP_K  # Default limit for queries (e.g., 19)
MAX_DISPLAY_ROWS = settings.MAX_DISPLAY_ROWS   # Maximum rows to display in UI response
SAMPLE_SIZE_FOR_GRAPH = settings.SAMPLE_SIZE_FOR_GRAPH # Sample size for graph recommendations


class AgentExecutionError(Exception):
    def __init__(self, original_exception, message=None, data=None):
        self.original_exception = original_exception
        self.message = message
        self.data = data
        super().__init__(str(original_exception))

class AgentValidationError(Exception):
    def __init__(self, original_exception: ValidationError, message: Optional[str] = None, data: Optional[dict] = None):
        self.original_exception = original_exception
        self.message = message
        self.data = data
        super().__init__(str(original_exception))
    

def build_sql_query_with_limit(sql_query: str, limit: int, remove: bool = False) -> str:
    """
    Build SQL query with appropriate LIMIT clause.
    
    Args:
        sql_query: Original SQL query
        limit: Number of rows to limit (0 means no limit)
        remove: If True, remove limit clause entirely
        
    Returns:
        SQL query with or without LIMIT clause
    """
    # Remove any existing LIMIT clause
    sql_query = re.sub(r'\bLIMIT\s+\d+\s*;?\s*$', '', sql_query, flags=re.IGNORECASE).strip()
    
    # Add semicolon if not present
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    # Remove semicolon to add LIMIT before it
    sql_query = sql_query.rstrip(';')
    
    if remove or limit == 0:
        return sql_query
    
    return f"{sql_query} LIMIT {limit}"





def compose_csv_response(db_data: list) -> StreamingResponse:
    """Create CSV response for download."""
    print(f"Composing CSV response for {len(db_data)} rows")
    df = pd.DataFrame(db_data)
    return StreamingResponse(
        stream_csv(df),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )


class SQLAgentState(AgentState):
    context: dict[str, Any]
    structured_response: Optional[dict]


class DatabaseReactAgent:
    """React Agent specifically for handling database queries with clear row handling logic."""

    def __init__(self, llm, db, system_prompt, request_payload, conn, memory, data_dictionary):
        self.llm = llm
        self.db = db
        self.payload = request_payload
        self.conn = conn
        self.memory = memory
        self.tools = SQLDatabaseToolkit(db=self.db, llm=self.llm).get_tools()
        self.data_dictionary = data_dictionary
        # self.summarization_node = SummarizationNode(
        #     model=self.llm,
        #     token_counter=count_tokens_approximately,
        #     max_tokens=20000,
        #     max_summary_tokens=10000,
        #     output_messages_key="llm_input_messages",
        # )

        self.agent_executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
            checkpointer=self.memory,
            debug=False,
            response_format=StructuredResponseSchema,
            # pre_model_hook=self.summarization_node,
            # state_schema=SQLAgentState,
        )

    def get_config(self):
        return {
            "recursion_limit": 20,
            "configurable": {
                "thread_id": self.payload.session_id,
            }
        }

    def execute(self, query, chat_history, **kwargs):
        """Execute database query and return appropriate response."""
        config = self.get_config()
        input_data = {"messages": [{"role": "user", "content": query}]}

        try:
            return self._attempt_converse(query, config, input_data, chat_history, **kwargs)
        
        except AgentValidationError as e:
            print("Validation error")
            print(f"Database agent failure: {e.original_exception}")
            print("Original Failure Message:", e.message)
            print("Data Extracted:", e.data)        

            return ResponseSchemaMod(
                sql_query="",
                suggested_visualization_type=[],
                answer="Looks like Nova model couldn’t format your response this time. A quick reload and re-prompt usually does the trick.",
                model_error=True
            )
            
        except AgentExecutionError as e:
            print(f"Database agent failure: {e.original_exception}")
            print("Original Failure Message:", e.message)
            print("Data Extracted:", e.data)
            return ResponseSchemaMod(
                sql_query="",
                suggested_visualization_type=[],
                answer="I couldn't find an exact match for your question in our data. Try rephrasing your question, or let us know if you'd like help.",
                model_error=True
            )

    def _attempt_converse(self, query, config, input_data, chat_history, **kwargs):
        """Main conversation logic with improved row handling."""
        data = None
        output = None
        message = None

        try:
            # Execute agent
            for s in self.agent_executor.stream(input_data, stream_mode="values", config=config, debug=False, checkpoint_during=True):
                message = s["messages"][-1]
                message.pretty_print()
                # if isinstance(message, ToolMessage) and message.name == "sql_db_query":
                #     data = message.content
                # if not isinstance(message, tuple):
                #     message.pretty_print()

            # Get structured response
            output = s.get('structured_response')
            if not output:
                raise ValueError("Structured response cannot be composed")

            # Extract user preferences
            result_response = ResponseSchemaMod(**output.model_dump())
            user_requested_rows = getattr(output, 'user_requested_top_k_rows')
            user_requested_csv = getattr(output, 'user_requested_csv')
            user_explicitly_asked = getattr(output, 'user_explicitly_asked_for_rows')
            
            print(f"\n\nNumber of rows user requested: {user_requested_rows}")
            print(f"Did user requested csv - {user_requested_csv}")
            print(f"Did user explicitely asked for some rows count - {user_explicitly_asked}")

            # CSV file logic
            if user_requested_csv:
                if user_explicitly_asked:  # csv but limited data
                    # User wants specific number of rows as CSV   # add user asked limit
                    final_sql_query = build_sql_query_with_limit(sql_query=result_response.sql_query, 
                                                                 limit=user_requested_rows)
                    db_data = fetch_data_from_db(final_sql_query)
                    
                else: # csv but whole data
                    # User wants all data as CSV - no limit
                    unlimited_sql_query = build_sql_query_with_limit(sql_query=result_response.sql_query, limit = 1000, remove=False)
                    db_data = fetch_data_from_db(unlimited_sql_query)
                
                if not db_data:
                    print("No matching data found")
                    result_response.suggested_visualization_type.clear()
                    result_response.model_error = False
                    result_response.query_type = 'database'
                    return result_response
                
                print(f"User requested CSV download with {len(db_data)} rows")
                return compose_csv_response(db_data)
            
            
            # Non Csv file logic
            # User didnot ask for csv 
            if user_explicitly_asked or user_requested_rows != TOP_K:    # but do they requested some number of rows? - yes
                final_sql_query = build_sql_query_with_limit(sql_query=result_response.sql_query,
                                                             limit=user_requested_rows)
                
                db_data = fetch_data_from_db(final_sql_query)
                
                
                if not db_data:
                    result_response.sql_query = final_sql_query
                    result_response.suggested_visualization_type.clear()
                    result_response.model_error = False
                    result_response.query_type = 'database'
                    return result_response
                
                else:
                    # Generate graph recommendations using sample
                    graph_sample = db_data[:SAMPLE_SIZE_FOR_GRAPH]
                    graph_recommendations = recommend_graph_object(data_extracted_from_database=graph_sample,
                                                                   output=output, 
                                                                   llm=self.llm, 
                                                                   chat_history=chat_history,
                                                                   latest_user_query=query, 
                                                                   query=result_response.sql_query)
                    
                    result_response.suggested_visualization_type.clear()
                    result_response.suggested_visualization_type = graph_recommendations
                    result_response.sql_query = final_sql_query
                    result_response.data = db_data[:user_requested_rows]
                    return result_response
                    
            # User didnot ask for csv and didnot reuqested any number of rows.... For simplicity we will return 100 rows
            elif not user_requested_csv and not user_explicitly_asked: 
                sample_query = build_sql_query_with_limit(sql_query=result_response.sql_query, limit=0,
                                                          remove=True)
                db_data = fetch_data_from_db(sample_query)
                if not db_data:
                    print("The Query returned no data.")
                    result_response.sql_query = sample_query
                    result_response.suggested_visualization_type.clear()
                    result_response.model_error = False
                    result_response.query_type = 'database'
                    return result_response
                else:
                    # Generate graph recommendations using sample
                    total_rows = len(db_data)
                    # if total_rows == user_requested_rows:
                    #     pass
                    # msg = ' It is only 19 sample of whole data.' if total_rows == 19 else ''
                    # if total_rows > MAX_DISPLAY_ROWS and total_rows != 19:
                    #     msg = f"\nOut of {total_rows} only {MAX_DISPLAY_ROWS} rows are displayed. Please say 'I want csv data if you want all {total_rows} rows'"
                    msg = f" Please say I want csv file if you want all {total_rows} rows." if total_rows > 1 else ''
                    graph_sample = db_data[:SAMPLE_SIZE_FOR_GRAPH]
                    graph_recommendations = recommend_graph_object(data_extracted_from_database=graph_sample,
                                                                   output=output, 
                                                                   llm=self.llm, 
                                                                   chat_history=chat_history,
                                                                   latest_user_query=query, 
                                                                   query=result_response.sql_query)
                    
                    result_response.suggested_visualization_type.clear()
                    result_response.suggested_visualization_type = graph_recommendations
                    result_response.answer += msg
                    result_response.sql_query = sample_query
                    result_response.data = db_data[:MAX_DISPLAY_ROWS]
                    return result_response
            else:
                # TODO find this case
                print("The unknown logic")

        except Exception as e:
            print("\n...Exception Occured...")
            print(type(e), str(e))
            if isinstance(e, ValidationError):
                print("\n\nValidationError Occured Recomposing response")
                raise AgentValidationError(e, message=message, data=data)
            raise AgentExecutionError(e, message=message, data=data)
        