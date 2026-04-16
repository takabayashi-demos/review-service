# review-service

Product reviews and ratings service for the Walmart platform. Owned by the **Social & Reviews** team.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Health Checks](#health-checks)
- [Metrics](#metrics)

## Overview

This service manages product reviews and ratings. It exposes a REST API for creating and retrieving reviews, computing aggregate statistics, and serving Prometheus-compatible metrics.

**Tech stack:** Python 3.11+ / Flask

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Local Development

```bash
# Install dependencies
pip install flask

# Start the service
python app.py
```

The service starts on port `5000` by default. Override with the `PORT` environment variable:

```bash
PORT=8080 python app.py
```

### Docker

```bash
docker build -t review-service .
docker run -p 5000:5000 review-service
```

## API Reference

### Get Reviews for a Product

```
GET /api/v1/reviews/:product_id
```

Returns all reviews for a given product, along with the average rating.

**Example:**

```bash
curl http://localhost:5000/api/v1/reviews/P001
```

**Response (200):**

```json
{
  "product_id": "P001",
  "reviews": [
    {
      "id": "REV-001",
      "product_id": "P001",
      "user_id": "USR-001",
      "rating": 5,
      "title": "Amazing TV!",
      "body": "Best 4K TV I've ever owned. Picture quality is stunning.",
      "verified_purchase": true,
      "helpful_votes": 42,
      "created_at": "2024-11-15"
    }
  ],
  "average_rating": 4.5,
  "total": 2
}
```

If no reviews exist for the product, returns an empty list with `average_rating: 0`.

### Create a Review

```
POST /api/v1/reviews
Content-Type: application/json
```

**Request body:**

| Field        | Type    | Required | Description                  |
|-------------|---------|----------|------------------------------|
| `product_id` | string  | yes      | Product identifier           |
| `rating`     | integer | yes      | Rating value (1-5)           |
| `title`      | string  | no       | Review headline              |
| `body`       | string  | no       | Review text                  |
| `user_id`    | string  | no       | Defaults to `"anonymous"`    |

**Example:**

```bash
curl -X POST http://localhost:5000/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "P001",
    "rating": 4,
    "title": "Solid purchase",
    "body": "Good value for the price.",
    "user_id": "USR-100"
  }'
```

**Response (201):**

```json
{
  "id": "REV-005",
  "product_id": "P001",
  "user_id": "USR-100",
  "rating": 4,
  "title": "Solid purchase",
  "body": "Good value for the price.",
  "verified_purchase": false,
  "helpful_votes": 0,
  "created_at": "2025-04-15"
}
```

### Get Review Statistics

```
GET /api/v1/reviews/stats
```

Returns aggregate statistics across all products.

**Example:**

```bash
curl http://localhost:5000/api/v1/reviews/stats
```

**Response (200):**

```json
{
  "total_reviews": 4,
  "products_reviewed": 3,
  "average_rating": 4.8,
  "rating_distribution": {
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 1,
    "5": 3
  }
}
```

## Configuration

| Variable | Default | Description             |
|----------|---------|-------------------------|
| `PORT`   | `5000`  | HTTP listen port        |

## Health Checks

| Endpoint  | Purpose                        |
|-----------|--------------------------------|
| `/health` | Liveness probe (always `UP`)   |
| `/ready`  | Readiness probe                |

Both return JSON with a `status` field. Used by Kubernetes liveness and readiness probes.

## Metrics

```
GET /metrics
```

Returns Prometheus-compatible metrics including total review count, average ratings, and per-product breakdowns.
