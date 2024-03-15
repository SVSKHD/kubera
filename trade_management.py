import MetaTrader5 as mt5
import threading

# Global variables
lock = threading.Lock()
initial_balance = None
trading_paused = False
profit_target = 0
max_trades_per_symbol = 4
trades = {}  # Dictionary to keep track of trades per symbol

def startup_check():
    global initial_balance
    if not mt5.initialize(login=212792645, server="OctaFX-Demo", password="pn^eNL4U"):
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    else:
        print("Connected successfully")

    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info")
        return
    initial_balance = account_info.balance
    print(f"Initial balance recorded: {initial_balance}")

def place_trade(symbol, trade_type, volume, price, deviation, stop_loss_distance=None):
    with lock:
        if trading_paused:
            print(f"Trading is paused. No new trades for {symbol}.")
            return None

        # Check for existing live trades for the symbol
        existing_positions = mt5.positions_get(symbol=symbol)
        if existing_positions:
            print(f"There are already live trades for {symbol}. No new trades will be placed.")
            return None

        order_type = mt5.ORDER_TYPE_BUY if trade_type == "BUY" else mt5.ORDER_TYPE_SELL
        current_price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

        take_profit_price = current_price * (1 + 0.00186) if order_type == mt5.ORDER_TYPE_BUY else current_price * (1 - 0.00186)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": current_price,
            "deviation": deviation,
            "magic": 0,
            "comment": "Placed by trading bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "tp": take_profit_price
        }

        if stop_loss_distance:
            stop_loss_price = current_price - stop_loss_distance * mt5.symbol_info(symbol).point if order_type == mt5.ORDER_TYPE_BUY else current_price + stop_loss_distance * mt5.symbol_info(symbol).point
            request["sl"] = stop_loss_price

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to place trade for {symbol}. Error code: {result.retcode}")
            return None
        else:
            print(f"Trade for {symbol} placed successfully. Ticket: {result.order}")
            trades[symbol] = [result.order]  # Update the trades dictionary with the new trade
            return result.order


def close_trade(position_ticket):
    with lock:
        position = mt5.positions_get(ticket=position_ticket)
        if not position:
            print(f"No position found with ticket {position_ticket}.")
            return

        position = position[0]
        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(position.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(position.symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 0,
            "comment": "Close trade",
            "type_time": mt5.ORDER_TIME_GTC,
        }

        print(f"Sending close request for {position.symbol}, Ticket: {position.ticket}, Volume: {position.volume}, Price: {price}")

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close trade {position_ticket}, Error: {mt5.last_error()}")
        else:
            print(f"Trade {position_ticket} closed successfully.")
            if position.symbol in trades:
                trades[position.symbol].remove(position.ticket)
                print(f"Trade {position.ticket} for {position.symbol} closed and removed from tracking.")

def check_daily_loss():
    global initial_balance, trading_paused, profit_target
    
    if initial_balance is None:
        print("Initial balance not set, cannot check daily loss.")
        return False

    # Fetch current balance and floating P/L
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get current account info.")
        return False

    current_balance = account_info.balance
    floating_profit = account_info.profit  # Include floating profits/losses

    # Adjust the current balance by including floating profits/losses
    adjusted_balance = current_balance + floating_profit

    # Calculate the loss based on adjusted balance
    current_loss = initial_balance - adjusted_balance
    loss_limit = initial_balance * 0.05

    if current_loss > loss_limit:
        print(f"Current loss ({current_loss}) exceeded the 5% loss limit.")
        trading_paused = True
        profit_target = initial_balance * 1.20
    else:
        print(f"Current loss ({current_loss}) has not yet exceeded the 5% loss limit.")
        if not trading_paused:
            profit_target = initial_balance * 1.15

    return trading_paused


def check_daily_profit():
    global initial_balance, trading_paused, profit_target
    current_balance = mt5.account_info().balance

    if current_balance >= profit_target:
        print(f"Profit target met or exceeded: {current_balance} >= {profit_target}")
        trading_paused = False
        initial_balance = current_balance
        profit_target = initial_balance * 1.15
    else:
        print(f"Current balance has not yet met the profit target: {current_balance} < {profit_target}")

def close_all_trades(symbol):
    with lock:
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            print(f"Found {len(positions)} open positions for {symbol}. Closing all.")
            for position in positions:
                close_trade(position.ticket)
        else:
            print(f"No open positions found for {symbol}.")

