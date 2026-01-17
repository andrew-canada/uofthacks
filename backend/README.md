# AI Product Optimizer Backend

Flask-based backend for optimizing Shopify product listings using AI trend analysis.

## Features

- 🛍️ **Shopify Integration**: Fetch and update products via GraphQL API
- 🤖 **Gemini AI**: Analyze products against trends for marketing recommendations
- 📈 **Trend Analysis**: Match products to current fashion/style trends
- 🎬 **Video Analysis**: (Optional) Extract trends from videos using Twelve Labs
- 🔄 **LangGraph Ready**: Services designed for workflow orchestration

## Directory Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── .env.template          # Environment variables template
│
├── services/              # Business logic services
│   ├── shopify_auth.py    # Shopify OAuth handling
│   ├── product_service.py # Product CRUD operations
│   ├── trends_service.py  # Trend data management
│   ├── ai_optimizer.py    # Gemini AI integration
│   └── video_analyzer.py  # Twelve Labs integration
│
├── routes/                # API endpoint definitions
│   ├── products.py        # /api/products endpoints
│   ├── trends.py          # /api/trends endpoints
│   └── health.py          # /health endpoints
│
├── graphs/                # LangGraph workflow definitions
│   ├── state.py           # Typed state schema
│   ├── nodes.py           # Node functions
│   └── workflow.py        # Graph definition
│
├── data/                  # Static data files
│   └── sample_trends.json # Sample trend data
│
└── utils/                 # Utility functions
    └── helpers.py         # Common helpers
```

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit .env with your credentials
```

Required environment variables:
- `SHOPIFY_STORE_DOMAIN`: Your Shopify store domain
- `SHOPIFY_ACCESS_TOKEN`: Shopify Admin API access token
- `GEMINI_API_KEY`: Google Gemini API key

Optional:
- `TWELVE_LABS_API_KEY`: For video analysis features
- `YOUTUBE_API_KEY`: For YouTube trend fetching

### 4. Run the Server

```bash
python app.py
```

Server starts at `http://localhost:5000`

## API Endpoints

### Health Check

```bash
# Basic health
GET /health

# Configuration status
GET /health/config

# All services status
GET /health/services
```

### Products

```bash
# List all products
GET /api/products

# Get single product
GET /api/products/<product_id>

# Analyze all products against trends
POST /api/products/analyze

# Analyze single product
POST /api/products/<product_id>/analyze

# Apply AI recommendations to product
POST /api/products/<product_id>/apply
```

### Trends

```bash
# List all trends
GET /api/trends

# Filter by platform
GET /api/trends?platform=TikTok

# Get top trends
GET /api/trends?top=5

# Get single trend
GET /api/trends/<trend_id>

# Get platforms list
GET /api/trends/platforms

# Match product to trends
GET /api/trends/match/<product_id>
```

## Example Usage

### Analyze Products

```bash
curl -X POST http://localhost:5000/api/products/analyze
```

Response:
```json
{
  "success": true,
  "analysis": [
    {
      "productId": "gid://shopify/Product/123",
      "productTitle": "Classic Trench Coat",
      "needsMakeover": true,
      "matchedTrends": ["Aura Aesthetic"],
      "confidence": 85,
      "recommendations": {
        "optimizedTitle": "Classic Trench Coat - Mysterious Elegance",
        "marketingAngle": "Cultivate your mysterious aura...",
        "layoutStyle": "luxury",
        ...
      }
    }
  ],
  "trends_analyzed": 6,
  "products_analyzed": 10,
  "ai_model": "gemini-pro"
}
```

### Apply Recommendations

```bash
curl -X POST http://localhost:5000/api/products/gid://shopify/Product/123/apply
```

## LangGraph Integration

Services are designed as stateless functions for easy LangGraph orchestration:

```python
from graphs.workflow import run_optimization

# Run the full workflow
result = run_optimization(
    product_ids=None,  # All products
    auto_apply=False,  # Manual approval
    dry_run=True       # Don't update Shopify
)

# Check recommendations
for rec in result['recommendations']:
    print(f"{rec['productTitle']}: {rec['matchedTrends']}")
```

## Development

### Adding New Trends

Edit `data/sample_trends.json` to add new trends:

```json
{
  "id": "trend_007",
  "name": "New Trend Name",
  "description": "...",
  "keywords": ["keyword1", "keyword2"],
  "target_products": ["product type 1", "product type 2"],
  "marketing_angle": "...",
  "popularity_score": 80,
  "platforms": ["TikTok", "Instagram"]
}
```

### Adding New Services

1. Create service in `services/`
2. Follow the singleton pattern with `__init__.py` export
3. Add corresponding route in `routes/`
4. (Optional) Add LangGraph node in `graphs/nodes.py`

## License

MIT
