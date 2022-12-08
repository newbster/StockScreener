import yfinance as yf
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from ta.trend import SMAIndicator
import csv
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

def get_forex_tickers():
    # reading the data from the file
    with open('forex_tickers.txt') as f:
        data = f.read()

    # reconstructing the data as a dictionary
    js = json.loads(data)
    
    return js

def add_stos(df):
    # Initialize Stochastic Indicator
    indicator_slow6 = StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"], window=6, smooth_window=1)
    indicator_slow12 = StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"], window=12, smooth_window=1)

    df['slow6'] = indicator_slow6.stoch()
    df['slow12'] = indicator_slow12.stoch()
    return df

def add_mas(df):
    # Initialize Bollinger Bands Indicator
    indicator_sma5 = SMAIndicator(close=df["Close"], window=5)
    indicator_sma200 = SMAIndicator(close=df["Close"], window=200)

    # Add Bollinger Bands features
    df['5dma'] = indicator_sma5.sma_indicator()
    df['200dma'] = indicator_sma200.sma_indicator()

    return df

def add_bb(df):
    # Initialize Bollinger Bands Indicator
    indicator_bb = BollingerBands(close=df["Close"], window=18, window_dev=2)

    # Add Bollinger Bands features
    df['bb_middle'] = indicator_bb.bollinger_mavg()
    df['bb_upper'] = indicator_bb.bollinger_hband()
    df['bb_lower'] = indicator_bb.bollinger_lband()

    return df

def analyze_stocks(df):
    # Add BB values to df
    df = add_bb(df)
    # Add sto's (12 and 6) to df
    df = add_stos(df)
    # Add 5-day ma
    df = add_mas(df)
    
    return df

def is_setup(df):
    count = 0
    row_count = 0
    # Get number of times stock touches lower band. Goal is 3 or more.
    for i, row in df.iterrows():
        
        if row_count > len(df) - 10: # we only care about the last 10 days
            if row['Low'] < row['bb_lower']:
                count += 1
        row_count += 1

    # Check for upward bias 
    upward_bias = df["Close"].values[-1] > df["5dma"].values[-1]

    # Check for upward momentum
    upward_momentum = df["slow12"].values[-1] > df["slow12"].values[-2]
    
    return count >= 3 and upward_bias and upward_momentum

def send_email(stocks_to_see, recipients):
    for recipient_address in recipients:
        mail_content = 'Forex Symbols:\n\n'
        for stock in stocks_to_see:
            mail_content += stock + '\n'
        #The mail addresses and password
        sender_address = 'newbystockscreener@gmail.com'
        sender_pass = 'deznmwxewjaslvcx'
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = recipient_address
        message['Subject'] = 'Check These Forex Symbols Out!'   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'plain'))
        #Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, recipient_address, text)
        session.quit()

# This is where the program starts
def main():
    stocks_to_see = []
    
    # Iterate through each stock from the stock screener, add indicators, and find good setups
    for k,v in get_forex_tickers().items():
        print('\n')
        print(k)
        stock = yf.Ticker(k)
        try:
            df = stock.history(period="1mo", interval='60m')
            df = analyze_stocks(df)
            if is_setup(df):
                stocks_to_see.append(v)
        except:
            print(f"Ticker {k} invalid, skipping.")

    print(stocks_to_see)
    if len(stocks_to_see) > 0:
        send_email(stocks_to_see, ['jtnewby88@gmail.com'])

if __name__ == "__main__":
    main()