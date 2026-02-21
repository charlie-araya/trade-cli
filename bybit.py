#pip install ccxt
#pip install pynput

from decimal import ROUND_FLOOR, Decimal
import os
import sys
import time
from pynput import keyboard
import ccxt

SYMBOL_DECIMALS = 2

# Get the value of an environment variable, returns None if not found
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

trade_config = {
    "coin": "BTC",
    "amount_usdt": 1.0,
    "leverage": 10,
    "stop_loss": 0.5,
    "take_profit": 1.1,
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

def get_symbol():
    return f"{trade_config['coin']}/USDT:USDT"

def get_amount_usdt():
    return trade_config['amount_usdt']

def get_leverage():
    return trade_config['leverage']

def get_stop_loss():
    return trade_config['stop_loss']

def get_take_profit():
    return trade_config['take_profit']

def calculate_amount(mark_price, amount_usdt, leverage):
    #return truncate_price(amount_usdt * leverage / mark_price)
    return exchange.amount_to_precision(get_symbol(), amount_usdt * leverage / mark_price)

def get_mark_price(symbol):
    print(f"Fetching mark price for {symbol}...")
    ticker = exchange.fetch_ticker(symbol)
    mark_price = ticker['last']  
    print(f"Mark Price for {symbol}: {mark_price}")
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

# --- Take Profit ---
def calculate_buy_take_profit_price(price, percent):
    return calculate_take_profit_price(price, 1, percent)

def calculate_sell_take_profit_price(price, percent):
    return calculate_take_profit_price(price, -1, percent)

def calculate_take_profit_price(price, factor, percent):
    tp_price = price * (1 + (factor * percent / 100))        
    return truncate_price(tp_price)

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
        symbol = get_symbol()
        mark_price = get_mark_price(symbol)
        amount = calculate_amount(mark_price, get_amount_usdt(), get_leverage())
        stop_loss_price = calculate_buy_stop_loss_price(mark_price, get_stop_loss())
        take_profit_price = calculate_buy_take_profit_price(mark_price, get_take_profit())
        params = {
            'stopLoss': str(stop_loss_price), # Trigger price for SL
            'slTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
            'takeProfit': str(take_profit_price), # Trigger price for TP
            'tpTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
            'tpslMode': 'Full',     # Ensures the Stop Loss covers 100% of your position size.
            'positionIdx': 0,        # Required for One-Way Mode
        }
        print(f"Opening LONG amount {amount} with SL @ {stop_loss_price} TP @ {take_profit_price}")
        order = exchange.create_market_buy_order(symbol, amount, params=params)
        id = order['id']
        print(f"Opened LONG with ID: {id}")

        print("⏳ Waiting for trade execution data...")
        time.sleep(1.5)  # Brief pause for exchange trade engine to sync

        details = get_trade_execution(id, symbol)
        if details:
            print(f"{details}")
        
        
    except Exception as e: print(f"❌ Error: {e}")

def open_short():
    try:
        symbol = get_symbol()
        mark_price = get_mark_price(symbol)
        amount = calculate_amount(mark_price, get_amount_usdt(), get_leverage())
        stop_loss_price = calculate_sell_stop_loss_price(mark_price, get_stop_loss())
        take_profit_price = calculate_sell_take_profit_price(mark_price, get_take_profit())
        params = {
            'stopLoss': str(stop_loss_price), # Trigger price for SL
            'slTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
            'takeProfit': str(take_profit_price), # Trigger price for TP
            'tpTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
            'tpslMode': 'Full',     # Ensures the Stop Loss covers 100% of your position size.
            'positionIdx': 0,        # Required for One-Way Mode
        }
        print(f"Opening SHORT amount {amount} with SL @ {stop_loss_price} TP @ {take_profit_price}")
        order = exchange.create_market_sell_order(symbol, amount, params=params)
        id = order['id']
        print(f"Opened SHORT with ID: {id}")

        print("⏳ Waiting for trade execution data...")
        time.sleep(1.5)  # Brief pause for exchange trade engine to sync

        details = get_trade_execution(id, symbol)
        if details:
            print(f"{details}")
    except Exception as e: print(f"❌ Error: {e}")

def get_trade_execution(order_id, symbol):
    # Fetch trades associated with this specific order ID
    trades = exchange.fetch_my_trades(symbol, params={'orderId': order_id})
    
    if trades:
        # If order was filled in multiple parts, average them
        avg_price = sum(t['price'] * t['amount'] for t in trades) / sum(t['amount'] for t in trades)
        total_fee = sum(t['fee']['cost'] for t in trades)
        print(f"Avg Price = {avg_price}, Total Fee = {total_fee}")
        return trades
    return None

def fetch_order(order_id, symbol):
    for _ in range(10):  # Try 10 times
        order = exchange.fetch_order(order_id, symbol)
        if order['status'] == 'closed':
            return order
        time.sleep(0.05)  # Wait 50ms before retrying
    return None

def set_stop_loss(position_side, mark_price):
    # Specifically for Bybit
    params = {
        'stopLoss': '58000',      # Your SL Price
        'slTriggerBy': 'LastPrice'
    }

    try:
        # On Bybit, you apply the SL to the SYMBOL/Position, not necessarily the Order ID
        response = exchange.set_trading_stop(symbol, params)
        print("✅ Position Stop Loss updated!")
    except Exception as e:
        print(f"❌ Failed: {e}")

def close_current_position(symbol):
    try:
        # 1. Fetch current positions for this symbol
        positions = exchange.fetch_positions([symbol])
        
        # 2. Find the active position (where size > 0)
        active_pos = None
        for p in positions:
            if float(p['contracts']) > 0:
                active_pos = p
                break
        
        if not active_pos:
            print("❌ No open position found to close.")
            return

        # 3. Determine the closing side
        # If you are LONG, you must SELL. If you are SHORT, you must BUY.
        side = 'sell' if active_pos['side'] == 'long' else 'buy'
        qty = active_pos['contracts']

        print(f"🛑 Closing {active_pos['side']} position: {qty} {symbol}...")

        # 4. Execute the closing Market Order
        order = exchange.create_market_order(
            symbol, 
            side, 
            qty, 
            params={'reduceOnly': True}
        )
        
        print(f"✅ Position closed! Order ID: {order['id']}")
        
    except Exception as e:
        print(f"❌ Error closing position: {e}")

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
        
        if key == '1': 
            open_long()
        elif key == '2':
            open_short()
        elif key == '3':
            trade_config['amount_usdt'] = float(input("\nEnter USDT Margin: ") or 100)
        elif key == '4':
            trade_config['leverage'] = int(input("\nEnter Leverage: ") or 10)
        elif key == 'X':
            sys.exit()

def position_menu():
    while True:
        print("[1] Close Current Position | [2] Close All Positions | [X] Back")
        key = get_single_key()
        
        if key == '1':
            close_current_position(get_symbol())
            return
        elif key == '2':
            close_all()
            return
        elif key == 'X':
            return

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