from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from typing import List


class DbQeryInput(BaseModel):
    table : str = Field(..., description="Name of the table related to the query")
    cols : List[str] = Field(..., description="Name of the columns in the query")
    
