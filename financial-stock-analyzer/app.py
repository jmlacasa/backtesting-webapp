import numpy as np 
import pandas as pd
import yfinance as yf
import datetime as dt
from plotly import express as px, graph_objects as go
from shiny import App, render, ui, reactive, req

import mplfinance as mpf

from pathlib import Path

from shinywidgets import output_widget, render_widget, render_plotly

import logging
logging.basicConfig(level=logging.INFO)


#USER INPUTS
#GET STOCK DATA

TITLE = "PyShiny Financial Stock Analyzer"
period = '1y'

# FUNCTIONS

def make_plotly_chart(stock_history, window_mavg_short=30, window_mavg_long=90):
    """
    
    """
    stock_df = stock_history[['Close']].reset_index()

    stock_df['mavg_short'] = stock_df['Close'].rolling(window=window_mavg_short).mean()
    stock_df['mavg_long'] = stock_df['Close'].rolling(window=window_mavg_long).mean()

    fig = px.line(stock_df.set_index('Date')
                  , color_discrete_map={'Close': '#212529', 'mavg_short': '#0d6efd', 'mavg_long': '#0dcaf0'}
                  )
    fig = fig.update_yaxes(title="Share Price")

    fig = fig.update_layout(
        plot_bgcolor = 'rgba(0, 0, 0, 0)',
        paper_bgcolor = 'rgba(0, 0, 0, 0)',
        legend_title_text = '',
    )


    return fig

def my_card(title, value, width=4, bg_color="bg-info", text_color="text-white"):
    """
    Generate a bootstrap card
    """
    card_ui = ui.div(
        ui.div(
            ui.div(
                ui.div(ui.h4(title), class_="card-title"),
                ui.div(value, class_="card-text"),
                class_="card-body flex-fill"
            ),
            class_=f"card {bg_color} {text_color}",
            style=f"flex-grow: 1; margin:5px;"
        ),
        class_ = f"col-md-{width} d-flex"
    )

    return card_ui

page_dependencies  = ui.tags.head(
    ui.tags.link(rel="stylesheet", type="text/css", href="style.css"),
)

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Stock Analysis",
        ui.layout_sidebar(
            ui.sidebar(
                ui.panel_title("Select a stock"),
                ui.input_selectize("stock_symbol", "Stock symbol", choices=["AAPL", "MSFT", "GOOGL"], selected="AAPL", multiple=False),
            ),
            ui.h2(
                ui.output_text("txt")
            ),
            ui.div(
                output_widget("stock_chart_widget", width="auto", height="auto"),
                class_="card"
            ),
            ui.navset_card_pill(
                ui.nav_panel(
                    "Company Summary",
                    ui.output_ui("stock_info_ui")
                ),
                ui.nav_panel(
                    "Income Statement",
                    ui.output_table("income_statement_table")
                )
            )
        )
    ),
    title=ui.tags.div(
        ui.img(src= "logo.jpg", height="50px", style="margin:10px"),
        ui.h4(" " + TITLE, style="align-self:center"),
        style="display:flex;-webkit-filter: drop-shadow(2px 2px 2px #222):"
    ),
    bg="#97CBFF",
    inverse=True,
    header = page_dependencies
)


def server(input, output, session):
    @reactive.calc
    def stock():
        return yf.Ticker(str(input.stock_symbol()))
        

    @render.text
    def txt():
        return f"You selected: {input.stock_symbol()}"
    
    
    @render_plotly
    # @reactive.effect
    def stock_chart_widget():
        stock_history = stock().history(period=period)
        fig = make_plotly_chart(stock_history, window_mavg_short=30, window_mavg_long=90)
        logging.info(f"fig: {fig}")
        return go.FigureWidget(fig)
    
    @render.ui
    def stock_info_ui():
        app_ui = ui.row(
            ui.h5("Company Information"),
            my_card("Industry", stock().info['industry'], bg_color='bg-dark'),
            my_card("Fulltime Employees", "{}".format(stock().info['fullTimeEmployees']), bg_color='bg-dark'),
            my_card("Website", ui.a(stock().info['website'], href=stock().info['website'], target_='blank'), bg_color='bg-dark'),
            
            ui.tags.hr(),

            # Financial Ratios
            ui.h5("Financial Ratios"),
            my_card("Profit Margin", f"{stock().info['profitMargins']:.1%}", bg_color='bg-primary'),
            my_card("Revenue Growth", f"{stock().info['revenueGrowth']:.1%}", bg_color='bg-primary'),
            my_card("Current Ratio", f"{stock().info['currentRatio']:.2f}", bg_color='bg-primary'),

            ui.tags.hr(),

            # Financial Operations
            ui.h5("Financial Operations"),
            my_card("Total Revenue", f"${stock().info['totalRevenue']:,.0f}", bg_color='bg-info'),
            my_card("EBITDA", f"${stock().info['ebitda']:,}", bg_color='bg-info'),
            my_card("Operating Cash Flow", f"${stock().info['operatingCashflow']:,.0f}", bg_color='bg-info'),


        )
        return app_ui
    
    @render.table
    def income_statement_table():
        return stock().incomestmt.reset_index()

www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
