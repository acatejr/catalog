from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/health")
async def health():
    return {
        "message": "ok"
    }