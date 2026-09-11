"""
Flask Backend Web API Server for Autonomous Twitter Support Agent (AmazonHelp).
Provides REST API endpoints for real-time customer query inference, benchmark metrics,
judge calibration stats, sample test scenarios, and health checks.
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify

try:
    from flask_cors import CORS
    has_cors = True
except ImportError:
    has_cors = False

# Resolve paths so backend modules and project root are cleanly in sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SupportAgentPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_DIST = os.path.abspath(os.path.join(PROJECT_ROOT, "frontend", "dist"))
if os.path.exists(FRONTEND_DIST):
    app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="")
else:
    app = Flask(__name__)

if has_cors:
    CORS(app)
else:
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        return response

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not Found"}), 404
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, path)) and path != "":
        return app.send_static_file(path)
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, "index.html")):
        return app.send_static_file("index.html")
    return jsonify({
        "status": "healthy",
        "service": "AmazonHelp AI Support Agent Backend",
        "version": "1.0.0"
    })


# Lazy initialization of Support Agent Pipeline
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        logger.info("Initializing Support Agent Pipeline...")
        pipeline_instance = SupportAgentPipeline()
        logger.info("Support Agent Pipeline initialized successfully.")
    return pipeline_instance

# Load benchmark metrics if available
def load_json_file(relative_path):
    possible_paths = [
        os.path.join(PROJECT_ROOT, relative_path),
        os.path.join(BACKEND_DIR, relative_path),
        os.path.join(os.getcwd(), relative_path)
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading {path}: {e}")
    return {}

SAMPLE_SCENARIOS = [
    {
        "id": "order_delay",
        "title": "Delayed Delivery Tracking",
        "intent": "order_status_delivery",
        "text": "Where is my package? The tracking has been stuck on carrier facility for 3 days!",
        "thread_length": 1,
        "badge": "Standard Query",
        "category": "Shipping & Delivery"
    },
    {
        "id": "refund_delay",
        "title": "Missing Refund Request",
        "intent": "refund_return",
        "text": "I returned my item 2 weeks ago via UPS drop-off and still haven't received my refund!",
        "thread_length": 1,
        "badge": "Standard Query",
        "category": "Returns & Refunds"
    },
    {
        "id": "double_charge",
        "title": "Double Charge Dispute",
        "intent": "billing_dispute",
        "text": "You charged my credit card twice for order #112-98421! Please issue a refund immediately.",
        "thread_length": 1,
        "badge": "Billing Issue",
        "category": "Payments & Billing"
    },
    {
        "id": "account_lockout",
        "title": "Account 2FA Lockout",
        "intent": "account_access",
        "text": "I am locked out of my Amazon account and not receiving the 2FA verification code on my phone.",
        "thread_length": 1,
        "badge": "Security Alert",
        "category": "Account Access"
    },
    {
        "id": "shattered_item",
        "title": "Damaged Product Delivered",
        "intent": "product_issue",
        "text": "The box arrived today but the glass blender inside was completely shattered. I need a replacement!",
        "thread_length": 1,
        "badge": "Product Damage",
        "category": "Product & Quality"
    },
    {
        "id": "cart_bug",
        "title": "Checkout Server 500 Error",
        "intent": "app_website_bug",
        "text": "Every time I click Place Order on the iOS app, it throws HTTP 500 server error. Is the site down?",
        "thread_length": 1,
        "badge": "Technical Bug",
        "category": "Tech & Platform"
    },
    {
        "id": "cancel_prime",
        "title": "Cancel Prime Membership",
        "intent": "cancellation",
        "text": "Please cancel my Prime membership immediately before the renewal fee charges tomorrow.",
        "thread_length": 1,
        "badge": "Subscription",
        "category": "Membership"
    },
    {
        "id": "general_complaint",
        "title": "Angry General Complaint",
        "intent": "general_complaint_vent",
        "text": "Your customer service is the absolute worst service I have ever experienced in my life!",
        "thread_length": 1,
        "badge": "Frustration",
        "category": "Customer Sentiment"
    },
    {
        "id": "legal_threat_escalation",
        "title": "Legal Action Safety Escalation",
        "intent": "billing_dispute",
        "text": "I am contacting my attorney and filing a lawsuit against Amazon for fraudulent charges!",
        "thread_length": 1,
        "badge": "Human Escalation Policy",
        "category": "High Risk & Safety"
    },
    {
        "id": "multi_turn_escalation",
        "title": "Multi-turn Thread Fatigue",
        "intent": "order_status_delivery",
        "text": "Still no response to my last 3 tweets! Why is no one resolving my order issue?!",
        "thread_length": 4,
        "badge": "Thread Escalation",
        "category": "High Risk & Safety"
    }
]

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "AmazonHelp AI Support Agent Backend",
        "version": "1.0.0"
    })

@app.route("/api/process", methods=["POST"])
def process_message():
    """Processes a customer tweet message through the end-to-end support pipeline."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    thread_length = int(data.get("thread_length", 1))

    if not text:
        return jsonify({"error": "Message text is required."}), 400

    try:
        agent = get_pipeline()
        result = agent.handle_message(text, thread_length=thread_length)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns stored benchmark evaluation metrics across baselines and full system."""
    metrics_data = load_json_file(os.path.join("results", "metrics_summary.json"))
    return jsonify({
        "status": "success",
        "metrics": metrics_data
    })

@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Returns preset test scenarios."""
    return jsonify({
        "status": "success",
        "samples": SAMPLE_SCENARIOS
    })

@app.route("/api/eval", methods=["GET"])
def get_eval_details():
    """Returns detailed evaluation and judge calibration statistics."""
    metrics_data = load_json_file(os.path.join("results", "metrics_summary.json"))
    calibration_data = load_json_file(os.path.join("results", "judge_vs_human_agreement.json"))
    return jsonify({
        "status": "success",
        "metrics": metrics_data,
        "calibration": calibration_data
    })

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  AmazonHelp AI Support Agent - Flask API Server")
    print(f"  Running on: http://{host}:{port}")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=False)
