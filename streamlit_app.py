import streamlit as st
import pandas as pd


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Portfolio Wrapped",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Portfolio Wrapped")
st.write(
    "Understand your individual-stock portfolio, explore compound growth, "
    "and see what your investing habits could become over time."
)

st.caption(
    "Educational tool only. Projections are hypothetical and are not guarantees of future returns."
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def future_value(starting_balance, monthly_contribution, annual_return, years):
    months = years * 12
    monthly_rate = (annual_return / 100) / 12

    if monthly_rate == 0:
        return starting_balance + (monthly_contribution * months)

    starting_growth = starting_balance * ((1 + monthly_rate) ** months)

    contribution_growth = (
        monthly_contribution
        * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    )

    return starting_growth + contribution_growth


def required_monthly_contribution(
    starting_balance,
    target_value,
    annual_return,
    years
):
    months = years * 12
    monthly_rate = (annual_return / 100) / 12

    if months <= 0:
        return 0

    if monthly_rate == 0:
        needed = (target_value - starting_balance) / months
        return max(0, needed)

    growth_factor = (1 + monthly_rate) ** months

    future_starting_balance = starting_balance * growth_factor

    needed = (
        (target_value - future_starting_balance)
        * monthly_rate
        / (growth_factor - 1)
    )

    return max(0, needed)


# --------------------------------------------------
# PORTFOLIO INPUT
# --------------------------------------------------

st.header("1. Your Portfolio")

number_of_stocks = st.number_input(
    "How many individual stocks do you own?",
    min_value=1,
    max_value=20,
    value=3,
    step=1
)

portfolio = []

for i in range(int(number_of_stocks)):

    st.subheader(f"Stock {i + 1}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ticker = st.text_input(
            "Ticker",
            key=f"ticker_{i}",
            placeholder="MSFT"
        ).upper()

    with col2:
        shares = st.number_input(
            "Shares",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key=f"shares_{i}"
        )

    with col3:
        average_price = st.number_input(
            "Average purchase price",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"average_{i}"
        )

    with col4:
        current_price = st.number_input(
            "Current share price",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"current_{i}"
        )

    cost_basis = shares * average_price
    current_value = shares * current_price

    portfolio.append(
        {
            "Ticker": ticker if ticker else f"Stock {i + 1}",
            "Shares": shares,
            "Average Price": average_price,
            "Current Price": current_price,
            "Cost Basis": cost_basis,
            "Current Value": current_value
        }
    )


# --------------------------------------------------
# INVESTMENT GOALS
# --------------------------------------------------

st.header("2. Your Investing Goals")

col1, col2 = st.columns(2)

with col1:
    current_age = st.number_input(
        "Current age",
        min_value=18,
        max_value=100,
        value=22
    )

    target_portfolio_value = st.number_input(
        "Target portfolio value",
        min_value=0.0,
        value=1000000.0,
        step=10000.0,
        format="%.2f"
    )

with col2:
    target_age = st.number_input(
        "Target age",
        min_value=int(current_age) + 1,
        max_value=110,
        value=max(int(current_age) + 1, 50)
    )

    current_monthly_contribution = st.number_input(
        "Current monthly contribution",
        min_value=0.0,
        value=300.0,
        step=25.0,
        format="%.2f"
    )


# --------------------------------------------------
# ANNUAL RETURN
# --------------------------------------------------

st.header("3. Growth Assumption")

expected_annual_return = st.number_input(
    "Expected annual return (%)",
    min_value=0.0,
    max_value=30.0,
    value=7.0,
    step=0.5,
    help="Enter 7 for a 7% annual return."
)

st.caption(
    f"Using a hypothetical annual return of {expected_annual_return:.1f}%."
)


# --------------------------------------------------
# ANALYZE BUTTON
# --------------------------------------------------

st.divider()

analyze = st.button(
    "Analyze My Portfolio",
    type="primary",
    use_container_width=True
)


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if analyze:

    df = pd.DataFrame(portfolio)

    total_portfolio_value = df["Current Value"].sum()
    total_cost_basis = df["Cost Basis"].sum()

    if total_portfolio_value <= 0:

        st.warning(
            "Enter shares and current prices before analyzing your portfolio."
        )

    else:

        # ------------------------------------------
        # PORTFOLIO CALCULATIONS
        # ------------------------------------------

        df["Gain/Loss"] = (
            df["Current Value"] - df["Cost Basis"]
        )

        df["Return %"] = df.apply(
            lambda row:
            (row["Gain/Loss"] / row["Cost Basis"] * 100)
            if row["Cost Basis"] > 0
            else 0,
            axis=1
        )

        df["Portfolio Weight %"] = (
            df["Current Value"]
            / total_portfolio_value
            * 100
        )

        total_gain_loss = (
            total_portfolio_value - total_cost_basis
        )

        if total_cost_basis > 0:
            total_return = (
                total_gain_loss
                / total_cost_basis
                * 100
            )
        else:
            total_return = 0


        # ------------------------------------------
        # PORTFOLIO SUMMARY
        # ------------------------------------------

        st.header("Portfolio Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Portfolio Value",
            f"${total_portfolio_value:,.2f}"
        )

        col2.metric(
            "Cost Basis",
            f"${total_cost_basis:,.2f}"
        )

        col3.metric(
            "Gain / Loss",
            f"${total_gain_loss:,.2f}"
        )

        col4.metric(
            "Portfolio Return",
            f"{total_return:,.2f}%"
        )


        # ------------------------------------------
        # PORTFOLIO BREAKDOWN
        # ------------------------------------------

        st.subheader("Current Portfolio Breakdown")

        display_df = df[
            [
                "Ticker",
                "Shares",
                "Current Value",
                "Gain/Loss",
                "Return %",
                "Portfolio Weight %"
            ]
        ].copy()

        st.dataframe(
            display_df.style.format(
                {
                    "Shares": "{:,.2f}",
                    "Current Value": "${:,.2f}",
                    "Gain/Loss": "${:,.2f}",
                    "Return %": "{:,.2f}%",
                    "Portfolio Weight %": "{:,.2f}%"
                }
            ),
            use_container_width=True,
            hide_index=True
        )


        st.subheader("Portfolio Allocation")

        allocation_chart = (
            df[["Ticker", "Portfolio Weight %"]]
            .set_index("Ticker")
        )

        st.bar_chart(allocation_chart)


        # ------------------------------------------
        # GOAL ANALYSIS
        # ------------------------------------------

        years_to_goal = target_age - current_age

        required_contribution = required_monthly_contribution(
            total_portfolio_value,
            target_portfolio_value,
            expected_annual_return,
            years_to_goal
        )

        current_goal_projection = future_value(
            total_portfolio_value,
            current_monthly_contribution,
            expected_annual_return,
            years_to_goal
        )

        st.header("Goal Analysis")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Target",
            f"${target_portfolio_value:,.0f}"
        )

        col2.metric(
            "Monthly Amount Needed",
            f"${required_contribution:,.2f}"
        )

        col3.metric(
            f"Projected Value at Age {target_age}",
            f"${current_goal_projection:,.0f}"
        )


        if current_monthly_contribution >= required_contribution:

            st.success(
                "Your current monthly contribution meets or exceeds "
                "the modeled amount needed for this goal."
            )

        else:

            additional_needed = (
                required_contribution
                - current_monthly_contribution
            )

            st.info(
                f"To match this projection, you would need approximately "
                f"${additional_needed:,.2f} more per month."
            )


        # ------------------------------------------
        # COMPOUND GROWTH OPPORTUNITIES
        # ------------------------------------------

        st.header("Compound Growth Opportunities")

        scenarios = [
            current_monthly_contribution,
            current_monthly_contribution + 50,
            current_monthly_contribution + 100,
            current_monthly_contribution + 250
        ]

        scenario_names = [
            "Current Plan",
            "+$50 / month",
            "+$100 / month",
            "+$250 / month"
        ]

        scenario_values = []

        for contribution in scenarios:

            value = future_value(
                total_portfolio_value,
                contribution,
                expected_annual_return,
                years_to_goal
            )

            scenario_values.append(value)


        scenario_df = pd.DataFrame(
            {
                "Scenario": scenario_names,
                "Projected Value": scenario_values
            }
        )

        st.dataframe(
            scenario_df.style.format(
                {
                    "Projected Value": "${:,.2f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        st.bar_chart(
            scenario_df.set_index("Scenario")
        )


        # ------------------------------------------
        # CONTRIBUTIONS VS GROWTH
        # ------------------------------------------

        st.header("Contributions vs. Investment Growth")

        months_to_goal = years_to_goal * 12

        future_contributions = (
            current_monthly_contribution
            * months_to_goal
        )

        total_contributed_capital = (
            total_cost_basis
            + future_contributions
        )

        modeled_growth = (
            current_goal_projection
            - total_contributed_capital
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Contributed Capital",
            f"${total_contributed_capital:,.0f}"
        )

        col2.metric(
            "Modeled Investment Growth",
            f"${modeled_growth:,.0f}"
        )

        col3.metric(
            "Projected Portfolio",
            f"${current_goal_projection:,.0f}"
        )


        # ------------------------------------------
        # LONG TERM PROJECTIONS
        # ------------------------------------------

        st.header("Long-Term Compound Growth")

        projection_years = [5, 10, 20, 30]

        projection_values = []

        for years in projection_years:

            value = future_value(
                total_portfolio_value,
                current_monthly_contribution,
                expected_annual_return,
                years
            )

            projection_values.append(value)


        projection_df = pd.DataFrame(
            {
                "Years": projection_years,
                "Projected Portfolio": projection_values
            }
        )

        st.line_chart(
            projection_df,
            x="Years",
            y="Projected Portfolio"
        )

        st.dataframe(
            projection_df.style.format(
                {
                    "Projected Portfolio": "${:,.2f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )


        # ------------------------------------------
        # PORTFOLIO OBSERVATIONS
        # ------------------------------------------

        st.header("Portfolio Observations")

        sorted_df = df.sort_values(
            "Current Value",
            ascending=False
        )

        largest = sorted_df.iloc[0]

        top_three_weight = (
            sorted_df
            .head(3)["Portfolio Weight %"]
            .sum()
        )


        st.write(
            f"**Largest holding:** {largest['Ticker']} "
            f"({largest['Portfolio Weight %']:.1f}% of your portfolio)"
        )

        st.write(
            f"**Top three holdings:** "
            f"{top_three_weight:.1f}% of your portfolio"
        )

        st.write(
            f"**Individual stocks:** {len(df)}"
        )

        st.write(
            f"**Time until target:** "
            f"{years_to_goal} years"
        )


        if largest["Portfolio Weight %"] >= 40:

            st.warning(
                "A large portion of your portfolio is concentrated "
                "in one individual stock."
            )

        elif largest["Portfolio Weight %"] >= 25:

            st.info(
                "Your largest holding represents a significant "
                "portion of your portfolio."
            )

        else:

            st.success(
                "No individual stock currently represents more "
                "than 25% of your portfolio."
            )


        # ------------------------------------------
        # ASSUMPTION REMINDER
        # ------------------------------------------

        st.divider()

        st.caption(
            f"All future projections above assume a constant "
            f"{expected_annual_return:.1f}% annual return and regular "
            f"monthly contributions. Actual investment returns will vary."
        )
