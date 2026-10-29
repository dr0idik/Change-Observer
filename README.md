# Change Observer 👁️
Python script that monitors a specific region of your screen for visual changes. When a change is detected, it can alert you with a sound notification and/or automatically save a screenshot of the new state.

## Features
- **Interactive Region Selection**: Simply point your mouse and press `CTRL` to draw the bounding box you want to monitor.
- **Audio Alerts**: Plays a notification sound immediately when a change happens.
- **Screenshot Logging**: Optionally saves images of every recorded change to a specified directory.
- **Configurable Polling & Cooldowns**: Control exactly how often the script checks the screen and how long it waits after detecting a change.

<img width="1126" height="296" alt="image" src="https://github.com/user-attachments/assets/146fcfb7-2a56-4a7b-a198-2585ae5d3185" />

### [Download](https://github.com/DroidExter/Change-Observer/releases/latest/download/Change_Observer.exe)
> [!WARNING]
> Some antivirus programs may falsely evaluate this file as positive 😕

### Usage
```
usage: Change Observer [-h] [-p PERIOD] [-c COOLDOWN] [-o OUTPUT] [-v VOLUME] [-s SOUNDPATH] [-t THICKNESS]
                       [-H HIGHLIGHT]

Monitors a selected region of your screen for visual changes. Alerts you via sound and/or saves a screenshot when
a change is detected.

options:
  -h, --help            show this help message and exit
  -p, --period PERIOD   Time in seconds between screen checks (default: 0.1)
  -c, --cooldown COOLDOWN
                        Cooldown time in seconds to cooldown AFTER a change is detected before resuming checks
                        (default: 1.0)
  -o, --output OUTPUT   Directory path to save screenshots of detected changes. If omitted, no screenshots are
                        saved.
  -v, --volume VOLUME   Sound volume from 0.0 to 1.0. Use 0 to disable sound (default: 1.0)
  -s, --soundpath SOUNDPATH
                        Path to a custom sound file to play on change.
  -t, --thickness THICKNESS
                        Thickness in pixels of the frame drawn around the observed area. Use 0 to disable the
                        frame (default: 2)
  -H, --highlight HIGHLIGHT
                        Seconds to highlight the part of the area where a change was detected (Windows 10 2004+
                        only). Use 0 to disable (default: 2)
```
## Build EXE
```ps1
uv run pyinstaller --onefile --add-data "notification.wav;." --icon=icon.ico main.py
```
