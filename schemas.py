from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class ChatMessage(BaseModel): #chat request(this is the input layer)
role: str = Field(..., description="The role of the message author (e.g., 'user', 'assistant', 'system').")
    content: str = Field(..., description="The actual text content of the message.")

class ChatRequest(BaseModel):
    model: str = Field(default="sentin-llm-v1", description="The ID of the model to use.")
    messages: List[ChatMessage] = Field(..., min_items=1, description="A list of messages comprising the conversation so far.")
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user.")
    temperature: Optional[float] = Field(0.7, ge=0, le=2.0)

class SecurityLog(BaseModel): #The Security Log(Storage Layer)
    request_id: str = Field(..., description="Unique ID for the intercepted request.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    original_prompt: str = Field(..., description="The raw prompt before redaction.")
    classification: str = Field(..., description="Classification from the Judge Agent (e.g., 'Safe', 'Jailbreak').")
    pii_detected: bool = Field(default=False)
    redacted_content: Optional[str] = Field(None, description="The version of the prompt with PII placeholders.")
    is_blocked: bool = Field(..., description="Whether the request was blocked by the firewall.")
    security_tag: str = Field(default="General Log", description="Tag such as 'Attempted Attack' for blocked requests.")

