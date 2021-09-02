import requests, datetime, json
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
