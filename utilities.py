import yfinance as yf
from langchain_core.tools import tool
import pandas as pd
from typing import List, Dict
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv 
load_dotenv()


#Function to get stock history
@tool
def get_stock_history(ticker: str, period: str = "4mo", interval: str = "1mo")->dict:
    """
    Fetches historical stock data for a given ticker symbol.

    Args:
        ticker (str): The stock ticker symbol.
        period (str): The period over which to fetch data (default is "1d").
        interval (str): The data interval (default is "1m").

    Returns:
        dict: A dictionary containing the historical stock data.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)
    return hist.to_dict()


#Function to get closing prices
def get_closing_prices(ticker: str, period:str = "1y", interval:str="1mo") -> dict:
    """
    Fetch closing prices for a given stock ticker using yfinance.

    Args:
        ticker : str
            Stock symbol or ticker recognized by yfinance (e.g., "AAPL", "MSFT").
        period : str, optional
            Data lookback period to download (default "1y"). Accepts yfinance period strings
            such as "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max".
        interval : str, optional
            Data sampling interval (default "1mo"). Accepts yfinance interval strings such as
            "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo".
   
   Returns:
        pd.Series
            Series of closing prices indexed by timestamp (pandas.DatetimeIndex). The series
            corresponds to the 'Close' column from the yfinance historical data for the
            requested period and interval.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)
    if not hist.empty:
        return hist['Close'].to_dict()
    else:
        raise {"error": "No historical data found for the given ticker and parameters."}


#Function to get stock info
@tool
def get_stock_info(ticker: str) -> dict:
    """
    Fetches general information about a stock.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        dict: A dictionary containing the stock information.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

#Function to get stock news
@tool
def get_stock_news(stock_symbol: str, 
                   finnhub_key: str = os.getenv("FINNHUB_API_KEY"),
                   target_count: int = 100) -> List[Dict]:
    """
    Fetch news about a stock from finhub.
    
    Args:
        stock_symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        finnhub_key: API key from finnhub.io
        target_count: Target number of news items to return (default: 100)
    
    Returns:
        List of dictionaries with format: {'source': str, 'content': str}
    """
    stock_symbol = stock_symbol.upper()
    all_news = []

    
    # Fetch from Finnhub
    if finnhub_key:
        url = "https://finnhub.io/api/v1/company-news"
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        headers = {'X-Finnhub-Token': finnhub_key}
        params = {
            'symbol': stock_symbol,
            'from': from_date,
            'to': to_date
        }
        url = "https://finnhub.io/api/v1/company-news"
        try:
            response = requests.get(url, params=params, headers=headers ,timeout=10)
            response.raise_for_status()
            data = response.json()
            for item in data[:target_count]:
                content = f"{item.get('headline', '')}. {item.get('summary', '')}"
                all_news.append({
                    'source': item.get('source', 'Finnhub'),
                    'content': content
                })
        except Exception as e:
            return {"error": f"Error fetching news from Finnhub: {str(e)}"}

    else:
        return {"error": "Finnhub API key is required to fetch stock news."}
    
    if not all_news:
        return {"error": "No news found for the given stock symbol. Check if the symbol is correct."}
    # Remove duplicates and limit to target count
    seen = set()
    unique_news = []
    for item in all_news:
        if item['content'] not in seen:
            seen.add(item['content'])
            unique_news.append(item)
    
    return unique_news[:target_count]

agent_tools = [get_stock_history, get_stock_info, get_stock_news]
