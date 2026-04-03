from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import time

# --- Input Layer ---
class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message author.")
    content: str = Field(..., description="The actual text content.")

class ChatRequest(BaseModel):
    model: str = Field(default="sentin-llm-v1")
    messages: List[ChatMessage] = Field(..., min_items=1)
    user: Optional[str] = None
    temperature: Optional[float] = Field(0.7, ge=0, le=2.0)

# --- Storage Layer ---
class SecurityLog(BaseModel):
    request_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    original_prompt: str = Field(...)
    classification: str = Field(...)
    pii_detected: bool = Field(default=False)
    redacted_content: Optional[str] = None
    is_blocked: bool = Field(...)
    security_tag: str = Field(default="General Log")
    
    # We add latency as an optional field so we can save it to the DB
    latency_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

# --- Example of how to actually calculate it in your app ---
def process_request(user_input: ChatRequest):
    start_time = time.time()  # Start timer here, not in the class
    
    # ... logic for Judge Agent and Redaction ...
    end_time = time.time()
    total_latency = (end_time - start_time) * 1000 # Convert to ms for the PRD KPI
    
    # Create the log object
    log_entry = SecurityLog(
        request_id="req_123",
        original_prompt=user_input.messages[-1].content,
        classification="Safe",
        is_blocked=False,
        latency_ms=total_latency
    )
    
    print(f"Log captured with latency: {log_entry.latency_ms}ms")
    return log_entry
