from fastapi import FastAPI
import uvicorn
from datetime import datetime

app = FastAPI(title="Catalog API", version="1.0.0")

@app.get("/health")
def health():
    now = datetime.now()
    return {"message": f"{now.strftime('%Y-%m-%d %H:%M:%S')} - Catalog API is running!"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)