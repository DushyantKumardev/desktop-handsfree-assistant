# Desktop Handsfree Assistant

> A privacy-first, free, and open-source "Hey Google" for Desktop.

## Vision
An always-listening or push-to-talk voice assistant running on your personal computer that controls workflows, launches applications, and manages desktop automation without sending your private voice recordings or screen activity to third-party ad networks.

## Architecture & Project Structure
This repository is organized as a modular monorepo:

```text
desktop-handsfree-assistant/
├── app/         # Desktop application wrapper (Neutralino / Tauri / Electron)
├── backend/     # Python voice & automation engine (STT, TTS, agent, automation)
├── frontend/    # React desktop interface
├── .editorconfig
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started
Follow the step-by-step setup guides inside each corresponding subfolder as modules are developed.
