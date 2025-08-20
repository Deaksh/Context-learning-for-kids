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
<img width="150" height="200" alt="IMG_2294" src="https://github.com/user-attachments/assets/da6f2bfd-b8a5-4fbb-9761-219500ae8c9c" />
<img width="150" height="200" alt="IMG_2295" src="https://github.com/user-attachments/assets/101a47de-fd4e-4bc5-8e94-2e87b8a00768" />
<img width="150" height="200" alt="IMG_2296" src="https://github.com/user-attachments/assets/3609e577-51a5-4dca-8938-6cf55eeec102" />
<img width="150" height="200" alt="IMG_2297" src="https://github.com/user-attachments/assets/e2fab88a-7020-430b-8fab-69b1275aedd9" />
<img width="150" height="200" alt="IMG_2298" src="https://github.com/user-attachments/assets/9d7b6654-56f7-4fcc-897b-a7a5e284c905" />
<img width="150" height="200" alt="IMG_2299" src="https://github.com/user-attachments/assets/2def488c-215f-40f9-876a-340d156faab0" />
<img width="150" height="200" alt="IMG_2300" src="https://github.com/user-attachments/assets/4a4b909f-2bc3-472b-b7f8-1bb5c51419fe" />


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

##  Repo Structure

'''
Context-learning-for-kids/
├── ios-app/
│   └── context-learning.xcodeproj/  # Xcode project for iOS frontend(← SwiftUI iOS frontend for real-time AI interaction)
│       └── …                        # internal Xcode files
│
├── backend/
│   ├── app.py                        # FastAPI backend(object recognition, AI responses, TTS)
│   └── …                             # other backend files (requirements, helpers, etc.)
│
└── …                                 # other repo files (README.md, etc.)
'''
## 🚀 Getting Started
**##Frontend**
Open ios-app/Context-learning.xcodeproj in Xcode.
Launch on the simulator or a connected device.
Ensure you’ve added NSCameraUsageDescription, NSPhotoLibraryUsageDescription, and NSSpeechRecognitionUsageDescription in Info.plist.

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
