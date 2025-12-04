# backend/services.py
import os
import uuid
import logging
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
LOG = logging.getLogger("services")

# Local uploads fallback
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./backend/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS config (optional)
S3_BUCKET = os.getenv("S3_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# Twilio (optional)
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_FROM", "")
EMERGENCY_PHONE = os.getenv("EMERGENCY_PHONE", "")
EMERGENCY_CONFIDENCE_THRESHOLD = float(os.getenv("EMERGENCY_CONFIDENCE_THRESHOLD", "0.95"))

# lazy imports
def get_s3_client():
    if not S3_BUCKET or not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        return None
    import boto3
    session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                    region_name=AWS_REGION)
    return session.client("s3", region_name=AWS_REGION)

def presign_upload(filename, content_type="application/octet-stream", expires=300):
    """
    If S3 configured -> return presigned put URL and key.
    Otherwise return local upload URL (backend's /upload/<key>)
    """
    key = f"{uuid.uuid4().hex}_{filename}"
    s3 = get_s3_client()
    if s3:
        params = {
            "Bucket": S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        }
        url = s3.generate_presigned_url("put_object", Params=params, ExpiresIn=expires)
        return {"provider": "s3", "url": url, "key": key, "expires": expires}
    else:
        # local backend upload endpoint
        upload_url = f"/upload/{key}"
        return {"provider": "local", "url": upload_url, "key": key, "expires": expires}

def save_local_file(key: str, data: bytes):
    path = os.path.join(UPLOAD_FOLDER, key)
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    LOG.info("Saved local upload: %s", path)
    return path

def get_local_file_url(host, port, key):
    # streamlit/clients can fetch via http://host:port/upload/<key>
    return f"http://{host}:{port}/upload/{key}"

# Twilio helpers (optional)
def init_twilio_client():
    if TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_SID.startswith("AC"):
        from twilio.rest import Client
        return Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    return None

_twilio_client = None
def twilio_client():
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = init_twilio_client()
    return _twilio_client

def send_sms(to, body):
    client = twilio_client()
    if not client:
        LOG.info("(no-twilio) send_sms to %s: %s", to, body)
        return {"skipped": True}
    msg = client.messages.create(from_=TWILIO_FROM, to=to, body=body)
    return {"sid": msg.sid, "status": msg.status}

def call_number(to, text):
    client = twilio_client()
    if not client:
        LOG.info("(no-twilio) call_number to %s: %s", to, text)
        return {"skipped": True}
    twiml = f"<Response><Say>{text}</Say></Response>"
    call = client.calls.create(from_=TWILIO_FROM, to=to, twiml=twiml)
    return {"sid": call.sid, "status": call.status}
