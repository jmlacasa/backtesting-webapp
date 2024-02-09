import numpy as np 
import pandas as pd
import yfinance as yf
import datetime as dt
from plotly import express as px
from shiny import App, render, ui, reactive, req

from pathlib import Path

from shinywidgets import output_widget, render_widget

import logging
logging.basicConfig(level=logging.INFO)


#USER INPUTS

TITLE = "PyShiny Financial Stock Analyzer"
symbol = 'AAPL'
period = '1y'
window_mavg_short = 30
window_mavg_long = 90

#GET STOCK DATA

page_dependencies  = ui.tags.head(
    ui.tags.link(rel="stylesheet", type="text/css", href="style.css"),
)


app_ui = ui.page_navbar(
    ui.nav_panel(
        "Stock Analysis",
        ui.layout_sidebar(
            ui.sidebar(
                ui.panel_title("Hello Shiny!"),
                ui.input_slider("n", "N", 0, 100, 20)
            ),
            ui.h2(
                ui.output_text_verbatim("txt")
            ),
            ui.navset_card_pill(
                ui.nav_panel(
                    "Company Summary",
                    "TODO - Company Summary"
                ),
                ui.nav_panel(
                    "Chart",
                    "TODO - CHart"
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
    @render.text
    def txt():
        return f"n*2 is {input.n() * 2}"

www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
