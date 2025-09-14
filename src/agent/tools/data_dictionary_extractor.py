from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import Field
from typing import Any, Optional
from src.data_dictionary.extract import explanations

class DataDictionaryExtractor(BaseTool):
    name: str = "table_column_description"
    description: str = (
        "Use this tool to get table column descriptions. "
        "This tool provides context about what the columns mean."
        "No input is required."
    )
    return_direct: bool = False  # Keep this as False
    
    def _run(
        self, 
        # tool_input, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
            Description of each column in the table. 
        """
        # Data dictionary content
        return explanations()

    def _arun(self, *args, **kwargs):
        return self._run()