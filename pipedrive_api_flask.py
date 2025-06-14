from flask import Flask, request, jsonify
import requests
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
PIPEDRIVE_BASE_URL = 'https://api.pipedrive.com/v1'

def get_deals(query):
    try:
        url = f"{PIPEDRIVE_BASE_URL}/deals/search"
        params = {
            'term': query,
            'api_token': PIPEDRIVE_API_TOKEN
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('items', [])
    except Exception as e:
        app.logger.exception("Error fetching deals from Pipedrive")
        return []

@app.route('/lookup', methods=['GET'])
def lookup():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    deals = get_deals(query)
    if not deals:
        return jsonify({'error': 'No deals found'}), 404

    results = []
    for item in deals:
        deal = item.get('item', {})
        results.append({
            'id': deal.get('id'),
            'title': deal.get('title'),
            'person_name': deal.get('person', {}).get('name'),
            'owner_name': deal.get('owner_name')
        })

    return jsonify(results)

@app.route('/find_person', methods=['GET'])
def find_person():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        people_url = f"{PIPEDRIVE_BASE_URL}/persons/search"
        params = {
            'term': query,
            'fields': 'phone,email,name',
            'api_token': PIPEDRIVE_API_TOKEN
        }
        response = requests.get(people_url, params=params)
        response.raise_for_status()
        people = response.json().get('data', {}).get('items', [])

        if not people:
            return jsonify({'error': 'No matching person found'}), 404

        results = []

        for person in people:
            person_data = person.get('item', {})
            person_id = person_data.get('id')
            person_name = person_data.get('name')

            deals_url = f"{PIPEDRIVE_BASE_URL}/persons/{person_id}/deals"
            deal_resp = requests.get(deals_url, params={'api_token': PIPEDRIVE_API_TOKEN})
            deal_resp.raise_for_status()
            deals = deal_resp.json().get('data') or []

            deal_list = []
            for deal in deals:
                deal_list.append({
                    'deal_id': deal.get('id'),
                    'title': deal.get('title'),
                    'owner_name': deal.get('owner_name')
                })

            results.append({
                'person_name': person_name,
                'deals': deal_list
            })

        return jsonify(results)

    except Exception as e:
        app.logger.exception("Error searching for person and their deals")
        return jsonify({'error': 'Server error'}), 500

@app.route('/jenny', methods=['GET'])
def jenny_lookup():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'response': 'I need a name, phone number, or address to look someone up.'}), 400

    try:
        url = f"https://jenny-flask-api.onrender.com/find_person?q={query}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            return jsonify({'response': f"Sorry, I couldn’t find anyone matching '{query}'."})

        replies = []
        for entry in data:
            person = entry.get("person_name")
            deals = entry.get("deals", [])
            if deals:
                for d in deals:
                    replies.append(f"{person} has a deal titled '{d['title']}' managed by {d['owner_name']}.")
            else:
                replies.append(f"{person} is in our system, but they don’t currently have any active deals.")

        return jsonify({'response': "\n".join(replies)})

    except Exception as e:
        app.logger.exception("Jenny lookup failed")
        return jsonify({'response': "Something went wrong while checking the system. Please try again."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
