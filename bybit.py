#pip install ccxt
#pip install pynput

from decimal import ROUND_FLOOR, Decimal
import os
from pynput import keyboard

# --- CONFIGURATION ---
SYMBOL = 'SOL/USDT:USDT'
SYMBOL_DECIMALS = 2
AMOUNT_UDST = 1
LEVERAGE = 10
STOP_LOSS = 0.5 # % stop loss

# Get the value of an environment variable, returns None if not found
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

import ccxt

# Initialize the exchange
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'} # Set to swap for derivatives
})

exchange.enable_demo_trading(True)

try:
    # Verify you are in demo mode by checking balance 
    # (Bybit usually gives you 50,000 USDT in demo)
    print("🔗 Connecting to Bybit Demo...")
    balance = exchange.fetch_balance()
    print(f"✅ Connected! Demo USDT: {balance['total']['USDT']}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit(1)


print(f"Listening: F1 (Long), F2 (Short), F3 (Close), ESC (Quit)")

def calculate_amount(mark_price, amount_usdt, leverage):
    return truncate_price(amount_usdt * leverage / mark_price)

def get_mark_price(symbol):
    ticker = exchange.fetch_ticker(symbol)
    mark_price = ticker['last']  
    return mark_price

# --- Decimal to Precision ---
def truncate_price(price):
    quantize_exp = Decimal(f"{0:.{SYMBOL_DECIMALS}f}")
    truncated = float(Decimal(str(price)).quantize(quantize_exp, rounding=ROUND_FLOOR))
    return truncated

# --- Stop Loss ---
def calculate_buy_stop_loss_price(price, percent):
    return calculate_stop_loss_price(price, -1, percent)

def calculate_sell_stop_loss_price(price, percent):
    return calculate_stop_loss_price(price, 1, percent)

def calculate_stop_loss_price(price, factor, percent):
    sl_price = price * (1 + (factor * percent / 100))        
    return truncate_price(sl_price)

# --- Printing output ---
def dict_to_string(d):
    return '\n'.join(f"{k}: {v}" for k, v in d.items())

def fetch_ticker():
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        #print(f"📈 {SYMBOL} Price: {ticker['last']}")
        print(f"📈 {SYMBOL} Price: {ticker}")
    except Exception as e:
        print(f"❌ Ticker Fetch Error: {e}")

def open_long():
    try:      
        mark_price = get_mark_price(SYMBOL)
        amount = calculate_amount(mark_price, AMOUNT_UDST, LEVERAGE)
        stop_loss_price = calculate_buy_stop_loss_price(mark_price, STOP_LOSS)
        params = {
            #'stopLossPrice': stop_loss_price, # Trigger price for SL
            'positionIdx': 0,        # Required for One-Way Mode
            #'reduceOnly': True,
            #'triggerBy': 'LastPrice',
        }
        print(f"Opening LONG @ {mark_price}, amount {amount} with SL @ {stop_loss_price}")
        order = exchange.create_market_buy_order(SYMBOL, amount, params=params)
        print(f"{dict_to_string(order)}")
        #print(f"🚀 LONG OPENED @ {order['price'] if order['price'] else 'Market'}")
    except Exception as e: print(f"❌ Error: {e}")

def open_short():
    try:
        mark_price = get_mark_price(SYMBOL)
        amount = calculate_amount(mark_price, AMOUNT_UDST, LEVERAGE)
        stop_loss_price = calculate_sell_stop_loss_price(mark_price, STOP_LOSS)
        params = {
            #'stopLossPrice': stop_loss_price, # Trigger price for SL
            'positionIdx': 0,        # Required for One-Way Mode
            #'triggerBy': 'LastPrice',
        }
        print(f"Opening SHORT @ {mark_price}, amount {amount} with SL @ {stop_loss_price}")
        order = exchange.create_market_sell_order(SYMBOL, amount, params=params)
        print(f"{dict_to_string(order)}")
    except Exception as e: print(f"❌ Error: {e}")

def close_all():
    try:
        print("Closing all positions...")
        pos = exchange.fetch_positions([SYMBOL])
        print(f"Current Positions: {pos}")
        if not pos:            
            print("No open positions to close.")

        for p in pos:
            side = 'sell' if p['side'] == 'long' else 'buy'
            qty = float(p['contracts'])
            if qty > 0:
                print(f"Closing {side.upper()} position of {qty} {SYMBOL}...")
                exchange.create_market_order(SYMBOL, side, qty, params={'reduceOnly': True})
                print(f"🛑 Position Closed: {qty} {SYMBOL}")
    except Exception as e: print(f"❌ Error: {e}")

# Map keys to functions
HOTKEYS = {
    keyboard.Key.f1: open_long,
    keyboard.Key.f2: open_short,
    keyboard.Key.f3: close_all,
    keyboard.Key.f5: fetch_ticker
}

def on_press(key):
    if key in HOTKEYS:
        HOTKEYS[key]()
    if key == keyboard.Key.esc:
        return False  # Stop listener

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()