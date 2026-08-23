"""Core calculations for the Smart Investment & Portfolio Analytics MVP."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import mean
from typing import Any

import numpy as np
import pandas as pd

from .seed import ASSET_ASSUMPTIONS, DEFAULT_PROFILE, MARKET_SNAPSHOT


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a numeric value within a safe range."""
    return max(minimum, min(maximum, value))


def rupees(value: float) -> str:
    """Format a number using Indian numbering style."""
    is_negative = value < 0
    rounded = int(round(abs(value)))
    digits = str(rounded)
    if len(digits) <= 3:
        result = digits
    else:
        tail = digits[-3:]
        head = digits[:-3]
        chunks = []
        while len(head) > 2:
            chunks.insert(0, head[-2:])
            head = head[:-2]
        if head:
            chunks.insert(0, head)
        result = ",".join(chunks + [tail])
    sign = "-" if is_negative else ""
    return f"{sign}₹{result}"


def get_default_profile() -> dict[str, Any]:
    """Return a deep-ish copy of the seed profile."""
    return {
        **DEFAULT_PROFILE,
        "monthly_expenses": dict(DEFAULT_PROFILE["monthly_expenses"]),
        "risk_inputs": dict(DEFAULT_PROFILE["risk_inputs"]),
        "goals": [dict(goal) for goal in DEFAULT_PROFILE["goals"]],
        "portfolio": [dict(item) for item in DEFAULT_PROFILE["portfolio"]],
    }


