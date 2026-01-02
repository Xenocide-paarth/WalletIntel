import pandas as pd
import plotly.express as px

from config import Configurations

class Graph:
    
    def expense_pie_topN(exp_df: pd.DataFrame, template: dict, topN: int = 7) -> px.pie:
        """
        Build a donut pie of expenses by Source, showing topN sources and
        collapsing the rest into 'Others'. Returns a Plotly figure.
        """
        # --- aggregate raw data like your original code ---
        pie_data = (
            exp_df.groupby("Source")["Amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )

        # --- Top N + Others logic (using index/value like your structure) ---
        data = pie_data  # naming to match your snippet

        top = data.head(topN)
        others_sum = data.iloc[topN:].sum()

        labels = list(top.index)
        values = list(top.values)

        if others_sum > 0:
            labels.append("Others")
            values.append(others_sum)

        df_plot = pd.DataFrame({"Account": labels, "Amount": values})

        # --- Plotly pie with outside labels + legend ---
        fig = px.pie(
            df_plot,
            names="Account",
            values="Amount",
            hole=0.45,
            color="Amount",
            color_discrete_sequence=Configurations.VIBRANT_SEQUENCE
        )

        fig.update_traces(
            textposition="outside",
            texttemplate="<b>%{label}</b><br>%{percent:.1%}",
            marker=dict(line=dict(color="white", width=1)),
            showlegend=True,
            hovertemplate=(
                "<b>Account:</b> %{label}<br>"
                "<b>Balance:</b> ₹%{value:,.2f}<extra></extra>"
            ),
        )

        fig.update_layout(**template, legend_title_text="Account")

        # center total in the donut
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper",
            text=f"<b>Total</b><br>₹{data.sum():,.2f}",
            showarrow=False,
            font=dict(size=16, color="#ffffff"),
            align="center",
        )

        return fig

    def balance_by_account_graph(df: pd.DataFrame, selected_accounts: list[str], template: dict) -> px.bar:
        """
        Build a bar chart of balances by Account for the selected_accounts,
        using a vibrant continuous color scale. Returns a Plotly figure.
        """
        # aggregate balances for selected accounts
        current_bals = (
            df[df["Account"].isin(selected_accounts)]
            .groupby("Account")["Amount"]
            .sum()
            .reset_index()
        )

        current_bals.columns = ["Account", "Amount"]

        fig = px.bar(
            current_bals,
            x="Account",
            y="Amount",
            color="Amount",
            color_continuous_scale=Configurations.VIBRANT_SCALE,
            labels={"Amount": "Amount (₹)", "Account": "Account"},
            text="Amount",
            text_auto=True,
        )

        # labels + hover
        fig.update_traces(
            texttemplate="₹%{text:,.2f}",
            textposition="outside",
            hovertemplate=(
                "<b>Account:</b> %{x}<br>"
                "<b>Balance:</b> ₹%{y:,.2f}<extra></extra>"
            ),
        )

        # layout with horizontal grid lines and colorbar
        fig.update_layout(**template,
            bargap=0.60,
            xaxis_title="Account",
            yaxis_title="Amount (₹)",
        )

        # horizontal grid lines from y‑axis across the plot
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="#292B33",  # soft grid color
            tickprefix="₹",
            tickformat=",",
        )  # [web:77][web:80]

        # keep the heatmap-style color axis on the right
        fig.update_coloraxes(
            showscale=True,
            colorbar=dict(
                title="Balance (₹)",
                thickness=25,
                len=0.8,
                x=1.05,
                xanchor="left",
                y=0.5,
                yanchor="middle",
            ),
        )  # [web:59][web:61][web:64]

        return fig

    def balance_overtime_graph(df: pd.DataFrame, mask, template: dict) -> px.line:
        """
        Balance over time by Account.
        Expects a long df with columns: Timestamp, Account, Amount.
        Cumulative sum is done for all accounts, then filtered.
        """

        df = df.copy()

        # 1) global running balance per account (no filter yet)
        df = df.sort_values(["Account", "Timestamp"])
        df["Balance"] = df.groupby("Account")["Amount"].cumsum()  # groupwise cumsum [web:148][web:150]
        
        # 2) filter to selected accounts
        df = df.loc[mask]
        
        # 3) sort for nice time-series plotting
        df = df.sort_values("Timestamp")

        fig = px.line(
            df,
            x="Timestamp",
            y="Balance",
            color="Account",
            line_group="Account",
            custom_data="Account",
            labels={"Balance": "Balance (₹)", "Timestamp": "Date/Time"},
            color_discrete_sequence=Configurations.VIBRANT_SEQUENCE,  # vibrant palette [web:140]
        )

        fig.update_traces(
            mode="lines",
            line=dict(width=2.5),
            fill="tozeroy",
            opacity=0.7,
            hovertemplate=(
                "<b>Date:</b> %{x|%Y-%m-%d}<br>"
                "<b>Account:</b> %{customdata[0]}<br>"
                "<b>Balance:</b> ₹%{y:,.2f}<extra></extra>"
            ),
        )

        fig.update_layout(**template,
            xaxis_title="Date",
            yaxis_title="Balance (₹)",
            legend_title_text="Account",
        )

        fig.update_yaxes(tickprefix="₹", tickformat=",")

        return fig
