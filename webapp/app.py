from shiny import ui
import datetime
import logging
import logging.config
logging.getLogger().setLevel(logging.DEBUG)


from os.path import expanduser
home = expanduser("~")


app_ui = ui.page_fluid(
    # Application title
    ui.panel_title("Backtest"),
    
    ui.row(
        ui.input_text("symbol", "Symbol", value="AAPL"),
        ui.input_select("type", "Type", 
                        {"auto": "auto", "candlesticks": "candlesticks", "matchsticks": "matchsticks", "bars": "bars", "line": "line"},
                        selected="auto"),
        ui.input_select("theme", "Theme", 
                        {"white": "white", "black": "black"}, 
                        selected="white")
    ), 
    ui.card(
        ui.card_header("High Indicator"),
        ui.row(
            ui.input_select("ilab1", "High ind", 
                            {"none": "None", "EMA": "EMA", "SMA": "SMA"}, 
                            selected="EMA"),
            ui.input_select("icol1", "Color", 
                            {"blue": "Blue", "red": "Red", "green": "Green", "purple": "Purple", "orange": "Orange"}, 
                            selected="blue"),
            ui.input_numeric("ival1", "Value", value=200),
            ui.input_numeric("imin1", "Min", value=10),
            ui.input_numeric("imax1", "Max", value=200),
            ui.input_numeric("istp1", "Step", value=10)
        )
    ),
    ui.card(
        ui.card_header("Low Indicator"),
        ui.row(
            ui.input_select("ilab2", "Low ind", 
                            {"none": "None", "EMA": "EMA", "SMA": "SMA"}, 
                            selected="SMA"),
            ui.input_select("icol2", "Color", 
                            {"blue": "Blue", "red": "Red", "green": "Green", "purple": "Purple", "orange": "Orange"}, 
                            selected="red"),
            ui.input_numeric("ival2", "Value", value=50),
            ui.input_numeric("imin2", "Min", value=10),
            ui.input_numeric("imax2", "Max", value=200),
            ui.input_numeric("istp2", "Step", value=10)
        )
    ),
    ui.row(
        ui.input_select("calc", "Calculate", 
                {"Use values": "Use values", "Vary high indicator": "Vary high indicator", "Vary low indicator": "Vary low indicator", "Vary both indicators": "Vary both indicators"},
                selected="Use values"
        ),
        ui.input_date_range("dateRange",
            label="Date range input: yyyy-mm-dd",
            start=datetime.date(2010, 1, 1),
            end=datetime.date.today()
        ),
        ui.input_radio_buttons("span", "Timespan:", 
                                ["Use above dates", "1M", "3M", "6M", "YTD", "1Y", "2Y", "5Y", "10Y", "MAX"], 
                                selected="MAX", 
                                inline=True
        ),
    ),
    ui.row(
        ui.input_checkbox("adjusted", "Adjusted", value=True),
        ui.input_checkbox("volume", "Volume", value=True),
        ui.input_checkbox("logscale", "Log Scale", value=False),
        ui.input_checkbox("bollinger", "Bollinger Bands", value=False),
        ui.input_checkbox("multicol", "4-colored Candles", value=False)
    ),
    ui.input_checkbox_group("cols", "Columns to include:", 
                            {"Open": 2, "High": 3, "Low": 4, "Close": 5, "Volume": 6, "Adjusted": 7}, 
                            selected=[2, 5], 
                            inline=True
    ),

    ui.row(
        ui.input_select("trade", "Trade at", 
                        {"open": "open", "close": "close"}, 
                        selected="close"),
        ui.input_numeric("itrade", "First trade to plot", value=-1),
        ui.input_numeric("ntrade", "# of trades to plot", value=1, min=1),
    ),
    ui.div(
        ui.navset_card_tab(
            # First tab with plots and gains text
            ui.nav_panel(
                "Charts",
                ui.output_plot("bt1Plot1"),
                ui.output_plot("bt1Plot2"),
                ui.output_text("bt1Gains")
            ),
            # Second tab with trades text
            ui.nav_panel(
                "Trades",
                ui.output_text("bt1Trades")
            ),
            # Third tab with data text
            ui.nav_panel(
                "Data",
                ui.output_text("bt1Data")
            ),
            # Fourth tab with scan text
            ui.nav_panel(
                "Scan",
                ui.output_text("bt1Scan")
            )
        )
    )
)

