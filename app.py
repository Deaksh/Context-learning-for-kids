# app.py
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from image_recognition import recognize_image
from dynamic_response import generate_response
from text_to_speech import speak

# Import your existing functions
# from your_module import recognize_image, generate_response, text_to_speech

app = FastAPI()

# Enable CORS for iOS app requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your app domain later
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    # Read image bytes
    image_bytes = await file.read()

    # Save temporarily or process directly
    image_stream = io.BytesIO(image_bytes)

    # 1️⃣ Recognize object
    object_label = recognize_image(image_stream)  # your function

    # 2️⃣ Generate AI response
    ai_response = generate_response(object_label)  # your function

    return JSONResponse(content={
        "object_label": object_label,
        "ai_response": ai_response
    })


@app.post("/get_speech")
async def get_speech(text: str):
    # 3️⃣ Convert text to speech
    audio_bytes = speak(text)  # should return bytes
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
