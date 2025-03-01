import pandas as pd
import matplotlib.pyplot as plt

# Prep data type and col name
def prepData(df):
    # Set col name
    df.rename(columns={"Close/Last": "Close"}, inplace=True)

    # Convert Data type
    df["Date"] = pd.to_datetime(df["Date"])

    # Use regex to replace $ before convert
    df["Close"] = pd.to_numeric(df["Close"].replace(r'[\$,]', '', regex=True))
    df["Open"] = pd.to_numeric(df["Open"].replace(r'[\$,]', '', regex=True))
    df["High"] = pd.to_numeric(df["High"].replace(r'[\$,]', '', regex=True))
    df["Low"] = pd.to_numeric(df["Low"].replace(r'[\$,]', '', regex=True))
    
    df = df.iloc[::-1].reset_index(drop=True)
    
    return df

# Create signal function
def generateMASignal(df, fast=50, slow=200):
    
    df[f"MA{fast}"] = df["Close"].rolling(window=fast).mean()
    df[f"MA{slow}"] = df["Close"].rolling(window=slow).mean()
    
    # Set signal
    df["Buy"] = (df[f"MA{fast}"] > df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) <= df[f"MA{slow}"].shift(1))
    df["Sell"] = (df[f"MA{fast}"] < df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) >= df[f"MA{slow}"].shift(1))
    
    return df

# Create testing function

def strategyTest(df, initInv=100, fast=50, slow=200): # initInv stands for initial investment
    generateMASignal(df, fast, slow)
    
    backtest_log_data = []
    first_date = df.iloc[0].Date - pd.Timedelta(days=1)
    # backtest_log = pd.DataFrame(columns=["Order_Date", "Action", "Balance $", "Share", "Share Price", "Net"])
    # backtest_log.loc[0] = [first_date, "Init", initInv, 0, df.iloc[0].Open, initInv]
    backtest_log_data = [[first_date, "Init", initInv, 0, df.iloc[0].Open, initInv]]
    
    for row in df.itertuples(index=True, name="Row"):
        date = row.Date
        price = row.Open
        buy_signal = row.Buy
        sell_signal = row.Sell
        
        bl_curr = backtest_log_data[-1] # stands for backlog current
        # print(f"Date: {date}, Buy Signal: {buy_signal}, Sell Signal: {sell_signal}") # Debug line
            
        if buy_signal and bl_curr[2] > 0:  # Check if we have balance to buy
            share_obtained = round(bl_curr[2] / price, 2)
            # balance = round(bl_curr[2] - (share_obtained * price), 2) # Remove for non-negative
            balance = 0
            net = round((share_obtained * price) + balance, 2)
            action = "BUY"
            backtest_log_data.append([date, action, balance, share_obtained, price, net])
        
        elif sell_signal and bl_curr[3] > 0:  # Check if we have shares to sell
            cash_obtained = round(bl_curr[3] * price, 2)
            # balance = round(bl_curr[2] + cash_obtained, 2) # Remove for non-negative
            balance = round(bl_curr[2] + cash_obtained, 2)
            net = round(cash_obtained + bl_curr[2], 2)
            action = "SELL"
            backtest_log_data.append([date, action, balance, 0, price, net])
            
    # Enter latest date data
    latest_date = df.iloc[-1].Date
    backtest_log_data.append([latest_date, "Final"] + backtest_log_data[-1][2:])  # Copy last values

    backtest_log = pd.DataFrame(
        backtest_log_data, columns=["Order_Date", "Action", "Balance $", "Share", "Share Price", "Net"]
    )
            
    return backtest_log

def multipleParaStrategyTest(df, fasts=list(range(5, 101, 5)), slows=list(range(100, 501, 50))):
    records = []
    # fasts = list(range(5, 101, 5))
    # slows = list(range(100, 501, 50))

    # print(strategyTest(df=df, slow=5, fast=100))

    for fast in fasts:
        result = []  # Reset log

        for slow in slows:
            # print(f"fast: {fast}, slow: {slow}")
            
            result = strategyTest(df=df, slow=slow, fast=fast)

            # Calculation
            init_investment = result.iloc[0]["Balance $"]
            final_value = result.iloc[-1]["Net"]
            pct_change = (final_value - init_investment) / init_investment * 100
            net = result.iloc[-1]["Net"]
            exe_order = len(result) - 2
            # print(init_investment)
            # print(final_value)
            # print(result)

            # Store data in a list
            records.append([fast, slow, net, pct_change, exe_order])

    # Convert the list to a DataFrame once (efficient)
    test_log = pd.DataFrame(records, columns=["Fast", "Slow", "Net", "Result%", "#Order"])
    
    return test_log
            
