
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union
from pydantic import model_validator
# from src.models.graph_models import Table, LineChart, BarChart, Pie


class ResponseSchemaChitchat(BaseModel):
    sql_query: str = ''
    suggested_visualization_type: List = []
    query_type: str = 'chitchat'
    answer: str = Field(
        ...,
        description="friendly answer to user chitchat question."
    )

class ResponseSchemaGeneral(BaseModel):
    sql_query: str = ''
    suggested_visualization_type: List = []
    answer: str = Field(
        ...,
        description="I can only answer from the database related query please ask about db"
    )
    query_type:str = 'general'


class StructuredResponseSchema(BaseModel):
    """
    Structured output format for agents generating SQL from user queries.
    Captures SQL, user intent (rows, CSV, visualizations), and a natural language answer.
    Designed for LangGraph, OpenAI Function Calling, Bedrock, and API docs.
    """

    query_type: Literal['database'] = Field(
        default='database',
        title="Query Type",
        description="Type of the query. Always set to 'database'.",
        example='database'
    )

    sql_query: str = Field(
        ...,
        title="Generated SQL Query",
        description="Agent-generated SQL query based on the user's natural language request.",
        example="SELECT column_1, column_2 FROM table ORDER BY column_1 DESC LIMIT 5"
    )


    user_requested_top_k_rows: int = Field(
        default=19,
        description="Number of rows requested by the user. Default is 19 unless user specifies otherwise.",    
        json_schema_extra={
            "examples": [
                {
                    "input": "Show me top 5 customers by revenue",
                    "user_requested_top_k_rows": 5
                },
                {
                    "input": "List the first 10 orders from today",
                    "user_requested_top_k_rows": 10
                },
                {
                    "input": "Display 25 most recent transactions",
                    "user_requested_top_k_rows": 25
                },
                {
                    "input": "Give me 3 highest selling products",
                    "user_requested_top_k_rows": 3
                },
                {
                    "input": "Show all customers without limit", # No specific number mentioned
                    "user_requested_top_k_rows": 19
                }
            ]
        }
    )

    user_explicitly_asked_for_rows: Optional[bool] = Field(
        default=False,
        description="True if user said they want specific number of rows or top k data. It is also True when user_requested_top_k_rows value is other than 19. Default is False",
        json_schema_extra={
            "examples": [
                {
                    "input": "Show me top 5 customers by revenue",
                    "user_explicitly_asked_for_rows": True,
                    "explanation": "User explicitly requested 5 rows"
                },
                {
                    "input": "List the first 10 orders from today",
                    "user_explicitly_asked_for_rows": True,
                    "explanation": "User explicitly requested 10 rows"
                },
                {
                    "input": "Display 25 most recent transactions",
                    "user_explicitly_asked_for_rows": True,
                    "explanation": "User explicitly requested 25 rows"
                },
                {
                    "input": "Give me 3 highest selling products",
                    "user_explicitly_asked_for_rows": True,
                    "explanation": "User explicitly requested 3 rows"
                },
                {
                    "input": "Show all customers without limit",
                    "user_explicitly_asked_for_rows": False,
                    "explanation": "No specific row count mentioned, uses default 19"
                },
                {
                    "input": "What are the payment methods available?",
                    "user_explicitly_asked_for_rows": False,
                    "explanation": "General query without row specification"
                }
            ]
        }
    )

    user_requested_csv: Optional[bool] = Field(
        default=False,
        description=(
            "True if user explicitly requests a CSV (e.g., mentions 'CSV', 'download', 'export') "
            "or implicitly requests a large dataset (e.g., more than 100 rows) "
            "or wants to save/download data for external use."
        ),
        json_schema_extra={
            "examples": [
                {
                    "input": "Can I download this customer data as CSV?",
                    "user_requested_csv": True,
                    "explanation": "Explicit CSV request with download intent"
                },
                {
                    "input": "Export all transactions to CSV format",
                    "user_requested_csv": True,
                    "explanation": "Direct CSV export request"
                },
                {
                    "input": "I need this sales data in CSV",
                    "user_requested_csv": True,
                    "explanation": "Explicit CSV format request"
                },
                {
                    "input": "Show me 500 customer records for analysis",
                    "user_requested_csv": True,
                    "explanation": "Large dataset (>100 rows) implies CSV need"
                },
                {
                    "input": "Give me all orders from last year",
                    "user_requested_csv": True,
                    "explanation": "Request for comprehensive data implies CSV"
                },
                {
                    "input": "I want to analyze this inventory data in Excel",
                    "user_requested_csv": True,
                    "explanation": "External tool usage implies CSV export"
                },
                {
                    "input": "Display recent 15 fraud cases",
                    "user_requested_csv": False,
                    "explanation": "Small dataset for viewing, no export intent"
                },
                {
                    "input": "Show top performing regions",
                    "user_requested_csv": False,
                    "explanation": "Small dataset for quick viewing"
                },
                {
                    "input": "What's the average order value by month?",
                    "user_requested_csv": False,
                    "explanation": "Aggregate query, not raw data request"
                },
                {
                    "input": "Show me 200 rows but don't export",
                    "user_requested_csv": False,
                    "explanation": "Large dataset but explicit no-download intent"
                }
            ]
        }
    )

    suggested_visualization_type: List[Union[Literal['table', 'bar', 'pie', 'line']]] = Field(
        default=[],
        description=(
            "Suggested visualizations for displaying the results. "
            "Choose from: 'table', 'bar', 'pie', 'line'.\n"
            "- 'table': For detailed data listing, raw data display, or when explicitly requested\n"
            "- 'bar': For categorical comparisons, rankings, counts by category\n"
            "- 'pie': For showing proportions, percentages, or parts of a whole\n"
            "- 'line': For time-series data, trends over time, temporal analysis"
        ),
        json_schema_extra={
            "examples": [
                {
                    "input": "Show payment method distribution across airports",
                    "suggested_visualization_type": ["bar", "pie"],
                    "explanation": "Distribution can be shown as bar chart (comparison) or pie chart (proportions)"
                },
                {
                    "input": "What percentage of transactions were fraudulent last month?",
                    "suggested_visualization_type": ["pie"],
                    "explanation": "Percentage/proportion question best shown with pie chart"
                },
                {
                    "input": "Display daily sales trend for the past 30 days",
                    "suggested_visualization_type": ["line"],
                    "explanation": "Time-series data over days requires line chart"
                },
                {
                    "input": "Show me this data in a table format please",
                    "suggested_visualization_type": ["table"],
                    "explanation": "User explicitly requested table format"
                },
                {
                    "input": "Compare revenue by product category using stacked bars",
                    "suggested_visualization_type": ["bar"],
                    "explanation": "Explicit bar chart request for category comparison"
                },
                {
                    "input": "List all high-value customers with details",
                    "suggested_visualization_type": ["table"],
                    "explanation": "Detailed listing of specific records best shown in table"
                },
                {
                    "input": "Which quarter had the highest fraud incidents?",
                    "suggested_visualization_type": ["bar", "line"],
                    "explanation": "Time-based comparison can use bar (comparison) or line (trend)"
                },
                {
                    "input": "Show monthly revenue growth over the past year",
                    "suggested_visualization_type": ["line"],
                    "explanation": "Growth trend over time requires line chart"
                },
                {
                    "input": "Break down customer segments by geographic region",
                    "suggested_visualization_type": ["bar", "pie"],
                    "explanation": "Regional breakdown can show comparison (bar) or proportion (pie)"
                },
                {
                    "input": "What's the market share of each product line?",
                    "suggested_visualization_type": ["pie"],
                    "explanation": "Market share implies proportions, best shown with pie chart"
                }
            ]
        }
    )

    answer: str = Field(
        ...,
        description=(
            "A natural language, user-friendly answer to the user query in 2-3 sentences. "
            "If the user requests a CSV response, return an empty string ''. "
            "Never generate tables or table markdown in this field. "
            "Be concise and directly address what the user asked for. "
            "Examples: 'Here are the top 5 customers by revenue.' or 'The data shows 23% of transactions were fraudulent.' "
            "If showing visualization data, briefly describe what the chart will display."
        ),
        json_schema_extra={
            "examples": [
                {
                    "user_query": "Show me top 5 customers by revenue",
                    "answer": "Here are the top 5 customers ranked by their total revenue contribution.",
                    "explanation": "Direct response to user's request"
                },
                {
                    "user_query": "What percentage of transactions were fraudulent?",
                    "answer": "Based on the analysis, 12.3% of all transactions were flagged as fraudulent.",
                    "explanation": "Provides specific insight with context"
                },
                {
                    "user_query": "Export all customer data to CSV",
                    "answer": "",
                    "explanation": "Empty string for CSV requests as specified"
                },
                {
                    "user_query": "Show daily sales trend for last month",
                    "answer": "The chart displays daily sales performance over the past 30 days, showing clear growth patterns and peak sales periods.",
                    "explanation": "Describes what the visualization will show"
                },
                {
                    "user_query": "List customers in New York",
                    "answer": "Here are all customers located in New York state, showing their contact details and account status.",
                    "explanation": "Sets context for the data being displayed"
                }
            ]
        }
    )
    
    
    
    @model_validator(mode="after")
    def infer_explicit_flag(self):
        if self.user_requested_top_k_rows != 19 and self.user_explicitly_asked_for_rows is False:
            self.user_explicitly_asked_for_rows = True
        return self
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query_type": "database",
                    "sql_query": "SELECT * FROM customers ORDER BY revenue DESC LIMIT 5",
                    "user_requested_top_k_rows": 5,
                    "user_explicitly_asked_for_rows": True,
                    "user_requested_csv": False,
                    "suggested_visualization_type": ["bar"],
                    "answer": "Here are the top 5 customers ranked by their revenue."
                },
                {
                    "query_type": "database",
                    "sql_query": "SELECT COUNT(*) FROM transactions WHERE is_fraud = TRUE",
                    "user_requested_top_k_rows": 19,
                    "user_explicitly_asked_for_rows": False,
                    "user_requested_csv": False,
                    "suggested_visualization_type": ["pie"],
                    "answer": "Approximately 12% of all transactions were marked as fraudulent."
                },
                {
                    "query_type": "database",
                    "sql_query": "SELECT * FROM transactions WHERE date >= '2023-01-01'",
                    "user_requested_top_k_rows": 500,
                    "user_explicitly_asked_for_rows": True,
                    "user_requested_csv": True,
                    "suggested_visualization_type": ["table"],
                    "answer": ""
                },
                
                {
                    "query_type": "database",
                    "sql_query": (
                        "SELECT column_x, COUNT(*) as count "
                        "FROM table_name "
                        "WHERE condition"
                        "GROUP BY column_x "
                        "ORDER BY count DESC "
                        "LIMIT 2"
                    ),
                    "user_requested_top_k_rows": 2,
                    "user_explicitly_asked_for_rows": True,
                    "user_requested_csv": False,
                    "suggested_visualization_type": ["bar", "table"],
                    "answer": "Here are the two most common types of ... "
                }
        
                
                
                
                
                
            ]
        }



class ResponseSchemaMod(BaseModel):
    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True
        
        