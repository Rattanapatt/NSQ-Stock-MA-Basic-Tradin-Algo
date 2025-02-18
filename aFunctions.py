import pandas as pd

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
    
    return

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
            
            