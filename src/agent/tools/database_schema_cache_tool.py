from typing import Dict, ClassVar, Optional, Type
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)

@dataclass
class CacheEntry:
    data: str
    timestamp: datetime

class BaseSQLDatabaseTool(BaseModel):
    db: SQLDatabase = Field(exclude=True, sample_rows_in_table_info=3)
    model_config = ConfigDict(arbitrary_types_allowed=True)

class _InfoSQLDatabaseToolInput(BaseModel):
    table_names: str = Field(
        ...,
        description="Comma-separated list of table names. Example: 'table1, table2'"
    )

class InfoSQLDatabaseTool(BaseSQLDatabaseTool, BaseTool):
    name: str = "sql_db_schema"
    description: str = "Get the schema and sample rows for the specified SQL tables."
    args_schema: Type[BaseModel] = _InfoSQLDatabaseToolInput
    
    _cache: ClassVar[Dict[str, CacheEntry]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    CACHE_TIMEOUT: ClassVar[timedelta] = timedelta(minutes=15)

    def _run(
        self,
        table_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs
    ) -> str:
        print("\n\nInfo sql database tool called....\n\n")
        tables = [t.strip() for t in table_names.split(",") if t.strip()]
        if not tables:
            raise ValueError("No valid table names provided")

        cache_key = f"{str(self.db._engine.url)}|{','.join(sorted(tables))}"
        
        with self._lock:
            if cache_entry := self._cache.get(cache_key):
                if (datetime.now() - cache_entry.timestamp) < self.CACHE_TIMEOUT:
                    print("\n\nUsing Schema from Cache\n\n")
                    return cache_entry.data

            result = self.db.get_table_info_no_throw(tables)
            self._cache[cache_key] = CacheEntry(data=result, timestamp=datetime.now())
            return result



    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache.clear()