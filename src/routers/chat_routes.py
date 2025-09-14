from fastapi import APIRouter, Query
from src.schemas.chat_request import ChatRequest
from src.schemas.chat_response import ResponseSchema
from src.services.chat_service import get_chat_service


chat_router = APIRouter()

@chat_router.post("/chat", response_model=ResponseSchema)
async def chat(payload: ChatRequest ):
    response = get_chat_service(payload)
    return response
