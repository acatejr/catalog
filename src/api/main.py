from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Data Catalog API")

@app.get("/health")
def health():
    now = datetime.now().isoformat()
    return {"status": "ok", "timestamp": now}
