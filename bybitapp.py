#pip install pynput
import math
import os, sys, time
from decimal import ROUND_FLOOR, Decimal
from pybit.unified_trading import HTTP

def get_order_id():
    return current_order.get('id')

def set_order_entry_price(entry_price):
    global current_order
    current_order['entry_price'] = entry_price

def get_order_entry_price():
    return current_order.get('entry_price')    

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
    return f"{config['pair']}"

def get_amount_usdt():
    return config['amount_usdt']

def get_leverage():
    return config['leverage']

def get_stop_loss():
    return config['stop_loss']

def get_take_profit():
    return config['take_profit']

def get_price_scale():
    return float(config['price_scale'])

def get_tick_size():
    return float(config['tick_size'])

def calculate_amount(price, amount_usdt, leverage, price_scale):
    return truncate_price(amount_usdt * leverage / price, price_scale)    

def get_price(symbol):
    ticker = session.get_tickers(category="linear", symbol=symbol)
    return ticker['result']['list'][0]['lastPrice']

# --- Decimal to Precision ---
def truncate_price(qty, step):
    #factor = 10.0 ** decimals
    #return math.trunc(price * factor) / factor
    return float(round(math.floor(qty / step) * step, 10))

# --- Stop Loss ---
def calculate_buy_stop_loss_price(price, percent):
    return calculate_stop_loss_price(price, -1, percent)

def calculate_sell_stop_loss_price(price, percent):
    return calculate_stop_loss_price(price, 1, percent)

def calculate_stop_loss_price(price, factor, percent):
    sl_price = price * (1 + (factor * percent / 100))        
    return round_price(sl_price, get_tick_size())

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

def round_price(price, tick_size):
    # Rounds to the nearest valid tickSize
    return round(math.floor(price / tick_size) * tick_size, 8)

def open_long():
    try:      
        symbol = get_symbol()
        #price = float(get_price(symbol))
        
        #stop_loss_price = calculate_buy_stop_loss_price(price, get_stop_loss())
        # take_profit_price = calculate_buy_take_profit_price(mark_price, get_take_profit())
        # params = {
        #     'stopLoss': str(stop_loss_price), # Trigger price for SL
        #     'slTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
        #     'takeProfit': str(take_profit_price), # Trigger price for TP
        #     'tpTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
        #     'tpslMode': 'Full',     # Ensures the Stop Loss covers 100% of your position size.
        #     'positionIdx': 1,        # 1 for Buy/Long, 2 for Sell/Short
        # }        
        #print(f"Opening LONG amount {amount} with SL @ {stop_loss_price} TP @ {take_profit_price}")
        # order = exchange.create_market_buy_order(symbol, amount, params=params)
        
        
        # Taker
        # order = session.place_order(
        #     category="linear",
        #     symbol=symbol,
        #     side="Buy",
        #     orderType="Market",
        #     qty=str(qty),
        #     stopLoss=str(stop_loss_price),
        #     slTriggerBy='MarkPrice',
        #     reduceOnly=False,
        #     positionIdx=1 # 1 for Buy/Long, 2 for Sell/Short
        # )


        # Maker
        entry_price = get_maker_price(symbol, "buy", get_tick_size())
        qty = calculate_amount(entry_price, get_amount_usdt(), get_leverage(), get_price_scale())
        stop_loss_price = calculate_buy_stop_loss_price(entry_price, get_stop_loss())
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Buy",
            orderType="Limit",
            qty=str(qty),
            price=str(entry_price),
            stopLoss=str(stop_loss_price),
            slTriggerBy='MarkPrice',
            reduceOnly=False,
            positionIdx=1, # 1 for Buy/Long, 2 for Sell/Short
            timeInForce="PostOnly" # CRITICAL: Ensures you only pay Maker fees
        )

        print(order)




        # id = order['id']
        # set_order_id(id)
        # print(f"Opened LONG with ID: {id}")

        # print("⏳ Waiting for trade execution data...")
        # time.sleep(0.5)  # Brief pause for exchange trade engine to sync

        # details = get_entry_price(id, symbol)
        # if details:
        #     set_order_entry_price(details['average'])
                            
    except Exception as e: print(f"❌ Error: {e}")

def open_short():
    try:
        symbol = get_symbol()
        #price = float(get_price(symbol))
        #qty = calculate_amount(price, get_amount_usdt(), get_leverage(), get_price_scale())
        
        # take_profit_price = calculate_sell_take_profit_price(mark_price, get_take_profit())
        # params = {
        #     'stopLoss': str(stop_loss_price), # Trigger price for SL
        #     'slTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
        #     'takeProfit': str(take_profit_price), # Trigger price for TP
        #     'tpTriggerBy': 'MarkPrice', #Highly Recommended for Futures to avoid "scam wicks"
        #     'tpslMode': 'Full',     # Ensures the Stop Loss covers 100% of your position size.
        #     'positionIdx': 2,        # 1 for Buy/Long, 2 for Sell/Short
        # }
        # print(f"Opening SHORT amount {amount} with SL @ {stop_loss_price} TP @ {take_profit_price}")
        # order = exchange.create_market_sell_order(symbol, amount, params=params)
        
        # Taker
        # order = session.place_order(
        #     category="linear",
        #     symbol=symbol,
        #     side="Sell",
        #     orderType="Market",
        #     qty=str(qty),
        #     stopLoss=str(stop_loss_price),
        #     slTriggerBy='MarkPrice',
        #     reduceOnly=False,
        #     positionIdx=2 # 1 for Buy/Long, 2 for Sell/Short
        # )

        # Maker
        entry_price = get_maker_price(symbol, "sell", get_tick_size())
        qty = calculate_amount(entry_price, get_amount_usdt(), get_leverage(), get_price_scale())
        stop_loss_price = calculate_sell_stop_loss_price(entry_price, get_stop_loss())
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Sell",
            orderType="Limit",
            qty=str(qty),
            price=str(entry_price),
            stopLoss=str(stop_loss_price),
            slTriggerBy='MarkPrice',
            reduceOnly=False,
            positionIdx=2, # 1 for Buy/Long, 2 for Sell/Short
            timeInForce="PostOnly" # CRITICAL: Ensures you only pay Maker fees
        )



        print(order)
        # id = order['id']
        # set_order_id(id)
        # print(f"Opened SHORT with ID: {id}")

        # print("⏳ Waiting for trade execution data...")
        # time.sleep(0.5)  # Brief pause for exchange trade engine to sync

        # details = get_entry_price(id, symbol)
        # if details:
        #     set_order_entry_price(details['average'])

    except Exception as e: print(f"❌ Error: {e}")

