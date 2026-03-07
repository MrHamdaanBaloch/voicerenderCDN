import os
from dotenv import load_dotenv
import requests

load_dotenv()
PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN")
SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL")

BASE_URL = f"https://{SPACE_URL}/api/laml/2010-04-01/Accounts/{PROJECT_ID}"

def test_search(params, endpoint="Local"):
    url = f"{BASE_URL}/AvailablePhoneNumbers/US/{endpoint}.json"
    print(f"Testing params: {params} on {url}")
    res = requests.get(url, auth=(PROJECT_ID, API_TOKEN), params=params)
    print("Status:", res.status_code)
    try:
        nums = res.json().get("available_phone_numbers", [])
        print("Count found:", len(nums))
        if nums:
            print("First number:", nums[0].get("phone_number"))
    except:
        print(res.text)
    print("-" * 20)

print("--- Testing SignalWire Search ---")
test_search({"AreaCode": "415"}, "Local")
test_search({"AreaCode": "888"}, "TollFree")
