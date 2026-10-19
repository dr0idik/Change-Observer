# Change Observer 👁️
Python script that monitors a specific region of your screen for visual changes. When a change is detected, it can alert you with a sound notification and/or automatically save a screenshot of the new state.

## Features
- **Interactive Region Selection**: Simply point your mouse and press `CTRL` to draw the bounding box you want to monitor.
- **Audio Alerts**: Plays a notification sound immediately when a change happens.
- **Screenshot Logging**: Optionally saves images of every recorded change to a specified directory.
- **Configurable Polling & Cooldowns**: Control exactly how often the script checks the screen and how long it waits after detecting a change.

<img width="1126" height="296" alt="image" src="https://github.com/user-attachments/assets/146fcfb7-2a56-4a7b-a198-2585ae5d3185" />

### [Download](https://github.com/DroidExter/Change-Observer/releases/latest/download/Change_Observer.exe)

## Build EXE
```ps1
uv run pyinstaller --onefile --add-data "notification.wav;." --icon=icon.ico main.py
```
