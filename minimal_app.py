"""Minimal FastAPI app for testing."""
from fastapi import FastAPI, HTTPException, Header
from typing import Optional
import os

app = FastAPI(title="PAI Minimal Test", version="1.0.0")

def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Simple API key validation."""
    expected_key = os.getenv("APP_API_KEY", "test-key")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/ping")
async def ping(api_key: str = Header(None)):
    """Health check endpoint."""
    if api_key != "test-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"status": "ok", "message": "PAI minimal test working!"}

@app.get("/healthz")
async def healthz():
    """Health check without auth."""
    return {"status": "ok", "message": "No auth required"}

@app.post("/test-budget")
async def test_budget(data: dict, api_key: str = Header(None)):
    """Test budget calculation."""
    if api_key != "test-key":
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Simple budget calculation
    categories = {
        "Food": 140.0,
        "Fun": 50.0,
        "Transport": 80.0
    }

    # Mock spending data
    spent = {
        "Food": 45.50,
        "Fun": 12.00,
        "Transport": 35.00
    }

    results = []
    for category, cap in categories.items():
        category_spent = spent.get(category, 0)
        delta = cap - category_spent
        status = "WARN" if category_spent / cap > 0.8 else "OK"

        results.append({
            "category": category,
            "cap": cap,
            "spent": category_spent,
            "delta": delta,
            "status": status
        })

    return {
        "message": "Budget calculation successful",
        "categories": results,
        "total_buffer": sum(r["delta"] for r in results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
