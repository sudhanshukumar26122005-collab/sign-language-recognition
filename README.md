
<div align="center">

# 🤟 Sign Language Recognition

### Real-time hand gesture translation — from sign to text to speech, live in your browser.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-00B2A9?style=flat&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#license)

</div>

---

## 📖 Overview

**Sign Language Recognition** is a real-time computer vision app that translates hand gestures into text and speech, aiming to close the communication gap between sign language users and non-signers.

It runs entirely through a webcam feed — no external hardware, no gloves, no sensors. Just a camera, a browser, and MediaPipe's hand-tracking model doing the heavy lifting underneath a clean Streamlit interface.

The project was built with a deliberate focus on **accuracy and real-time responsiveness**, not just a working demo — with particular attention paid to thumb tracking, historically one of the trickiest parts of gesture recognition due to its rotational range of motion.

---

## ✨ Features

- 🎥 **Real-time hand detection** via webcam, no extra hardware required
- ✋ **21-point hand landmark tracking** powered by MediaPipe
- 🔤 **Alphabet gesture recognition** using geometric finger-state logic
- 🧩 **Word building** from sequential recognized letters
- 🔊 **Text-to-speech output** so recognized words are spoken aloud
- 🖥️ **Interactive web UI** built with Streamlit — runs locally in the browser

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Computer Vision | OpenCV |
| Hand Landmark Detection | MediaPipe |
| Web Interface | Streamlit |
| Text-to-Speech | pyttsx3 |

---

## 🔍 How It Works

```
Webcam Feed → MediaPipe Landmark Detection → Finger-State Geometry
     → Letter Mapping → Word Builder → On-screen Text + Speech Output
```

1. **Capture** — the webcam streams live video into the app.
2. **Detect** — MediaPipe locates 21 landmarks on the hand in each frame.
3. **Interpret** — finger states (extended/curled) are calculated from joint angles and geometric relationships between landmarks.
4. **Map** — recognized finger patterns are mapped to specific letters.
5. **Build** — consecutive letters accumulate into words.
6. **Output** — the recognized word is displayed on screen and spoken aloud via TTS.

---

## 📂 Project Structure

```
sign-language-recognition/
├── app.py              # Streamlit web app entry point
├── main.py              # Core application logic
├── recognizer.py         # Gesture / landmark recognition logic
├── word_builder.py        # Combines recognized letters into words
├── tts.py               # Text-to-speech conversion
├── requirements.txt       # Project dependencies
└── .gitignore
```

---

## ▶️ Getting Started

### Prerequisites
- Python 3.9+
- A working webcam

### Installation

```bash
# Clone the repository
git clone https://github.com/srivathsangms/sign-language-recognition.git
cd sign-language-recognition

# Install dependencies
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

Then open the local URL Streamlit gives you (usually `http://localhost:8501`) in your browser.

---

## 📌 Usage Tips

For the best recognition accuracy:

- Face the **palm** of your hand toward the camera
- Hold each gesture **steady for a moment** to let it register
- Make a **fist** to separate words or trigger speech output
- Use **good, even lighting** — recognition quality depends on visibility

---

## 🚧 Current Limitations

- Supports a **selected set of alphabets** via logic-based detection (not the full sign language lexicon)
- Complex or continuous signs may require deeper shape/depth analysis than the current geometric approach provides
- Accuracy is sensitive to **lighting conditions** and **camera quality**

---

## 🚀 Roadmap

- [ ] Expand alphabet/gesture coverage
- [ ] Sentence-level recognition (beyond isolated words)
- [ ] Multi-language translation support
- [ ] Mobile-friendly interface
- [ ] Cloud deployment for public access

---

## 👨‍💻 Author

**Srivathsan GMS**
B.Tech Artificial Intelligence & Data Science
K.L.N. College of Engineering, Madurai

[![GitHub](https://img.shields.io/badge/GitHub-srivathsangms-181717?style=flat&logo=github&logoColor=white)](https://github.com/srivathsangms)

---

<div align="center">

*Built as a hands-on exploration of computer vision and human-computer interaction — a foundation for more advanced sign language translation systems.*

</div>
