const byId = (id) => document.getElementById(id);
const BrowserSpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;
let activeRecognition = null;
let isListening = false;

function setHidden(id, hidden) {
  const element = byId(id);
  if (element) {
    element.hidden = hidden;
  }
}

function setText(id, text) {
  const element = byId(id);
  if (element) {
    element.textContent = text;
  }
}

function appendMessage(text, type) {
  const container = byId("response");
  if (!container || !text) {
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className =
    type === "sender"
      ? "d-flex justify-content-end mb-2"
      : "d-flex justify-content-start mb-2";

  const bubble = document.createElement("div");
  bubble.className =
    type === "sender"
      ? "sender_message width-size"
      : "receiver_message width-size";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
}

function setAgentStatus(active, text = "Agent is thinking...") {
  const status = byId("AgentStatus");
  const statusText = byId("AgentStatusText");
  if (!status || !statusText) {
    return;
  }

  statusText.textContent = text;
  status.hidden = !active;
}

function showAssistant() {
  setHidden("Start", true);
  setHidden("SiriWave", true);
  setHidden("Oval", false);
  setAgentStatus(false);
}

function showWave(message = "Listening...") {
  setHidden("Oval", true);
  setHidden("SiriWave", false);
  setText("SiriMessage", message);
}

function clearConversation() {
  const container = byId("response");
  if (container) {
    container.innerHTML = "";
  }

  setAgentStatus(false);
}

function DisplayMessage(text) {
  setText("WishMessage", text);
  setText("SiriMessage", text);
}

function speakAloud(text) {
  if (!window.speechSynthesis || !text) {
    return;
  }
  try {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#`_~]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(
      (v) =>
        v.lang &&
        v.lang.startsWith("en") &&
        (v.name.includes("Natural") ||
          v.name.includes("Online") ||
          v.name.includes("Google") ||
          v.name.includes("Zira") ||
          v.name.includes("David"))
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => {
      setAgentStatus(true, "AI Nabeel is speaking...");
    };
    utterance.onend = () => {
      setAgentStatus(false);
    };
    utterance.onerror = () => {
      setAgentStatus(false);
    };

    window.speechSynthesis.speak(utterance);
  } catch (error) {
    console.warn("Speech synthesis unavailable:", error);
  }
}

if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}

function receiverText(text) {
  setAgentStatus(false);
  appendMessage(text, "receiver");
  speakAloud(text);
}

function senderText(text) {
  appendMessage(text, "sender");
}

function hideLoader() {
  setHidden("Loader", true);
  setHidden("FaceAuth", false);
  setText("WishMessage", "Ready for face authentication");
}

function showBackupPassword() {
  setHidden("Start", false);
  setHidden("Loader", true);
  setHidden("FaceAuth", true);
  setHidden("FaceAuthSuccess", true);
  setHidden("HelloGreet", true);
  setHidden("BackupPassword", false);
  setText("WishMessage", "Backup authentication required");

  const input = byId("backupPasswordInput");
  if (input) {
    input.value = "";
    input.focus();
  }
}

function hideBackupPassword() {
  setHidden("BackupPassword", true);
  setText("WishMessage", "Backup password accepted");
  setHidden("HelloGreet", false);
}

function hideFaceAuth() {
  setHidden("FaceAuth", true);
  setHidden("FaceAuthSuccess", false);
  setText("WishMessage", "Face recognized successfully");
}

function hideFaceAuthSuccess() {
  setHidden("FaceAuthSuccess", true);
  setHidden("HelloGreet", false);
}

function hideStart() {
  showAssistant();
}

function ShowHood() {
  showAssistant();
}

function registerPythonCallbacks() {
  if (!window.eel) {
    return;
  }

  eel.expose(DisplayMessage);
  eel.expose(receiverText);
  eel.expose(senderText);
  eel.expose(hideLoader);
  eel.expose(showBackupPassword);
  eel.expose(hideBackupPassword);
  eel.expose(hideFaceAuth);
  eel.expose(hideFaceAuthSuccess);
  eel.expose(hideStart);
  eel.expose(ShowHood);
}

function setupSiriWave() {
  if (!window.SiriWave) {
    return;
  }

  const container = byId("siri-container");
  if (!container) {
    return;
  }

  new SiriWave({
    container,
    width: 640,
    height: 180,
    speed: 0.08,
    amplitude: 0.8,
    style: "ios9",
    color: "#c52fff",
    autostart: true,
  });
}

function submitTextCommand() {
  const input = byId("chatbox");
  if (!input) {
    return;
  }

  const message = input.value.trim();
  if (!message) {
    DisplayMessage("Please type a command first.");
    return;
  }

  input.value = "";
  senderText(message);
  setAgentStatus(true, "AI Nabeel is thinking...");

  if (window.eel && typeof eel.takeAllCommands === "function") {
    eel.takeAllCommands(message)();
    return;
  }

  setAgentStatus(false);
}

