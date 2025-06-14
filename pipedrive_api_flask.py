from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PIPEDRIVE_API_TOKEN = 'd46e611c6a19504113d46bce437f69136c9eff7a'
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
        return data.get('data', {}).get('items', [])  # Always return a list
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
            'person_name': deal.get('person_name')
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
