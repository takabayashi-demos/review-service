"""Review Service - Walmart Platform
Product reviews and ratings service.

INTENTIONAL ISSUES (for demo):
- XSS vulnerability in review text (vulnerability)
- No input length validation (bug)
- Unescaped HTML output (vulnerability)
"""
from flask import Flask, request, jsonify
import os, time, random, logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("review-service")

reviews_db = {
    "P001": [
        {"id": "REV-001", "product_id": "P001", "user_id": "USR-001", "rating": 5, "title": "Amazing TV!", "body": "Best 4K TV I've ever owned. Picture quality is stunning.", "verified_purchase": True, "helpful_votes": 42, "created_at": "2024-11-15"},
        {"id": "REV-002", "product_id": "P001", "user_id": "USR-003", "rating": 4, "title": "Great but pricey", "body": "Excellent picture but wish it was a bit cheaper.", "verified_purchase": True, "helpful_votes": 18, "created_at": "2024-11-20"},
    ],
    "P002": [
        {"id": "REV-003", "product_id": "P002", "user_id": "USR-002", "rating": 5, "title": "Best phone ever", "body": "The camera is incredible. Worth every penny.", "verified_purchase": True, "helpful_votes": 156, "created_at": "2024-10-05"},
    ],
    "P004": [
        {"id": "REV-004", "product_id": "P004", "user_id": "USR-004", "rating": 5, "title": "Kitchen essential", "body": "Makes baking so much easier. Built like a tank.", "verified_purchase": True, "helpful_votes": 89, "created_at": "2024-09-12"},
    ],
}

review_counter = 4

@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "review-service", "version": "1.4.2"})

@app.route("/ready")
def ready():
    return jsonify({"status": "READY"})

@app.route("/api/v1/reviews/<product_id>")
def get_reviews(product_id):
    product_reviews = reviews_db.get(product_id, [])
    if not product_reviews:
        return jsonify({"product_id": product_id, "reviews": [], "average_rating": 0, "total": 0})

    avg = sum(r["rating"] for r in product_reviews) / len(product_reviews)
    return jsonify({
        "product_id": product_id,
        "reviews": product_reviews,
        "average_rating": round(avg, 1),
        "total": len(product_reviews),
    })

@app.route("/api/v1/reviews", methods=["POST"])
def create_review():
    global review_counter
    data = request.get_json() or {}

    product_id = data.get("product_id")
    rating = data.get("rating")
    title = data.get("title", "")
    body = data.get("body", "")

    # ❌ VULNERABILITY: No XSS sanitization on user input
    # body could contain: <script>alert('xss')</script>

    # ❌ BUG: No validation on rating range
    # Could submit rating: 999 or rating: -5

    # ❌ BUG: No input length validation
    # Title and body could be megabytes long

    review_counter += 1
    review = {
        "id": f"REV-{review_counter:03d}",
        "product_id": product_id,
        "user_id": data.get("user_id", "anonymous"),
        "rating": rating,
        "title": title,
        "body": body,  # ❌ Stored unsanitized
        "verified_purchase": False,
        "helpful_votes": 0,
        "created_at": time.strftime("%Y-%m-%d"),
    }

    if product_id not in reviews_db:
        reviews_db[product_id] = []
    reviews_db[product_id].append(review)

    return jsonify(review), 201

@app.route("/api/v1/reviews/stats")
def review_stats():
    total_reviews = sum(len(reviews) for reviews in reviews_db.values())
    products_reviewed = len(reviews_db)
    all_ratings = [r["rating"] for reviews in reviews_db.values() for r in reviews]
    avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0

    return jsonify({
        "total_reviews": total_reviews,
        "products_reviewed": products_reviewed,
        "average_rating": round(avg_rating, 1),
        "rating_distribution": {
            str(i): len([r for r in all_ratings if r == i]) for i in range(1, 6)
        },
    })

@app.route("/metrics")
def metrics():
    total = sum(len(r) for r in reviews_db.values())
    return f"""# HELP reviews_total Total reviews stored
# TYPE reviews_total gauge
reviews_total {total}
# HELP review_service_up Service health
# TYPE review_service_up gauge
review_service_up 1
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
