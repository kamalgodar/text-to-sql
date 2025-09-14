from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.schemas.chat_request import ChatRequest
from src.services.chat_service import ChatService
import os
import shutil
import asyncio
import time
from src.schemas.chat_response import ResponseSchemaMod

def clear_local_db_folder(path="db-agent"):
    if os.path.exists(path):
        shutil.rmtree(path)  # Deletes the folder and all its contents
        print(f"Cleared all files in {path}")
    else:
        print(f"Folder {path} doesn't exist.")

async def create_directories_async(path="db-agent"):
    """
    Asynchronously creates the necessary directories.
    Uses asyncio.to_thread to run the blocking os.makedirs in a separate thread.
    """
    history_path = os.path.join(path, "history")
    try:
        # os.makedirs can create intermediate directories, so one call is often enough
        # if the base path itself needs to be created.
        # However, using exist_ok=True handles cases where parts of the path already exist.
        await asyncio.to_thread(os.makedirs, path, exist_ok=True)
        print(f"Ensured base directory exists: {path}")
        await asyncio.to_thread(os.makedirs, history_path, exist_ok=True)
        print(f"Ensured history directory exists: {history_path}")
    except OSError as e:
        print(f"Error creating directories {path} or {history_path}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous lifespan manager for the FastAPI application.
    Creates directories on startup and clears them on shutdown.
    """
    # Startup: Create directories asynchronously
    await create_directories_async("db-agent")
    
    yield  # Application runs after this point
    
    # Shutdown: Clear the local db folder asynchronously
    print("Shutting down application and clearing db-agent folder...")
    clear_local_db_folder()
    print("Cleanup complete.")

app = FastAPI(lifespan=lifespan)


@app.post("/test_chat")
async def get_chat(payload: ChatRequest):
    print(f"{payload.session_id=}")
    print(f"{payload.user_query=}\n")
    start_time = time.time()
    try:
        service = ChatService(payload=payload)
        response = service.converse()
        
        if isinstance(response, ResponseSchemaMod):
            print(f"{payload.session_id=}, {payload.user_query=}, {response.model_dump(exclude={'data'})}")
        else:
            print(f"{payload.session_id=}, {payload.user_query=}, csv response")
        return response
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    finally:
        end_time = time.time()
        print(f"Conversation duration: {end_time - start_time:.2f} seconds")


origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)


# app.include_router(chat_routes.chat_router, tags=['chat'])