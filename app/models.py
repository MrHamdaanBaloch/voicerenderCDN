import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_customer_id = Column(String, nullable=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    balance_seconds = Column(Integer, default=6000) # 100 Free Minutes (6000 seconds)

    users = relationship("User", back_populates="organization")
    agents = relationship("Agent", back_populates="organization")
    calls = relationship("Call", back_populates="organization")
    api_keys = relationship("APIKey", back_populates="organization")
    phone_numbers = relationship("PhoneNumber", back_populates="organization")
    plan = relationship("Plan", back_populates="organizations")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_annual = Column(Numeric(10, 2), nullable=True)
    features = Column(JSONB, nullable=False, default={}) # e.g., {"max_agents": 5, "max_calls_per_month": 1000}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizations = relationship("Organization", back_populates="plan")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="member") # e.g., "admin", "member", "billing"

    organization = relationship("Organization", back_populates="users")
    calls = relationship("Call", back_populates="user")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    llm_model = Column(String, default="llama3-8b-8192")
    tts_model = Column(String, default="playai-tts")
    tts_voice = Column(String, default="Fritz-PlayAI")
    deepgram_model = Column(String, default="nova-2-phonecall")
    system_prompt = Column(Text, nullable=False, default="You are a helpful, professional, and concise AI assistant. Respond naturally, like a human, keeping your responses under 20 words. Maintain a positive and engaging tone, and always strive to provide value to the user.")
    deepgram_config = Column(JSONB, nullable=False, default={
        "utterance_end_ms": "1000",
        "endpointing": "1500",
        "filler_words": True
    })
    silence_timeout_seconds = Column(Integer, default=7)
    silence_prompt_text = Column(String, default="Are you still there? How can I help?")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    signalwire_phone_number = Column(String, nullable=True, unique=True, index=True)

    organization = relationship("Organization", back_populates="agents")
    calls = relationship("Call", back_populates="agent")

class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Can be null if initiated via API key
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    call_sid = Column(String, unique=True, nullable=False, index=True) # SignalWire/Twilio Call SID
    from_number = Column(String, nullable=True)
    to_number = Column(String, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, default="in_progress") # e.g., "in_progress", "completed", "failed"
    transcript_url = Column(String, nullable=True) # S3 URL for full transcript
    audio_url = Column(String, nullable=True) # S3 URL for full audio recording
    cost = Column(Numeric(10, 4), nullable=True) # Calculated cost of the call
    call_metadata = Column(JSONB, nullable=False, default={}) # Additional call-specific data

    agent = relationship("Agent", back_populates="calls")
    user = relationship("User", back_populates="calls")
    organization = relationship("Organization", back_populates="calls")
    transcripts = relationship("Transcript", back_populates="call", order_by="Transcript.timestamp")

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    speaker = Column(String, nullable=False) # "user" or "agent"
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Numeric(5, 2), nullable=True) # Duration of this segment in seconds
    confidence = Column(Numeric(3, 2), nullable=True) # Deepgram confidence score

    call = relationship("Call", back_populates="transcripts")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    key_hash = Column(String, nullable=False, unique=True) # Hashed API key
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSONB, nullable=False, default=[]) # e.g., ["create_call", "read_calls"]

    organization = relationship("Organization", back_populates="api_keys")

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    phone_number = Column(String, nullable=False, unique=True, index=True) # E.g., "+18885551234"
    provider = Column(String, default="signalwire") # "signalwire" or "twilio"
    status = Column(String, default="active") # "active", "pending", "disabled"
    friendly_name = Column(String, nullable=True) # Optional user-assigned name
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="phone_numbers")
