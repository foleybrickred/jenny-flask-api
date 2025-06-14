from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
API_TOKEN = os.getenv("API_TOKEN")
API_URL = "https://api.pipedrive.com/v1/deals/search"

@app.route("/lookup")
def lookup():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    params = {
        "term": query,
        "fields": "title,person_id,org_id,custom_fields",
        "api_token": API_TOKEN
    }
    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({
            "error": "Failed to fetch data from Pipedrive",
            "status_code": response.status_code,
            "details": response.text
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
