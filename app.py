# app.py
import io
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from image_recognition import recognize_image
from dynamic_response import generate_response
from text_to_speech import speak

app = FastAPI()

# CORS for iOS app requests (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image_stream = io.BytesIO(image_bytes)

        object_label = recognize_image(image_stream)
        ai_response = generate_response(object_label=object_label)

        return JSONResponse(content={
            "object_label": object_label,
            "ai_response": ai_response
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/chat_about_image")
async def chat_about_image(
    file: UploadFile = File(...),
    question: str = Form(""),
    history: str | None = Form(None),   # optional JSON string from client
):
    try:
        image_bytes = await file.read()
        image_stream = io.BytesIO(image_bytes)

        object_label = recognize_image(image_stream)

        parsed_history = None
        if history:
            try:
                parsed_history = json.loads(history)
            except Exception:
                parsed_history = None

        ai_response = generate_response(
            object_label=object_label,
            question=question,
            history=parsed_history
        )

        return JSONResponse(content={
            "object_label": object_label,
            "question": question,
            "ai_response": ai_response
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/get_speech")
async def get_speech(text: str = Form(...)):
    try:
        audio_bytes = speak(text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
