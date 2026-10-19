"""Compound Village: a small, session-only economy prototype."""

import math
import random

import streamlit as st


# Fictional game parameters per season, not real investment estimates.
GUILDS = {
    "water": {
        "name": "Waterworks Guild",
        "icon": "💧",
        "price": 10.0,
        "growth": 0.006,
        "volatility": 0.05,
        "payout": 0.015,
        "description": "Water deliveries earn coins; repairs can reduce payouts.",
    },
    "cooks": {
        "name": "Cooks' Guild",
        "icon": "🍲",
        "price": 8.0,
        "growth": 0.012,
        "volatility": 0.10,
        "payout": 0.02,
        "description": "Food sales grow with demand; ingredients affect results.",
    },
    "hunters": {
        "name": "Hunters' Guild",
        "icon": "🏹",
        "price": 5.0,
        "growth": 0.022,
        "volatility": 0.18,
        "payout": 0.025,
        "description": "Expeditions can succeed or disappoint; payouts vary.",
    },
}

STATE_KEY = "cv_game_v1"
COTTAGE_COST = 35.0
COTTAGE_DIVIDENDS = 5.0


def new_game(seed=None):
    return {
        "cash": 100.0,
        "season": 0,
        "citizens": 2,
        "prices": {key: guild["price"] for key, guild in GUILDS.items()},
        "shares": {key: 0.0 for key in GUILDS},
        "dividends": 0.0,
        "reinvested": 0.0,
        "work_income": 0.0,
        "town_spending": 0.0,
        "worked_season": -1,
        "cottage": False,
        "seed": seed if seed is not None else random.SystemRandom().randrange(2**63),
        "last_season": None,
        "activity": ["Your village begins with 100 gold and two citizens."],
    }


def invested_value(game):
    return sum(game["shares"][key] * game["prices"][key] for key in GUILDS)


def add_activity(game, message):
    game["activity"] = [message] + game["activity"][:4]


def buy_share(game, guild_key):
    price = game["prices"][guild_key]
    if game["cash"] < price:
        return False
    game["cash"] -= price
    game["shares"][guild_key] += 1.0
    add_activity(game, f"Bought one {GUILDS[guild_key]['name']} share for {price:.2f} gold.")
    return True


def work_shift(game):
    if game["worked_season"] == game["season"]:
        return False
    game["worked_season"] = game["season"]
    game["cash"] += 2.0
    game["work_income"] += 2.0
    add_activity(game, "A work shift earned two gold. This is work income, not a dividend.")
    return True


def build_cottage(game):
    if (
        game["cottage"]
        or game["dividends"] < COTTAGE_DIVIDENDS
        or game["cash"] < COTTAGE_COST
    ):
        return False
    game["cash"] -= COTTAGE_COST
    game["town_spending"] += COTTAGE_COST
    game["citizens"] += 2
    game["cottage"] = True
    add_activity(game, "Your first cottage welcomes two citizens! New town content comes next.")
    return True


def advance_season(game, reinvest_percent, rng=None):
    if reinvest_percent not in (0, 50, 100):
        raise ValueError("Reinvestment must be 0, 50, or 100 percent.")

    before = game["cash"] + invested_value(game)
    game["season"] += 1
    rng = rng if rng is not None else random.Random(game["seed"] + game["season"])
    paid = reinvested = 0.0
    expected_total = game["cash"]

    for key, guild in GUILDS.items():
        opening_price = game["prices"][key]
        opening_shares = game["shares"][key]
        sigma = guild["volatility"]
        # Positive prices; sigma describes the seasonal log-return variability.
        factor = math.exp(guild["growth"] - sigma**2 / 2 + sigma * rng.gauss(0, 1))
        before_payout = opening_price * factor
        expected_total += opening_shares * before_payout

        payout_scale = rng.choice((0.0, 0.5, 1.0, 1.0, 1.25))
        if factor < 0.90:
            payout_scale = 0.0
        per_share = min(opening_price * guild["payout"] * payout_scale, before_payout * 0.20)

        # A distribution moves value from the holding into cash.
        closing_price = before_payout - per_share
        dividend = opening_shares * per_share
        purchase = dividend * reinvest_percent / 100
        game["prices"][key] = closing_price
        game["shares"][key] += purchase / closing_price
        game["cash"] += dividend - purchase
        paid += dividend
        reinvested += purchase

    game["dividends"] += paid
    game["reinvested"] += reinvested
    after = game["cash"] + invested_value(game)
    if not math.isclose(after, expected_total, rel_tol=1e-10, abs_tol=1e-8):
        raise ArithmeticError("Dividend accounting failed its value-conservation check.")
    game["last_season"] = {"paid": paid, "reinvested": reinvested, "change": after - before}
    add_activity(game, f"Season {game['season']}: {paid:.2f} gold in dividends; {reinvested:.2f} reinvested.")


