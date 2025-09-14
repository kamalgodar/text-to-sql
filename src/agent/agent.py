import re
import sqlite3
from fastapi.responses import StreamingResponse

from langgraph.checkpoint.sqlite import SqliteSaver

from src.agent.chitchat import ChitchatReactAgent
from src.agent.database import DatabaseReactAgent
from src.agent.general import GeneralReactAgent
from src.agent.tools.chat_history import get_chat_history
from src.agent.tools.classifier import QueryClassifier
from src.data_dictionary.extract import explanations
# from src.schemas.chat_request import ChatRequest
from src.schemas.chat_response import ResponseSchemaMod


data_dictionary = explanations()

class MultiAgentChatSystem:
    """Main orchestrator that follows the exact steps: 1. Classify 2. Route to React Agent 3. Compose Response"""
    

    def __init__(self, llm, sql_db, system_message, payload, memory, conn):
        self.llm = llm     
        self.db = sql_db
        self.payload = payload
        self.system_prompt = system_message
        
        # Initialize memory and chat history
        self.memory = memory
        self.conn = conn

        self.config = self.get_config()
        self.state = self.memory.get(self.config)
        self.chat_history = get_chat_history(self.state["channel_values"]["messages"]) if self.state else ""
        print("Creating agents....")
        
        self.query_classifier = QueryClassifier(
            data_dictionary=data_dictionary, 
            chat_history=self.chat_history, 
            model=self.llm
        )
        print("Query classififer initialized...")
        print("Creating chitchat, general and db agents...")
        self.chitchat_react_agent = ChitchatReactAgent(llm)
        self.general_react_agent = GeneralReactAgent(llm)
        self.database_react_agent = DatabaseReactAgent(llm=llm, 
                                                       db=self.db, 
                                                       system_prompt=self.system_prompt, 
                                                       request_payload=self.payload,
                                                       memory=self.memory,
                                                       conn=self.conn,
                                                       data_dictionary=data_dictionary)
        print("All agents initialized...")

    def get_config(self):
        return {
            "recursion_limit": 15,
            "configurable": {
                "thread_id": self.payload.session_id,
            }
        }

    def converse(self, query):
        """
        Main entry point following exact steps:
        1. Classify query
        2. Route to appropriate React Agent
        3. Compose ResponseSchema
        """
        
        # Step 1: Classify query
        classification = self.query_classifier.classify_query(query)
        query_type = classification.query_type
        # user_asking_csv = classification.user_asking_csv # True or False
        # user_query_top_k = classification.top_k
        print(f"---Step 1: Query Classified as {query_type} ---")
        
        # Step 2 & 3: Route to React Agent and Compose Response
        if query_type == "chitchat":
            print("---Step 2: Using Chitchat React Agent---")
            response = self.chitchat_react_agent.execute(query=query, 
                                                         chat_history=self.chat_history)
            print("---Step 3: Composed ResponseSchemaChitchat---")
            # Convert to ResponseSchemaMod for backward compatibility
            return ResponseSchemaMod(
                sql_query=response.sql_query,
                suggested_visualization_type=response.suggested_visualization_type,
                answer=response.answer,
                query_type="chitchat",
                model_error=False
            )
            
        elif query_type == "database":
            print("---Step 2: Using Database React Agent---")
            response = self.database_react_agent.execute(query=query, 
                                                         chat_history=self.chat_history, 
                                                         )
            print("---Step 3: Composed ResponseSchemaDatabase---")
            return response
            
        elif query_type == "general":
            print("---Step 2: Using General React Agent---")
            # response = self.general_react_agent.execute(query)
            print("---Step 3: Composed ResponseSchemaGeneral---")
            # Convert to ResponseSchemaMod for backward compatibility
            return ResponseSchemaMod(
                sql_query='',
                suggested_visualization_type=[],
                answer="I'm only able to answer questions related to the connected database. If you believe this is a mistake, please rephrase the question or reach out to our support team." , # response.answer,
                query_type="general",
                model_error=False
            )
        else:
            # Fallback for unknown query type
            print(f"Unknown query type: {query_type}")
            return ResponseSchemaMod(
                sql_query='',
                suggested_visualization_type=[],
                answer="I'm not sure how to handle that query. Could you please refresh and rephrase your question?",
                query_type="unknown",
                model_error=True
            )

class ChatAgent(MultiAgentChatSystem):
    """Backward compatibility wrapper""" 
    def __init__(self, llm, sql_db, system_message, payload, memory, conn):
        super().__init__(llm, sql_db, system_message, payload, memory, conn)
        print("ChatAgent initialized with multi-agent React system")


