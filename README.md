# AI Human Safety Reflex — Python + Streamlit version

## Prereqs
- Python 3.10+ installed
- Git (optional)
- (Optional) AWS credentials if you want S3 uploads
- (Optional) Twilio account (Account SID starts with `AC...`) for SMS/calls

## Setup (Windows PowerShell / Linux)
1. Clone or create repo and open terminal in project dir.
2. Create virtualenv and install dependencies:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1   # (Windows PowerShell) or `source .venv/bin/activate` on mac/linux
pip install -r requirements.txt
