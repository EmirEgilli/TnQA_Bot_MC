import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpl_patches

from datetime import date
from time import sleep

from bob_telegram_tools.utils import TelegramTqdm
from bob_telegram_tools.bot import TelegramBot

from telegram.ext import Updater, CommandHandler

token = '---------'
user_id = int('--------')

def MC_Sim(update, context):

    start = "2012-08-01"
    end = date.today()
    
    try:
        ticker = str(context.args[0])
        
    except (IndexError, ValueError):
        update.message.reply_text('Please check the ticker for the symbol!')

    
    bot = TelegramBot(token, user_id)

    stock_data = yf.download(ticker, start, end)

    returns = stock_data["Adj Close"].pct_change()
    daily_vol = returns.std()

    T = 252
    count = 0
    price_list = []
    last_price = stock_data["Adj Close"][-1].copy()

    price = last_price * (1 + np.random.normal(0, daily_vol))
    price_list.append(price)

    for y in range(T):
        if count == 251:
            break
        price = price_list[count] * (1+ np.random.normal(0, daily_vol))
        price_list.append(price)
        count += 1

    NUM_SIMULATIONS = 1000
    df = pd.DataFrame()
    last_price_list = []
    for x in range(NUM_SIMULATIONS):
        count = 0
        price_list = []
        price = last_price * (1 + np.random.normal(0, daily_vol))
        price_list.append(price)
        
        for y in range(T):
            if count == 251:
                break
            price = price_list[count] * (1 + np.random.normal(0, daily_vol))
            price_list.append(price)
            count += 1
            
        df[x] = price_list
        last_price_list.append(price_list[-1])


    handles = [mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0,
                                      alpha=0)]*3
    labels = []
    labels.append("Expected Price: ${}".format(round(np.mean(last_price_list),2)))
    labels.append("Quantile (5%): {}".format(round(np.percentile(last_price_list, 5),2)))
    labels.append("Quantile (95%): {}".format(round(np.percentile(last_price_list, 95),2)))             

    plt.hist(last_price_list, bins=100)
    plt.suptitle("Monte Carlo Histogram: {}".format(ticker))
    plt.axvline(np.percentile(last_price_list, 5), color="r", linestyle="dashed", linewidth=2)
    plt.axvline(np.percentile(last_price_list, 95), color="r", linestyle="dashed", linewidth=2)
    plt.legend(handles, labels, loc="best", fontsize="small", fancybox=True, framealpha=0.7, handlelength=0, handletextpad=0)


    pb = TelegramTqdm(bot)
    for i in pb(range(3)):
        sleep(1)

    bot.send_plot(plt)    
    bot.clean_tmp_dir()
    plt.clf() #To clear the plot
    
def help(update, context):
    update.message.reply_text("""Available Commands :
    /MC <ticker> - Performs a Monte Carlo Analysis on the selected 
    symbol.
    Tickers for symbols can be found on Yahoo Finance.
    Ticker Examples:
        AAPL - Apple
        AMZN - Amazon
        GOOG - Google
        NFLX - Netflix
        ES=F - S&P500
        NQ=F - Nasdaq
        YM=F - Dow Jones
        BZ=F - Brent Oil
        CL=F - Crude Oil
        NG=F - Natural Gas
        GC=F - Gold
        """)
    
def start(update, context):
    update.message.reply_text(
        """Hello and welcome to TnQA Bot.
        Please type /help to see the list of available commands.""")

if __name__ == '__main__':
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("MC", MC_Sim))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.start_polling()
    updater.idle()
    MC_Sim()
