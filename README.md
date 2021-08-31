# python-tradingcv2-binance
A gui made with cv2 for market visualisation using the Binance API

# Usage

```
python3 ./binance_hifreq.py <symbol> -t <candle duration, default : 5 (seconds)> -d <length of data, default : 5 (minutes)>
```
Exemple : python3 ./binance_hifreq.py  -t 2 -d 10
gives ..

# Disclaimer

I did this over a day, this is only a prototype.

The program uses a win32 lib for getting the size of the window, can be modified, but works only on Windows yet.