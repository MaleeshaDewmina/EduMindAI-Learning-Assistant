/* Chat enhancements. Speech recognition is browser-provided; no custom audio storage. */
(() => {
  "use strict";
  const form = document.getElementById("chat-compose-form");
  if (!form) return;
  const input = document.getElementById("chat-message");
  const fileInput = document.getElementById("chat-attachment");
  const preview = document.getElementById("attachment-preview");
  const attachmentName = document.getElementById("attachment-name");
  const removeAttachment = document.getElementById("remove-attachment");
  const status = document.getElementById("chat-feature-status");
  const counter = document.getElementById("chat-character-count");
  const submit = document.getElementById("chat-send-btn");
  const mic = document.getElementById("voice-input-btn");
  const stopAudio = document.getElementById("voice-stop-btn");
  const chatWindow = document.getElementById("chat-window");
  const allowed = ["pdf", "docx", "txt", "md"];
  const sizeLimit = 5 * 1024 * 1024;
  const tell = message => { status.textContent = message; };
  let recognizer = null;
  let listening = false;

  const refreshLength = () => {
    counter.textContent = `${input.value.length} / 2000`;
    counter.classList.toggle("near-limit", input.value.length > 1800);
    input.style.height = "auto";
    input.style.height = `${Math.min(Math.max(input.scrollHeight, 65), 170)}px`;
  };
  input.addEventListener("input", refreshLength);
  refreshLength();
  if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

  document.querySelectorAll("[data-prompt]").forEach(button => {
    button.addEventListener("click", () => {
      input.value = button.dataset.prompt || "";
      refreshLength();
      input.focus();
    });
  });

  const resetAttachment = () => {
    fileInput.value = "";
    preview.hidden = true;
    attachmentName.textContent = "";
  };
  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) { resetAttachment(); return; }
    const ext = file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext) || file.size > sizeLimit) {
      tell("Please attach a PDF, DOCX, TXT or Markdown file no larger than 5 MB.");
      resetAttachment();
      return;
    }
    attachmentName.textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KB`;
    preview.hidden = false;
    tell("This document will be read in memory and its extracted text sent to the AI provider for this request.");
  });
  removeAttachment.addEventListener("click", resetAttachment);
  form.addEventListener("submit", event => {
    if (!input.value.trim() && !fileInput.files.length) {
      event.preventDefault();
      tell("Write a message or choose a study document first.");
      input.focus();
      return;
    }
    if (input.value.length > 2000) { event.preventDefault(); tell("Message must be under 2,000 characters."); return; }
    submit.disabled = true;
    submit.querySelector("span").textContent = "Thinking…";
    tell("Sending your question to EduMind AI. The page will refresh when it replies.");
  });
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); form.requestSubmit(); }
  });

  // SpeechRecognition support varies by browser and permission. No pretend voice support.
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    mic.disabled = true;
    mic.title = "Voice dictation is unavailable in this browser. Try an updated Chrome or Edge browser.";
    mic.setAttribute("aria-label", "Voice dictation unavailable in this browser");
  } else {
    mic.addEventListener("click", () => {
      if (listening && recognizer) { recognizer.stop(); return; }
      recognizer = new SpeechRecognition();
      recognizer.lang = navigator.language || "en-US";
      recognizer.continuous = false;
      recognizer.interimResults = false;
      recognizer.onstart = () => { listening = true; mic.classList.add("is-listening"); tell("Listening… speak your question. Click the microphone again to stop."); };
      recognizer.onresult = event => {
        const transcript = event.results[0][0].transcript;
        const draft = `${input.value.trim()} ${transcript}`.trim();
        input.value = draft.slice(0, 2000);
        refreshLength(); input.focus();
        tell("Voice transcription added. Review it before sending.");
      };
      recognizer.onerror = event => tell(`Voice input unavailable (${event.error}). Please type instead.`);
      recognizer.onend = () => { listening = false; mic.classList.remove("is-listening"); };
      try { recognizer.start(); } catch (_) { tell("Could not start the microphone. Check browser permissions."); }
    });
  }

  const supportedSpeech = "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  if (!supportedSpeech) {
    document.querySelectorAll("[data-read-reply]").forEach(b => { b.disabled = true; b.title = "Text-to-speech is unsupported in this browser"; });
    stopAudio.hidden = true;
  } else {
    const stop = () => { window.speechSynthesis.cancel(); stopAudio.hidden = true; };
    stopAudio.addEventListener("click", stop);
    document.querySelectorAll("[data-read-reply]").forEach(button => {
      button.addEventListener("click", () => {
        const node = document.getElementById(button.dataset.readReply);
        if (!node) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(node.textContent.trim());
        utterance.lang = document.documentElement.lang || "en";
        utterance.rate = 1;
        utterance.onend = () => { stopAudio.hidden = true; tell("Audio playback finished."); };
        utterance.onerror = () => { stopAudio.hidden = true; tell("Unable to read this response aloud."); };
        stopAudio.hidden = false;
        tell("Reading this answer aloud. Use Stop audio to stop playback.");
        window.speechSynthesis.speak(utterance);
      });
    });
    window.addEventListener("beforeunload", () => window.speechSynthesis.cancel());
  }

  document.querySelectorAll("[data-copy-reply]").forEach(button => {
    button.addEventListener("click", async () => {
      const node = document.getElementById(button.dataset.copyReply);
      if (!node) return;
      try {
        await navigator.clipboard.writeText(node.textContent.trim());
        tell("Response copied to clipboard.");
      } catch (_) { tell("Copy wasn't available. Select the text and copy it manually."); }
    });
  });
})();
