import datetime
import json
import os
import sqlite3
import struct
import subprocess
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path
from shlex import quote

import eel

from backend.auth.commend import speak
from backend.auth.config import ASSISTANT_NAME
from backend.auth.helper import extract_yt_term, remove_words

# ── Load .env for Gemini API key ─────────────────────────────────────────────
_ENV_PATH = Path(__file__).resolve().parents[2] / "backend" / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


def _optional_import(module_name, attribute_name=None):
    try:
        module = import_module(module_name)
    except ImportError:
        return None

    if attribute_name is None:
        return module

    return getattr(module, attribute_name, None)


hugchat = _optional_import("hugchat", "hugchat")
pvporcupine = _optional_import("pvporcupine")
pyaudio = _optional_import("pyaudio")
pyautogui = _optional_import("pyautogui")
kit = _optional_import("pywhatkit")
pygame = _optional_import("pygame")

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "jarvis.db"
COOKIE_PATH = BASE_DIR / "backend" / "cookie.json"
DEFAULT_SOUND_FILE = BASE_DIR / "frontend" / "assets" / "audio" / "start_sound.mp3"
FALLBACK_SOUND_FILE = BASE_DIR / "frontend" / "frontend_assets_audio_start_sound.mp3"
SOUND_FILE = DEFAULT_SOUND_FILE if DEFAULT_SOUND_FILE.exists() else FALLBACK_SOUND_FILE
SCHEMA_STATEMENTS = (
    "CREATE TABLE IF NOT EXISTS sys_command("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(100), "
    "path VARCHAR(1000)"
    ")",
    "CREATE TABLE IF NOT EXISTS web_command("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(100), "
    "url VARCHAR(1000)"
    ")",
    "CREATE TABLE IF NOT EXISTS contacts("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(200), "
    "Phone VARCHAR(255), "
    "email VARCHAR(255) NULL"
    ")",
    "CREATE TABLE IF NOT EXISTS memory("
    "key VARCHAR(100) PRIMARY KEY, "
    "value TEXT"
    ")",
)


def _initialize_database():
    connection = sqlite3.connect(DB_PATH)
    db_cursor = connection.cursor()
    try:
        for statement in SCHEMA_STATEMENTS:
            db_cursor.execute(statement)
        connection.commit()
    finally:
        db_cursor.close()
        connection.close()


_initialize_database()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
PYGAME_AUDIO_READY = False

if pygame is not None:
    try:
        pygame.mixer.init()
        PYGAME_AUDIO_READY = True
    except Exception as exc:
        print(f"Unable to initialize pygame audio: {exc}")


def _require_dependency(module, package_name, feature_name):
    if module is None:
        raise RuntimeError(
            f"{feature_name} requires the '{package_name}' package to be installed."
        )


@eel.expose
def play_assistant_sound():
    if pygame is None or not PYGAME_AUDIO_READY:
        print("Assistant sound is unavailable because pygame audio is not ready.")
        return False

    if not SOUND_FILE.exists():
        print(f"Assistant sound file was not found at {SOUND_FILE}.")
        return False

    try:
        pygame.mixer.music.load(str(SOUND_FILE))
        pygame.mixer.music.play()
        return True
    except Exception as exc:
        print(f"Unable to play assistant sound: {exc}")
        return False


def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query = query.lower()

    app_name = query.strip()

    if app_name != "":
        try:
            cursor.execute(
                "SELECT path FROM sys_command WHERE name IN (?)",
                (app_name,),
            )
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening " + query)
                os.startfile(results[0][0])

            else:
                cursor.execute(
                    "SELECT url FROM web_command WHERE name IN (?)",
                    (app_name,),
                )
                results = cursor.fetchall()

                if len(results) != 0:
                    speak("Opening " + query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening " + query)
                    try:
                        os.system(f'start "" "{query.strip()}"')
                    except Exception:
                        speak("not found")
        except Exception:
            speak("some thing went wrong")


def PlayYoutube(query):
    _require_dependency(kit, "pywhatkit", "YouTube playback")
    search_term = extract_yt_term(query)
    if not search_term:
        speak("I could not find what to play on YouTube.")
        return

    speak("Playing " + search_term + " on YouTube")
    kit.playonyt(search_term)


def hotword():
    _require_dependency(pvporcupine, "pvporcupine", "Hotword detection")
    _require_dependency(pyaudio, "pyaudio", "Hotword detection")
    _require_dependency(pyautogui, "pyautogui", "Hotword detection")

    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("hotword detected")
                pyautogui.keyDown("win")
                pyautogui.press("j")
                time.sleep(2)
                pyautogui.keyUp("win")

    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


def findContact(query):
    words_to_remove = [
        ASSISTANT_NAME,
        "make",
        "a",
        "to",
        "phone",
        "call",
        "send",
        "message",
        "whatsapp",
        "wahtsapp",
        "video",
    ]
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute(
            "SELECT Phone FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ("%" + query + "%", query + "%"),
        )
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])

        if not mobile_number_str.startswith("+91"):
            mobile_number_str = "+91" + mobile_number_str

        return mobile_number_str, query
    except Exception:
        speak("not exist in contacts")
        return 0, 0


