import numpy as np 
import pandas as pd
import yfinance as yf
import datetime as dt
from plotly import express as px

#USER INPUTS

symbol = 'AAPL'
period = '1y'
window_mavg_short = 30
window_mavg_long = 90

#GET STOCK DATA