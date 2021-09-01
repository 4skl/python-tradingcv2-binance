# python-tradingcv2-binance
A gui made with cv2 for market visualisation using the Binance API


# Usage

```
python3 ./binance_hifreq.py <symbol> -t <candle duration, default : 5 (seconds)> -d <length of data, default : 5 (minutes)>
```
Exemple : python3 ./binance_hifreq.py  -t 2 -d 10
![Exemple image, candles 2 seconds over 10 minutes](https://github.com/4skl/python-tradingcv2-binance/raw/main/1ETHBUSD2s10min.png)


# Disclaimer

I did this over a day, this is only a prototype, but I plan to improve it more for some cool visualisations.

The program uses a win32 lib for getting the size of the window, can be modified, but works only on Windows yet.
