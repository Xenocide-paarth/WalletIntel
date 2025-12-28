import plotly.express as px

class Configurations:
    
    # --- THEME SETTINGS ---

    VIBRANT_SEQUENCE = px.colors.qualitative.Bold 
    VIBRANT_SCALE: str = "Plasma" 
    CHART_TEMPLATE: str = "plotly_white" 

    ABOUT: str = """## 📊 About This Dashboard

    This **Personal Finance Dashboard** helps you turn everyday transactions into **clear, actionable insights**.

    Track your **net flow**, monitor **account balances**, analyze **expense categories**, and visualize **balance trends over time** — all with dynamic filters for precise control.

    Built with a **clean, dark-mode friendly design**, the focus is on **clarity over clutter** and **decisions over raw data**.

    > *Measure smart. Spend intentionally. Grow consistently.*

    """

    # --- DATA ---
    
    with open("data.txt", "r") as f:
        URL: str = f.read()

    with open("responder_link.txt", "r") as f:
        responder_link: str = f.read()
         
    SHEET: str = "Form Responses 2"


    # --- GRAPH SETTINGS ---
    PLOTLY_TEMPLATE = {
    "template": "simple_white",
    "font": {"family": "DejaVu Sans, Helvetica, Arial", "size": 11},
    "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
    "yaxis": {"tickprefix": "₹", "tickformat": ","}
    }

    # --- ADMIN ---
    ADMIN_PASSWORD = "paarth@99_streamlitApp"