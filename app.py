# app.py
import io
import json
import logging
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from image_recognition import recognize_image
from dynamic_response import generate_response
from text_to_speech import speak

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS for iOS app requests (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend is running. Use /analyze_image or /chat_about_image."}


@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file:
            return JSONResponse(content={"error": "No file uploaded"}, status_code=400)

        image_bytes = await file.read()
        logger.info(f"Received image: {file.filename}, size={len(image_bytes)} bytes")

        image_stream = io.BytesIO(image_bytes)

        object_label = recognize_image(image_stream)
        logger.info(f"Object recognized: {object_label}")

        try:
            ai_response = generate_response(object_label=object_label)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            ai_response = "Sorry, I couldn't generate a response."

        return JSONResponse(content={
            "object_label": object_label,
            "ai_response": ai_response
        })
    except Exception as e:
        logger.error(f"Error in /analyze_image: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/chat_about_image")
async def chat_about_image(
    file: UploadFile = File(...),
    question: str = Form(""),
    history: str | None = Form(None),
):
    try:
        if not file:
            return JSONResponse(content={"error": "No file uploaded"}, status_code=400)

        image_bytes = await file.read()
        logger.info(f"Chat image received: {file.filename}, size={len(image_bytes)} bytes")

        image_stream = io.BytesIO(image_bytes)
        object_label = recognize_image(image_stream)
        logger.info(f"Object recognized for chat: {object_label}")

        parsed_history = None
        if history:
            try:
                parsed_history = json.loads(history)
                logger.info(f"History parsed successfully: {parsed_history}")
            except Exception as e:
                logger.warning(f"Failed to parse history: {e}")
                parsed_history = None

        try:
            ai_response = generate_response(
                object_label=object_label,
                question=question,
                history=parsed_history
            )
        except Exception as e:
            logger.error(f"AI chat generation failed: {e}")
            ai_response = "Sorry, I couldn't generate a response."

        return JSONResponse(content={
            "object_label": object_label,
            "question": question,
            "ai_response": ai_response
        })
    except Exception as e:
        logger.error(f"Error in /chat_about_image: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/get_speech")
async def get_speech(text: str = Form(...)):
    try:
        if not text or text.strip() == "":
            return JSONResponse(content={"error": "No text provided"}, status_code=400)

        logger.info(f"Generating speech for text: {text[:50]}...")

        audio_bytes = speak(text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error in /get_speech: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
