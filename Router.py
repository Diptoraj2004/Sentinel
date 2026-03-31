import time
import httpx #supports async
from fastapi import HTTPException #fastapi tool to send error message
from schemas import ChatRequest #pydantic model that ensures correctly formatted payload(user data)

async def forward_to_llm(payload: ChatRequest): #asyn ->awaitable op
    url = "https://api.dummy-llm-provider.com/v1/chat/completions"
    headers = {"Authorization": "Bearer YOUR_DUMMY_API_KEY"} #replacing with env var later

    start_time = time.time()

    async with httpx.AsyncClient() as client: #ensures client session opens and closes, including error
        try:
            # Send request
            response = await client.post( #waits for LLM response
                url,
                json=payload.model_dump(), #pydantic obj -> Py dict
                headers=headers,
                timeout=10.0
            )

            latency = time.time() - start_time

            # Check status
            response.raise_for_status()
            return response.json(), latency #Success: LLM's ans

        except httpx.HTTPStatusError as e: # Upstream error ( LLM side error/Wrong API key)
            raise HTTPException(status_code=e.response.status_code, detail="Upstream LLM Error")

        except httpx.RequestError:  # Network Error(wrong Url etc.)
            raise HTTPException(status_code=500, detail="LLM Connection Failed")
