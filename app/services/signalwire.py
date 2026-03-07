import os
import requests
import logging
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("SignalWireService")

# Configuration from environment variables
PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN")
SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL")

# Base URL for the Compatibility REST API
# The Compatibility API behaves similarly to Twilio's REST API
BASE_URL = f"https://{SPACE_URL}/api/laml/2010-04-01/Accounts/{PROJECT_ID}"

def _get_auth():
    return HTTPBasicAuth(PROJECT_ID, API_TOKEN)

def search_available_numbers(area_code: str = None, limit: int = 10):
    """
    Search for available local or toll-free US numbers.
    """
    endpoint = "Local"
    if area_code and area_code in ["800", "888", "877", "866", "855", "844", "833"]:
        endpoint = "TollFree"
        
    url = f"{BASE_URL}/AvailablePhoneNumbers/US/{endpoint}.json"
    params = {}
    if area_code:
        params["AreaCode"] = area_code
        
    try:
        response = requests.get(url, auth=_get_auth(), params=params)
        response.raise_for_status()
        data = response.json()
        
        # Return a list of available numbers
        available_numbers = data.get("available_phone_numbers", [])
        return [
            {
                "phone_number": num.get("phone_number"),
                "friendly_name": num.get("friendly_name"),
                "locality": num.get("locality"),
                "region": num.get("region"),
                "monthly_cost": 1.00 # Base cost on SignalWire
            }
            for num in available_numbers[:limit]
        ]
    except Exception as e:
        logger.error(f"Failed to search SignalWire numbers: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise

def purchase_number(phone_number: str):
    """
    Purchases a specific phone number on the master SignalWire account.
    """
    url = f"{BASE_URL}/IncomingPhoneNumbers.json"
    data = {
        "PhoneNumber": phone_number
    }
    
    try:
        response = requests.post(url, auth=_get_auth(), data=data)
        response.raise_for_status()
        result = response.json()
        return {
            "sid": result.get("sid"),
            "phone_number": result.get("phone_number")
        }
    except Exception as e:
        logger.error(f"Failed to purchase SignalWire number {phone_number}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise

def configure_number_webhook(phone_number_sid: str, webhook_url: str):
    """
    Updates the Voice URL (webhook) for a purchased SignalWire number.
    """
    url = f"{BASE_URL}/IncomingPhoneNumbers/{phone_number_sid}.json"
    data = {
        "VoiceUrl": webhook_url,
        "VoiceMethod": "POST"
    }
    
    try:
        response = requests.post(url, auth=_get_auth(), data=data)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to configure SignalWire number {phone_number_sid}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise
