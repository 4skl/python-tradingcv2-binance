import cv2, sys, datetime, time
import numpy as np
from trading import *
# first argument is symbol
# draw candlestick based on -t <s, default: 5> seconds intervals, and with a duration of -d <d, default: 5> minutes

_windowName = "Candles"
_default_width = 1600
_default_height = 800
_base_font = cv2.FONT_HERSHEY_DUPLEX
_FPS = 15

# utils to standardize
import win32gui
get_window_rect = lambda name: win32gui.GetWindowRect(win32gui.FindWindow(None, name))

# parsing arguments
_symbol = sys.argv[1]

#...
global _t
global _d
_t = 5.0 # seconds
_d = 5.0*60 # seconds
_ut = 0.5 # seconds


try:
    i = sys.argv.index('-t')
    _t = float(sys.argv[i+1])
except ValueError:
    print(f"Candle duration default value {_t} seconds")

try:
    i = sys.argv.index('-d')
    _d = float(sys.argv[i+1])*60
except ValueError:
    print(f"View duration default value {_d} seconds")
# check timestamp, ms,...

# cv2 shortcuts
# Create a black image
blank_img = lambda width=512, height=512: cv2.cvtColor(np.zeros((height,width,3), np.uint8), cv2.COLOR_RGB2BGR)
# Draw a diagonal blue line with thickness of 5 px

print_timestamp = lambda timestamp: datetime.datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S %f")


def draw_candles(img, candles, candle_down_color = [32,32,192], candle_up_color = [32, 192, 32], candle_color=[128,32,32]): # if buggy, increase frame size
    height = len(img)
    width = len(img[0])
    max_price = candles[0]['h']
    min_price = candles[0]['l']
    for candle in candles[1:]:
        max_price = max(max_price, candle['h'])
        min_price = min(min_price, candle['l'])
    px_by_candle = width/(len(candles)+1)
    i = 0
    for candle in candles: # starts by last..
        x = int(i*px_by_candle)
        o = candle['o']
        c = candle['c']
        bottom = int((o-min_price)/(max_price-min_price)*height)
        top = int((c-min_price)/(max_price-min_price)*height)
        top, bottom = (top, bottom) if o < c else (bottom, top)
        if o == c:
            color = candle_color
        else:
            color = candle_up_color if o > c else candle_down_color
        line_size = max(int(px_by_candle/4), 1)
        cv2.line(img,(width-x,height-top+line_size),(width-x,height-bottom-line_size),color,line_size*3)
        min_ = int((candle['l']-min_price)/(max_price-min_price)*height)
        max_ = int((candle['h']-min_price)/(max_price-min_price)*height)
        cv2.line(img,(width-x,height-min_),(width-x,height-max_),color,line_size)

        i += 1
    return img, max_price, min_price


def draw_volume(img, candles, candle_down_color = [32,32,192], candle_up_color = [32, 192, 32], candle_color=[128,32,32]): # if buggy, increase img size
    height = len(img)
    width = len(img[0])
    v = candles[0]['v']
    max_volume = v
    min_volume = v
    for candle in candles[1:]:
        v = candle['v']
        max_volume = max(max_volume, v)
        min_volume = min(min_volume, v)
    px_by_candle = width/(len(candles)+1)

    i = 0
    for candle in candles: # starts by last..
        x = int(i*px_by_candle)
        o = candle['o']
        c = candle['c']
        v = candle['v']
        if o == c:
            color = candle_color
        else:
            color = candle_up_color if o > c else candle_down_color

        line_size = max(int(px_by_candle/2), 1)
        cv2.line(img,(width-x,height-int(height*(v-min_volume)/(max_volume-min_volume))+line_size),(width-x,height-line_size),color,line_size)

        i += 1
    return img, max_volume, min_volume

def draw_checkbox(img, pos, pressed = False, size = 10, color = (192,192,192)):
    # draw square, filled if pressed else only borders
    if pressed:
        cv2.rectangle(img, pos, (pos[0]+size, pos[1]+size), color, -1)
    else:
        cv2.rectangle(img, pos, (pos[0]+size, pos[1]+size), color, 1)