def whatsApp(phone, message, flag, name):
    _require_dependency(pyautogui, "pyautogui", "WhatsApp automation")

    if flag == "message":
        target_tab = 12
        jarvis_message = "message send successfully to " + name
    elif flag == "call":
        target_tab = 7
        message = ""
        jarvis_message = "calling to " + name
    else:
        target_tab = 6
        message = ""
        jarvis_message = "staring video call with " + name

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={phone}&text={encoded_message}"
    full_command = f'start "" "{whatsapp_url}"'

    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)

    pyautogui.hotkey("ctrl", "f")

    for _ in range(1, target_tab):
        pyautogui.hotkey("tab")

    pyautogui.hotkey("enter")
    speak(jarvis_message)


SYSTEM_AI_PROMPT = (
    "You are AI Nabeel — an advanced, loyal, polite, and highly intelligent personal AI voice and chat assistant. "
    "You were created by and belong exclusively to Sir Nabeel Muhammad. "

    # ── Creator / User Profile ──────────────────────────────────────────────
    "CREATOR PROFILE: "
    "Name: Nabeel Muhammad. "
    "Age: 17 years old. "
    "Location: Kollam, Kerala, India. "
    "Education: Currently in Class 12 (Higher Secondary). "
    "Passion & Identity: Vibe Coder — someone who codes with creativity, style, and passion. "

    # ── Technical Skills ────────────────────────────────────────────────────
    "TECHNICAL SKILLS OF SIR NABEEL: "
    "Frontend: HTML5 (semantic, accessible markup), CSS3 (Flexbox, Grid, animations, responsive design, glassmorphism), "
    "JavaScript (DOM manipulation, event handling, async/await, fetch API), Bootstrap 5. "
    "Backend & Scripting: Python (intermediate-advanced — automation, file handling, APIs, web scraping, AI integration, eel desktop apps). "
    "Database: SQL (SQLite — schema design, CRUD, queries, joins, indexes). "
    "AI & ML Exposure: Prompt engineering, integrating LLM APIs (Pollinations, Ollama), building AI-powered desktop apps. "
    "Tools: VS Code, Git basics, PyCharm, pip, venv, Powershell. "
    "Projects: Built this AI Nabeel assistant (voice + chat + desktop GUI + SQLite memory), web projects, automation scripts. "

    # ── Developer Knowledge Base ────────────────────────────────────────────
    "DEVELOPMENT KNOWLEDGE — you can help Sir Nabeel with: "
    "Web development (HTML/CSS/JS full projects, responsive UI, animations, APIs), "
    "Python scripting and automation, "
    "Database design and SQL queries, "
    "Building desktop apps with Python Eel, "
    "AI/chatbot integration, "
    "Debugging code, explaining errors, suggesting improvements, "
    "Best practices in clean code, project structure, and version control, "
    "Career and learning guidance for a young developer. "

    # ── Behavior Rules ──────────────────────────────────────────────────────
    "BEHAVIOR: Always address the user as 'Sir Nabeel'. "
    "Respond in a polite, confident, friendly tone — like a brilliant AI companion who knows Sir Nabeel personally. "
    "For voice/spoken replies keep answers to 1-3 short sentences. For text/chat replies you may be more detailed. "
    "When helping with code, be precise, correct, and explain your reasoning if needed. "
    "Never use markdown asterisks, bullet symbols, or code fences unless the user explicitly asks for code. "
    "Remember: Sir Nabeel is young, talented, and ambitious — always encourage and support him. "
    "Long-term memory is stored in the SQLite 'memory' table — reference it to give personalised responses."
)


