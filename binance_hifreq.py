import cv2, json, sys, requests, datetime, time
import numpy as np
# first argument is symbol
# draw candlestick based on -t <s, default: 5> seconds intervals, and with a duration of -d <d, default: 5> minutes

_windowName = "Candles"
_default_width = 1600
_default_height = 800

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

# api shortcuts
api_endpoint = "https://api.binance.com"
api_ping = lambda: requests.get(api_endpoint+"/api/v3/ping")
api_time = lambda: datetime.datetime.fromtimestamp(requests.get(api_endpoint+"/api/v3/time").json()['serverTime']/1e3)
api_symbol_data = lambda symbol: requests.get(api_endpoint+f"/api/v3/exchangeInfo?symbol={symbol}")
api_symbol_priceticker = lambda symbol: requests.get(api_endpoint+f"/api/v3/ticker/price?symbol={symbol}")
api_symbol_trades = lambda symbol: requests.get(api_endpoint+f"/api/v3/trades?symbol={symbol}")
api_symbol_aggTrades = lambda symbol, from_, to_: requests.get(api_endpoint+f"/api/v3/aggTrades?symbol={symbol}&startTime={int(from_.timestamp()*1e3)}&endTime={int(to_.timestamp()*1e3)}")


# api checks
if api_ping().json() == {}:
    print("API Online")
else:
    print("API Offline")
    quit()

# functions

def create_candles(trades, duration): # float duration in seconds
    # best pricematch & buyermaker ignored
    d = duration * 1e3 # duration in ms
    last_trade = trades[-1]
    open_timestamp = last_trade['T']
    open_price = float(last_trade['p'])
    qty = float(last_trade['q']) # volume
    
    aws = open_price*qty # actual weighted price sum
    low_price = open_price
    high_price = open_price

    '''
    candle = {
        'ot': int, # Open time
        'o': float, # Open price
        'h': float, # High price
        'l': float, # Low price
        'c': float, # Close price
        'v': float, # Volume
        'ct': int, # Close time
        #... Quote asset volume
    }
    '''
    candles = []
    for trade in trades[::-1][1:]:
        timestamp = trade['T']
        if timestamp > open_timestamp-d:
            q = float(trade['q'])
            p = float(trade['p'])
            aws += p * q
            qty += q
            if high_price < p:
                high_price = p
            elif low_price > p:
                low_price = p
        else:
            # ? open_timestamp = trade['T'] 
            open_timestamp -= d
            candles.append({
                'ot': int(open_timestamp+d), # Open time
                'o': float(open_price), # Open price
                'h': float(high_price), # High price
                'l': float(low_price), # Low price
                'c': float(last_trade['p']), # Close price
                'v': float(qty), # Volume
                'ct': int(open_timestamp), # Close time
                'aw': float(aws/qty)
                #... Quote asset volume
            })
            open_price = float(trade['p'])
            qty = float(trade['q']) # volume
            aws = open_price*qty # actual weighted price sum
            
            aws = open_price*qty # actual weighted price sum
            low_price = open_price
            high_price = open_price
        
        last_trade = trade
    return candles

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
        cv2.line(img,(width-x,height-top),(width-x,height-bottom),color,int(px_by_candle/2))
        min_ = int((candle['l']-min_price)/(max_price-min_price)*height)
        max_ = int((candle['h']-min_price)/(max_price-min_price)*height)
        cv2.line(img,(width-x,height-min_),(width-x,height-max_),color,max(int(px_by_candle/5), 2))

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
        cv2.line(img,(width-x,height-int(height*(v-min_volume)/(max_volume-min_volume))),(width-x,height),color,int(px_by_candle/2))

        i += 1
    return img, max_volume, min_volume

def draw_checkbox(img, pos, pressed = False, size = 10, color = (192,192,192)):
    # draw square, filled if pressed else only borders
    if pressed:
        cv2.rectangle(img, pos, (pos[0]+size, pos[1]+size), color, -1)
    else:
        cv2.rectangle(img, pos, (pos[0]+size, pos[1]+size), color, 1)

def draw_actions(img):
    # show ma
    pass

def draw_view(data, width=1600, height=800):

    img = blank_img(width=width, height=height)

    candles = data['candles']

    candles_img = blank_img(width=width-50, height=height//3*2)
    candles_img, max_price, min_price = draw_candles(candles_img, candles)

    volume_img = blank_img(width=width-50, height=height//3//3)
    volume_img, max_volume, min_volume = draw_volume(volume_img, candles)

    #actions_img = blank_img(width=width-50, height=height//3//3*2)
    #actions_img = draw_actions(actions_img)

    # draw above
    img[30 : candles_img.shape[0] + 30, 25 : width-25] = candles_img
    img[candles_img.shape[0] + 30*2 : candles_img.shape[0] + volume_img.shape[0] + 30*2, 25 : width-25] = volume_img

    # draw ui
    font = cv2.FONT_HERSHEY_SIMPLEX
    st_text = print_timestamp(candles[-1]['ot']/1e3)
    ed_text = print_timestamp(candles[0]['ct']/1e3)
    max_price = candles[0]['h']
    min_price = candles[0]['l']
    for candle in candles[1:]:
        max_price = max(max_price, candle['h'])
        min_price = min(min_price, candle['l'])
    cv2.putText(img,f'max price {max_price}',(10, 20), font, 0.75,(32,255,32),2,cv2.LINE_8)
    cv2.putText(img,f'min price {min_price}',(10,height-20), font, 0.75,(32,32,255),2,cv2.LINE_8)

    cv2.putText(img,f'max volume {max_volume:.4f}',(width//4*3, candles_img.shape[0] + 45), font, 0.5,(192,192,192), 1,cv2.LINE_8)
    cv2.putText(img,f'min volume {min_volume:.4f}',(width//4*3, candles_img.shape[0] + volume_img.shape[0] + 75), font, 0.5,(192,192,192), 1,cv2.LINE_8)

    cv2.putText(img,f'start {st_text}',(width//3,height-30), font, 0.5,(255,255,255),1,cv2.LINE_8)
    cv2.putText(img,f'end {ed_text}',(width//3*2,height-30), font, 0.5,(255,255,255),1,cv2.LINE_8)
    cv2.putText(img,f'symbol {_symbol} {_t}s candles',(width//3*2, 20), font, 0.75,(255,255,255),2,cv2.LINE_8)

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
    view_updater_thread = None
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
        elif chr(k & 0xFF) == '+':
            _t /= 2
            _d /= 2
        elif k != -1:
            print(k)

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
        self.content_img = draw_view(request_view(), width=_default_width, height=_default_height)
        self.view_updater_thread = Thread(target=self.view_updater)
        self.view_updater_thread.start()
        while self.run:
            cv2.imshow(_windowName, self.content_img)
            k = cv2.waitKey(1)
            self.on_key(k)

        self.run = False
        cv2.destroyAllWindows()

    def update_view(self):
        try:
            x, y, width, height = get_window_rect(_windowName)
            if width > 0 and height > 0:
                self.content_img = draw_view(request_view(), width=width, height=height)
        except Exception as e:
            print(f"Update Error : {e}")

    def view_updater(self):
        #print('called')
        while self.run:
            #print("update")
            self.update_view()
            time.sleep(_ut)


if __name__ == '__main__':
    App().run()