# Note: This translation assumes a single-column sidebar layout with input controls.
# The main panel is left as a placeholder for outputs or other content based on the complete UI definition.
from shiny import reactive, render, ui, App, render_plot
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas_ta as ta

# Define the server logic
def server(input, output, session):

    ohlcv_agg = dict((
        ('Open', 'first'),
        ('High', 'max'),
        ('Low', 'min'),
        ('Close', 'last'),
        ('Volume', 'sum'),
    ))
    session.kdata = pd.read_csv(home + r'\repos\backtesting-webapp\webapp\BTCUSDT_1m.csv', parse_dates=True, index_col=0)
    session.kdata = session.kdata.resample('60T').agg(ohlcv_agg)
    
    session.kdata = (session.kdata / 1e3).assign(Volume=session.kdata.Volume * 1e3) # mBTC OHLC prices
    session.kdata.iloc[:, :4] = session.kdata.iloc[:, :4].ffill()

    # set gstart to start of specific year

    gstart1 = session.kdata.index[0]
    gend2 = session.kdata.index[-1]
    # Reactive expression for date manipulation based on user input
    @reactive.effect
    def getSpan():
        symbol = input.symbol()  # Triggering reactivity on symbol change
        span_selection = input.span()#input.span
        toDate = None  # Python's equivalent of NULL
        
        # Current date in pandas Timestamp format for consistency with operations
        current_date = gend2 #pd.Timestamp(datetime.now().date())

        if span_selection == "1M":
            fromDate = current_date - pd.DateOffset(months=1)
        elif span_selection == "3M":
            fromDate = current_date - pd.DateOffset(months=3)
        elif span_selection == "6M":
            fromDate = current_date - pd.DateOffset(months=6)
        elif span_selection == "YTD":
            fromDate = pd.Timestamp(datetime(current_date.year, 1, 1))
        elif span_selection == "1Y":
            fromDate = current_date - pd.DateOffset(years=1)
        elif span_selection == "2Y":
            fromDate = current_date - pd.DateOffset(years=2)
        elif span_selection == "5Y":
            fromDate = current_date - pd.DateOffset(years=5)
        elif span_selection == "10Y":
            fromDate = current_date - pd.DateOffset(years=10)
        elif span_selection == "MAX":
            fromDate = gstart1
        else:
            date_range = input.dateRange()
            fromDate = pd.Timestamp(date_range[0])
            toDate = pd.Timestamp(date_range[1])

        # Ensure fromDate does not precede gstart1
        fromDate = max(fromDate, gstart1)

        # Constructing the date span string
        if toDate is None:
            strSpan = f"{fromDate}::"
        else:
            strSpan = f"{fromDate}::{toDate}"
        logging.info(("fromDate, toDate, strSpan", fromDate, toDate, strSpan))
        session.fromDate = fromDate
        session.toDate = toDate
        session.strSpan = strSpan
        return fromDate, toDate, strSpan
    
    @reactive.effect
    def getSpan2():
        symbol = input.symbol()  # Assuming symbol changes trigger this reactive
        indx1 = input.itrade()
        ntrade = input.ntrade()
        kdata = session.kdata  # Assuming kdata is stored in the session or fetched dynamically
        
        # Adjust indx1 based on the input and the size of kdata
        if indx1 < 0:
            indx1 = len(kdata) + indx1
        elif indx1 >= (len(kdata) - 2):
            indx1 = len(kdata) - 2
        
        indx2 = indx1 + ntrade
        if indx2 >= len(kdata):
            indx2 = len(kdata) - 1
        
        # Assuming kdata has a datetime index or a 'date' column for extracting date values
        logging.debug((indx1, indx2, len(kdata)))
        date1 = kdata.index[indx1] if hasattr(kdata, 'index') else kdata['date'].iloc[indx1]
        date2 = kdata.index[indx2] if hasattr(kdata, 'index') else kdata['date'].iloc[indx2]
        
        # Formatting dates as strings and constructing the span string
        strSpan2 = f"{date1.strftime('%Y-%m-%d')}::{date2.strftime('%Y-%m-%d')}"
        
        logging.info((date1, date2, strSpan2))
        session.date1 = date1
        session.date2 = date2
        session.strSpan2 = strSpan2
        return strSpan2

    @reactive.Effect
    def get_data():
        symbol = input.symbol()
        
        # Adjusting the symbol if it starts with "^"
        gsymbol = symbol[1:] if symbol.startswith("^") else symbol
        
        # Fetching the data from Yahoo Finance
        # data = yf.Ticker(gsymbol)
        gdata = yf.download(gsymbol, start=session.fromDate, end=session.toDate)
        
        # Storing the fetched data and additional info in the session
        session.gdata = gdata
        session.gsymbol = gsymbol
        
        # Extracting start dates from the data
        if not gdata.empty:
            session.gstart0 = gdata.index[0].date()
            ival1 = input.ival1()
            # Ensure ival1 is within the range before accessing the index
            if ival1 is not None and 0 <= ival1 < len(gdata):
                session.gstart1 = gdata.index[ival1].date()
            else:
                session.gstart1 = gdata.index[0].date()


    @reactive.Effect
    def bt1data():
        # Ensure getData() and getSpan() have been called and processed
        # session.strSpan = getSpan()
        
        # Accessing global data (assuming gdata is stored in the session by getData())
        gdata = session.gdata

        logging.debug(gdata.columns)
        
        # Adjusting the 'Close' column based on 'adjusted' input
        Close = gdata['Adj Close'] if input.adjusted() else gdata['Close']
        
        # Calculating long and short moving averages
        if input.ilab1() == "SMA":
            longMA = ta.overlap.sma(Close, n=input.ival1())
        else:
            longMA = ta.overlap.ema(Close, n=input.ival1())

        if input.ilab2() == "SMA":
            shrtMA = ta.overlap.sma(Close, n=input.ival2())
        else:
            shrtMA = ta.overlap.ema(Close, n=input.ival2())

        logging.debug((longMA.shape, shrtMA.shape))
        
        # Combining data with long and short MAs
        hdata = pd.concat([gdata, longMA.rename('longMA'), shrtMA.rename('shrtMA')], axis=1)
        
        # Calculating flags based on MA crossovers
        flag = (hdata['shrtMA'] > hdata['longMA']).astype(int)
        flag[flag.isna()] = -1
        lag1 = flag.shift(1).fillna(-1)
        lag2 = flag.shift(2).fillna(-1)
        
        # Merging flags and lags with the main data
        hdata = pd.concat([hdata, flag.rename('flag'), lag1.rename('lag1'), lag2.rename('lag2')], axis=1)
        
        # Filter data based on strSpan
        idata = hdata.loc[session.fromDate:session.toDate]
        # Further calculations and manipulations...
        # This section needs to be adjusted based on the actual logic you need to implement,
        # as the original R code involves complex operations specific to financial data analysis.
        
        # Store the processed data back in the session for global access
        session.hdata = hdata
        session.idata = idata

    # def bt1Plot(gdata, gsymbol, plot_type='line', theme='classic', volume=False, mav=(None, None)):
    #     """
    #     A simplified plotting function using matplotlib.pyplot.

    #     Parameters:
    #     - gdata: DataFrame containing the stock data with a DateTimeIndex.
    #     - gsymbol: The symbol of the stock being plotted.
    #     - plot_type: Type of plot ('line' for line plot, 'candle' for candlestick, but candlestick requires mplfinance).
    #     - theme: Plot theme ('classic' for white background, 'dark' for dark background).
    #     - volume: Whether to plot volume data (True/False). This example does not include volume plotting.
    #     - mav: Tuple of moving average periods, e.g., (20, 50) for 20 and 50 periods.
    #     """
        
    #     # Setting the plot theme
    #     if theme == 'dark':
    #         plt.style.use('dark_background')
    #     else:
    #         plt.style.use('classic')

    #     # Preparing data
    #     dates = gdata.index
    #     close_prices = gdata['Close']

    #     # Creating the plot
    #     fig, ax = plt.subplots(figsize=(10, 6))

    #     # Plotting the 'Close' prices
    #     ax.plot(dates, close_prices, label=f'{gsymbol} Close', color='blue')

    #     # Plotting moving averages if specified
    #     if mav[0]:
    #         gdata['MA' + str(mav[0])] = gdata['Close'].rolling(window=mav[0]).mean()
    #         ax.plot(dates, gdata['MA' + str(mav[0])], label=f'{mav[0]}-period MA', color='orange')
    #     if mav[1]:
    #         gdata['MA' + str(mav[1])] = gdata['Close'].rolling(window=mav[1]).mean()
    #         ax.plot(dates, gdata['MA' + str(mav[1])], label=f'{mav[1]}-period MA', color='green')

    #     # Customizing the plot
    #     ax.set_title(f'{gsymbol} Closing Prices')
    #     ax.set_xlabel('Date')
    #     ax.set_ylabel('Price')
    #     ax.legend()

    #     # Showing the plot
    #     plt.show()

    
    
    # @render.plot
    # def bt1Plot2():
    #     # Assuming bt1data() and getSpan2() are functions that prepare the data and set global variables or session state
    #     # bt1data()  # Prepare the data
    #     # getSpan2()  # Update session or global variables for the span
    #     gdata = session.kdata
    #     gsymbol = input.symbol()
    #     plot_type='line'
    #     theme='classic'
    #     volume=False
    #     mav=(None, None)
    #     # Now, generate and render the plot. This assumes bt1Plot() is adapted to Python and returns a Matplotlib figure
    #     # fig = bt1Plot(session.kdata, input.symbol())
    #     # Setting the plot theme
    #     if theme == 'dark':
    #         plt.style.use('dark_background')
    #     else:
    #         plt.style.use('classic')

    #     # Preparing data
    #     dates = gdata.index
    #     close_prices = gdata['Close']

    #     # Creating the plot
    #     fig, ax = plt.subplots(figsize=(10, 6))

    #     # Plotting the 'Close' prices
    #     ax.plot(dates, close_prices, label=f'{gsymbol} Close', color='blue')

    #     # Plotting moving averages if specified
    #     if mav[0]:
    #         gdata['MA' + str(mav[0])] = gdata['Close'].rolling(window=mav[0]).mean()
    #         ax.plot(dates, gdata['MA' + str(mav[0])], label=f'{mav[0]}-period MA', color='orange')
    #     if mav[1]:
    #         gdata['MA' + str(mav[1])] = gdata['Close'].rolling(window=mav[1]).mean()
    #         ax.plot(dates, gdata['MA' + str(mav[1])], label=f'{mav[1]}-period MA', color='green')

    #     # Customizing the plot
    #     ax.set_title(f'{gsymbol} Closing Prices')
    #     ax.set_xlabel('Date')
    #     ax.set_ylabel('Price')
    #     ax.legend()
    #     return fig

        
# Create the app with UI and server logic
app = App(app_ui, server)

# Note: Replace `app_ui` with your translated UI definition from the previous step.