def get_stored_memory():
    """Return formatted long-term memory from SQLite, with rich defaults about Sir Nabeel."""
    default_memory = (
        "name: Nabeel Muhammad | "
        "age: 17 years old | "
        "location: Kollam, Kerala, India | "
        "education: Class 12 (Higher Secondary) | "
        "identity: Vibe Coder and AI builder | "
        "skills: HTML5, CSS3, JavaScript, Bootstrap, Python, SQL (SQLite), AI API integration | "
        "projects: AI Nabeel assistant, web projects, automation scripts | "
        "tools: VS Code, PyCharm, Git, pip, venv | "
        "role: Creator of AI Nabeel"
    )
    try:
        cursor.execute("SELECT key, value FROM memory")
        rows = cursor.fetchall()
        if rows:
            db_memory = " | ".join(f"{r[0]}: {r[1]}" for r in rows)
            return default_memory + " | " + db_memory
    except Exception:
        pass
    return default_memory


def _clean_ai_text(text):
    """Remove markdown formatting and fix encoding for spoken/displayed output."""
    if not text:
        return ""
    # Normalize unicode to ascii-friendly where possible
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    # Remove markdown symbols
    for ch in ["*", "#", "`", "_", "~", ">"]:
        text = text.replace(ch, "")
    # Remove excessive blank lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return " ".join(lines).strip()


def _build_full_system_prompt():
    """Combine system prompt with live memory for any AI engine."""
    return SYSTEM_AI_PROMPT + "\n\nUser Long-Term Memory: " + get_stored_memory()


