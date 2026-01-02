# %%
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from datetime import date, timedelta, datetime

from config import Configurations 
from graphs import Graph 
# %%
class Finance:
    
    AMOUNT_COLS = [
        "Income Amount",
        "Expense Amount",
        "Transfer Amount",
        "Transfer-In Amount",
        "Transfer-Out Amount",
    ]

    ACCOUNT_COLS = [
        "Income Account",
        "Expense Source",
        "Transfer Account",
        "Transfer-In Account",
        "Transfer-Out Source",
    ]

    SOURCE_COLS = [
        "Income Source",
        "Expense Account",
        "Transfer Source",
        "Transfer-In Source",
        "Transfer-Out Account",
    ]

    DESC_COLS = [
        "Income Note",
        "Expense Note",
        "Transfer Note",
        "Transfer-In Note",
        "Transfer-Out Note",
    ]

    def __init__(self):
        self.raw = None
        self.df = None

    # ---------- public API ----------

    def run(self):
        """Main pipeline: load, transform, type-cast."""
        self._load_raw()
        self._combine_columns()
        self._split_transfers()
        self._finalise_schema()
        self._enforce_types()
        return self.df
   
    def monthly_profit_and_loss(self, month: int, year: int):
        mask = (
            (self.df["Timestamp"].dt.year == year) &
            (self.df["Timestamp"].dt.month == month)
        )

        df_m = self.df[mask].copy()
        print(df_m)
        pnl = df_m.pivot_table(
            index=["Nature of Record", "Account"],
            values="Amount",
            aggfunc="sum",
            fill_value=0.0
        )
        print(pnl)
        return pnl
    # ---------- internal steps ----------

    # --- Data Processing --- #
    def _load_raw(self):
        self.raw = pd.read_excel(Configurations.URL, sheet_name=Configurations.SHEET)

    def _combine_columns(self):
        raw = self.raw

        # flip sign for Expense and Transfer-Out
        raw["Expense Amount"] = -raw["Expense Amount"]
        raw["Transfer-Out Amount"] = -raw["Transfer-Out Amount"]

        # coalesce across columns using first non-null
        raw["Amount"] = raw[self.AMOUNT_COLS].bfill(axis=1).iloc[:, 0]
        raw["Account"] = raw[self.ACCOUNT_COLS].bfill(axis=1).iloc[:, 0]
        raw["Source"] = raw[self.SOURCE_COLS].bfill(axis=1).iloc[:, 0]
        raw["Description"] = raw[self.DESC_COLS].bfill(axis=1).iloc[:, 0]

        # drop original cols
        drop_cols = (
            self.AMOUNT_COLS
            + self.ACCOUNT_COLS
            + self.SOURCE_COLS
            + self.DESC_COLS
        )
        self.raw = raw.drop(columns=drop_cols)

    def _split_transfers(self):
        raw = self.raw

        is_transfer = raw["Nature of Record"].str.strip().fillna("") == "Transfer"
        transfer_rows = raw[is_transfer].copy()
        non_transfer_rows = raw[~is_transfer].copy()

        # expense leg
        transfer_expense = transfer_rows.copy()
        transfer_expense["Amount"] = -transfer_expense["Amount"]
        
        temp = transfer_expense["Source"]
        transfer_expense["Source"] = transfer_expense["Account"]
        transfer_expense["Account"] = temp

        transfer_expense["Nature of Record"] = "Transfer-Out"

        # income leg
        transfer_income = transfer_rows.copy()
        transfer_income["Amount"] = transfer_income["Amount"]
        transfer_income["Nature of Record"] = "Transfer-In"

        split_transfers = pd.concat(
            [transfer_expense, transfer_income], ignore_index=True
        )

        self.df = pd.concat(
            [non_transfer_rows, split_transfers], ignore_index=True
        )

    def _finalise_schema(self):
        df = self.df
        df = df[
            ["Timestamp", "Nature of Record", "Amount", "Source", "Account", "Description"]
        ]
        df = df.sort_values("Timestamp", ascending=True).reset_index(drop=True)
        self.df = df

    def _enforce_types(self):
        df = self.df
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Nature of Record"] = df["Nature of Record"].astype("string")
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df["Account"] = df["Account"].astype("string")
        df["Source"] = df["Source"].astype("string")
        df["Description"] = df["Description"].astype("string")
        df["Description"] = df["Description"].fillna("").astype(str)
    
    # ---------- Visualization ----------

    def monthly_expense_compare(self, periods: list, topN: int):
        """
        periods: list of (year, month) tuples, e.g. [(2025, 11), (2025, 12)]
        topN:    number of top accounts per month to include (Others grouped)
        """

        all_rows = []

        for (year, month) in periods:
            data = self.monthly_expense(month=month, year=year)["Amount"].copy()

            # --- Top N + others per month ---
            topN_series = data.head(topN)
            others_sum = data.iloc[topN:].sum()

            labels = list(topN_series.index)
            values = list(topN_series.values)

            if others_sum > 0:
                labels.append("Others")
                values.append(others_sum)

            # add rows for this period
            for acc, amt in zip(labels, values):
                all_rows.append({
                    "Account": acc,
                    "Amount": amt,
                    "Period": f"{year}-{month:02d}"   # display label for x axis / legend
                })

        df_plot = pd.DataFrame(all_rows)

        # --- grouped bar chart ---
        fig = px.bar(
            df_plot,
            x="Account",
            y="Amount",
            color="Period",                     # one color per month
            barmode="group",
            labels={"Amount": "Amount (₹)", "Account": "Account", "Period": "Month"},
            title=f"Monthly Expense by Account {periods[0][1]}/{periods[0][0]} - {periods[-1][1]}/{periods[-1][0]}",
            text="Amount",
            text_auto=True,
            color_discrete_sequence=px.colors.sequential.Blues_r  # reuse palette
        )

        fig.update_traces(
            texttemplate="₹%{text:,.2f}",
            textposition="outside",
            hovertemplate=(
                "<b>Month:</b> %{fullData.name}<br>"
                "<b>Account:</b> %{x}<br>"
                "<b>Amount:</b> ₹%{y:,.2f}<extra></extra>"
            ),
        )

        fig.update_layout(
            template="simple_white",
            bargap=0.35,
            bargroupgap=0.12,
            xaxis_title="Account",
            yaxis_title="Amount (₹)",
            font=dict(family="DejaVu Sans, Helvetica, Arial", size=11),
            title_font=dict(
                size=18, family="DejaVu Sans, Helvetica, Arial",
                color="#102a43", weight="bold"
            ),
            margin=dict(l=60, r=40, t=60, b=80),
            legend_title_text="Month",
        )

        fig.update_yaxes(tickprefix="₹", tickformat=",")

        fig.show()

