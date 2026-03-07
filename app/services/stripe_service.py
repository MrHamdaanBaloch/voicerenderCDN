import os
import stripe
import logging
from fastapi import HTTPException
from app.services.signalwire import purchase_number, configure_number_webhook
from app.database import SessionLocal
from app.models import Agent, Organization, PhoneNumber

logger = logging.getLogger("StripeService")

# Configuration
stripe.api_key = os.getenv("STRIPE_API_KEY", "sk_test_dummy")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
STRIPE_PHONE_NUMBER_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_dummy") # The $5/month product ID
FRONTEND_URL = os.getenv("PUBLIC_URL_BASE", "http://localhost:3000")

def create_checkout_session(org_id: str, phone_number: str, user_email: str, agent_id: str = None):
    """
    Creates a Stripe Checkout Session to subscribe to a phone number.
    Stores the org_id, agent_id (optional), and phone_number in metadata so the webhook knows what to provision.
    """
    try:
        success_url = f"{FRONTEND_URL}/dashboard/phone-numbers?checkout_success=true&phone_number={phone_number}"
        if agent_id:
            success_url = f"{FRONTEND_URL}/dashboard/agents?checkout_success=true&agent_id={agent_id}"

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price': STRIPE_PHONE_NUMBER_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{FRONTEND_URL}/dashboard/agents?checkout_success=true&agent_id={agent_id}",
            cancel_url=f"{FRONTEND_URL}/dashboard/phone-numbers?checkout_cancelled=true",
            metadata={
                "org_id": str(org_id),
                "agent_id": str(agent_id) if agent_id else "",
                "phone_number": phone_number,
                "type": "phone_number_subscription"
            }
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_wallet_recharge_session(org_id: str, amount_usd: int, user_email: str):
    """
    Creates a Stripe Checkout Session to recharge the prepaid wallet.
    amount_usd should be the whole dollar amount (e.g., 5, 10, 50).
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'VoiceRender AI Prepaid Compute (${amount_usd})',
                        'description': 'Funds used for $0.03/min inbound call processing.'
                    },
                    'unit_amount': amount_usd * 100, # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{FRONTEND_URL}/dashboard/settings?recharge_success=true&amount={amount_usd}",
            cancel_url=f"{FRONTEND_URL}/dashboard/settings?recharge_cancelled=true",
            metadata={
                "org_id": str(org_id),
                "amount_usd": str(amount_usd),
                "type": "wallet_recharge"
            }
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Failed to create wallet recharge session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def handle_stripe_webhook(payload: bytes, sig_header: str):
    """
    Handles incoming Stripe Webhooks, verifies signature, and provisions the phone number if payment succeeds.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle successful checkout
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Check if this is a phone number purchase
        metadata = session.get("metadata", {})
        if metadata.get("type") == "phone_number_subscription":
            phone_number = metadata.get("phone_number")
            agent_id = metadata.get("agent_id")
            org_id = metadata.get("org_id")
            
            logger.info(f"Checkout completed for {phone_number} on Org {org_id}. Provisioning via SignalWire...")
            
            try:
                # 1. Buy the number on SignalWire
                sw_result = purchase_number(phone_number)
                sid = sw_result.get("sid")
                
                # 2. Configure the webhook to point to our app
                clean_url = os.getenv("RENDER_EXTERNAL_URL", "").replace('http://', 'https://')
                webhook_url = f"{clean_url}/incoming_call" 
                configure_number_webhook(sid, webhook_url)
                
                # 3. Update the Database
                db = SessionLocal()
                # Create PhoneNumber record
                new_num = PhoneNumber(
                    organization_id=org_id,
                    phone_number=phone_number,
                    provider="signalwire"
                )
                db.add(new_num)
                
                # If agent_id was provided (from legacy flow), update the agent too
                if agent_id:
                    agent = db.query(Agent).filter(Agent.id == agent_id).first()
                    if agent:
                        agent.signalwire_phone_number = phone_number
                
                db.commit()
                db.close()
                
                logger.info(f"Successfully provisioned and attached {phone_number}.")
            except Exception as e:
                logger.error(f"Provisioning failed after successful payment: {e}")
                # In a real production app, you might want to queue a retry or notify an admin here.

        elif metadata.get("type") == "wallet_recharge":
            org_id = metadata.get("org_id")
            amount_usd = int(metadata.get("amount_usd", 0))
            
            # $0.03 per minute = $0.0005 per second. amount_usd / 0.03 * 60 = seconds
            seconds_to_add = int((amount_usd / 0.03) * 60)
            
            logger.info(f"Recharge completed for org {org_id}. Adding {seconds_to_add} seconds for ${amount_usd}.")
            
            try:
                db = SessionLocal()
                org = db.query(Organization).filter(Organization.id == org_id).first()
                if org:
                    org.balance_seconds = org.balance_seconds + seconds_to_add
                    db.commit()
                db.close()
                logger.info(f"Successfully recharged wallet for org {org_id}.")
            except Exception as e:
                logger.error(f"Wallet recharge failed after successful payment: {e}")

    return {"status": "success"}
