from pynput import keyboard, mouse
from PIL import ImageGrab, ImageChops
import time
import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pathlib import Path
import argparse
import tkinter as tk

IS_WINDOWS = sys.platform == 'win32'


def exclude_from_capture(win):
    """Hides a tk window from screen capture (Windows 10 2004+ only).
    Returns True on success, False if unsupported."""
    if not IS_WINDOWS:
        return False
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    win.update_idletasks()
    hwnd = user32.GetAncestor(win.winfo_id(), 2)  # GA_ROOT
    return bool(user32.SetWindowDisplayAffinity(hwnd, 0x11))  # WDA_EXCLUDEFROMCAPTURE


class ChangeObserver:
    def __init__(self, soundPath=None, screenshotDir=None, volume=1.0,
                 frameThickness=2, highlightTime=1.0):
        self.captureKeys = ['Key.ctrl', 'Key.ctrl_l', 'Key.ctrl_r']

        # Volume 0 disables sound completely (pygame isn't even loaded)
        self.sound = None
        volume = max(0.0, min(1.0, volume))
        if soundPath and volume > 0:
            import pygame
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound(str(resource_path(soundPath)))
            self.sound.set_volume(volume)

        self.screenshotDir = Path(screenshotDir) if screenshotDir else None
        if self.screenshotDir:
            self.screenshotDir.mkdir(exist_ok=True)

        self.changesCount = 0
        self.prevScreen = None

        # Initialized separately to prevent shared reference bugs
        self.mousePos1 = [0, 0]
        self.mousePos2 = [0, 0]

        self.mouse = mouse.Controller()
        self.mousePos1Captured = False
        self.klis = None

        self.frameThickness = max(0, frameThickness)
        self.highlightTime = max(0.0, highlightTime)
        self.overlay = None

    def _grabScreen(self, x1, y1, x2, y2):
        bbox = (x1, y1, x2, y2)
        return ImageGrab.grab(bbox=bbox, include_layered_windows=False, all_screens=True)

    def _onPress(self, key):
        key = str(key).strip("'")
        if key in self.captureKeys:
            # Read the actual current position, so it's correct even if
            # the mouse hasn't moved since the script started
            pos = list(self.mouse.position)
            if not self.mousePos1Captured:
                self.mousePos1 = pos
                self.mousePos1Captured = True
                print('Press "CTRL" to capture mouse position for second area corner')
                return True
            else:
                self.mousePos2 = pos
                return False  # stops the keyboard listener

    def captureCoords(self):
        self.mousePos1Captured = False
        print('Press "CTRL" to capture mouse position for first area corner')
        with keyboard.Listener(on_press=self._onPress) as self.klis:
            self.klis.join()

        # for observing one pixel
        if self.mousePos1 == self.mousePos2:
            self.mousePos2 = [self.mousePos2[0] + 1, self.mousePos2[1] + 1]

        # correction for reverse capture
        if self.mousePos1[0] > self.mousePos2[0]:
            self.mousePos1[0], self.mousePos2[0] = self.mousePos2[0], self.mousePos1[0]

        if self.mousePos1[1] > self.mousePos2[1]:
            self.mousePos1[1], self.mousePos2[1] = self.mousePos2[1], self.mousePos1[1]

        print()
        print(f"OK I'm observing changes on the screen between position [X:{self.mousePos1[0]} Y:{self.mousePos1[1]}] AND [X:{self.mousePos2[0]} Y:{self.mousePos2[1]}]...")

        self.prevScreen = self._grabScreen(self.mousePos1[0], self.mousePos1[1], self.mousePos2[0], self.mousePos2[1])

        if self.frameThickness > 0 or self.highlightTime > 0:
            self.overlay = AreaOverlay(self.mousePos1[0], self.mousePos1[1],
                                       self.mousePos2[0], self.mousePos2[1],
                                       thickness=self.frameThickness)

    def check(self):
        screen = self._grabScreen(self.mousePos1[0], self.mousePos1[1], self.mousePos2[0], self.mousePos2[1])
        if screen != self.prevScreen:
            self.changesCount += 1
            print(f"{time.localtime().tm_hour:02}:{time.localtime().tm_min:02}:{time.localtime().tm_sec:02} - change detected ({self.changesCount})")

            # Must run before prevScreen is overwritten
            if self.overlay and self.highlightTime > 0:
                box = ImageChops.difference(self.prevScreen, screen).getbbox()
                if box:
                    ox, oy = self.mousePos1
                    self.overlay.highlight(ox + box[0], oy + box[1],
                                           ox + box[2], oy + box[3],
                                           self.highlightTime)

            self.prevScreen = screen
            if self.screenshotDir:
                screen.save(self.screenshotDir / f"{self.changesCount}.png", 'PNG')
            if self.sound:
                self.sound.play()
            return True

        return False

    def wait(self, seconds):
        end = time.time() + seconds
        while True:
            if self.overlay:
                self.overlay.update()
            remaining = end - time.time()
            if remaining <= 0:
                break
            time.sleep(min(0.05, remaining))


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller/Nuitka onefile."""
    path = Path(relative_path)
    if path.is_absolute():
        return path

    # Nuitka and PyInstaller expose sys._MEIPASS when running in onefile mode
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return base_path / path


def _strips(x1, y1, x2, y2, t):
    """Four (w, h, x, y) rectangles forming a frame just outside the box."""
    w, h = x2 - x1, y2 - y1
    return [
        (w + 2 * t, t, x1 - t, y1 - t),  # top
        (w + 2 * t, t, x1 - t, y2),      # bottom
        (t, h, x1 - t, y1),              # left
        (t, h, x2, y1),                  # right
    ]


class AreaOverlay:
    """Frame around the observed area + temporary highlight of detected changes."""
    def __init__(self, x1, y1, x2, y2, thickness=2, color='red',
                 highlightColor='lime', highlightThickness=2):
        self.root = tk.Tk()
        self.root.withdraw()
        self.highlightThickness = highlightThickness
        self.highlightUntil = 0.0

        self.windows = []
        if thickness > 0:
            for sw, sh, sx, sy in _strips(x1, y1, x2, y2, thickness):
                self.windows.append(self._makeStrip(color, sw, sh, sx, sy))

        # The highlight lies inside the observed area, so it must be invisible
        # to screen capture, otherwise it would trigger false changes.
        # That is only possible on Windows 10 2004+.
        self.hlWindows = [self._makeStrip(highlightColor, 1, 1, 0, 0, hidden=True)
                          for _ in range(4)]
        self.highlightOk = all([exclude_from_capture(w) for w in self.hlWindows])
        if not self.highlightOk:
            print("Warning: change highlight is not supported on this system "
                  "(needs Windows 10 2004+). Highlight disabled.")
        self.root.update()

    def _makeStrip(self, color, w, h, x, y, hidden=False):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.configure(bg=color)
        win.geometry(f"{w}x{h}+{x}+{y}")
        if hidden:
            win.withdraw()
        return win

    def highlight(self, x1, y1, x2, y2, seconds):
        if not self.highlightOk:
            return
        pad = 2  # keep the frame off the changed pixels
        strips = _strips(x1 - pad, y1 - pad, x2 + pad, y2 + pad, self.highlightThickness)
        for win, (sw, sh, sx, sy) in zip(self.hlWindows, strips):
            win.geometry(f"{sw}x{sh}+{sx}+{sy}")
            win.deiconify()
            win.attributes('-topmost', True)
        self.highlightUntil = time.time() + seconds

    def update(self):
        if self.highlightUntil and time.time() >= self.highlightUntil:
            for win in self.hlWindows:
                win.withdraw()
            self.highlightUntil = 0.0
        self.root.update()

    def close(self):
        self.root.destroy()


if __name__ == '__main__':
    if IS_WINDOWS:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)

    arg_parser = argparse.ArgumentParser(
        prog='Change Observer',
        description='Monitors a selected region of your screen for visual changes. Alerts you via sound and/or saves a screenshot when a change is detected.',
    )

    arg_parser.add_argument('-p', '--period', type=float, default=0.1,
                            help='Time in seconds between screen checks (default: 0.1)')
    arg_parser.add_argument('-c', '--cooldown', type=float, default=1.0,
                            help='Cooldown time in seconds to cooldown AFTER a change is detected before resuming checks (default: 1.0)')
    arg_parser.add_argument('-o', '--output', type=str, default='',
                            help='Directory path to save screenshots of detected changes. If omitted, no screenshots are saved.')
    arg_parser.add_argument('-v', '--volume', type=float, default=1.0,
                            help='Sound volume from 0.0 to 1.0. Use 0 to disable sound (default: 1.0)')
    arg_parser.add_argument('-s', '--soundpath', type=str, default='',
                            help='Path to a custom sound file to play on change.')
    arg_parser.add_argument('-t', '--thickness', type=int, default=2,
                            help='Thickness in pixels of the frame drawn around the observed area. '
                                 'Use 0 to disable the frame (default: 2)')
    arg_parser.add_argument('-H', '--highlight', type=float, default=2, help='Seconds to highlight the part of the area where a change was detected (Windows 10 2004+ only). Use 0 to disable (default: 2)')

    args = arg_parser.parse_args()

    print("---CHANGE OBSERVER---")

    soundPath = args.soundpath or 'notification.wav'

    changeObserver = ChangeObserver(
        soundPath=soundPath,
        screenshotDir=args.output or None,
        volume=args.volume,
        frameThickness=args.thickness,
        highlightTime=args.highlight
    )

    period = args.period
    cooldown = args.cooldown
    changeObserver.captureCoords()
    while True:
        if changeObserver.check():
            changeObserver.wait(cooldown)
        else:
            changeObserver.wait(period)