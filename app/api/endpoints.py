import uuid
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from app.database import get_db
from app.models import User, Organization, Agent, Call, Transcript, Plan
from app.api.schemas import (
    UserCreate, UserResponse, Token, AgentCreate, AgentUpdate, AgentResponse,
    CallResponse, TranscriptResponse
)
from app.core.security import (
    hash_password, verify_password, create_access_token, get_current_user_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# Dependency to get the current authenticated user object
async def get_current_user(
    email: str = Depends(get_current_user_email), db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --- Authentication Endpoints ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        # Create a default organization for the new user
        default_org_name = f"{user_data.first_name or user_data.email.split('@')[0]}'s Organization"
        default_org_slug = f"{user_data.email.split('@')[0]}-{uuid.uuid4().hex[:6]}"
        
        # Ensure a default plan exists or create one
        default_plan = db.query(Plan).filter(Plan.name == "Free Tier").first()
        if not default_plan:
            default_plan = Plan(name="Free Tier", description="Default free plan", price_monthly=0.00)
            db.add(default_plan)
            db.commit()
            db.refresh(default_plan)

        organization = Organization(name=default_org_name, slug=default_org_slug, plan_id=default_plan.id)
        db.add(organization)
        db.commit()
        db.refresh(organization)

        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            organization_id=organization.id,
            role="admin" # First user of an organization is an admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug or email already exists (race condition)")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register user: {e}")


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Agent Endpoints ---
@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = Agent(
        **agent_data.model_dump(exclude_unset=True),
        organization_id=current_user.organization_id
    )
    db.add(agent)
    try:
        db.commit()
        db.refresh(agent)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent with this phone number already exists.")
    return agent

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agents = db.query(Agent).filter(Agent.organization_id == current_user.organization_id).all()
    return agents

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    for field, value in agent_data.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    
    db.add(agent)
    try:
        db.commit()
        db.refresh(agent)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent with this phone number already exists.")
    return agent

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Call Endpoints ---
@router.get("/calls", response_model=List[CallResponse])
async def list_calls(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    calls = db.query(Call).filter(Call.organization_id == current_user.organization_id).all()
    return calls

@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call_details(
    call_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.organization_id == current_user.organization_id
    ).first()
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return call

# --- Dashboard Stats Endpoint ---
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Total calls for the user's organization
    total_calls = db.query(Call).filter(Call.organization_id == current_user.organization_id).count()
    
    # Active agents count
    active_agents = db.query(Agent).filter(
        Agent.organization_id == current_user.organization_id,
        Agent.is_active == True
    ).count()
    
    # Success rate (calls with status 'completed')
    completed_calls = db.query(Call).filter(
        Call.organization_id == current_user.organization_id,
        Call.status == 'completed'
    ).count()
    
    success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    
    # Recent calls
    recent_calls = db.query(Call).filter(
        Call.organization_id == current_user.organization_id
    ).order_by(Call.start_time.desc()).limit(5).all()
    
    # Placeholder for chart data
    chart_data = [
        {"month": "Jan", "calls": 0},
        {"month": "Feb", "calls": 0},
        {"month": "Mar", "calls": 0},
        {"month": "Apr", "calls": 0},
        {"month": "May", "calls": 0},
        {"month": "Jun", "calls": 0},
        {"month": "Jul", "calls": total_calls}
    ]

    # Active calls (currently in progress)
    active_calls = db.query(Call).filter(
        Call.organization_id == current_user.organization_id,
        Call.status == 'in_progress'
    ).count()

    # Calculate average call duration for completed calls
    avg_duration_result = db.query(func.avg(Call.duration_seconds)).filter(
        Call.organization_id == current_user.organization_id,
        Call.status == 'completed',
        Call.duration_seconds.isnot(None)
    ).scalar()
    
    avg_duration_seconds = int(avg_duration_result) if avg_duration_result else 0
    minutes = avg_duration_seconds // 60
    seconds = avg_duration_seconds % 60
    avg_call_duration = f"{minutes}:{seconds:02d}"

    return {
        "totalCalls": total_calls,
        "successRate": round(success_rate, 1),
        "avgCallDuration": avg_call_duration,
        "activeCalls": active_calls,
        "activeAgents": active_agents,
        "recentCalls": recent_calls,
        "monthlyCallVolume": chart_data
    }

# --- Billing and Phone Number Endpoints ---
from app.services.signalwire import search_available_numbers
from app.services.stripe_service import create_checkout_session, handle_stripe_webhook

@router.get("/phone-numbers/search")
async def search_numbers(area_code: Optional[str] = None):
    try:
        numbers = search_available_numbers(area_code=area_code)
        return numbers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class CheckoutRequest(BaseModel):
    agent_id: str
    phone_number: str

@router.post("/billing/create-checkout-session")
async def create_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        result = create_checkout_session(agent_id=req.agent_id, phone_number=req.phone_number, user_email=current_user.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")
    return handle_stripe_webhook(payload, sig_header)
