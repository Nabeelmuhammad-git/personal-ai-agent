from importlib import import_module
import os
import webbrowser

import eel

from backend.auth.commend import speak
from backend.auth.config import BACKUP_PASSWORD
from backend.auth.feature import play_assistant_sound


def _load_face_auth_module():
    for module_name in ("backend.auth.recoganize", "backend.auth.recognize"):
        try:
            return import_module(module_name)
        except ImportError:
            continue
    return None


def _safe_play_assistant_sound():
    try:
        play_assistant_sound()
    except Exception as exc:
        print(f"Unable to play startup sound: {exc}")


def _open_app_window(url):
    try:
        os.system(f'start msedge.exe --app="{url}"')
        return
    except Exception:
        pass

    try:
        webbrowser.open(url)
    except Exception as exc:
        print(f"Unable to open app window automatically: {exc}")


def start():
    face_auth_module = _load_face_auth_module()
    app_url = "http://127.0.0.1:8000/index.html"
    eel.init("frontend")
    _safe_play_assistant_sound()

    @eel.expose
    def verify_backup_password(password):
        entered = str(password or "").strip()
        return entered == str(BACKUP_PASSWORD).strip()

    @eel.expose
    def initialize_app():
        eel.hideLoader()
        speak("Welcome to AI Nabeel")

        if face_auth_module is None:
            speak("Face authentication module is not available. Please use the backup password.")
            eel.showBackupPassword()
            return

        speak("Ready for Face Authentication")
        flag = face_auth_module.AuthenticateFace()
        if flag == 1:
            speak("Face recognized successfully")
            eel.hideFaceAuth()
            eel.hideFaceAuthSuccess()
            speak("Welcome to your assistant")
            eel.hideStart()
            _safe_play_assistant_sound()
        else:
            speak("Face not recognized. Please use the backup password")
            eel.showBackupPassword()

    eel.start(
        "index.html",
        mode=None,
        host="localhost",
        port=8000,
        block=False,
        size=(1280, 900),
    )
    _open_app_window(app_url)

    while True:
        eel.sleep(1.0)


if __name__ == "__main__":
    start()
