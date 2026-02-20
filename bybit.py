#pip install ccxt
#pip install pynput

from decimal import ROUND_FLOOR, Decimal
import os
import sys
from pynput import keyboard
import ccxt

# --- CONFIGURATION ---
SYMBOL = 'SOL/USDT:USDT'
SYMBOL_DECIMALS = 2
AMOUNT_UDST = 1
LEVERAGE = 10
STOP_LOSS = 0.5 # % stop loss

# Get the value of an environment variable, returns None if not found
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

trade_config = {
    "coin": "BTC",
    "amount_usdt": 1.0,
    "leverage": 10
}

def get_single_key():
    if os.name == 'nt':  # Windows logic
        import msvcrt
        # Returns bytes, so we decode to string
        char = msvcrt.getch().decode('utf-8', errors='ignore').upper()
        return char
    else:  # Linux/Mac logic
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1).upper()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char




# print(f"Listening: F1 (Long), F2 (Short), F3 (Close), ESC (Quit)")

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

# with keyboard.Listener(on_press=on_press) as listener:
#     listener.join()

# Coins 
def load_coins(filename):
    try:
        with open(filename, 'r') as f:
            # .strip() removes whitespace/newlines
            return [line.strip().upper() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def get_user_choice(options):
    print("--- Available Coins ---")
    # Display options in a numbered list
    for i, coin in enumerate(options, 1):
        print(f"{i}. {coin}")
    
    while True:
        choice = input("\nSelect a coin (Name or Number): ").strip().upper()
        
        # Check if input matches a name (e.g., "BTC")
        if choice in options:
            return choice
        
        # Check if input matches a number (e.g., "1")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        
        print(f"Invalid selection. Please choose from: {', '.join(options)}")

# --- 4. MENUS ---    
def coin_selection_menu():
    coins = load_coins('coins.txt')
    while True:
        for i, c in enumerate(coins, 1): print(f"{i}. {c}")
        choice = input("\nChoose number or type name: ").strip().upper()

        if choice in coins: return choice
        if choice.isdigit() and 0 < int(choice) <= len(coins):
            return coins[int(choice)-1]

def main_trading_menu():
    while True:
        
        print(f"Coin:      {trade_config['coin']}")
        print(f"Amount:    ${trade_config['amount_usdt']} USDT")
        print(f"Leverage:  {trade_config['leverage']}x")
        print("-" * 30)
        print("[1] Long | [2] Short | [3] Amount | [4] Leverage | [X] Exit")
        
        key = get_single_key()
        
        if key == '1': trade_config['side'] = "LONG"
        elif key == '2': trade_config['side'] = "SHORT"
        elif key == '3':
            trade_config['amount_usdt'] = float(input("\nEnter USDT Margin: ") or 100)
        elif key == '4':
            trade_config['leverage'] = int(input("\nEnter Leverage: ") or 10)
        elif key == 'X':
            sys.exit()

if __name__ == "__main__":
    # # Initialize the exchange
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
        print("Connecting ...")
        balance = exchange.fetch_balance()
        print(f"Connected! Balance: {balance['total']['USDT']}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        exit(1)

    trade_config['coin'] = coin_selection_menu()
    main_trading_menu()