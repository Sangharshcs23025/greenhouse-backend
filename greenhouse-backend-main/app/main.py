from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_indexes
from app.routers import auth_router, sensors, devices, ai_router, disease_router

app = FastAPI(title="Smart Greenhouse Digital Twin API", version="1.0.0")

# Allow the Flutter app (any origin during dev) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(sensors.router)
app.include_router(devices.router)
app.include_router(ai_router.router)
app.include_router(disease_router.router)


@app.on_event("startup")
async def on_startup():
    await init_indexes()


@app.get("/")
async def root():
    return {"status": "ok", "service": "Smart Greenhouse Digital Twin API"}