def normalize_profile(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Merge a partial payload into the default profile."""
    profile = get_default_profile()
    if not payload:
        return profile

    for key, value in payload.items():
        if key in {"monthly_expenses", "risk_inputs"} and isinstance(value, dict):
            profile[key].update(value)
        elif key in {"goals", "portfolio"} and isinstance(value, list):
            profile[key] = value
        else:
            profile[key] = value
    return profile


def monthly_expense_breakdown(profile: dict[str, Any]) -> dict[str, float]:
    """Summarize expense buckets used by later planning calculations."""
    expenses = profile["monthly_expenses"]
    essential = (
        expenses["rent"]
        + expenses["food"]
        + expenses["electricity"]
        + expenses["transportation"]
        + expenses["education"]
        + expenses["healthcare"]
        + expenses["other_essential"]
    )
    emi = expenses["emis"]
    insurance = expenses["insurance"]
    discretionary = expenses["subscriptions"] + expenses["entertainment"]
    total = essential + emi + insurance + discretionary
    return {
        "essential": essential,
        "emi": emi,
        "insurance": insurance,
        "discretionary": discretionary,
        "total": total,
    }


def emergency_months_target(profile: dict[str, Any]) -> int:
    """Pick a simple emergency-fund target rule based on job stability."""
    employment = str(profile.get("employment_status", "")).lower()
    dependents = int(profile.get("dependents", 0))
    if "self" in employment or "business" in employment:
        return 9
    if dependents >= 3:
        return 8
    return 6


def risk_score(profile: dict[str, Any]) -> float:
    """Convert user and financial inputs into a 0-100 risk score."""
    risk_inputs = profile["risk_inputs"]
    age_factor = clamp((60 - profile["age"]) / 35, 0, 1) * 20
    horizon_factor = clamp(risk_inputs["investment_horizon_years"] / 20, 0, 1) * 20
    tolerance_factor = clamp(risk_inputs["loss_tolerance"] / 30, 0, 1) * 20
    volatility_factor = clamp(risk_inputs["volatility_comfort"] / 10, 0, 1) * 15
    knowledge_factor = clamp(risk_inputs["market_knowledge"] / 10, 0, 1) * 10
    stability_factor = clamp(risk_inputs["income_stability"] / 10, 0, 1) * 15

    expense = monthly_expense_breakdown(profile)
    surplus = max(profile["monthly_income"] - expense["total"], 0)
    debt_load = profile["loans"] + profile["credit_card_obligations"]
    debt_ratio = debt_load / max(profile["monthly_income"] * 12, 1)
    financial_resilience = clamp((surplus / max(profile["monthly_income"], 1)) * 1.8, 0, 1) * 10
    debt_penalty = clamp(debt_ratio / 2.5, 0, 1) * 10

    return clamp(
        age_factor
        + horizon_factor
        + tolerance_factor
        + volatility_factor
        + knowledge_factor
        + stability_factor
        + financial_resilience
        - debt_penalty,
        0,
        100,
    )


def classify_risk(score: float) -> str:
    """Translate a numeric score into a label."""
    if score < 42:
        return "Conservative"
    if score < 68:
        return "Moderate"
    return "Aggressive"


def allocation_for_profile(profile: dict[str, Any], risk_profile: str) -> dict[str, Any]:
    """Adjust the base allocation for emergency readiness and short horizons."""
    base = dict(ASSET_ASSUMPTIONS[risk_profile]["allocation"])
    expense = monthly_expense_breakdown(profile)
    emergency_target = expense["essential"] * emergency_months_target(profile)
    emergency_gap = max(emergency_target - profile["emergency_fund"], 0)
    gap_pressure = clamp(emergency_gap / max(profile["monthly_income"] * 12, 1), 0, 0.25)
    short_horizon = profile["risk_inputs"]["investment_horizon_years"] < 5

    if gap_pressure > 0:
        shift = round(gap_pressure * 20)
        base["Cash"] += shift
        base["Equity"] -= ceil(shift * 0.7)
        base["International"] = max(base["International"] - ceil(shift * 0.2), 0)
        base["Debt"] += ceil(shift * 0.3)

    if short_horizon:
        base["Debt"] += 10
        base["Equity"] -= 8
        base["International"] = max(base["International"] - 2, 0)

    total = sum(base.values())
    normalized = {key: round(value * 100 / total) for key, value in base.items()}
    delta = 100 - sum(normalized.values())
    normalized["Cash"] += delta
    return {
        "allocation_pct": normalized,
        "expected_return": ASSET_ASSUMPTIONS[risk_profile]["expected_return"],
        "expected_volatility": ASSET_ASSUMPTIONS[risk_profile]["volatility"],
        "emergency_gap": emergency_gap,
        "emergency_target": emergency_target,
    }


def portfolio_summary(profile: dict[str, Any], target_allocation: dict[str, int]) -> dict[str, Any]:
    """Analyze allocation, diversification, and concentration of the portfolio."""
    frame = pd.DataFrame(profile["portfolio"])
    total = float(frame["amount"].sum()) if not frame.empty else 0.0
    if total <= 0:
        return {
            "total_value": 0,
            "asset_allocation": [],
            "sector_allocation": [],
            "portfolio_return_pct": 0,
            "portfolio_volatility_pct": 0,
            "diversification_score": 0,
            "concentration_risk": "High",
            "health_score": 0,
            "alignment_score": 0,
            "observations": ["No portfolio data available yet."],
        }

    frame["weight"] = frame["amount"] / total
    asset_allocation = (
        frame.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .assign(weight_pct=lambda df: (df["amount"] / total * 100).round(1))
        .to_dict(orient="records")
    )
    sector_allocation = (
        frame.groupby("sector")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .assign(weight_pct=lambda df: (df["amount"] / total * 100).round(1))
        .to_dict(orient="records")
    )
    weighted_return = float((frame["return_pct"] * frame["weight"]).sum())
    weighted_volatility = float((frame["volatility_pct"] * frame["weight"]).sum())
    herfindahl = float((frame["weight"] ** 2).sum())
    diversification_score = round(clamp((1 - herfindahl) * 125, 0, 100), 1)
    largest_weight = float(frame["weight"].max() * 100)

    category_map = {
        "Equity": "Equity",
        "Mutual Funds": "Equity",
        "Debt": "Debt",
        "Gold": "Gold",
        "International": "International",
        "Cash": "Cash",
    }
    actual_map = {row["category"]: row["weight_pct"] for row in asset_allocation}
    alignment_gap = 0
    for category, target_weight in target_allocation.items():
        relevant_actual = sum(
            weight
            for asset_category, weight in actual_map.items()
            if category_map.get(asset_category) == category
        )
        alignment_gap += abs(target_weight - relevant_actual)
    alignment_score = round(clamp(100 - alignment_gap * 1.2, 0, 100), 1)

    liquidity_score = round(float((frame["liquidity_score"] * frame["weight"]).sum()) * 10, 1)
    health_score = round(
        0.35 * diversification_score
        + 0.25 * alignment_score
        + 0.2 * clamp(100 - weighted_volatility * 3, 0, 100)
        + 0.2 * liquidity_score,
        1,
    )
    concentration_risk = "Low"
    if largest_weight > 35:
        concentration_risk = "High"
    elif largest_weight > 22:
        concentration_risk = "Moderate"

    observations = []
    if concentration_risk != "Low":
        observations.append(
            f"Largest single holding is {largest_weight:.1f}% of the portfolio, which raises concentration risk."
        )
    if alignment_score < 70:
        observations.append("Current holdings do not fully match the recommended asset mix.")
    if weighted_volatility > 15:
        observations.append("Portfolio volatility is elevated relative to a balanced long-term allocation.")
    if not observations:
        observations.append("Portfolio is broadly diversified and close to the target risk posture.")

    return {
        "total_value": round(total, 2),
        "asset_allocation": asset_allocation,
        "sector_allocation": sector_allocation,
        "portfolio_return_pct": round(weighted_return, 2),
        "portfolio_volatility_pct": round(weighted_volatility, 2),
        "diversification_score": diversification_score,
        "concentration_risk": concentration_risk,
        "health_score": health_score,
        "alignment_score": alignment_score,
        "observations": observations,
    }


def goal_plan(profile: dict[str, Any], expected_return: float) -> list[dict[str, Any]]:
    """Estimate goal progress and required monthly savings."""
    plans = []
    monthly_return = (1 + expected_return) ** (1 / 12) - 1
    for goal in profile["goals"]:
        years = max(int(goal["years"]), 1)
        months = years * 12
        target = float(goal["target_amount"])
        current = float(goal["current_amount"])
        future_value_current = current * ((1 + monthly_return) ** months)
        remaining = max(target - future_value_current, 0)
        if monthly_return == 0:
            required_sip = remaining / months
        else:
            annuity_factor = (((1 + monthly_return) ** months) - 1) / monthly_return
            required_sip = remaining / max(annuity_factor, 1)
        progress = clamp(current / max(target, 1) * 100, 0, 100)
        plans.append(
            {
                "name": goal["name"],
                "priority": goal["priority"],
                "target_amount": target,
                "current_amount": current,
                "time_horizon_years": years,
                "progress_pct": round(progress, 1),
                "required_monthly_investment": round(required_sip, 2),
            }
        )
    return plans


def run_simulation(monthly_investment: float, years: int, risk_profile: str) -> dict[str, Any]:
    """Monte Carlo style goal simulation with deterministic percentiles."""
    assumptions = ASSET_ASSUMPTIONS[risk_profile]
    expected_return = assumptions["expected_return"]
    volatility = assumptions["volatility"]
    months = max(years * 12, 1)
    monthly_mean = (1 + expected_return) ** (1 / 12) - 1
    monthly_volatility = volatility / np.sqrt(12)

    rng = np.random.default_rng(42)
    trials = 400
    paths = rng.normal(monthly_mean, monthly_volatility, size=(trials, months))
    corpus = np.zeros(trials)
    for month in range(months):
        corpus = (corpus + monthly_investment) * (1 + paths[:, month])

    percentiles = np.percentile(corpus, [20, 50, 80])
    growth_path = []
    corpus_path = np.zeros(trials)
    for month in range(months):
        corpus_path = (corpus_path + monthly_investment) * (1 + paths[:, month])
        if (month + 1) % 12 == 0:
            growth_path.append(
                {
                    "year": (month + 1) // 12,
                    "conservative": round(float(np.percentile(corpus_path, 20)), 2),
                    "base": round(float(np.percentile(corpus_path, 50)), 2),
                    "optimistic": round(float(np.percentile(corpus_path, 80)), 2),
                }
            )

    return {
        "monthly_investment": monthly_investment,
        "years": years,
        "conservative_outcome": round(float(percentiles[0]), 2),
        "base_outcome": round(float(percentiles[1]), 2),
        "optimistic_outcome": round(float(percentiles[2]), 2),
        "path": growth_path,
    }


def explanation(profile: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Generate a compact narrative summary."""
    surplus = analysis["cash_flow"]["investable_surplus"]
    risk = analysis["risk_profile"]["label"]
    emergency_gap = analysis["emergency_fund"]["gap"]
    top_gap = analysis["portfolio"]["observations"][0]
    monthly_capacity = analysis["recommendation"]["suggested_monthly_investment"]
    return (
        f"{profile['name']} currently has an estimated investable surplus of {rupees(surplus)} per month. "
        f"The profile scores as {risk.lower()} risk because the investment horizon is "
        f"{profile['risk_inputs']['investment_horizon_years']} years, income stability is "
        f"{profile['risk_inputs']['income_stability']}/10, and loss tolerance is "
        f"{profile['risk_inputs']['loss_tolerance']}%. "
        f"The immediate priority is to close the emergency-fund gap of {rupees(emergency_gap)} before taking "
        f"on additional aggressive exposure. A practical starting point is a monthly plan of "
        f"{rupees(monthly_capacity)} split across the recommended allocation. Portfolio review note: {top_gap}"
    )


def build_analysis(profile_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the full end-to-end analytics flow."""
    profile = normalize_profile(profile_payload)
    expenses = monthly_expense_breakdown(profile)
    surplus = max(profile["monthly_income"] - expenses["total"], 0)
    emergency_target = expenses["essential"] * emergency_months_target(profile)
    emergency_gap = max(emergency_target - profile["emergency_fund"], 0)
    reserve_priority = min(surplus * 0.35, emergency_gap / 12 if emergency_gap else surplus * 0.1)
    suggested_investment = max(surplus - reserve_priority, 0)
    score = risk_score(profile)
    risk_label = classify_risk(score)
    allocation = allocation_for_profile(profile, risk_label)
    portfolio = portfolio_summary(profile, allocation["allocation_pct"])
    goals = goal_plan(profile, allocation["expected_return"])
    simulation = run_simulation(
        monthly_investment=max(suggested_investment, 1000),
        years=max(profile["risk_inputs"]["investment_horizon_years"], 1),
        risk_profile=risk_label,
    )

    invest_now = {
        bucket: round(suggested_investment * pct / 100, 2)
        for bucket, pct in allocation["allocation_pct"].items()
    }

    analysis = {
        "profile": profile,
        "cash_flow": {
            "monthly_income": profile["monthly_income"],
            "essential_expenses": round(expenses["essential"], 2),
            "emi": round(expenses["emi"], 2),
            "insurance": round(expenses["insurance"], 2),
            "discretionary": round(expenses["discretionary"], 2),
            "total_expenses": round(expenses["total"], 2),
            "investable_surplus": round(surplus, 2),
        },
        "emergency_fund": {
            "months_target": emergency_months_target(profile),
            "target_amount": round(emergency_target, 2),
            "current_amount": round(profile["emergency_fund"], 2),
            "gap": round(emergency_gap, 2),
        },
        "risk_profile": {
            "score": round(score, 1),
            "label": risk_label,
            "reasoning": [
                f"Age {profile['age']} and a {profile['risk_inputs']['investment_horizon_years']}-year horizon support growth assets.",
                f"Loss tolerance of {profile['risk_inputs']['loss_tolerance']}% and volatility comfort of {profile['risk_inputs']['volatility_comfort']}/10 shape the core risk bucket.",
                f"Debt load and emergency-fund readiness act as guardrails on aggressive positioning.",
            ],
        },
        "recommendation": {
            "suggested_monthly_investment": round(suggested_investment, 2),
            "reserve_priority": round(reserve_priority, 2),
            "target_allocation_pct": allocation["allocation_pct"],
            "target_monthly_amounts": invest_now,
            "expected_annual_return_pct": round(allocation["expected_return"] * 100, 1),
            "expected_annual_volatility_pct": round(allocation["expected_volatility"] * 100, 1),
        },
        "portfolio": portfolio,
        "goals": goals,
        "simulation": simulation,
    }
    analysis["assistant_explanation"] = explanation(profile, analysis)
    return analysis


def market_overview() -> dict[str, Any]:
    """Build derived market analytics for the dashboard."""
    sectors = MARKET_SNAPSHOT["sectors"]
    sector_frame = pd.DataFrame(sectors)
    sector_frame["risk_adjusted"] = sector_frame["return_pct"] / sector_frame["volatility_pct"]
    strongest = sector_frame.sort_values("risk_adjusted", ascending=False).head(3)
    weakest = sector_frame.sort_values("return_pct", ascending=True).head(2)
    sentiment_score = round(
        mean(item["change_pct"] for item in MARKET_SNAPSHOT["indices"][:3]) * 25
        + strongest["risk_adjusted"].mean() * 40,
        1,
    )
    regime = "Balanced"
    if sentiment_score > 28:
        regime = "Risk-On"
    elif sentiment_score < 18:
        regime = "Defensive"

    return {
        **MARKET_SNAPSHOT,
        "derived": {
            "market_regime": regime,
            "sentiment_score": sentiment_score,
            "top_sectors": strongest[
                ["name", "return_pct", "volatility_pct", "momentum", "risk_adjusted"]
            ].round(2).to_dict(orient="records"),
            "lagging_sectors": weakest[
                ["name", "return_pct", "volatility_pct", "momentum"]
            ].round(2).to_dict(orient="records"),
        },
    }


def bootstrap_payload() -> dict[str, Any]:
    """Return everything the frontend needs for first render."""
    return {
        "analysis": build_analysis(),
        "market": market_overview(),
    }