if __name__ == "__main__":
    # --- WEBPAGE SETUP ---
    st.set_page_config(
    page_title="Finance Dashboard",
    layout="wide",           
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "mailto:paarthmakkar99@gmail.com",
        "Report a bug": "mailto:paarthmakkar99@gmail.com",
        "About": Configurations.ABOUT
    }
    )
    
    # --- ADMIN LOGIN ---
    if "is_admin" not in st.session_state:
        pwd = st.sidebar.text_input("Admin password", type="password")
        if st.sidebar.button("Login as admin"):
            st.session_state["is_admin"] = (pwd == Configurations.ADMIN_PASSWORD)

            if st.session_state["is_admin"]:
                st.sidebar.success("Admin mode enabled")
            else:
                st.sidebar.error("Wrong password")
    
    is_admin = st.session_state.get("is_admin", False)

    # --- DATA LOADING ---
    @st.cache_data
    def load_data():
        engine = Finance()
        df = engine.run()
        return df
    
    try:
        with st.spinner("Fetching latest financial data..."):
            df = load_data()    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop
    
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filter Options")

    # Date Filter
    min_date = df["Timestamp"].min().date()
    max_date = df["Timestamp"].max().date()

    today = date.today()
    default_start = today.replace(day=1)

    date_range = st.sidebar.date_input(
        "📅 Select date range",
        value=[default_start, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # date_range is either a single date or a tuple/list of 2 dates during selection
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        # show friendly message / animation while user is still picking
        st.sidebar.info("Please select both start and end dates to update the dashboard.")
        st.stop()   # prevent rest of app from running until 2 dates exist

    # Account Filter
    accounts = df["Account"].dropna().unique()
    selected_accounts = st.sidebar.multiselect("🏦 Select Accounts",
                                               options=accounts,
                                               default=accounts)
    
    # Transaction Filter
    transactions = df["Nature of Record"].dropna().unique()
    selected_transactions = st.sidebar.multiselect("🔁 Select Transactions",
                                                   options=transactions,
                                                   default=transactions)
    
    # --- FILTERING DATA ---
    mask = (
        (df["Timestamp"].dt.date >= start_date) &
        (df["Timestamp"].dt.date <= end_date) &
        (df["Account"].isin(selected_accounts)) &
        (df["Nature of Record"].isin(selected_transactions))
    )
    filtered_df = df.loc[mask]

    # --- QUICK ACTIONS ---

    # 1. Responder Link
    st.sidebar.markdown("---")

    side_r1c1, side_r1c2 = st.sidebar.columns(2)

    with side_r1c1:
        if is_admin:
            st.link_button("✍️ Record", Configurations.responder_link)
        else:
            st.caption("Login as admin for quick actions.")

    # --- DASHBOARD LAYOUT ---
    st.title("⚡ Personal Finance Dashboard")
    st.markdown(f"*Data from {start_date} to {end_date}*")
    st.markdown("---")  

    # 1. KPI METRICS
    filtered_record_totals = filtered_df.groupby("Nature of Record")["Amount"].sum().to_dict()
    unfiltered_record_totals = df.groupby("Nature of Record")["Amount"].sum().to_dict()

    balance = filtered_record_totals.get("Income", 0) + filtered_record_totals.get("Expense", 0)
    transfer_InOut = unfiltered_record_totals.get("Transfer-In", 0) + unfiltered_record_totals.get("Transfer-Out", 0)

    try:
        expense_ratio = abs(filtered_record_totals.get("Expense") / filtered_record_totals.get("Income"))
    except ZeroDivisionError:
        expense_ratio = 0

    delta_metric1 = "In Line" if balance >= 0 else "Alert!"
    delta_metric2 = "In Line" if balance == 0 else "Alert!"
    delta_metric3 = "In Line" if expense_ratio <= 0.3 else "Alert!"
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Net Flow (Selected Period)", f"₹{balance:,.2f}",
                delta_color="normal" if balance >=0 else "inverse",
                delta= delta_metric1)
    col2.metric("🔁 Transfer In/Out (All Period)", f"₹{transfer_InOut:,.2f}",
                delta_color="normal" if transfer_InOut == 0 else "inverse",
                delta=delta_metric2)
    col3.metric("📉 Expense Ratio (Selected Period)", f"{expense_ratio:,.2%}",
                delta_color="normal" if expense_ratio <= 0.3 else "inverse",
                delta=delta_metric3)
    
    st.markdown("---")

    # 2. Account Balances and Expenses for period
    r1c1, r2c2 = st.columns((4,3))
    with r1c1:
        st.subheader("💸 Current Balance by Accounts")
        #current_bals = df[df['Account'].isin(selected_accounts)].groupby('Account')['Amount'].sum().reset_index()
        fig_bar = Graph.balance_by_account_graph(df=df, selected_accounts=selected_accounts, template=Configurations.PLOTLY_TEMPLATE)
        st.plotly_chart(fig_bar, width="stretch")

    with r2c2:
        st.subheader("📃 Expense Categories")
        exp_df = filtered_df[filtered_df['Nature of Record'] == 'Expense'].copy()
        if not exp_df.empty:
            fig_pie = Graph.expense_pie_topN(exp_df, topN=7, template=Configurations.PLOTLY_TEMPLATE)
            st.plotly_chart(fig_pie, width="stretch") 
        else:
            st.info("No expenses found.")
    
    st.markdown("---")

    # 3. Balance overtime
    st.subheader("📈 Balance over time (Selected Period)")
    fig_line = Graph.balance_overtime_graph(df, mask, template=Configurations.PLOTLY_TEMPLATE)
    if not filtered_df.empty:
        st.plotly_chart(fig_line, width="stretch")
    else:
        st.info("No Balances found.")
    st.markdown("---")
    # Raw Data
    with st.expander("📄 View Raw Data"):
        st.dataframe(filtered_df.sort_values('Timestamp', ascending=False).reset_index(drop=True)) 
    
    # filtered_df.info()
    # filtered_df.head(4)

    # tmp = df.set_index("Timestamp")
    # out=tmp.groupby([
    #     pd.Grouper(freq="W-SUN"),
    #     "Nature of Record",
    #     "Source"
    # ])["Amount"].sum()

    # last_week = out.index.get_level_values(0).max()
    
    # df_filtered_till_last_week = df[df["Timestamp"] <= timedelta(-7)]

    # test=df_filtered_till_last_week.pivot_table(
    #     values="Amount",
    #     index=[pd.Grouper(freq="W-SUN"), "Nature of Record", "Source"],
    #     aggfunc="sum",
    #     margins=True
    # )
    
    # test.to_excel("test.xlsx")
    # test = out.loc[out.index.get_level_values(0) == last_week]
    # test2 = out.loc[out.index.get_level_values(0) != last_week]
    # test3 = out.loc[out.index.get_level_values(0) != last_week].flatten().sum().union()

    # prior_weeks_sum = (
    #     out.loc[(out.index.get_level_values(0) < last_week)]
    #     .groupby(["Timestamp", "Source"])
    #     .sum()
    # )
    # print(prior_weeks_sum)
    # this_week_sum = (
    #     out.loc[(out.index.get_level_values(0) == last_week)]
    #     .groupby(level="Source")
    #     .sum()
    # )

    # summary = pd.DataFrame({
    #     "Prior Weeks": prior_weeks_sum,
    #     "This Week": this_week_sum
    # })

    
    # out.to_excel("test.xlsx")
    # test.to_excel("test2.xlsx")
    # test2.to_excel("test3.xlsx")
    # test3.to_excel("test4.xlsx")
    
    # engine.monthly_expense_compare([(2025, 11), (2025, 12)], 3)
    # engine.monthly_profit_and_loss(11,2025)
# %%
