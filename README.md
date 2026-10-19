# Change Observer 👁️
Python script that monitors a specific region of your screen for visual changes. When a change is detected, it can alert you with a sound notification and/or automatically save a screenshot of the new state.

## Features
- **Interactive Region Selection**: Simply point your mouse and press `CTRL` to draw the bounding box you want to monitor.
- **Audio Alerts**: Plays a notification sound immediately when a change happens.
- **Screenshot Logging**: Optionally saves images of every recorded change to a specified directory.
- **Configurable Polling & Cooldowns**: Control exactly how often the script checks the screen and how long it waits after detecting a change.

![change_observer](https://github.com/DroidExter/Change-Observer/assets/73828018/d424fc7a-ecb1-4584-afc2-829ea05f3b01)

## [Download](https://github.com/DroidExter/Change-Observer/releases/latest/download/Change_Observer.exe)

## Build EXE
```ps1
uv run nuitka --onefile --include-data-files=notification.wav=notification.wav --windows-icon-from-ico=icon.ico main.py
```
