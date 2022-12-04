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

def add_good_stocks():
    symbols = []
    print('Scanning stocks...')
    with open('test_stocks.csv', newline='') as f:
        for row in csv.reader(f):
            symbols.append(row[0])
    return symbols[1:]

def add_stos(df):
    # Initialize Stochastic Indicator
    indicator_slow6 = StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"], window=6, smooth_window=1)
    indicator_slow12 = StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"], window=12, smooth_window=1)

    df['slow6'] = indicator_slow6.stoch()
    df['slow12'] = indicator_slow12.stoch()
    return df

def add_ma(df, days):
    # Initialize Bollinger Bands Indicator
    indicator_sma = SMAIndicator(close=df["Close"], window=days)

    # Add Bollinger Bands features
    df['5dma'] = indicator_sma.sma_indicator()

    return df

def add_bb(df):
    # Initialize Bollinger Bands Indicator
    indicator_bb = BollingerBands(close=df["Close"], window=18, window_dev=2)

    # Add Bollinger Bands features
    df['bb_middle'] = indicator_bb.bollinger_mavg()
    df['bb_upper'] = indicator_bb.bollinger_hband()
    df['bb_lower'] = indicator_bb.bollinger_lband()

    return df

def get_events(df):
    count = 0
    for index, row in df.iterrows():
        if row['Low'] < row['bb_lower']:
            count += 1
        else:
            count = 0
    return count

def analyze_stocks(df):
    # Add BB values to df
    df = add_bb(df)
    # Add sto's (12 and 6) to df
    df = add_stos(df)
    # Add 5-day ma
    df = add_ma(df,5)
    
    return df

def send_email(stocks_to_see, recipients):
    for recipient_address in recipients:
        mail_content = 'Stonks:\n\n'
        for stock in stocks_to_see:
            mail_content += stock + '\n'
        #The mail addresses and password
        sender_address = 'newbystockscreener@gmail.com'
        sender_pass = 'deznmwxewjaslvcx'
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = recipient_address
        message['Subject'] = 'Check These Stocks Out!'   #The subject line
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
    for index, symbol in enumerate(add_good_stocks()):
        stock = yf.Ticker(symbol)
        df = stock.history(period="2mo")
        df = analyze_stocks(df)
        if get_events(df) >= 3:
            stocks_to_see.append(symbol)
        if index % 50 == 0 and index != 0:
            sleep(10)
    send_email(stocks_to_see, ['jtnewby88@gmail.com'])

if __name__ == "__main__":
    main()