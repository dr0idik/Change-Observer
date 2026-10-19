from pynput import keyboard, mouse
from PIL import ImageGrab
import time
import sys
from pygame import mixer
from pathlib import Path
import argparse

class ChangeObserver:
    def __init__(self, soundPath=None, screenshotDir = None):
        self.captureKeys = ['Key.ctrl', 'Key.ctrl_l', 'Key.ctrl_r']

        if soundPath:
            mixer.init()
            self.soundPlayer = mixer.Sound(resource_path(soundPath))
        else:
            self.soundPlayer = None

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
        print(key)
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
            print(f"Change {self.changesCount} detected - {time.localtime().tm_hour:02}:{time.localtime().tm_min:02}:{time.localtime().tm_sec:02}")
            self.prevScreen = screen
            if self.screenshotDir:
                screen.save(fr"{self.screenshotDir}/screenshot{self.changesCount}.png", 'PNG')
            if self.soundPlayer:
                self.soundPlayer.play()
                

# for PyInstaller
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent

    return Path(base_path)/relative_path


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        prog='Change Observer',
        description='',
    )

    arg_parser.add_argument('-p', '--period', type=float, default=0.1)
    arg_parser.add_argument('-o', '--output', type=str, default='')
    arg_parser.add_argument('--nosound', action='store_true')
    arg_parser.add_argument('-s', '--soundpath', type=str, default='')

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
    changeObserver.captureCoords()
    while True:
        changeObserver.check()
        time.sleep(period)
