"""bolledger web server: voice + text Hinglish ledger.

Run:  uvicorn server:app --port 8100    then open http://localhost:8100
"""
import csv
import io
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from bolledger.brain import handle_text
from bolledger.ledger import Ledger
from bolledger.nlu import HinglishNLU
from bolledger import stt

BASE = Path(__file__).parent
FRONTEND = BASE / "frontend"
DB = BASE / "data" / "bolledger.db"
DB.parent.mkdir(exist_ok=True)

app = FastAPI(title="bolledger")
NLU = HinglishNLU.load(str(BASE / "bolledger" / "nlu_model.json"))
LEDGER = Ledger(DB)


@app.get("/api/state")
def state():
    return {
        "customers": LEDGER.list_customers(),
        "recent": LEDGER.recent(20),
        "hisaab": LEDGER.hisaab(),
        "stt_available": stt.available(),
    }


@app.post("/api/entry")
def entry(payload: dict):
    text = (payload.get("text") or "").strip()
    if not text:
        return {"error": "empty"}
    try:
        result = handle_text(text, NLU, LEDGER)
    except Exception as e:
        return {"error": f"Kuch galat ho gaya: {e}"}
    result["state"] = state()
    return result


@app.post("/api/voice")
async def voice(file: UploadFile):
    if not stt.available():
        return {"error": "STT not installed (pip install faster-whisper)"}
    tmp = Path("/tmp") / f"bolledger-voice-{uuid.uuid4().hex}.wav"
    tmp.write_bytes(await file.read())
    try:
        tr = stt.transcribe(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)
    if not tr["text"]:
        return {"error": "Kuch sunai nahi diya - dobara boliye.", "transcript": ""}
    try:
        result = handle_text(tr["text"], NLU, LEDGER)
    except Exception as e:
        return {"error": f"Kuch galat ho gaya: {e}", "transcript": tr["text"]}
    result["transcript"] = tr["text"]
    result["state"] = state()
    return result


@app.post("/api/undo/{tx_id}")
def undo(tx_id: int):
    ok = LEDGER.delete(tx_id)
    return {"ok": ok, "state": state()}


@app.get("/api/export.csv")
def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "ts", "kind", "name", "amount", "note", "raw_text"])
    for t in LEDGER.recent(10000):
        w.writerow([t["id"], t["ts"], t["kind"], t["name"] or "", t["amount"], t["note"] or "", t["raw_text"] or ""])
    return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                             headers={"content-disposition": "attachment; filename=bolledger.csv"})


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
