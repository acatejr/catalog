from fastapi import FastAPI

app = FastAPI(name="catalog-api", version="0.1.0", title="Catalog API", description="API for managing product catalog")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
