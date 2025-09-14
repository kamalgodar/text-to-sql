import uvicorn
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv(override=True)
    uvicorn.run("src.app:app", port=9000, host="0.0.0.0", reload=True)