from pynput import keyboard, mouse
from PIL import ImageGrab
import time
import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pathlib import Path
import argparse
import tkinter as tk
import ctypes


class ChangeObserver:
    def __init__(self, soundPath=None, screenshotDir=None, volume=1.0, frameThickness=2):
        self.captureKeys = ['Key.ctrl', 'Key.ctrl_l', 'Key.ctrl_r']

        self.sound = None
        if soundPath:
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound(str(resource_path(soundPath)))
            self.sound.set_volume(max(0.0, min(1.0, volume)))

        self.screenshotDir = Path(screenshotDir) if screenshotDir else None
        if self.screenshotDir:
            self.screenshotDir.mkdir(exist_ok=True)

        self.changesCount = 0
        self.prevScreen = None
        
        # Initialized separately to prevent shared reference bugs
        self.mousePos = [0, 0]
        self.mousePos1 = [0, 0]
        self.mousePos2 = [0, 0]
        
        self.mousePos1Captured = False
        self.klis = None
        self.mlis = None

        self.frameThickness = max(0, frameThickness)
        self.overlay = None

    def _grabScreen(self, x1,y1,x2,y2):
        bbox = (x1,y1,x2,y2)
        im = ImageGrab.grab(bbox=bbox, include_layered_windows=False, all_screens=True)
        return im

    def _getCoord(self, x,y):
        global mousePos
        mousePos = [x,y]     

    def _onPress(self, key):
        key = str(key).strip("'")
        if key in self.captureKeys:
            if not self.mousePos1Captured:
                self.mousePos1 = mousePos
                self.mousePos1Captured = True
                print('Press "CTRL" to capture mouse position for second area corner')
                return True
            else:
                self.mousePos2 = mousePos
                self.mlis.stop()
                self.klis.stop()  
                return False
            
    def captureCoords(self):
        self.mousePos1Captured = False
        print('Press "CTRL" to capture mouse position for first area corner')
        with keyboard.Listener(on_press = self._onPress) as self.klis:
            with mouse.Listener(on_move = self._getCoord) as self.mlis:
                self.klis.join()
                self.mlis.join()
        
         # for observing one pixel
        if self.mousePos1 == self.mousePos2:
            self.mousePos2 = [self.mousePos2[0]+1,self.mousePos2[1]+1]

        # correction for reverse capture
        if self.mousePos1[0] > self.mousePos2[0]:
            self.mousePos1[0], self.mousePos2[0] = self.mousePos2[0], self.mousePos1[0]

        if self.mousePos1[1] > self.mousePos2[1]:
            self.mousePos1[1], self.mousePos2[1] = self.mousePos2[1], self.mousePos1[1]

        print()
        print(f"OK I'm observing changes on the screen between position [X:{self.mousePos1[0]} Y:{self.mousePos1[1]}] AND [X:{self.mousePos2[0]} Y:{self.mousePos2[1]}]...")
        
        self.prevScreen = self._grabScreen(self.mousePos1[0], self.mousePos1[1], self.mousePos2[0], self.mousePos2[1])

        if self.frameThickness > 0:
            self.overlay = AreaOverlay(self.mousePos1[0], self.mousePos1[1],
                                    self.mousePos2[0], self.mousePos2[1],
                                    thickness=self.frameThickness)

    def check(self):
        screen = self._grabScreen(self.mousePos1[0], self.mousePos1[1], self.mousePos2[0], self.mousePos2[1])
        if screen != self.prevScreen:
            self.changesCount += 1
            print(f"{time.localtime().tm_hour:02}:{time.localtime().tm_min:02}:{time.localtime().tm_sec:02} - change detected ({self.changesCount})")
            self.prevScreen = screen
            if self.screenshotDir:
                screen.save(Path(self.screenshotDir)/f"{self.changesCount}.png", 'PNG')
            if self.sound:
                self.sound.play()
            return True
        
        else:
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


class AreaOverlay:
    """Draws a frame around the observed area, just outside of it."""
    def __init__(self, x1, y1, x2, y2, color='red', thickness=2):
        self.root = tk.Tk()
        self.root.withdraw()
        t = thickness
        w, h = x2 - x1, y2 - y1

        # (width, height, x, y)
        strips = [
            (w + 2*t, t, x1 - t, y1 - t),  # top
            (w + 2*t, t, x1 - t, y2),      # bottom
            (t, h, x1 - t, y1),            # left
            (t, h, x2, y1),                # right
        ]
        
        self.windows = []
        for sw, sh, sx, sy in strips:
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes('-topmost', True)
            win.configure(bg=color)
            win.geometry(f"{sw}x{sh}+{sx}+{sy}")
            self.windows.append(win)
        self.root.update()

    def update(self):
        self.root.update()

    def close(self):
        self.root.destroy()

if __name__ == '__main__':
    if sys.platform == 'win32':
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
                        help='Sound volume from 0.0 (silent) to 1.0 (full), default: 1.0')
    arg_parser.add_argument('-s', '--soundpath', type=str, default='', 
                            help='Path to a custom sound file to play on change.')
    arg_parser.add_argument('--nosound', action='store_true', 
                            help='Disable sound playback when a change is detected.')
    arg_parser.add_argument('-t', '--thickness', type=int, default=2, help='Thickness in pixels of the frame drawn around the observed area. Use 0 to disable the frame (default: 2)')

    args = arg_parser.parse_args()

    print("---CHANGE OBSERVER---")

    if args.nosound:
        soundPath = None
    elif args.soundpath:
        soundPath = args.soundpath
    else:
        soundPath = 'notification.wav'

    changeObserver = ChangeObserver(
        soundPath = soundPath,
        screenshotDir = args.output or None,
        volume = args.volume,
        frameThickness = args.thickness
    )

    period = args.period
    cooldown = args.cooldown
    changeObserver.captureCoords()
    while True:
        if changeObserver.check():
            changeObserver.wait(cooldown)
        else:
            changeObserver.wait(period)
