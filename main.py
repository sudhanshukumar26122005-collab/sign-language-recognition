import os
import sys

# Auto-activate local .venv if executed with system Python
_base_dir = os.path.dirname(os.path.abspath(__file__))
_venv_dir = os.path.join(_base_dir, ".venv")
_venv_python = os.path.join(_venv_dir, "bin", "python")
if os.path.isdir(_venv_dir) and sys.prefix != _venv_dir:
    os.execv(_venv_python, [_venv_python] + sys.argv)

# pyrefly: ignore [missing-import]
import cv2
import math

# Set safe matplotlib cache dir to avoid permission warnings
os.environ.setdefault("MPLCONFIGDIR", os.path.join(_base_dir, ".cache", "matplotlib"))

from hand_detector import HandDetector
from recognizer import recognize_letter
from word_builder import WordBuilder
from tts import speak_async

# ---------- angle helper ----------
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

def main():
    detector = HandDetector(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        print("Please check: macOS System Settings -> Privacy & Security -> Camera -> allow Terminal / Python.")
        return

    word_builder = WordBuilder()
    spoken = False

    print("Sign Language Recognition started. Press 'q' to quit, 'c' to clear, 'Backspace' to delete.")

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read from camera.")
            break

        # Flip horizontally for natural mirror view
        img = cv2.flip(img, 1)
        hands = detector.find_hands(img)

        detected_letter = ""
        fingers = []

        if hands:
            lm = hands[0]
            detector.draw_landmarks(img, lm)

            # ---------- thumb ----------
            thumb_tip, thumb_ip, thumb_mcp, wrist = lm[4], lm[3], lm[2], lm[0]
            thumb_angle = angle(thumb_tip, thumb_ip, thumb_mcp)
            thumb_dist = math.hypot(thumb_tip[1] - wrist[1], thumb_tip[2] - wrist[2])
            mcp_dist = math.hypot(thumb_mcp[1] - wrist[1], thumb_mcp[2] - wrist[2])

            fingers.append(1 if (thumb_angle > 150 and thumb_dist > mcp_dist + 10) else 0)

            # ---------- other fingers ----------
            for tip in [8, 12, 16, 20]:
                fingers.append(1 if lm[tip][2] < lm[tip - 2][2] else 0)

            detected_letter = recognize_letter(fingers)
            word = word_builder.update(detected_letter, fingers)

            cv2.putText(img, f"Fingers: {fingers}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            if detected_letter:
                hold_pct = int(word_builder.progress * 100)
                status_str = f"Letter: {detected_letter} ({hold_pct}%)" if hold_pct > 0 else f"Letter: {detected_letter}"
                cv2.putText(img, status_str, (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)

            cv2.putText(img, f"Word: {word}", (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # ---------- speak on fist ----------
            if fingers == [0, 0, 0, 0, 0] and len(word.strip()) > 0:
                if not spoken:
                    speak_async(word)
                    spoken = True
            else:
                spoken = False

        cv2.imshow("Sign Language Recognition", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            word_builder.clear()
        elif key == 8: # Backspace
            word_builder.backspace()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
