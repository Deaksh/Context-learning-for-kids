# 📚 Context-Learning iOS App for Kids

An **iOS + AI app** designed to make learning fun and interactive for children.  
Kids can **take a picture or upload an image**, then **chat with an AI assistant** (via text or voice) to learn about what’s in the picture.  

---

## ✨ Features
- 📷 Capture or upload an image in real-time.
- 🔍 AI backend recognizes **objects** and **dominant colors** in the picture.
- 💬 Kids can ask questions about the image (e.g., "What is this animal?", "Why is it green?").
- 🔊 AI can reply **via text and speech** (text-to-speech).
- 🧠 Context-aware: remembers previous questions during a session.
- 🎨 Child-friendly UI built with SwiftUI, with scrollable chat and voice input.

---

## 🛠️ Tech Stack
- **Frontend (iOS):** SwiftUI, AVFoundation (camera, voice), Xcode
- **Backend:** Python, FastAPI, Pillow, NumPy
- **AI & Speech:** Custom image recognition, contextual response generation, text-to-speech
- **Deployment:** Xcode device testing (TestFlight/App Store ready)

---

## 📸 Screenshots
<img width="200" height="200" alt="IMG_2294" src="https://github.com/user-attachments/assets/da6f2bfd-b8a5-4fbb-9761-219500ae8c9c" />

(Add screenshots of the app interface here — capture flow, chat screen, speech output)

---

## ▶️ How It Works
1. User captures or uploads an image.
2. Backend:
   - Resizes + analyzes the image.
   - Recognizes the main object and dominant color.
   - Generates an educational AI response (e.g., facts about the object).
   - Optionally converts response into **audio speech**.
3. Frontend displays AI response in a **chat interface** (text + speech).
4. User can continue asking questions, and AI remembers context.

---

## 📂 Backend Services
- `/analyze_image` → Detect object + color + generate AI response.
- `/chat_about_image` → Continue a contextual conversation about the uploaded image.
- `/get_speech` → Convert AI response into speech (MP3 stream).

---

## 🚀 Getting Started
### Frontend (iOS)
- Open `Context-learning.xcodeproj` in Xcode.
- Build & run on simulator or device.

### Backend
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