def draw_ui(top_img, bottom_img, left_img, candles, max_price, min_price, max_volume, min_volume):
    # draw top
    height = len(top_img)
    width = len(top_img[0])

    font = _base_font
    st_text = print_timestamp(candles[-1]['ot']/1e3)
    ed_text = print_timestamp(candles[0]['ct']/1e3)
    cv2.putText(top_img,f'max price {max_price}',(10, height//2), font, 0.75,(32,255,32),1,cv2.LINE_AA)
    cv2.putText(top_img,f'max volume {max_volume:.4f}',(width//4, height//2), font, 0.5,(192,192,192), 1,cv2.LINE_AA)
    cv2.putText(top_img,f'symbol {_symbol} {_t}s candles ({_d} min total)',(width//2, height//2), font, 0.75,(255,255,255),1,cv2.LINE_AA)

    # draw bottom
    height = len(bottom_img)
    width = len(bottom_img[0])
    cv2.putText(bottom_img,f'min price {min_price}',(10,height//2), font, 0.75,(32,32,255),1,cv2.LINE_AA)
    cv2.putText(bottom_img,f'min volume {min_volume:.4f}',(width//4, height//2), font, 0.5,(192,192,192), 1,cv2.LINE_AA)
    cv2.putText(bottom_img,f'start {st_text}',(10,height//4*3), font, 0.5,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(bottom_img,f'end {ed_text}',(width//4*3,height//4*3), font, 0.5,(255,255,255),1,cv2.LINE_AA)

    # draw left (actions)
    cv2.putText(left_img,f'Checkbox',(10,10), font, 2,(255,255,255),1,cv2.LINE_AA)
    return top_img, bottom_img, left_img

def draw_view(data, img):
    height = len(img)
    width = len(img[0])
    left_panel_w = width//4

    candles = data['candles']

    candles_img = blank_img(width=width-left_panel_w, height=height//3*2)
    candles_img, max_price, min_price = draw_candles(candles_img, candles)

    volume_img = blank_img(width=width-left_panel_w, height=height//3//3)
    volume_img, max_volume, min_volume = draw_volume(volume_img, candles)

    top_img = blank_img(width=width-left_panel_w, height=height//3//3)
    bottom_img = blank_img(width=width-left_panel_w, height=height//3//3)

    left_img = blank_img(width=left_panel_w, height=height)

    top_img, bottom_img, left_img = draw_ui(top_img, bottom_img, left_img, candles, max_price, min_price, max_volume, min_volume)

    # draw left part
    img[0 : left_img.shape[0], 0 : left_img.shape[1]] = left_img

    # draw parts vertically
    vacc = 0
    img[vacc : vacc + top_img.shape[0], left_panel_w : width] = top_img
    vacc += top_img.shape[0]
    img[vacc : vacc + candles_img.shape[0], left_panel_w : width] = candles_img
    vacc += candles_img.shape[0]
    img[vacc : vacc + volume_img.shape[0], left_panel_w : width] = volume_img
    vacc += volume_img.shape[0]
    img[vacc : vacc + bottom_img.shape[0], left_panel_w : width] = bottom_img

    return img
    # show
    #cv2.imshow(_windowName, img)

def request_view():
    # get time
    server_time = api_time()
    symbol_data = api_symbol_data(_symbol).json()

    trades = api_symbol_aggTrades(_symbol, server_time-datetime.timedelta(seconds=_d),server_time).json()
    candles = create_candles(trades, _t)
    return {'server_time': server_time, 'symbol_data': symbol_data, 'trades': trades, 'candles': candles}

# main
from threading import Thread

class App:
    content_img = None
    run = False
    def __init__(self):
        cv2.namedWindow(_windowName, cv2.WINDOW_NORMAL )
        cv2.setWindowProperty(_windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN )
        cv2.setMouseCallback(_windowName,self.on_mouse)

    def on_key(self, k):
        global _t
        global _d
        if chr(k & 0xFF) == 'q':
            self.run = False
        elif chr(k & 0xFF) == 'f':
            cv2.setWindowProperty(_windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN )
        elif k == 27: # esc
            cv2.setWindowProperty(_windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL )
        elif chr(k & 0xFF) == '-':
            _t *= 2
            _d *= 2
            self.data = request_view()
        elif chr(k & 0xFF) == '+':
            _t /= 2
            _d /= 2
            self.data = request_view()
        elif k != -1:
            print(k)
        else:
            return
        self.update_view()

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pass
        elif event == cv2.EVENT_LBUTTONUP:
            pass
        elif event == cv2.EVENT_RBUTTONDOWN:
            pass
        elif event == cv2.EVENT_RBUTTONUP:
            pass
        elif event == cv2.EVENT_MOUSEMOVE:
            pass

    def run(self):
        self.run = True
        self.content_img = blank_img(width=_default_width, height=_default_height)
        self.trading_updater_thread = Thread(target=self.trading_updater)
        self.trading_updater_thread.start()
        while self.run:
            cv2.imshow(_windowName, self.content_img)
            k = cv2.waitKey(int(1e3/_FPS))
            self.on_key(k)

        self.run = False
        cv2.destroyAllWindows()

    def update_view(self):
        try:
            x, y, width, height = get_window_rect(_windowName)
            if width > 0 and height > 0:
                self.content_img = draw_view(self.data, blank_img(width=_default_width, height=_default_height))
        except Exception as e:
            print(f"Update Error : {e}")

    def trading_updater(self):
        #print('called')
        while self.run:
            #print("update")
            self.data = request_view()
            self.update_view()
            time.sleep(_ut) # todo move update view in main while and do request with a timing


if __name__ == '__main__':
    App().run()