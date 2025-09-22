import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# --- Agent Schemas ---
class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    llm_model: str = Field("llama3-8b-8192", max_length=50)
    tts_model: str = Field("playai-tts", max_length=50)
    tts_voice: str = Field("Fritz-PlayAI", max_length=50)
    deepgram_model: str = Field("nova-2-phonecall", max_length=50)
    system_prompt: str = Field(..., min_length=1, max_length=1000)
    deepgram_config: dict = Field(default_factory=lambda: {
        "utterance_end_ms": "1000",
        "endpointing": "1500",
        "filler_words": True
    })
    silence_timeout_seconds: int = Field(7, ge=1, le=60)
    silence_prompt_text: str = Field("Are you still there? How can I help?", max_length=200)
    is_active: bool = True
    signalwire_phone_number: Optional[str] = Field(None, max_length=20)

class AgentCreate(AgentBase):
    # organization_id will be set by the backend based on the authenticated user
    pass

class AgentUpdate(AgentBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    llm_model: Optional[str] = Field(None, max_length=50)
    tts_model: Optional[str] = Field(None, max_length=50)
    tts_voice: Optional[str] = Field(None, max_length=50)
    deepgram_model: Optional[str] = Field(None, max_length=50)
    system_prompt: Optional[str] = Field(None, min_length=1, max_length=1000)
    deepgram_config: Optional[dict] = None
    silence_timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    silence_prompt_text: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    signalwire_phone_number: Optional[str] = Field(None, max_length=20)


class AgentResponse(AgentBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # For SQLAlchemy ORM compatibility

# --- Transcript Schemas ---
class TranscriptResponse(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    speaker: str
    text: str
    timestamp: datetime
    duration: Optional[float] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

# --- Call Schemas ---
class CallResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    call_sid: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str
    transcript_url: Optional[str] = None
    audio_url: Optional[str] = None
    cost: Optional[float] = None
    call_metadata: dict

    transcripts: List[TranscriptResponse] = [] # Nested transcripts

    class Config:
        from_attributes = True

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    role: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
