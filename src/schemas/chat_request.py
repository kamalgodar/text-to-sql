from pydantic import BaseModel, Field
from uuid import uuid4

class ChatRequest(BaseModel):
    user_query : str
    session_id : str