from fastapi.responses import StreamingResponse
import asyncio
import json

async def mock_token_stream(text: str):
    """Simulates token streaming for the UI."""
    for word in text.split():
        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        await asyncio.sleep(0.05)

def get_streaming_response(text: str):
    return StreamingResponse(mock_token_stream(text), media_type="text/event-stream")
