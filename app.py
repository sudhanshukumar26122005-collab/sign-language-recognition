import os
import sys

# Auto-activate local .venv if executed with system Python
_base_dir = os.path.dirname(os.path.abspath(__file__))
_venv_dir = os.path.join(_base_dir, ".venv")
_venv_python = os.path.join(_venv_dir, "bin", "python")
if os.path.isdir(_venv_dir) and sys.prefix != _venv_dir:
    os.execv(_venv_python, [_venv_python] + sys.argv)

import streamlit as st

# If executed directly with `python app.py`, bypass prompts and start Streamlit server
if not st.runtime.exists():
    # Pre-seed credentials so Streamlit never blocks waiting for email on first run
    try:
        from streamlit.runtime.credentials import Credentials, _Activation
        creds = Credentials.get_current()
        creds._conf_file = os.path.join(_base_dir, ".streamlit", "credentials.toml")
        creds.activation = _Activation(email="", is_valid=True)
    except Exception:
        pass

    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
    sys.exit(stcli.main())

# Safe matplotlib cache dir and Streamlit config dir
os.environ.setdefault("MPLCONFIGDIR", os.path.join(_base_dir, ".cache", "matplotlib"))
os.environ.setdefault("STREAMLIT_CONFIG_DIR", os.path.join(_base_dir, ".streamlit"))

# ---------- Streamlit UI Config (MUST be first Streamlit call) ----------
st.set_page_config(page_title="Sign Language Recognition", page_icon="🤟", layout="wide")

import math
import time
import cv2
from hand_detector import HandDetector
from recognizer import recognize_letter
from word_builder import WordBuilder
from tts import speak_async

# ---------- Angle helper ----------
def angle(a, b, c):
    ab = (a[1] - b[1], a[2] - b[2])
    cb = (c[1] - b[1], c[2] - b[2])
    dot = ab[0] * cb[0] + ab[1] * cb[1]
    mag_ab = math.hypot(ab[0], ab[1])
    mag_cb = math.hypot(cb[0], cb[1])
    if mag_ab * mag_cb == 0:
        return 0
    cos_val = max(-1.0, min(1.0, dot / (mag_ab * mag_cb)))
    return math.degrees(math.acos(cos_val))

# ---------- Camera Helper ----------
def open_working_camera(preferred_index=0):
    """
    Attempts to open a working webcam on macOS using AVFoundation or default backend.
    Tries preferred_index first, then tests fallback indices (0, 1, 2).
    """
    indices_to_try = [preferred_index] + [i for i in [0, 1, 2] if i != preferred_index]

    for idx in indices_to_try:
        # Try explicit AVFoundation on macOS
        cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
        if cap is not None and cap.isOpened():
            for _ in range(6):
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    return cap, idx
                time.sleep(0.04)
            cap.release()

        # Fallback to default backend
        cap = cv2.VideoCapture(idx)
        if cap is not None and cap.isOpened():
            for _ in range(6):
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    return cap, idx
                time.sleep(0.04)
            cap.release()

    return None, preferred_index

@st.cache_resource
def get_detector():
    return HandDetector(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize session state
if "word_builder" not in st.session_state:
    st.session_state.word_builder = WordBuilder()
if "spoken" not in st.session_state:
    st.session_state.spoken = False

st.title("🤟 Real-Time Sign Language Recognition")
st.caption("Show your palm facing the camera to recognize alphabet gestures, build words, and hear them spoken.")

st.info("💡 **Tips**: Face your palm toward the camera. Hold each gesture steady for ~1 second. Make a closed fist to insert a space or finish a word.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Camera Settings")
    cam_option = st.selectbox(
        "Camera Device",
        options=["Auto-detect", "Camera 0", "Camera 1", "Camera 2"],
        index=0,
        help="Select a specific camera if you have multiple devices (e.g. FaceTime HD vs Continuity Camera)."
    )
    cam_index_map = {"Auto-detect": 0, "Camera 0": 0, "Camera 1": 1, "Camera 2": 2}
    preferred_cam = cam_index_map[cam_option]

    st.divider()
    st.markdown("**Instructions:**")
    st.markdown("1. Run `python app.py` from your terminal.\n2. Ensure terminal has Camera access in macOS settings.\n3. Click '▶ Start Camera' below.")

# Reference Guide
with st.expander("📖 View Supported Sign Gestures"):
    cols = st.columns(5)
    cols[0].markdown("**A** — Thumb out, fingers curled")
    cols[0].markdown("**B** — 4 fingers up, thumb in")
    cols[1].markdown("**D** — Index up, others curled")
    cols[1].markdown("**E** — All fingers curled (fist)")
    cols[2].markdown("**F** — Thumb & index touch, 3 fingers up")
    cols[2].markdown("**I** — Pinky up, others curled")
    cols[3].markdown("**L** — Thumb and index in 'L' shape")
    cols[3].markdown("**V** — Index and middle up ('peace')")
    cols[4].markdown("**W** — Index, middle, ring up")
    cols[4].markdown("**Y** — Thumb and pinky out ('shaka')")

# Control Buttons
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.5, 1, 1, 1])
run = ctrl_col1.checkbox("▶ Start Camera", key="camera_toggle")
if ctrl_col2.button("🗑️ Clear Text"):
    st.session_state.word_builder.clear()
    st.session_state.spoken = False
