import os
import requests
import logging
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("SignalWireService")

PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
API_TOKEN  = os.getenv("SIGNALWIRE_API_TOKEN")
SPACE_URL  = os.getenv("SIGNALWIRE_SPACE_URL")  # e.g. myspace.signalwire.com

# ── Native Relay REST API (recommended, not compat API) ──────────────────────
RELAY_BASE = f"https://{SPACE_URL}/api/relay/rest"

# ── Compat API (kept for purchase + webhook config) ──────────────────────────
COMPAT_BASE = f"https://{SPACE_URL}/api/laml/2010-04-01/Accounts/{PROJECT_ID}"

TOLL_FREE_PREFIXES = {"800", "888", "877", "866", "855", "844", "833", "822"}


def _auth() -> tuple:
    """Return (project_id, api_token) for HTTPBasicAuth."""
    return (PROJECT_ID, API_TOKEN)


def search_available_numbers(area_code: str = None, limit: int = 20):
    """
    Search available inbound phone numbers using the SignalWire Relay REST API.
    Endpoint: GET /api/relay/rest/phone_numbers/search
    Docs: https://developer.signalwire.com/apis/reference/list_available_numbers
    """
    if not PROJECT_ID or not API_TOKEN or not SPACE_URL:
        raise ValueError("SignalWire env vars are not configured (SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN, SIGNALWIRE_SPACE_URL)")

    # Determine number type
    number_type = "toll-free" if area_code in TOLL_FREE_PREFIXES else "local"

    url = f"{RELAY_BASE}/phone_numbers/search"
    params: dict = {"number_type": number_type, "limit": limit}
    if area_code:
        params["areacode"] = area_code

    try:
        logger.info(f"Searching SignalWire numbers | url={url} | params={params}")
        resp = requests.get(url, auth=_auth(), params=params, timeout=15)
        logger.info(f"SignalWire response status: {resp.status_code}")

        if not resp.ok:
            logger.error(f"SignalWire search error {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        data = resp.json()
        logger.debug(f"SignalWire raw response keys: {list(data.keys())}")

        # The Relay REST API returns { "data": [ { "e164": "+12025551234", ... } ] }
        numbers = data.get("data", [])
        results = []
        for num in numbers[:limit]:
            results.append({
                "phone_number":  num.get("e164") or num.get("number") or num.get("phone_number", ""),
                "friendly_name": num.get("name") or num.get("friendly_name") or num.get("e164", ""),
                "locality":      num.get("rate_center", ""),
                "region":        num.get("state") or num.get("region", ""),
                "monthly_cost":  1.00,
                "capabilities":  num.get("call_handling_enabled", True),
            })
        logger.info(f"Found {len(results)} available numbers")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"SignalWire search request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        raise


def purchase_number(phone_number: str):
    """
    Purchase a phone number using the SignalWire Relay REST API.
    Endpoint: POST /api/relay/rest/phone_numbers
    """
    url = f"{RELAY_BASE}/phone_numbers"
    payload = {"number": phone_number}

    try:
        logger.info(f"Purchasing SignalWire number: {phone_number}")
        resp = requests.post(url, auth=_auth(), json=payload, timeout=20)
        if not resp.ok:
            logger.error(f"Purchase error {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        result = resp.json()
        # Relay REST returns { "id": "uuid", "number": "+12025551234", ... }
        return {
            "sid":          result.get("id"),
            "phone_number": result.get("number") or result.get("e164") or phone_number,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"SignalWire purchase failed for {phone_number}: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        raise


def configure_number_webhook(phone_number_id: str, webhook_url: str):
    """
    Set the voice webhook for a purchased number.
    Endpoint: PUT /api/relay/rest/phone_numbers/{id}
    """
    url = f"{RELAY_BASE}/phone_numbers/{phone_number_id}"
    payload = {
        "call_handler": "laml_webhooks",
        "call_receive_mode": "voice",
        "call_laml_url": webhook_url,
    }

    try:
        logger.info(f"Configuring webhook for number id={phone_number_id}: {webhook_url}")
        resp = requests.put(url, auth=_auth(), json=payload, timeout=15)
        if not resp.ok:
            logger.error(f"Webhook config error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"SignalWire webhook config failed for {phone_number_id}: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        raise
