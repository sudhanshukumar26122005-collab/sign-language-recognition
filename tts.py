import pyttsx3
import threading
import queue

_speech_queue = queue.Queue()
_worker_thread = None
_lock = threading.Lock()

def _worker():
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
    except Exception:
        engine = None

    while True:
        text = _speech_queue.get()
        if text is None:
            break
        if engine and text and text.strip():
            try:
                engine.say(text.strip())
                engine.runAndWait()
            except Exception:
                pass
        _speech_queue.task_done()

def speak_async(text):
    """
    Speaks the given text asynchronously without thread safety conflicts.
    """
    if not text or not str(text).strip():
        return

    global _worker_thread
    with _lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=_worker, daemon=True)
            _worker_thread.start()

    _speech_queue.put(str(text))
