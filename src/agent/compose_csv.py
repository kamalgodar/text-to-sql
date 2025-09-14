# from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO, TextIOWrapper
from typing import Generator


def stream_csv(df: pd.DataFrame, chunk_size: int = 10000) -> Generator[bytes, None, None]:
    for i, start in enumerate(range(0, len(df), chunk_size)):
        end = min(start + chunk_size, len(df))
        chunk = df.iloc[start:end]

        buffer = BytesIO()
        text_wrapper = TextIOWrapper(buffer, encoding="utf-8", newline="")

        chunk.to_csv(text_wrapper, index=False, header=(i == 0), lineterminator='\n')
        text_wrapper.flush()
        buffer.seek(0)

        yield buffer.read()

        buffer.close()
        text_wrapper.close()