def generateMASignalGraph(df, fast=50, slow=200, size=(12, 8)):
    df = df.copy()  # Prevent modify original DataFrame
    generateMASignal(df, fast, slow) 
    
    plt.figure(figsize=size)

    # Plot the lines
    plt.plot(df["Date"], df["Close"], color="black", linewidth=0.5, label="Close")
    plt.plot(df["Date"], df[f"MA{fast}"], color="red", linewidth=0.5, label=f"MA{fast}")
    plt.plot(df["Date"], df[f"MA{slow}"], color="blue", linewidth=0.5, label=f"MA{slow}")

    # Fill areas
    plt.fill_between(df["Date"], df[f"MA{fast}"], df[f"MA{slow}"], 
                     where=(df[f"MA{fast}"] < df[f"MA{slow}"]), color="red", alpha=0.2, label="Bear (Down)")
    plt.fill_between(df["Date"], df[f"MA{fast}"], df[f"MA{slow}"], 
                     where=(df[f"MA{fast}"] > df[f"MA{slow}"]), color="green", alpha=0.2, label="Bull (Up)")

    # Set Position Points
    # df["Buy"] = (df[f"MA{fast}"] > df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) <= df[f"MA{slow}"].shift(1))
    # df["Sell"] = (df[f"MA{fast}"] < df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) >= df[f"MA{slow}"].shift(1))

    # Plot Buy/Sell signals
    plt.scatter(df["Date"][df["Buy"]], df["Close"][df["Buy"]], marker="^", color="green", s=50, label="Buy-Position")
    plt.scatter(df["Date"][df["Sell"]], df["Close"][df["Sell"]], marker="v", color="red", s=50, label="Sell-Position")

    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.title(f"Price with MAs MA{fast}-MA{slow}")
    plt.legend()
    plt.grid()
    plt.show()

    
    return

# Create Function

def generateMulMASignalGraph(df, fast_periods=[50], slow_periods=[200], size=(12, 8)):
    for fast in fast_periods:
        for slow in slow_periods:
            plt.figure(figsize=size)
            df = generateMASignal(df)
            
            df[f"MA{fast}"] = df["Close"].rolling(window=fast).mean()
            df[f"MA{slow}"] = df["Close"].rolling(window=slow).mean()
            
            # Set Position points
            # df["Buy"] = (df[f"MA{fast}"] > df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) <= df[f"MA{slow}"].shift(1))
            # df["Sell"] = (df[f"MA{fast}"] < df[f"MA{slow}"]) & (df[f"MA{fast}"].shift(1) >= df[f"MA{slow}"].shift(1))
            
            # Fill the colour between
            plt.fill_between(df["Date"], df[f"MA{fast}"], df[f"MA{slow}"], where=(df[f"MA{fast}"] < df[f"MA{slow}"]), color="green", alpha=0.2, label="Bull (Up)")
            plt.fill_between(df["Date"], df[f"MA{fast}"], df[f"MA{slow}"], where=(df[f"MA{fast}"] > df[f"MA{slow}"]), color="red", alpha=0.2, label="Bear (Down)")
            
            # Visual position point  
            plt.scatter(df["Date"][df["Buy"]], df["Close"][df["Buy"]], marker="^", color="green", s=50, label="Buy-Position")
            plt.scatter(df["Date"][df["Sell"]], df["Close"][df["Sell"]], marker="v", color="red", s=50, label="Sell-Position")
            
            plt.plot(df["Date"], df["Close"], color="black", linewidth=0.5, label="Close")
            plt.plot(df["Date"], df[f"MA{fast}"], color="red", linewidth=0.5, label=f"MA{fast}")
            plt.plot(df["Date"], df[f"MA{slow}"], color="blue", linewidth=0.5, label=f"MA{slow}")

            plt.xlabel("Date")
            plt.ylabel("Price ($)")
            plt.title(f"AAPL Price with MAs MA{fast}-MA{slow}")
            plt.legend()
            plt.grid()
            plt.show()
    
    return

def handle_splits(df, stock_symbol):
    SPLITS = {
        "AAPL": [("2020-08-31", 4), 
                 ("2014-06-09", 7), 
                 ("2005-02-28", 2), 
                 ("2000-06-21", 2), 
                 ("1987-06-16", 2)],
        "AMZN": [("2022-06-06", 20), 
                 ("1999-09-02", 2), 
                 ("1999-01-05", 3), 
                 ("1998-06-02", 2)],
        "MSFT": [("2003-02-18", 2), 
                 ("1999-03-29", 2), 
                 ("1998-02-23", 2), 
                 ("1996-12-09", 2), 
                 ("1994-05-23", 2), 
                 ("1992-06-15", 1.5), 
                 ("1991-06-27", 1.5), 
                 ("1987-09-21", 2)],
        "NVDA": [("2024-06-10", 10), 
                 ("2021-07-20", 4), 
                 ("2007-09-11", 1.5)],
        "TSLA": [("2022-08-25", 3), 
                 ("2020-08-31", 5)]
    }
    
    df = df.copy()
    if stock_symbol not in SPLITS:
        print(f"NO SPLIT DATA FOR {stock_symbol}")
        return df
    
    for split_data, factor in SPLITS[stock_symbol]:
        df.loc[df["Date"] < split_data, ["Close", "Open", "High", "Low"]] /= factor
        df.loc[df["Date"] < split_data, ["Volume"]] *= factor
    
    return df