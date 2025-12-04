# backend/main.py
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import SessionLocal, Event, init_db
from services import presign_upload, save_local_file, get_local_file_url, send_sms, call_number
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import logging

load_dotenv()
LOG = logging.getLogger("backend")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("API_KEY", "demo_api_key_please_change")
HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", 3000))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# middleware: api key check (except root/health)
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if request.url.path in ["/", "/health", "/upload"]:
        return await call_next(request)
    key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if not key or key != API_KEY:
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)


@app.get("/")
def root():
    return {"status": "backend ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Presign endpoint
class PresignRequest(BaseModel):
    filename: str
    contentType: Optional[str] = "application/octet-stream"

@app.post("/api/presign")
def presign(req: PresignRequest):
    res = presign_upload(req.filename, req.contentType)
    # if local provider, return full url (backend absolute) for convenience
    if res["provider"] == "local":
        res["url"] = f"http://{HOST}:{PORT}{res['url']}"
    return res

# Local upload endpoint (used if S3 not configured)
@app.put("/upload/{key}")
async def upload_local(key: str, request: Request):
    # read bytes
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No data uploaded")
    path = save_local_file(key, body)
    return {"status": "ok", "path": path, "key": key, "url": f"http://{HOST}:{PORT}/upload/{key}"}

# serve uploaded local file for playback
@app.get("/upload/{key}")
def get_upload(key: str):
    path = os.path.join(os.getenv("UPLOAD_FOLDER", "./backend/uploads"), key)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    # return direct file stream
    return FileResponse(path, media_type="application/octet-stream", filename=key)

# Event model for POST
class EventIn(BaseModel):
    userId: Optional[str] = "unknown"
    type: str
    confidence: float
    lat: Optional[float] = None
    lon: Optional[float] = None
    audioKey: Optional[str] = None
    videoKey: Optional[str] = None
    speed: Optional[float] = None
    accelPeak: Optional[float] = None
    metadata: Optional[Dict] = {}

# Create event
@app.post("/api/events")
def create_event(e: EventIn):
    db = SessionLocal()
    ev = Event(
        user_id=e.userId,
        type=e.type,
        confidence=e.confidence,
        lat=e.lat,
        lon=e.lon,
        audio_key=e.audioKey,
        video_key=e.videoKey,
        speed=e.speed,
        accel_peak=e.accelPeak,
        metadata=e.metadata
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # Optionally auto-notify depending on confidence and config
    # We'll not crash if twilio missing - services.send_sms will log if missing
    try:
        contacts = (e.metadata or {}).get("trustedContacts", [])
        # send SMS to contacts
        for c in contacts:
            phone = c.get("phone") if isinstance(c, dict) else c
            if phone:
                send_sms(phone, f"ALERT: {e.type.upper()} detected (confidence {e.confidence}).")
        # emergency call fallback
        from dotenv import load_dotenv
        load_dotenv()
        emergency_phone = os.getenv("EMERGENCY_PHONE")
        threshold = float(os.getenv("EMERGENCY_CONFIDENCE_THRESHOLD") or 0.95)
        if (e.confidence >= threshold) and emergency_phone:
            call_number(emergency_phone, f"Emergency: {e.type.upper()} detected with confidence {e.confidence}.")
    except Exception as err:
        LOG.exception("notify error: %s", err)

    return {"status": "ok", "eventId": ev.id}

# Get events (latest first)
@app.get("/api/events")
def get_events(limit: int = 50):
    db = SessionLocal()
    rows = db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "userId": r.user_id,
            "type": r.type,
            "confidence": r.confidence,
            "lat": r.lat,
            "lon": r.lon,
            "audioKey": r.audio_key,
            "videoKey": r.video_key,
            "speed": r.speed,
            "accelPeak": r.accel_peak,
            "metadata": r.metadata,
            "status": r.status,
            "createdAt": r.created_at.isoformat()
        })
    return {"status": "ok", "events": out}

# Acknowledge/update event
@app.put("/api/events/{event_id}/ack")
def ack_event(event_id: int, payload: dict):
    db = SessionLocal()
    ev = db.query(Event).get(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="not found")
    ev.status = payload.get("status", "acknowledged")
    db.commit()
    return {"ok": True, "event": {"id": ev.id, "status": ev.status}}

# Force notify (manual)
@app.post("/api/notify/{event_id}")
def notify_event(event_id: int):
    db = SessionLocal()
    ev = db.query(Event).get(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="not found")
    # simple notify: use metadata.trustedContacts if present
    contacts = (ev.metadata or {}).get("trustedContacts", [])
    results = []
    for c in contacts:
        phone = c.get("phone") if isinstance(c, dict) else c
        if phone:
            results.append(send_sms(phone, f"ALERT: {ev.type.upper()} user {ev.user_id} at confidence {ev.confidence}"))
    # possibly call emergency number for high confidence
    emergency_phone = os.getenv("EMERGENCY_PHONE")
    threshold = float(os.getenv("EMERGENCY_CONFIDENCE_THRESHOLD") or 0.95)
    if ev.confidence >= threshold and emergency_phone:
        results.append(call_number(emergency_phone, f"Emergency: {ev.type.upper()} detected with confidence {ev.confidence}"))
    return {"ok": True, "results": results}

if __name__ == "__main__":
    # ensure DB exists
    init_db()
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
