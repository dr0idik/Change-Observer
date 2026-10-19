from pynput import keyboard, mouse
from PIL import ImageGrab
import time
import sys
from playsound3 import playsound
from pathlib import Path
import argparse

class ChangeObserver:
    def __init__(self, soundPath=None, screenshotDir=None):
        self.captureKeys = ['Key.ctrl', 'Key.ctrl_l', 'Key.ctrl_r']

        self.soundPath = str(resource_path(soundPath)) if soundPath else None

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

    def check(self):
        screen = self._grabScreen(self.mousePos1[0], self.mousePos1[1], self.mousePos2[0], self.mousePos2[1])
        if screen != self.prevScreen:
            self.changesCount += 1
            print(f"{time.localtime().tm_hour:02}:{time.localtime().tm_min:02}:{time.localtime().tm_sec:02} - change detected ({self.changesCount})")
            self.prevScreen = screen
            if self.screenshotDir:
                screen.save(Path(self.screenshotDir)/f"{self.changesCount}.png", 'PNG')
            if self.soundPath:
                playsound(self.soundPath, block=False)
            return True
        
        else:
            return False
                

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller/Nuitka onefile."""
    path = Path(relative_path)
    if path.is_absolute():
        return path
    
    # Nuitka and PyInstaller expose sys._MEIPASS when running in onefile mode
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return base_path / path


if __name__ == '__main__':

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
    arg_parser.add_argument('-s', '--soundpath', type=str, default='', 
                            help='Path to a custom sound file to play on change.')
    arg_parser.add_argument('--nosound', action='store_true', 
                            help='Disable sound playback when a change is detected.')

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
        screenshotDir = args.output or None  
    )

    period = args.period
    cooldown = args.cooldown
    changeObserver.captureCoords()
    while True:
        if changeObserver.check():
            time.sleep(cooldown)
        else:
            time.sleep(period)