if ctrl_col3.button("⌫ Backspace"):
    st.session_state.word_builder.backspace()
if ctrl_col4.button("🔊 Speak Word"):
    current = st.session_state.word_builder.word.strip()
    if current:
        speak_async(current)

# Layout: camera on left, text on right
left_col, right_col = st.columns([2, 1])

FRAME_WINDOW = left_col.image([])
letter_placeholder = right_col.empty()
word_placeholder = right_col.empty()
status_placeholder = right_col.empty()

# Show existing word if available
if st.session_state.word_builder.word.strip():
    word_placeholder.markdown(f"## 🧾 Recognized Word\n### **`{st.session_state.word_builder.word}`**")

if run:
    try:
        detector = get_detector()
    except Exception as e:
        st.error(f"Failed to initialize hand detector: {e}")
        st.stop()

    status_placeholder.info("🔄 Connecting to camera...")
    cap, active_cam_idx = open_working_camera(preferred_cam)

    if cap is None:
        status_placeholder.empty()
        st.error(
            "⚠️ **Camera could not be opened.**\n\n"
            "**Troubleshooting steps:**\n"
            "1. **Start from Terminal:** Make sure the app is launched from your terminal: `python app.py` (not a sandboxed daemon).\n"
            "2. **macOS Permissions:** Go to **System Settings → Privacy & Security → Camera** and ensure your Terminal / Python has camera permission.\n"
            "3. **Switch Camera:** In the sidebar on the left, change **Camera Device** from `Auto-detect` to `Camera 1` or `Camera 2`.\n"
            "4. **Close Other Camera Apps:** Make sure FaceTime, Zoom, or `main.py` aren't currently using the webcam."
        )
    else:
        # Optimize OpenCV camera settings for real-time streaming
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except Exception:
            pass

        status_placeholder.success(f"📷 Camera active (Device #{active_cam_idx})")

        last_letter_display = None
        last_word_display = None

        try:
            while run:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                hands = detector.find_hands(frame)

                detected_letter = ""
                fingers = []

                if hands:
                    lm = hands[0]
                    detector.draw_landmarks(frame, lm)

                    # ---------- Thumb ----------
                    thumb_tip, thumb_ip, thumb_mcp, wrist = lm[4], lm[3], lm[2], lm[0]
                    thumb_angle = angle(thumb_tip, thumb_ip, thumb_mcp)
                    thumb_dist = math.hypot(thumb_tip[1] - wrist[1], thumb_tip[2] - wrist[2])
                    mcp_dist = math.hypot(thumb_mcp[1] - wrist[1], thumb_mcp[2] - wrist[2])

                    fingers.append(1 if (thumb_angle > 150 and thumb_dist > mcp_dist + 10) else 0)

                    # ---------- Other fingers ----------
                    for tip in [8, 12, 16, 20]:
                        fingers.append(1 if lm[tip][2] < lm[tip - 2][2] else 0)

                    detected_letter = recognize_letter(fingers)
                    word = st.session_state.word_builder.update(detected_letter, fingers)

                    hold_pct = int(st.session_state.word_builder.progress * 100)

                    # Draw HUD overlay directly on the frame
                    cv2.putText(frame, f"Fingers: {fingers}", (10, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    if detected_letter:
                        status_str = f"Letter: {detected_letter} ({hold_pct}%)" if hold_pct > 0 else f"Letter: {detected_letter}"
                        cv2.putText(frame, status_str, (10, 75),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

                    cv2.putText(frame, f"Word: {word}", (10, 115),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 100, 0), 2)

                    # ---------- Speak on fist ----------
                    if fingers == [0, 0, 0, 0, 0] and word.strip():
                        if not st.session_state.spoken:
                            speak_async(word)
                            st.session_state.spoken = True
                    else:
                        st.session_state.spoken = False

                # Ensure frame is compact for fast WebSocket transmission
                if frame.shape[1] > 640:
                    h, w = frame.shape[:2]
                    scale = 640.0 / w
                    display_frame = cv2.resize(frame, (640, int(h * scale)))
                else:
                    display_frame = frame

                # Update camera image using compressed JPEG format (prevents browser/WebSocket backlog)
                FRAME_WINDOW.image(display_frame, channels="BGR", output_format="JPEG")

                # Selective UI updates: only re-render markdown when content actually changes
                hold_pct = int(st.session_state.word_builder.progress * 100) if hands else 0
                current_letter_key = f"{detected_letter}:{hold_pct}"
                if current_letter_key != last_letter_display:
                    last_letter_display = current_letter_key
                    if detected_letter:
                        progress_text = f" *(Hold: {hold_pct}%)*" if 0 < hold_pct < 100 else (" ✅" if hold_pct >= 100 else "")
                        letter_placeholder.markdown(
                            f"## 🅰️ Detected Letter\n# **{detected_letter}**{progress_text}"
                        )
                    else:
                        letter_placeholder.empty()

                current_word = st.session_state.word_builder.word.strip()
                if current_word != last_word_display:
                    last_word_display = current_word
                    if current_word:
                        word_placeholder.markdown(
                            f"## 🧾 Recognized Word\n### **`{current_word}`**"
                        )
                    else:
                        word_placeholder.empty()

                # Minimal yield so UI events are processed without starving the camera loop
                time.sleep(0.005)

        finally:
            cap.release()

