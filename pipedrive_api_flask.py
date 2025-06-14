from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
API_TOKEN = os.getenv("API_TOKEN")
PERSON_SEARCH_URL = "https://api.pipedrive.com/v1/persons/search"
DEALS_BY_PERSON_URL = "https://api.pipedrive.com/v1/persons/{person_id}/deals"

@app.route("/lookup")
def lookup():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    # Step 1: Search for matching people
    person_params = {
        "term": query,
        "api_token": API_TOKEN
    }
    person_response = requests.get(PERSON_SEARCH_URL, params=person_params)
    if person_response.status_code != 200:
        return jsonify({"error": "Failed to search persons", "details": person_response.text}), 500

    people = person_response.json().get("data", {}).get("items", [])
    if not people:
        return jsonify({"message": "No matching contacts found."})

    all_deals = []

    # Step 2: For each person, get all deals (open, won, or lost)
    for person in people:
        person_id = person.get("item", {}).get("id")
        if not person_id:
            continue

        deals_params = {
            "api_token": API_TOKEN
        }
        deals_response = requests.get(DEALS_BY_PERSON_URL.format(person_id=person_id), params=deals_params)
        if deals_response.status_code != 200:
            continue

        deals = deals_response.json().get("data", [])
        for deal in deals:
            all_deals.append({
                "title": deal.get("title"),
                "person_name": deal.get("person_id", {}).get("name"),
                "status": deal.get("status"),
                "value": deal.get("value"),
                "custom_fields": deal
            })

    return jsonify({"deals": all_deals})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