function submitRecognizedCommand(message) {
  const normalizedMessage = String(message || "").trim();
  if (!normalizedMessage) {
    DisplayMessage("I did not catch that.");
    showAssistant();
    return;
  }

  senderText(normalizedMessage);
  showAssistant();

  if (window.eel && typeof eel.takeAllCommands === "function") {
    setAgentStatus(true, "AI Nabeel is thinking...");
    eel.takeAllCommands(normalizedMessage)();
    return;
  }

  DisplayMessage("Voice input is not available.");
  showAssistant();
}

function stopVoiceRecognition() {
  if (activeRecognition) {
    activeRecognition.onstart = null;
    activeRecognition.onresult = null;
    activeRecognition.onerror = null;
    activeRecognition.onend = null;
    activeRecognition.stop();
    activeRecognition = null;
  }

  isListening = false;
}

function submitVoiceCommand() {
  if (isListening) {
    stopVoiceRecognition();
    showAssistant();
    DisplayMessage("Voice recognition stopped.");
    return;
  }

  showWave("Listening...");

  if (BrowserSpeechRecognition) {
    const recognition = new BrowserSpeechRecognition();
    activeRecognition = recognition;
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isListening = true;
      DisplayMessage("Listening...");
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join(" ")
        .trim();

      if (transcript) {
        setText("SiriMessage", transcript);
      }

      const latestResult = event.results[event.results.length - 1];
      if (latestResult?.isFinal) {
        stopVoiceRecognition();
        submitRecognizedCommand(transcript);
      }
    };

    recognition.onerror = (event) => {
      stopVoiceRecognition();

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        DisplayMessage("Microphone permission is blocked. Please allow microphone access.");
      } else if (event.error === "no-speech") {
        DisplayMessage("No speech was detected. Please try again.");
      } else if (event.error === "audio-capture") {
        DisplayMessage("No microphone was found for voice recognition.");
      } else {
        DisplayMessage("Voice recognition failed. Please try again or type your command.");
      }

      showAssistant();
    };

    recognition.onend = () => {
      const wasListening = isListening;
      stopVoiceRecognition();
      if (wasListening) {
        showAssistant();
      }
    };

    recognition.start();
    return;
  }

  if (window.eel && typeof eel.takeAllCommands === "function") {
    eel.takeAllCommands()();
    return;
  }

  DisplayMessage("Voice input is not available.");
  showAssistant();
}

function attachEvents() {
  const chatButton = byId("ChatBtn");
  const micButton = byId("MicBtn");
  const resetButton = byId("SettingBtn");
  const input = byId("chatbox");
  const backupPasswordButton = byId("BackupPasswordBtn");
  const backupPasswordInput = byId("backupPasswordInput");

  if (chatButton) {
    chatButton.addEventListener("click", submitTextCommand);
  }

  if (micButton) {
    micButton.addEventListener("click", submitVoiceCommand);
  }

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      clearConversation();
      DisplayMessage("Conversation cleared.");
    });
  }

  if (input) {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submitTextCommand();
      }
    });
  }

  if (backupPasswordButton) {
    backupPasswordButton.addEventListener("click", async () => {
      const value = backupPasswordInput ? backupPasswordInput.value : "";
      if (!value) {
        DisplayMessage("Please enter the backup password.");
        return;
      }

      try {
        const valid = await eel.verify_backup_password(value)();
        if (valid) {
          setHidden("BackupPassword", true);
          setText("WishMessage", "Backup password accepted");
          showAssistant();
          DisplayMessage("Welcome to your assistant");
          return;
        }

        DisplayMessage("Invalid backup password. Please try again.");
        if (backupPasswordInput) {
          backupPasswordInput.value = "";
          backupPasswordInput.focus();
        }
      } catch (error) {
        console.error("Backup password verification failed:", error);
        DisplayMessage("Password check failed. Please try again.");
      }
    });
  }

  if (backupPasswordInput) {
    backupPasswordInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        backupPasswordButton?.click();
      }
    });
  }
}

async function bootApp() {
  if (!window.eel || typeof eel.initialize_app !== "function") {
    DisplayMessage("Frontend loaded without the Eel bridge.");
    showAssistant();
    return;
  }

  try {
    await eel.initialize_app()();
  } catch (error) {
    console.error("Failed to initialize the app:", error);
    DisplayMessage("App startup failed. Check the Python console for details.");
    showAssistant();
  }
}

window.addEventListener("DOMContentLoaded", () => {
  registerPythonCallbacks();
  setupSiriWave();
  attachEvents();
  bootApp();
});
