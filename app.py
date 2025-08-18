# app.py
import io
import json
import logging
import math
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from image_recognition import recognize_image
from dynamic_response import generate_response
from text_to_speech import speak  # keep even if iOS TTS is used; harmless

from PIL import Image
import numpy as np

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers: dominant color ----------
NAMED_COLORS = {
    "red":        (220, 20, 60),
    "orange":     (255, 140, 0),
    "yellow":     (255, 215, 0),
    "green":      (34, 139, 34),
    "blue":       (30, 144, 255),
    "purple":     (138, 43, 226),
    "pink":       (255, 105, 180),
    "brown":      (139, 69, 19),
    "black":      (0, 0, 0),
    "white":      (245, 245, 245),
    "gray":       (128, 128, 128),
}

def closest_named_color(rgb):
    r, g, b = rgb
    best_name, best_dist = None, 1e9
    for name, (R, G, B) in NAMED_COLORS.items():
        d = (r - R) ** 2 + (g - G) ** 2 + (b - B) ** 2
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name

def get_dominant_color_name_from_bytes(image_bytes: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((64, 64))
        arr = np.asarray(img).reshape(-1, 3)

        # Simple quantization to reduce noise
        q = (arr // 32) * 32
        # Find modal (most frequent) color
        colors, counts = np.unique(q, axis=0, return_counts=True)
        dominant = colors[counts.argmax()]
        color_name = closest_named_color(tuple(int(x) for x in dominant))
        return color_name
    except Exception as e:
        logger.warning(f"Color extraction failed: {e}")
        return ""

# ---------- Routes ----------
@app.get("/")
async def root():
    return {"message": "Backend is running. Use /analyze_image or /chat_about_image."}

@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file:
            return JSONResponse({"error": "No file uploaded"}, status_code=400)

        image_bytes = await file.read()
        logger.info(f"Received image: {file.filename}, size={len(image_bytes)} bytes")

        # Object label
        object_label = recognize_image(io.BytesIO(image_bytes))
        logger.info(f"Object recognized: {object_label}")

        # Visual facts
        dom_color = get_dominant_color_name_from_bytes(image_bytes)
        visual_facts = {"dominant_color": dom_color} if dom_color else {}

        # AI response
        try:
            ai_response = generate_response(
                object_label=object_label,
                question="",
                history=None,
                visual_facts=visual_facts
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            ai_response = "Sorry, I couldn't generate a response."

        return JSONResponse({
            "object_label": object_label,
            "visual_facts": visual_facts,
            "ai_response": ai_response
        })
    except Exception as e:
        logger.error(f"Error in /analyze_image: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/chat_about_image")
async def chat_about_image(
    file: UploadFile = File(...),
    question: str = Form(""),
    history: str | None = Form(None),
):
    try:
        if not file:
            return JSONResponse({"error": "No file uploaded"}, status_code=400)

        image_bytes = await file.read()
        logger.info(f"Chat image received: {file.filename}, size={len(image_bytes)} bytes")

        object_label = recognize_image(io.BytesIO(image_bytes))
        logger.info(f"Object recognized for chat: {object_label}")

        dom_color = get_dominant_color_name_from_bytes(image_bytes)
        visual_facts = {"dominant_color": dom_color} if dom_color else {}

        parsed_history = None
        if history:
            try:
                parsed_history = json.loads(history)
                logger.info(f"History parsed successfully")
            except Exception as e:
                logger.warning(f"History parse failed: {e}")
                parsed_history = None

        # If question is about color, answer directly using visual fact
        if question and "color" in question.lower():
            if dom_color:
                direct = f"The dominant color appears to be {dom_color}."
            else:
                direct = "I couldn't reliably detect the color from the image."
            return JSONResponse({
                "object_label": object_label,
                "question": question,
                "visual_facts": visual_facts,
                "ai_response": direct
            })

        try:
            ai_response = generate_response(
                object_label=object_label,
                question=question,
                history=parsed_history,
                visual_facts=visual_facts
            )
        except Exception as e:
            logger.error(f"AI chat generation failed: {e}")
            ai_response = "Sorry, I couldn't generate a response."

        return JSONResponse({
            "object_label": object_label,
            "question": question,
            "visual_facts": visual_facts,
            "ai_response": ai_response
        })
    except Exception as e:
        logger.error(f"Error in /chat_about_image: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/get_speech")
async def get_speech(text: str = Form(...)):
    try:
        if not text or text.strip() == "":
            return JSONResponse({"error": "No text provided"}, status_code=400)
        audio_bytes = speak(text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error in /get_speech: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
