from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit
from pydantic import ConfigDict, Field
from typing import Any, List, Optional
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLCheckerTool
from src.agent.tools.database_schema_cache_tool import InfoSQLDatabaseTool
from typing import Any, Dict, Optional, Sequence, Type, Union
import ast
from pydantic import BaseModel

class BaseSQLDatabaseTool(BaseModel):
    """Base tool for interacting with a SQL database."""

    db: SQLDatabase = Field(exclude=True)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class _QuerySQLDatabaseToolInput(BaseModel):
    query: str = Field(..., description="A detailed and correct SQL query.")
    
class QuerySQLDatabaseTool(BaseSQLDatabaseTool, BaseTool):
    """Tool for querying a SQL database and returning results as JSON with column names."""
    
    name: str = "sql_db_query"
    description: str = """
    Execute a SQL query against the database and get back the result..
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """ 
    args_schema: Type[BaseModel] = _QuerySQLDatabaseToolInput    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ):
        """Execute the SQL query and return the results as JSON."""
        # Make timeout database-agnostic
        try:
            if self.db.dialect.lower() == 'postgresql':
                _ = self.db.run_no_throw("SET LOCAL statement_timeout = 60000")  # 60 seconds
            elif self.db.dialect.lower() == 'mysql':
                _ = self.db.run_no_throw("SET SESSION max_execution_time = 60000")  # 60 seconds
        except Exception:
            # If timeout setting fails, continue without it
            pass
            
        result = self.db.run_no_throw(query, include_columns=True)
        try:
            result = ast.literal_eval(result)
        except Exception as e:
            pass
        return {"sql_query": query, "result":result}
    
    
class _ListSQLDatabaseToolInput(BaseModel):
    tool_input: str = Field("", description="An empty string")
    

class FixedListSQLDatabaseTool(BaseSQLDatabaseTool, BaseTool):
    """Tool for listing tables in SQL database."""
    
    name: str = "sql_db_list_tables"
    description: str = "Input is an empty string, output is a list of tables in the database."
    args_schema: Type[BaseModel] = _ListSQLDatabaseToolInput
        
    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """List all tables in the SQL database."""
        tables = self.db.get_usable_table_names()
        if not tables:
            return "No tables found in the database."
        return ", ".join(tables)


class SQLDatabaseToolkit(BaseToolkit):
    """Tools that should be called by agent to talk with the database"""
    
    db: SQLDatabase = Field(exclude=True)
    llm: BaseLanguageModel = Field(exclude=True)
    
    @property
    def dialect(self) -> str:
        """Return string representation of SQL dialect to use."""
        return self.db.dialect
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    
    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        list_sql_database_tool = FixedListSQLDatabaseTool(db=self.db)  # check
        
        info_sql_database_tool_description = (
            "Input to this tool is a comma-separated list of tables, output is the "
            "schema and sample rows for those tables. "
            "Be sure that the tables actually exist by calling "
            f"{list_sql_database_tool.name} first! "
            "Example Input: table1, table2, table3"
        )
        # Pass the description correctly to the custom InfoSQLDatabaseTool
        info_sql_database_tool = InfoSQLDatabaseTool(
            db=self.db
        )
        # Override the description after instantiation
        info_sql_database_tool.description = info_sql_database_tool_description
        
        query_sql_database_tool_description = (
            "Input to this tool is a detailed and correct SQL query. Use this input to compose  output response sql_query "
            "Output is a result from the database in JSON format including column names. If the query is not correct, "
            "an error message will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. If you encounter an issue with Unknown column "
            f"'xxxx' in 'field list', use {info_sql_database_tool.name} "
            "to query the correct table fields. "
        )
        
        # Use our JSON version instead of QuerySQLDatabaseTool
        query_sql_database_tool = QuerySQLDatabaseTool(
            db=self.db, description=query_sql_database_tool_description
        )
        
        query_sql_checker_tool_description = (
            "Use this tool to validate if your query is correct before executing "
            "it."
            "Always use this tool before executing a query with "
            f"{query_sql_database_tool.name}!"
        )
        query_sql_checker_tool = QuerySQLCheckerTool(
            db=self.db, llm=self.llm, description=query_sql_checker_tool_description
        )
        
        return [
                query_sql_database_tool,
                info_sql_database_tool,
                list_sql_database_tool,
                query_sql_checker_tool,
            ]
    
    def get_context(self) -> dict:
        """Return db context that you may want in agent prompt."""
        return self.db.get_context()

# Rebuild the model to apply changes
SQLDatabaseToolkit.model_rebuild()
