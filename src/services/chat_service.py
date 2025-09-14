from src.configs.settings import settings
from src.agent.agent import ChatAgent
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from src.schemas.chat_request import ChatRequest
from src.db.db import Database
from src.agent.prompts.templates import prompt_template
from src.data_dictionary.extract import explanations
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

data_dictionary = explanations()

import os
import sqlite3
from datetime import datetime

class SingletonSQLiteConnection:
    _instance = None
    _conn = None

    def __new__(cls, db_path=None):
        if cls._instance is None:
            # If no path is provided, create a timestamped one
            if db_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_dir = f"db-agent/history/{timestamp}"
                os.makedirs(base_dir, exist_ok=True)
                db_path = os.path.join(base_dir, f"agent_checkpoints_{timestamp}.sqlite")
            
            cls._instance = super(SingletonSQLiteConnection, cls).__new__(cls)
            cls._conn = sqlite3.connect(db_path, check_same_thread=False)
            print(f"Created new SQLite connection at {db_path}")
        else:
            print("Reusing existing SQLite connection")
        return cls._instance

    def get_connection(self):
        return self._conn



class ComponentFactory:
    _db_instance = None
    _sql_db = None
    _llm = None
    _memory = None

    @classmethod
    def get_db_engine(cls):
        if cls._db_instance is None:
            cls._db_instance = Database()
            print(f"Connected to database: {cls._db_instance.database}")
        return cls._db_instance.get_engine()

    @classmethod
    def get_sql_database(cls):
        if cls._sql_db is None:
            engine = cls.get_db_engine()
            print("\nConnecting to SQLDatabase")
            cls._sql_db = SQLDatabase(
                engine=engine,
                sample_rows_in_table_info=3,
                include_tables=settings.INCLUDE_TABLES,
            )
            print("Connected...")
        return cls._sql_db

    @classmethod
    def get_llm(cls, with_guard_rails=False):
        if cls._llm is None:
            additional_params = {}

            if settings.LLM_PROVIDER == "bedrock":
                # Base Bedrock connection parameters
                additional_params.update({
                    "aws_access_key_id": settings.BEDROCK_ACCESS_KEY_ID,
                    "aws_secret_access_key": settings.BEDROCK_SECRET_ACCESS_KEY,
                    "region_name": settings.BEDROCK_REGION,
                    "model_kwargs": {
                            "trace": "enabled",
                            "temperature": 0.1,
                            "top_p": 0.5,
                            "top_k": 10,
                        }
                })

                if with_guard_rails:
                    additional_params.update({
                        "guardrails": {
                            'guardrailIdentifier': 'fev16vp539yt',
                            'guardrailVersion': 'DRAFT',
                        },
                    })

            cls._llm = init_chat_model(
                model=settings.LLM_MODEL,
                model_provider=settings.LLM_PROVIDER,
                **additional_params
            )
            print(f"LLM Used: {settings.LLM_MODEL} from {settings.LLM_PROVIDER}")

        return cls._llm

    @classmethod
    def get_memory(cls):
        if cls._memory is None:
            conn = SingletonSQLiteConnection().get_connection()
            cls._memory = SqliteSaver(conn=conn)
        return cls._memory

    @classmethod
    def get_sqlite_conn(cls):
        return SingletonSQLiteConnection().get_connection()


class ChatService:
    def __init__(self, payload: ChatRequest):
        print("Paylod passed to chatserivce")
        self.payload = payload
        self.agent = self._create_agent()
        print("agent created ..._create_agent() completed.")

    def _create_agent(self):
        print("Initializing agent components")
        sql_db = ComponentFactory.get_sql_database()
        
        print("Database initialized...")
        llm = ComponentFactory.get_llm(with_guard_rails=False)
        # non_guard_rail_llm = ComponentFactory.get_llm(with_guard_rails=False)
        # guard_rail_llm = ComponentFactory.get_llm(with_guard_rails=True)
        print("LLM initialized..")
        memory = ComponentFactory.get_memory()
        conn = ComponentFactory.get_sqlite_conn()
        print("Conversational chat history memory initialized...")

        system_message = prompt_template.format(
            dialect=settings.DIALECT,
            top_k=settings.TOP_K,
            table_names=sql_db.get_usable_table_names(),
            data_dictionary=data_dictionary,
        )
        
        return ChatAgent(llm=llm, 
                         sql_db=sql_db, 
                         system_message=system_message,
                         payload=self.payload, 
                         memory=memory, 
                         conn=conn)

        # return ChatAgent(non_guard_rail_llm, guard_rail_llm, sql_db, system_message, self.payload, memory, conn)

    def converse(self):
        return self.agent.converse(self.payload.user_query)
