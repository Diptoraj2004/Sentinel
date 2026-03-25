"""
SentinLLM - Main API Gateway
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time

# Importing the modular components
from schemas import ChatRequest, SecurityLog
from judge import classify_prompt
from Redactor import redact_pii
from router import forward_to_llm

app = FastAPI(
    title="SentinLLM AI Firewall",
    description="A kernel-level security gateway for Large Language Models.",
    version="1.0.0"
)

# - MIDDLEWARE: TokenThrottle Rate Limiter -
memory_db = {}
MAX_TOKENS = 5
REFILL_TIME_SECONDS = 10

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_host = request.client.host
    current_time = time.time()
    
    if client_host not in memory_db:
        memory_db[client_host] = {"tokens": MAX_TOKENS, "time": current_time}
    else:
        time_passed = current_time - memory_db[client_host]["time"]
        if time_passed > REFILL_TIME_SECONDS:
            memory_db[client_host]["tokens"] = MAX_TOKENS

    if memory_db[client_host]["tokens"] > 0:
        memory_db[client_host]["tokens"] -= 1
        memory_db[client_host]["time"] = current_time
        return await call_next(request)
    else:
        return JSONResponse(
            status_code=429, 
            content={"error": "Too Many Requests. Rate Limiter blocked your IP."}
        )

# - CORE GATEWAY ENDPOINT -
@app.post("/v1/chat/completions")
async def secure_chat(request: ChatRequest):
    """
    The main integration pipeline: Receives JSON -> Judges Intent -> Redacts PII -> Forwards to LLM.
    """
    # 1. Extract the user's latest message
    # (Assuming the last message in the array is the current prompt)
    user_message = request.messages[-1].content

    # 2. Enforcement
    classification = classify_prompt(user_message)
    if classification in ["Jailbreak", "Toxic", "Malware_Generation"]:
        # Block the request immediately
        return JSONResponse(
            status_code=403, 
            content={"error": f"SentinLLM Firewall Blocked Request. Reason: {classification}"}
        )

    # 3. Extraction/Redaction
    sanitized_text = redact_pii(user_message)
    
    # Replace the unsafe text with the sanitized text in the payload
    request.messages[-1].content = sanitized_text
    payload_dict = request.model_dump() # Using Pydantic V2 syntax

    # 4. Relay
    try:
        llm_response = await forward_to_llm(payload_dict)
        return llm_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upstream Error: {str(e)}")

    # 5. Archiving (Database - Coming Soon)
    # TODO: Log the 'classification' and 'sanitized_text' via database file

@app.get("/")
async def health_check():
    return {"status": "Active", "message": "SentinLLM Firewall is online."}