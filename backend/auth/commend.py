from importlib import import_module

import eel


def _optional_import(module_name):
    try:
        return import_module(module_name)
    except ImportError:
        return None


pyttsx3 = _optional_import("pyttsx3")
sr = _optional_import("speech_recognition")


def _safe_ui_call(function_name, *args):
    try:
        getattr(eel, function_name)(*args)
    except Exception:
        pass


def speak(text):
    text = str(text)
    _safe_ui_call("DisplayMessage", text)
    _safe_ui_call("receiverText", text)

    if pyttsx3 is None:
        return

    try:
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty("voices")
        if len(voices) > 2:
            engine.setProperty("voice", voices[2].id)
        engine.setProperty("rate", 174)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def takecommand():
    if sr is None:
        raise RuntimeError(
            "Voice input requires the 'speech_recognition' package to be installed."
        )

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("I'm listening...")
        _safe_ui_call("DisplayMessage", "I'm listening...")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, 10, 8)

    try:
        print("Recognizing...")
        _safe_ui_call("DisplayMessage", "Recognizing...")
        query = recognizer.recognize_google(audio, language="en-US")
        print(f"User said: {query}\n")
        _safe_ui_call("DisplayMessage", query)
    except Exception as exc:
        print(f"Error: {exc}\n")
        return None

    return query.lower()


@eel.expose
def takeAllCommands(message=None):
    try:
        if message is None:
            try:
                query = takecommand()
            except RuntimeError as exc:
                speak(str(exc))
                return

            if not query:
                speak("I did not catch that.")
                return

            print(query)
            _safe_ui_call("senderText", query)
        else:
            query = str(message).strip()
            if not query:
                speak("Please type a command.")
                return

            print(f"Message received: {query}")
            _safe_ui_call("senderText", query)

        if query:
            if "open" in query:
                from backend.auth.feature import openCommand

                openCommand(query)
            elif "send message" in query or "call" in query or "video call" in query:
                from backend.auth.feature import findContact, whatsApp

                flag = ""
                phone, name = findContact(query)
                if phone != 0:
                    if "send message" in query:
                        flag = "message"
                        speak("What message to send?")
                        try:
                            query = takecommand()
                        except RuntimeError as exc:
                            speak(str(exc))
                            return

                        if not query:
                            speak("I did not catch the message.")
                            return
                    elif "call" in query:
                        flag = "call"
                    else:
                        flag = "video call"
                    whatsApp(phone, query, flag, name)
            elif "on youtube" in query:
                from backend.auth.feature import PlayYoutube

                PlayYoutube(query)
            else:
                from backend.auth.feature import chatBot

                chatBot(query)
        else:
            speak("No command was given.")
    except Exception as exc:
        print(f"An error occurred: {exc}")
        speak("Sorry, something went wrong.")
    finally:
        _safe_ui_call("ShowHood")
