from flask import Flask, jsonify
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID")
API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN")
SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL")


@app.route("/generate-token", methods=["GET"])
def generate_jwt():
    url = f"https://{SPACE_URL}/api/relay/rest/jwt"
    payload = {
        "resource": "myagent",
        "expires_in": 15
    }
    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(PROJECT_ID, API_TOKEN),
            json=payload
        )
        response.raise_for_status()
        token = response.json().get("jwt_token")
        return jsonify({"jwt": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)
