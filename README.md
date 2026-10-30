# Desktop Handsfree Assistant

> A privacy-first, free, and open-source "Alexa" for Desktop.

Desktop Handsfree Assistant is a voice-controlled desktop automation system. It listens for a configured wake word, converts speech to text, performs supported actions, and responds with synthesized speech.

## Features

- Local wake-word detection, speech recognition, and text-to-speech
- Desktop automation, application control, media, and volume controls
- Web search, timers, reminders, and scheduled tasks
- React desktop overlay with live status and transcripts
- Python backend connected to the frontend through WebSockets

## Project Structure

```text
desktop-handsfree-assistant/
├── app/         # Neutralino desktop wrapper
├── backend/     # Python voice and automation engine
├── frontend/    # React and TypeScript desktop overlay
└── release/     # Packaged release files
```

## Build

Run the bundler from the project root:

```powershell
.\bundle.ps1
```

The packaged app is created in `release/HandsfreeAssistant/`.
