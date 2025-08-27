from flask import Flask, jsonify, request
from flask_cors import CORS
from utils.trends import fetch_trends


app = Flask(__name__)
CORS(app)  

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "FactSphere API is running"
    })

@app.route('/api/trends', methods=['GET'])
def get_trends():
    try:
        trends = fetch_trends()
        return jsonify({"success": True, "trends": trends})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)