def get_entry_price(order_id, symbol):
    # Market orders move to 'closed' almost instantly
    for attempt in range(10):
        print(f"⏳ syncing trade data (attempt {attempt + 1}/5)")
        
        # We fetch recently closed orders for this symbol
        closed_orders = exchange.fetch_closed_orders(symbol)
        
        # Look for our specific order in the list
        for order in closed_orders:
            if order['id'] == order_id:
                print(f"✅ Entry Price: {order['average']}, fee: {order['fee']['cost']} {order['fee']['currency']}")
                return order
        
        time.sleep(0.4) # Short wait for API sync
        
    return None

def close_position_market(symbol):
    try:
        print(f"Fetching current position for {symbol}...")
        # 1. Fetch current position for the symbol
        # Bybit V5 requires a list of symbols or category
        positions = exchange.fetch_positions([symbol])
        
        # 2. Find the active position
        active_pos = next((p for p in positions if float(p['contracts']) > 0), None)

        if not active_pos:
            print(f"⚠️ No active position found for {symbol}")
            return

        # 3. Prepare the closing order details
        # If side is 'long', we 'sell'. If 'short', we 'buy'.
        side = 'sell' if active_pos['side'] == 'long' else 'buy'
        qty = active_pos['contracts']

        print(f"🛑 Closing {active_pos['side']} position of {qty} {symbol}...")

        # 4. Execute the market close order
        # We use camelCase 'reduceOnly' for Bybit V5 in CCXT
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=qty,
            params={'reduceOnly': True}
        )

        print(f"✅ Position Closed! Order ID: {order['id']}")
        
        # (Optional) Verify closure with your fetch_closed_orders logic
        time.sleep(1)
        final = exchange.fetch_closed_orders(symbol, limit=1)[0]
        print(f"🏁 Final Exit Price: {final['average']} USDT")

    except Exception as e:
        print(f"❌ Error closing position: {e}")

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
        
        print(f"Coin:      {config['pair']}")
        print(f"Amount:    ${config['amount_usdt']} USDT")
        print(f"Leverage:  {config['leverage']}x")
        print(f"Stop Loss: {config['stop_loss']}%")
        print(f"Take Profit: {config['take_profit']}%")
        print("-" * 30)
        print("[1] Long | [2] Short | [3] Amount | [4] Leverage | [X] Exit")
        
        key = get_single_key()
        
        if key == '1': 
            open_long()
        elif key == '2':
            open_short()
        elif key == '3':
            config['amount_usdt'] = float(input("\nEnter USDT Margin: ") or 10)
        elif key == '4':
            config['leverage'] = int(input("\nEnter Leverage: ") or 10)
        elif key == 'X':
            sys.exit()

def get_maker_price(symbol, side, tick_size):
    # 1. Get tickSize for precision
    # instrument = session.get_instruments_info(category="linear", symbol=symbol)
    # tick_size = float(instrument['result']['list'][0]['priceFilter']['tickSize'])
    
    # 2. Get current market price (LTP)
    ticker = session.get_tickers(category="linear", symbol=symbol)
    lastPrice = float(ticker['result']['list'][0]['lastPrice'])
    
    # 3. Calculate a price 1 tick away to improve Maker chances
    if side.lower() == "buy":
        # Place buy order 1 tick below current price
        target_price = lastPrice - (tick_size * 2)
    else:
        # Place sell order 1 tick above current price
        target_price = lastPrice + (tick_size * 2)
        
    # Round to the correct tickSize precision
    #precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
    return round_price(target_price, tick_size)


if __name__ == "__main__":
    global session

    api_key = os.getenv('BYBIT_DEMO_API_KEY')
    api_secret = os.getenv('BYBIT_DEMO_API_SECRET')


    import logging
    
    session = HTTP(
        testnet=False,
        demo=True,
        api_key=api_key,
        api_secret=api_secret,
    )

    symbol = "SOLUSDT"
    category = "linear"
    instrument_info = session.get_instruments_info(category=category, symbol=symbol)
    print(f"{instrument_info}")
    price_scale = (instrument_info['result']['list'][0]['lotSizeFilter']['qtyStep'] )
    tick_size = (instrument_info['result']['list'][0]['priceFilter']['tickSize'] )

    global config
    config = {
        "pair": "SOLUSDT",
        "price_scale": price_scale,
        "tick_size": tick_size,
        "amount_usdt": 2.0,
        "leverage": 10,
        "stop_loss": 0.5,
        "take_profit": 1.1,
    }

    main_trading_menu()