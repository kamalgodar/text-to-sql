import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from src.configs.settings import settings
import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.engine import Result


class SingletonMeta(type):
    """
    Singleton metaclass for database connections.
    
    When to use Singleton:
    - Database connection pools (shared across application)
    - Configuration objects that should be shared
    - Cache managers or shared resources
    - Thread-safe objects that are expensive to create
    
    When NOT to use Singleton:
    - Objects that need different configurations
    - Testing scenarios (makes mocking difficult)
    - When you need multiple instances with different states
    - Objects that should be stateless or have short lifecycles
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # First time creating this class instance
            print(f"Creating new {cls.__name__} singleton instance")
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        else:
            # Reusing existing instance
            print(f"Reusing existing {cls.__name__} singleton instance")
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.user = settings.POSTGRES_USER
        self.password = settings.POSTGRES_PASSWORD
        self.host = settings.POSTGRES_HOST
        self.port = settings.POSTGRES_PORT
        self.database = settings.POSTGRES_DATABASE
        self._engine = None

    def get_uri(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_engine(self):
        if not self._engine:
            try:
                self._engine = create_engine(
                    self.get_uri(),
                    poolclass=QueuePool,
                    pool_size=5,  # Production-ready pool size
                    max_overflow=30,  # Higher overflow for peak loads
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=900,  # Recycle connections every hour
                    pool_timeout=30,  # Connection timeout
                    echo=False
                )
                print("Database engine connection created...")
            except Exception as e:
                return None
        return self._engine

    def disconnect(self):
        if self._engine:
            try:
                self._engine.dispose()
                self._engine = None
            except Exception:
                pass


def fetch_data_from_db_fast(query: str) -> List[Dict[str, Any]]:
    """
    Executes SQL query and returns results as list of dictionaries.
    Optimized version without pandas overhead.
    
    Parameters:
        query (str): The raw SQL query to execute.
    
    Returns:
        List[Dict[str, Any]]: Query results where each row is a dict keyed by column names.
    """
    engine = Database().get_engine()
    if not engine:
        raise ConnectionError("Failed to initialize database engine.")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        raise




def fetch_data_from_db_pandas(query: str) -> List[Dict[str, Any]]:
    """
    Executes SQL query using pandas (for complex data processing needs).
    
    Parameters:
        query (str): The raw SQL query to execute.
    
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries.
    """
    import pandas as pd
    
    engine = Database().get_engine()
    if not engine:
        raise ConnectionError("Failed to initialize database engine.")
    
    try:
        # Use pandas read_sql for better type handling and large datasets
        df = pd.read_sql(query, engine)
        return df.to_dict(orient='records')
    except Exception as e:
        raise


async def fetch_data_async(query: str) -> List[Dict[str, Any]]:
    """
    Async version using asyncpg for high-performance applications.
    
    Parameters:
        query (str): The raw SQL query to execute.
    
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries.
    """
    db = Database()
    conn_str = f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}"
    
    try:
        conn = await asyncpg.connect(conn_str)
        try:
            rows = await conn.fetch(query)
            # Convert asyncpg.Record to dict
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    except Exception as e:
        raise


# Connection pool for async operations
class AsyncDatabase:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self.db = Database()

    async def get_pool(self) -> asyncpg.Pool:
        if not self._pool:
            conn_str = self.db.get_uri()
            self._pool = await asyncpg.create_pool(
                conn_str,
                min_size=10,  # Production scale
                max_size=50,  # Higher for production
                command_timeout=60,
                server_settings={
                    'application_name': 'production_app',
                    'jit': 'off'  # Disable JIT for consistent performance
                }
            )
        return self._pool

    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """High-performance async data fetching with connection pooling."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def execute(self, query: str, *args) -> str:
        """Execute non-SELECT queries (INSERT/UPDATE/DELETE)."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def close(self):
        if self._pool:
            await self._pool.close()


# Convenience functions
def fetch_data_from_db(query: str) -> List[Dict[str, Any]]:
    """Wrapper for backward compatibility - uses optimized version."""
    return fetch_data_from_db_fast(query)


async def fetch_data_from_db_async(query: str) -> List[Dict[str, Any]]:
    """Async wrapper for backward compatibility - uses optimized async version."""
    async_db = AsyncDatabase()
    return await async_db.fetch_data(query)