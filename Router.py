import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="SentinLLM API Gateway")

# Define the expected request structure
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7

# Asynchronous function to forward the prompt to the dummy LLM
async def forward_to_llm(payload: dict):
    """
    Forwards the processed prompt to a dummy upstream LLM provider.
    """
    dummy_upstream_url = "https://api.dummy-llm-provider.com/v1/chat/completions"
    headers = {"Authorization": "Bearer YOUR_DUMMY_API_KEY"}

    async with httpx.AsyncClient() as client:
        try:
            # Forward the request asynchronously
            response = await client.post(
                dummy_upstream_url, 
                json=payload, 
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Upstream LLM Error")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Could not connect to LLM provider")

@app.post("/v1/chat/completions")
async def chat_endpoint(request: ChatCompletionRequest):
    """
    Endpoint that receives user messages, (would typically run security checks here),
    and then forwards them to the LLM.
    """
    # Convert Pydantic model to dictionary for the upstream call
    payload = request.dict()
    
    # Forward to the dummy upstream LLM
    llm_response = await forward_to_llm(payload)
    
    return llm_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
