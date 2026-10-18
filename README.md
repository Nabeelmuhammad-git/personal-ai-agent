# AI Nabeel

<img width="1280" height="563" alt="Image" src="https://github.com/user-attachments/assets/0bffe15a-fdf8-4ab0-a6bf-428b46689621" />
An interactive desktop application built with Python and Eel, featuring a stunning black background with white constellation effects.

## Requirements

- **Python 3.10.7 or higher**
- Windows/Mac/Linux

## Installation

### 1. Verify Python Version

```bash
python --version
```

Should show Python 3.10.7 or higher.

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

Or using the editable setup:

```bash
pip install -e .
```

### 3. Optional Assistant Extras

Voice and audio features use browser speech recognition first, with optional
Python packages such as `SpeechRecognition`, `pyttsx3`, and `pygame` as
fallbacks for local assistant features. On Python 3.14, `pygame` may be
unavailable, so the app will still start but skip the startup sound
automatically.

## Running the Application

```bash
python main.py
```

The application will start on `http://localhost:8000`

When you use the mic button, allow microphone access in the browser window if
prompted.

## Project Structure

```
ai nabeel/
├── main.py                 # Backend with Eel
├── requirements.txt        # Project dependencies
├── pyproject.toml         # Project configuration
├── .python-version        # Python version specification
├── frontend/
│   ├── index.html         # Frontend HTML
│   ├── style.css          # Styling with constellation background
│   ├── main.js            # JavaScript with particle effects
│   └── assets/            # Static assets
└── README.md              # This file
```

## Features

- **Beautiful UI**: Black background with white constellation effects
- **Particle System**: 3D rotating particle sphere
- **Python-JavaScript Bridge**: Use Eel for seamless communication
- **Modern Design**: Responsive and visually appealing interface

## Available Python Functions (Exposed to JavaScript)

### `initialize_app()`
Starts the UI flow and face-authentication handshake.

### `takeAllCommands(message=None)`
Processes either typed or voice commands.

## Development

### Calling Python from JavaScript

```javascript
eel.takeAllCommands("open youtube")();
```

### Calling JavaScript from Python

```python
eel.js_function_name(arg1, arg2)
```

## License

MIT License

## Support

For issues and questions, please visit the GitHub repository.