def query_local_ollama(prompt):
    """Query local Ollama instance (100% private & offline)."""
    try:
        url = "http://127.0.0.1:11434/api/generate"
        payload = json.dumps({
            "model": "llama3.2:1b",
            "prompt": prompt,
            "system": _build_full_system_prompt(),
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            result = json.loads(response.read().decode("utf-8"))
            text = _clean_ai_text(result.get("response", ""))
            if text:
                print("AI Nabeel [Ollama]: responding...")
                return text
    except Exception:
        pass
    return None


def query_gemini_ai(prompt):
    """Query Google Gemini 1.5 Flash via REST API."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    # Only attempt if key looks like a real Gemini key (starts with AIzaSy)
    if not api_key or not api_key.startswith("AIzaSy"):
        return None
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={api_key}"
        )
        payload = json.dumps({
            "system_instruction": {"parts": [{"text": _build_full_system_prompt()}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.75,
                "maxOutputTokens": 400,
            },
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = _clean_ai_text(
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if text:
                print("AI Nabeel [Gemini]: responding...")
                return text
    except Exception as e:
        print(f"Gemini failed: {e}")
    return None


def query_pollinations_ai(prompt):
    """Query Pollinations AI JSON endpoint — supports system prompt injection."""
    try:
        url = "https://text.pollinations.ai/"
        system_prompt = _build_full_system_prompt()
        payload = json.dumps({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "model": "openai",
            "temperature": 0.75,
            "max_tokens": 400,
            "private": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read()
            text = _clean_ai_text(raw.decode("utf-8", errors="replace"))
            if text and "Payment Required" not in text and len(text) > 5:
                print("AI Nabeel [Pollinations]: responding...")
                return text
    except Exception as e:
        print(f"Pollinations JSON failed: {e}")

    # Fallback: GET endpoint with encoded system+user prompt combined
    try:
        combined = f"{_build_full_system_prompt()}\n\nUser: {prompt}\nAI Nabeel:"
        url2 = f"https://text.pollinations.ai/{urllib.parse.quote(combined)}?model=openai&private=true"
        req2 = urllib.request.Request(
            url2,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req2, timeout=12) as response2:
            raw2 = response2.read()
            text2 = _clean_ai_text(raw2.decode("utf-8", errors="replace"))
            if text2 and "Payment Required" not in text2 and len(text2) > 5:
                print("AI Nabeel [Pollinations-GET]: responding...")
                return text2
    except Exception as e2:
        print(f"Pollinations GET failed: {e2}")

    return None


def query_openrouter_ai(prompt):
    """Query OpenRouter free models (Llama 3.1 8B or similar) — no API key needed for free tier."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = json.dumps({
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": _build_full_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 400,
            "temperature": 0.75,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "AI Nabeel",
                "Authorization": "Bearer sk-or-v1-free",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = _clean_ai_text(
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if text and len(text) > 5:
                print("AI Nabeel [OpenRouter]: responding...")
                return text
    except Exception as e:
        print(f"OpenRouter failed: {e}")
    return None


def fetch_news_headlines(limit=5):
    """Fetch the latest top headlines from a live public RSS feed."""
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_text = response.read().decode("utf-8", errors="replace")
        root = ET.fromstring(xml_text)
        items = []
        for item in root.findall("./channel/item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = (item.findtext("description") or "").strip()
            if title:
                items.append({
                    "title": _clean_ai_text(title),
                    "link": link,
                    "description": _clean_ai_text(desc),
                })
        return items
    except Exception as exc:
        print(f"News fetch failed: {exc}")
        return []


def external_news_response(query):
    q = str(query).lower()
    if not any(keyword in q for keyword in ["news", "headlines", "breaking", "latest"]):
        return None

    items = fetch_news_headlines(limit=3)
    if not items:
        return None

    lines = ["Here are the latest headlines from live news sources:"]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item['title']}")
        if item.get("link"):
            lines.append(f"Source: {item['link']}")
    return "\n".join(lines)


def offline_fallback_response(query):
    q = query.lower().strip()
    sn = "Sir Nabeel"  # shorthand

    # ── Time / Date ────────────────────────────────────────────────────────
    if any(k in q for k in ["time", "current time", "what time"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}, {sn}."
    if any(k in q for k in ["date", "today's date", "what is today", "today date"]):
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}, {sn}."
    if "year" in q and "what" in q:
        return f"The current year is {datetime.datetime.now().year}, {sn}."

    # ── Identity: who am I ─────────────────────────────────────────────────
    if any(k in q for k in ["who am i", "my name", "know me", "tell me about me", "about myself", "about me"]):
        return (
            f"You are Sir Nabeel Muhammad, a 17-year-old vibe coder from Kollam, Kerala, India. "
            f"You are in Class 12 and the brilliant creator of this AI Nabeel assistant. "
            f"Your skills include HTML5, CSS3, JavaScript, Python, SQL, and AI integration."
        )

    # ── Identity: who are you ──────────────────────────────────────────────
    if any(k in q for k in ["who are you", "your name", "introduce yourself", "what are you", "what is your name"]):
        return (
            f"I am AI Nabeel, your personal AI assistant built exclusively for you, {sn}. "
            f"I am powered by neural intelligence and I know everything about your skills and projects. "
            f"Ask me anything about coding, development, or life!"
        )

    # ── Location ───────────────────────────────────────────────────────────
    if any(k in q for k in ["where am i", "my location", "where i live", "my place", "where are you from", "my city", "kerala", "kollam"]):
        return f"You are based in Kollam, Kerala, India, {sn}. It is a beautiful coastal city in God's own country!"

    # ── Skills ────────────────────────────────────────────────────────────
    if any(k in q for k in ["my skills", "what i know", "what can i do", "my abilities", "my tech stack"]):
        return (
            f"Your skills include HTML5, CSS3, JavaScript, Bootstrap 5, Python, and SQL with SQLite. "
            f"You also have experience with AI API integration, building desktop apps with Python Eel, and prompt engineering, {sn}."
        )

    # ── Python knowledge ──────────────────────────────────────────────────
    if "what is python" in q or ("python" in q and "what" in q and "is" in q):
        return (
            "Python is a high-level, easy-to-read programming language created by Guido van Rossum in 1991. "
            "It is used for web development, AI, automation, data science, scripting, and much more. "
            f"It is one of your strongest languages, {sn}!"
        )
    if "python" in q and "list" in q:
        return f"A Python list is an ordered, mutable collection. Example: my_list = [1, 2, 3]. You can append, remove, and slice lists easily, {sn}."
    if "python" in q and "function" in q:
        return f"In Python, you define a function using 'def'. Example: def greet(name): return 'Hello ' + name. Functions make your code reusable, {sn}!"
    if "python" in q and ("loop" in q or "for" in q):
        return f"Python for loops iterate over a sequence. Example: for i in range(5): print(i). This prints 0 to 4, {sn}."
    if "python" in q and "class" in q:
        return f"Python classes are blueprints for objects. Use 'class MyClass:' and define '__init__' as the constructor. OOP is powerful, {sn}!"
    if "python" in q and ("import" in q or "module" in q):
        return f"In Python, use 'import module_name' to bring in external code. Popular modules include os, json, datetime, and requests, {sn}."
    if "python" in q:
        return f"Python is your strongest tool, {sn}! It is great for automation, web scraping, AI, and backend development. What do you want to build?"

    # ── HTML knowledge ────────────────────────────────────────────────────
    if "what is html" in q or ("html" in q and "what" in q and "is" in q):
        return (
            "HTML stands for HyperText Markup Language. It is the standard language for creating web pages. "
            f"You use HTML tags like div, p, h1, and button to structure content, {sn}."
        )
    if "html" in q and ("form" in q or "input" in q):
        return f"HTML forms use the form tag with input elements. Add 'action' and 'method' attributes to handle submission, {sn}."
    if "html" in q and "semantic" in q:
        return f"Semantic HTML uses meaningful tags like header, nav, main, section, article, and footer instead of generic divs. It improves SEO and accessibility, {sn}."
    if "html" in q:
        return f"HTML is the backbone of every web page, {sn}. You build structure with tags and then style with CSS. What HTML topic do you need help with?"

    # ── CSS knowledge ─────────────────────────────────────────────────────
    if "what is css" in q or ("css" in q and "what" in q and "is" in q):
        return (
            "CSS stands for Cascading Style Sheets. It is used to style and layout HTML web pages. "
            f"You can control colors, fonts, spacing, animations, and responsive design with CSS, {sn}."
        )
    if "css" in q and "flexbox" in q:
        return f"CSS Flexbox is a layout model. Use 'display: flex' on a container, then control alignment with justify-content and align-items. Very powerful, {sn}!"
    if "css" in q and "grid" in q:
        return f"CSS Grid is a 2D layout system. Use 'display: grid' with grid-template-columns and rows to build complex layouts easily, {sn}."
    if "css" in q and ("animation" in q or "transition" in q):
        return f"CSS animations use @keyframes and the animation property. Transitions are smoother with 'transition: all 0.3s ease'. You already use this in your AI Nabeel UI, {sn}!"
    if "css" in q and ("glassmorphism" in q or "glass" in q):
        return f"Glassmorphism uses 'backdrop-filter: blur()' and semi-transparent backgrounds with rgba. Your AI Nabeel UI already has this style, {sn}!"
    if "css" in q:
        return f"CSS makes your websites beautiful, {sn}. You are skilled with Flexbox, Grid, animations, and glassmorphism. What CSS challenge are you working on?"

    # ── JavaScript knowledge ───────────────────────────────────────────────
    if "what is javascript" in q or ("javascript" in q and "what" in q and "is" in q):
        return (
            "JavaScript is the programming language of the web. It runs in the browser and makes web pages interactive. "
            f"It handles events, updates the DOM, and communicates with APIs, {sn}."
        )
    if ("javascript" in q or " js " in q) and "dom" in q:
        return f"The DOM is the Document Object Model. In JavaScript, use document.getElementById or document.querySelector to select and manipulate HTML elements, {sn}."
    if ("javascript" in q or " js " in q) and ("async" in q or "await" in q or "fetch" in q):
        return f"Async/await in JavaScript makes asynchronous code readable. Use 'async function' and 'await fetch()' to call APIs without blocking the UI, {sn}."
    if ("javascript" in q or " js " in q) and ("event" in q or "click" in q):
        return f"JavaScript events let you respond to user actions. Use addEventListener to handle clicks, keypresses, and more. Example: button.addEventListener('click', handler), {sn}."
    if "javascript" in q or "jquery" in q:
        return f"JavaScript is essential for web interactivity, {sn}. You already use it in your AI Nabeel frontend. What JS feature do you need help with?"

    # ── SQL / Database knowledge ───────────────────────────────────────────
    if "what is sql" in q or ("sql" in q and "what" in q and "is" in q):
        return (
            "SQL stands for Structured Query Language. It is used to create, read, update, and delete data in relational databases. "
            f"You use SQLite in your AI Nabeel project for memory storage, {sn}."
        )
    if "sql" in q and ("select" in q or "query" in q):
        return f"A basic SQL SELECT query looks like: SELECT * FROM table_name WHERE condition. You can filter, sort, and join data, {sn}."
    if "sql" in q and ("insert" in q or "add" in q):
        return f"To add data in SQL use: INSERT INTO table_name (column1, column2) VALUES (value1, value2). SQLite handles this perfectly, {sn}."
    if "sqlite" in q or ("database" in q and "python" in q):
        return f"SQLite is a lightweight file-based database. In Python, use 'import sqlite3' and 'sqlite3.connect()' to work with it. Your AI Nabeel already uses it for memory, {sn}."
    if "sql" in q or "database" in q:
        return f"SQL databases store data in tables. You use SQLite in this project. What database query or design do you need help with, {sn}?"

    # ── Bootstrap knowledge ───────────────────────────────────────────────
    if "bootstrap" in q:
        return f"Bootstrap is a CSS framework that gives you ready-made components and a grid system. Use classes like 'd-flex', 'container', 'btn', and 'col-md-6' to build responsive layouts quickly, {sn}."

    # ── Web development general ────────────────────────────────────────────
    if any(k in q for k in ["web development", "web dev", "frontend", "backend", "full stack", "fullstack"]):
        return (
            f"Web development splits into frontend (HTML, CSS, JS) and backend (Python, databases, APIs). "
            f"As a full-stack developer, you will work on both. You are already building strong frontend skills, {sn}!"
        )
    if "api" in q and "what" in q:
        return f"An API (Application Programming Interface) lets two programs talk to each other. REST APIs use HTTP requests to exchange data in JSON format. You already integrate AI APIs, {sn}!"
    if "responsive" in q:
        return f"Responsive design makes websites work on all screen sizes. Use CSS media queries, Flexbox, or Bootstrap grid to achieve this, {sn}."

    # ── AI / Machine Learning ──────────────────────────────────────────────
    if any(k in q for k in ["what is ai", "what is artificial intelligence"]):
        return (
            "Artificial Intelligence is the simulation of human intelligence in machines. "
            f"It includes machine learning, natural language processing, and computer vision. "
            f"You are already building AI-powered apps, {sn}. That is impressive for a 17-year-old!"
        )
    if "machine learning" in q or "ml" in q:
        return f"Machine Learning is a branch of AI where models learn from data. Libraries like scikit-learn, TensorFlow, and PyTorch are popular. You can start with scikit-learn, {sn}!"
    if "prompt engineering" in q:
        return f"Prompt engineering is the art of writing effective instructions for AI models to get better responses. It is one of your listed skills, {sn}, and very valuable in the AI age!"
    if any(k in q for k in ["llm", "large language model", "chatgpt", "gemini", "ai model"]):
        return f"Large Language Models like GPT-4 and Gemini are trained on huge datasets to understand and generate text. You integrate them into your projects, {sn}. That is cutting-edge work!"
    if any(k in q for k in ["ai", "machine learning", "api", "chatbot"]):
        return f"AI integration is your speciality, {sn}! You built this entire AI assistant. Keep exploring LLMs, APIs, and automation. The future is AI."

    # ── Git / Version control ──────────────────────────────────────────────
    if "git" in q or "github" in q or "version control" in q:
        return f"Git is a version control system. Use 'git init', 'git add .', 'git commit -m', and 'git push' to save and share your code. GitHub hosts your repos online, {sn}."

    # ── Career / Learning ──────────────────────────────────────────────────
    if any(k in q for k in ["career", "future", "job", "become a developer", "become programmer"]):
        return (
            f"At 17 with your skills, you are already ahead, {sn}! "
            f"Focus on building projects, learning React or Node.js next, and contributing to open source on GitHub. "
            f"Your future as a developer is very bright."
        )
    if any(k in q for k in ["what should i learn", "next skill", "learn next", "roadmap"]):
        return (
            f"Since you already know HTML, CSS, Python, and SQL, great next steps are: "
            f"JavaScript frameworks like React, backend with FastAPI or Django, and deploying apps to the cloud. "
            f"You are on the perfect track, {sn}!"
        )

    # ── Greetings ─────────────────────────────────────────────────────────
    if any(k in q for k in ["hello", "hi", "hey", "good morning", "good evening", "good night", "sup", "yo"]):
        hour = datetime.datetime.now().hour
        if hour < 12:
            greet = "Good morning"
        elif hour < 17:
            greet = "Good afternoon"
        else:
            greet = "Good evening"
        return f"{greet}, {sn}! I am online and ready to assist. What can I do for you?"

    if any(k in q for k in ["how are you", "how are you doing", "are you okay", "how do you feel"]):
        return f"I am running at full capacity and ready to assist you, {sn}. How can I help you today?"

    # ── Gratitude ─────────────────────────────────────────────────────────
    if any(k in q for k in ["thank you", "thanks", "thank u", "thx"]):
        return f"Always at your service, {sn}! Keep building great things. You are doing amazing!"

    # ── Motivation ────────────────────────────────────────────────────────
    if any(k in q for k in ["motivate", "inspire", "encourage", "feeling down", "tired", "stressed", "give up"]):
        return (
            f"You are only 17 and already building AI-powered desktop applications, {sn}. "
            f"That puts you ahead of most developers your age. Every great developer started exactly where you are. "
            f"Keep going. Your future is extraordinary!"
        )

    # ── Education ─────────────────────────────────────────────────────────
    if any(k in q for k in ["class 12", "study", "school", "exam", "timetable", "routine", "schedule", "board"]):
        return (
            f"As a Class 12 student and developer, balance is everything, {sn}. "
            f"Study academics in the morning with full focus, code your projects in the evening, and rest well at night. "
            f"Both your studies and coding career need your attention equally."
        )

    # ── Math ──────────────────────────────────────────────────────────────
    if any(k in q for k in ["calculate", "what is 2+2", "solve", "math", "equation"]):
        try:
            # Safe eval for simple math
            safe_q = q.replace("what is", "").replace("calculate", "").replace("solve", "").strip()
            # Only allow digits and basic operators
            import re
            if re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', safe_q):
                result = eval(safe_q)
                return f"The answer is {result}, {sn}."
        except Exception:
            pass
        return f"I can help with basic math calculations, {sn}. Please type the expression clearly."

    # ── General knowledge fallback ─────────────────────────────────────────
    if any(k in q for k in ["what is", "what are", "explain", "tell me about", "how does", "how do"]):
        topic = q.replace("what is", "").replace("what are", "").replace("explain", "").replace("tell me about", "").replace("how does", "").replace("how do", "").strip()
        return (
            f"That is a great question about '{topic}', {sn}! "
            f"I am currently working offline, but I know you have the skills to look this up and understand it quickly. "
            f"Would you like me to help you relate it to your coding or web development work?"
        )

    # ── Default ───────────────────────────────────────────────────────────
    return f"I am right here with you, {sn}! Ask me anything — coding, Python, HTML, CSS, SQL, AI, career, or anything else. I am your AI assistant."





def chatBot(query):
    query_str = str(query).strip()
    if not query_str:
        message = "I am listening, Sir Nabeel."
        speak(message)
        return message

    response_text = None

    # 1. Try live external news first for news-related questions
    response_text = external_news_response(query_str)

    # 2. Try local Ollama first (100% private & offline)
    if not response_text:
        response_text = query_local_ollama(query_str)

    # 3. Try Google Gemini 1.5 Flash (only if valid API key)
    if not response_text:
        response_text = query_gemini_ai(query_str)

    # 4. Try Pollinations AI with system prompt (JSON API — best free cloud option)
    if not response_text:
        response_text = query_pollinations_ai(query_str)

    # 5. Try OpenRouter free tier (Llama 3.1 8B)
    if not response_text:
        response_text = query_openrouter_ai(query_str)

    # 6. Smart contextual offline fallback (always works, no internet needed)
    if not response_text:
        response_text = offline_fallback_response(query_str)

    # Final clean — use _clean_ai_text for safety
    response_text = _clean_ai_text(response_text) or "I am here, Sir Nabeel. How can I help you?"

    try:
        clean_log = response_text.encode("ascii", "replace").decode("ascii")
        print(f"AI Nabeel: {clean_log}")
    except Exception:
        pass

    speak(response_text)
    return response_text