@st.fragment
def _render_game():
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = new_game()
    game = st.session_state[STATE_KEY]

    st.subheader("Compound Village")
    st.caption(
        "Economy prototype · fictional gold and companies · one button press per season. "
        "Progress lasts for this browser session; refreshing or reconnecting may reset it."
    )

    cash_col, shares_col, people_col, season_col = st.columns(4)
    cash_col.metric("Spendable gold", f"{game['cash']:,.2f}")
    shares_col.metric("Shares' current value", f"{invested_value(game):,.2f}")
    people_col.metric("Citizens", game["citizens"])
    season_col.metric("Season", game["season"])

    home = "🏡" if game["cottage"] else "🏕️"
    st.html(
        f'<div style="background:#f3e8cc;border:1px solid #cbb98a;'
        f'border-radius:12px;padding:18px;text-align:center;color:#433721">'
        f'<div style="font-size:2.2rem">🌲 {home} 🌾 💧 🍲 🏹 🌲</div>'
        f'<div>A new settlement · {game["citizens"]} citizens</div></div>'
    )

    st.write("Buy guild shares, advance a season, then choose what to reinvest or spend on your town.")
    reinvest_percent = st.select_slider(
        "Dividend reinvestment",
        options=[0, 50, 100],
        value=50,
        format_func=lambda value: f"{value}%",
        key="cv_reinvest_percent",
    )

    for column, (key, guild) in zip(st.columns(3), GUILDS.items()):
        with column:
            with st.container(border=True):
                st.markdown(f"**{guild['icon']} {guild['name']}**")
                st.caption(guild["description"])
                price = game["prices"][key]
                st.metric("Gold per share", f"{price:.2f}")
                st.caption(f"Owned: {game['shares'][key]:.4f} shares")
                st.caption(f"Simulated volatility: {guild['volatility']:.0%} per season")
                st.caption(
                    f"Base payout estimate: {price * guild['payout']:.3f} gold/share next season. "
                    "Actual payouts can be zero or differ from this estimate."
                )
                st.button(
                    "Buy one share",
                    key=f"cv_buy_{key}",
                    on_click=buy_share,
                    args=(game, key),
                    disabled=game["cash"] < price,
                    width="stretch",
                )

    next_col, work_col = st.columns(2)
    next_col.button(
        "Advance one season",
        type="primary",
        key="cv_advance",
        on_click=advance_season,
        args=(game, reinvest_percent),
        width="stretch",
    )
    work_col.button(
        "Work a shift · +2 gold",
        key="cv_work",
        on_click=work_shift,
        args=(game,),
        disabled=game["worked_season"] == game["season"],
        width="stretch",
    )

    if game["last_season"] is not None:
        result = game["last_season"]
        st.info(
            f"Last season: {result['paid']:.2f} gold paid, "
            f"{result['reinvested']:.2f} used to buy more shares, and "
            f"{result['paid'] - result['reinvested']:.2f} kept as cash. "
            f"Cash plus investments changed by {result['change']:+.2f} gold."
        )

    st.markdown("**First milestone: build a cottage**")
    st.progress(
        min(1.0, game["dividends"] / COTTAGE_DIVIDENDS),
        text=f"Earn {COTTAGE_DIVIDENDS:.0f} gold in cumulative dividends, then spend {COTTAGE_COST:.0f} cash gold.",
    )
    st.button(
        "Build first cottage · 35 gold",
        key="cv_build_cottage",
        on_click=build_cottage,
        args=(game,),
        disabled=(
            game["cottage"]
            or game["dividends"] < COTTAGE_DIVIDENDS
            or game["cash"] < COTTAGE_COST
        ),
    )
    if game["cottage"]:
        st.success("Cottage complete! Your village now has four citizens.")

    st.caption(
        f"Ledger · Starting gold: 100 · Work income: {game['work_income']:.2f} · "
        f"Dividends paid: {game['dividends']:.2f} · Reinvested: {game['reinvested']:.2f} · "
        f"Town spending: {game['town_spending']:.2f}"
    )
    st.caption(
        "Volatility is the model's standard deviation of seasonal log returns before payouts. "
        "Seasons have no real-world time equivalent. Dividends move value into cash; "
        "reinvestment exchanges that cash for shares. Taxes and fees are excluded."
    )
    st.markdown("**Village journal**")
    for message in game["activity"]:
        st.caption(message)


def render_compound_village():
    with st.expander("🏰 Compound Village · Play the prototype", expanded=False):
        _render_game()
