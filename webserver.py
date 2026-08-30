from flask import Flask, request, jsonify
import asyncio
from payu import PayUProcessor, proxy_rotator

app = Flask(__name__)

@app.route('/pay', methods=['POST'])
def handle_payment():
    """
    Expects JSON: { "card": "number|mm|yy|cvv" }
    Returns payment result.
    """
    data = request.get_json()
    if not data or 'card' not in data:
        return jsonify({"error": "Missing 'card' field"}), 400

    card_input = data['card'].strip()
    if not card_input:
        return jsonify({"error": "Card field is empty"}), 400

    proxy_info = proxy_rotator.get_next()
    processor = PayUProcessor(proxy_info=proxy_info)

    try:
        result = asyncio.run(processor.process(card_input))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "PayU API"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
