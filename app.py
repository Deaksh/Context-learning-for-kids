# app.py
import io
import json
import base64
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from image_recognition import recognize_image
from dynamic_response import generate_response
from text_to_speech import speak

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

# ---------------------------
# App & Middleware
# ---------------------------
app = FastAPI()

# Allow CORS for iOS app requests (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # TODO: Restrict to your app domain/bundle later
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# GZip large responses (helpful for audio / larger JSON)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.get("/")
async def root():
    return {"message": "Backend is running. Use /analyze_image, /chat_about_image or /analyze_image_base64."}


# ---- Helpers ----
async def _read_upload_file(upload: UploadFile) -> bytes:
    """Safely read bytes from an UploadFile with logging."""
    content = await upload.read()
    logger.info(f"Uploaded file: name={upload.filename!r}, size={len(content)} bytes, type={upload.content_type}")
    return content


def _safe_log(prefix: str, text: Optional[str], max_len: int = 160) -> None:
    """Log first part of a possibly long string."""
    if text is None:
        logger.info(f"{prefix}: None")
        return
    clipped = (text[:max_len] + "…") if len(text) > max_len else text
    logger.info(f"{prefix}: {clipped}")


# ---------------------------------------------------------
# 1) Analyze image (multipart form) — accepts 'file' or 'image'
# ---------------------------------------------------------
@app.post("/analyze_image")
async def analyze_image(
    file: Optional[UploadFile] = File(None),     # preferred field name
    image: Optional[UploadFile] = File(None),    # fallback field name if client sent 'image'
):
    try:
        upload = file or image
        if not upload:
            return JSONResponse(content={"error": "No file uploaded (field must be 'file' or 'image')."}, status_code=400)

        image_bytes = await _read_upload_file(upload)
        image_stream = io.BytesIO(image_bytes)

        # 1) Recognize object
        object_label = recognize_image(image_stream)
        _safe_log("Object recognized", object_label)

        # 2) Generate AI response
        try:
            ai_response = generate_response(object_label=object_label)
        except Exception as e:
            logger.exception("AI generation failed")
            ai_response = "Sorry, I couldn't generate a response."

        _safe_log("AI response", ai_response)

        return JSONResponse(content={
            "object_label": object_label,
            "ai_response": ai_response
        })

    except Exception as e:
        logger.exception("Error in /analyze_image")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ------------------------------------------------------------------
# 2) Chat about image (multipart form) — accepts 'file' or 'image'
# ------------------------------------------------------------------
@app.post("/chat_about_image")
async def chat_about_image(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    question: str = Form(""),
    history: Optional[str] = Form(None),   # JSON string from client (optional)
):
    try:
        upload = file or image
        if not upload:
            return JSONResponse(content={"error": "No file uploaded (field must be 'file' or 'image')."}, status_code=400)

        image_bytes = await _read_upload_file(upload)
        image_stream = io.BytesIO(image_bytes)

        # 1) Recognize object
        object_label = recognize_image(image_stream)
        _safe_log("Object recognized (chat)", object_label)
        _safe_log("Question", question)

        # 2) Parse conversation history if provided
        parsed_history = None
        if history:
            try:
                parsed_history = json.loads(history)
                logger.info("History parsed successfully")
            except Exception as e:
                logger.warning(f"Failed to parse history JSON: {e}")
                parsed_history = None

        # 3) Generate AI response
        try:
            ai_response = generate_response(
                object_label=object_label,
                question=question,
                history=parsed_history
            )
        except Exception as e:
            logger.exception("AI chat generation failed")
            ai_response = "Sorry, I couldn't generate a response."

        _safe_log("AI response (chat)", ai_response)

        return JSONResponse(content={
            "object_label": object_label,
            "question": question,
            "ai_response": ai_response
        })

    except Exception as e:
        logger.exception("Error in /chat_about_image")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------------------------------------------------------
# 3) Analyze image via JSON base64 (avoids multipart boundary issues)
# ----------------------------------------------------------------------
from pydantic import BaseModel

class AnalyzeBase64Request(BaseModel):
    image_base64: str                 # base64 data (data URL or raw base64)
    question: Optional[str] = ""
    history: Optional[list] = None    # list of {"role": "...", "content": "..."}

@app.post("/analyze_image_base64")
async def analyze_image_base64(req: AnalyzeBase64Request):
    try:
        # Accept both "data:image/jpeg;base64,..." and raw base64
        b64_str = req.image_base64.split(",", 1)[-1] if "," in req.image_base64 else req.image_base64
        image_bytes = base64.b64decode(b64_str)
        logger.info(f"Received base64 image, size={len(image_bytes)} bytes")

        image_stream = io.BytesIO(image_bytes)

        # 1) Recognize
        object_label = recognize_image(image_stream)
        _safe_log("Object recognized (b64)", object_label)

        # 2) Generate AI response
        try:
            ai_response = generate_response(
                object_label=object_label,
                question=req.question or "",
                history=req.history if isinstance(req.history, list) else None
            )
        except Exception:
            logger.exception("AI generation (b64) failed")
            ai_response = "Sorry, I couldn't generate a response."

        _safe_log("AI response (b64)", ai_response)

        return JSONResponse(content={
            "object_label": object_label,
            "question": req.question or "",
            "ai_response": ai_response
        })

    except Exception as e:
        logger.exception("Error in /analyze_image_base64")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -----------------------------------
# 4) Text-to-Speech (form or JSON)
# -----------------------------------
class SpeechRequest(BaseModel):
    text: str

@app.post("/get_speech")
async def get_speech(
    text: Optional[str] = Form(None)
):
    try:
        if text is None:
            # Try JSON body if not provided as Form
            # (FastAPI will parse JSON automatically via request body model, but we keep this single endpoint simple)
            return JSONResponse(content={"error": "No text provided"}, status_code=400)

        txt = text.strip()
        if not txt:
            return JSONResponse(content={"error": "No text provided"}, status_code=400)

        _safe_log("Generating speech for text", txt)

        audio_bytes = speak(txt)
        headers = {
            "Content-Disposition": 'inline; filename="speech.mp3"'
        }
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg", headers=headers)

    except Exception as e:
        logger.exception("Error in /get_speech")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ---------------------------
# Uvicorn entrypoint (local)
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
