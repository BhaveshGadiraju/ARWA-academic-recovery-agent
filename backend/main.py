from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(

    title="ARWA Academic Recovery AI",

    description="AI-powered academic recovery agent",

    version="1.0.0",

)

# Add CORS middleware to allow requests from frontend (localhost:3000 in dev, or any origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # In production, replace "*" with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)