const state = {
  analysis: null,
  market: null,
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatPercent(value) {
  return `${Number(value).toFixed(1)}%`;
}

function formatCompactCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value || 0);
}

function statusClass(signal) {
  if (signal === "positive" || signal === "stable") {
    return "status-positive";
  }
  if (signal === "watch" || signal === "neutral") {
    return "status-watch";
  }
  return "status-alert";
}

function createBarRows(items, valueKey, formatter, variant = "") {
  const max = Math.max(...items.map((item) => Number(item[valueKey]) || 0), 1);
  return `
    <div class="bar-chart">
      ${items
        .map((item) => {
          const width = ((Number(item[valueKey]) || 0) / max) * 100;
          return `
            <div class="bar-row">
              <div class="bar-label">
                <span>${item.name}</span>
                <span>${formatter(item[valueKey])}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill ${variant}" style="width: ${width}%;"></div>
              </div>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function fillSummaryGrid(analysis, market) {
  const metrics = [
    {
      label: "Investable Surplus",
      value: formatCurrency(analysis.cash_flow.investable_surplus),
      note: `After ${formatCurrency(analysis.cash_flow.total_expenses)} in monthly expenses.`,
    },
    {
      label: "Risk Profile",
      value: `${analysis.risk_profile.label} (${analysis.risk_profile.score})`,
      note: `${analysis.recommendation.expected_annual_return_pct}% expected annual return assumption.`,
    },
    {
      label: "Portfolio Health",
      value: `${analysis.portfolio.health_score}/100`,
      note: `${analysis.portfolio.concentration_risk} concentration risk.`,
    },
    {
      label: "Market Regime",
      value: market.derived.market_regime,
      note: `Sentiment score ${market.derived.sentiment_score}.`,
    },
  ];

  const template = document.getElementById("metric-template");
  const grid = document.getElementById("summary-grid");
  grid.innerHTML = "";
  metrics.forEach((metric) => {
    const fragment = template.content.cloneNode(true);
    fragment.querySelector(".metric-label").textContent = metric.label;
    fragment.querySelector(".metric-value").textContent = metric.value;
    fragment.querySelector(".metric-note").textContent = metric.note;
    grid.appendChild(fragment);
  });
}

function fillCashFlowPanel(analysis) {
  document.getElementById("cash-flow-panel").innerHTML = `
    <p class="mini-label">Monthly Cash Flow</p>
    <h3 class="big-number">${formatCurrency(analysis.cash_flow.monthly_income)}</h3>
    <div class="inline-metrics">
      <div class="mini-stat">
        Essential
        <strong>${formatCurrency(analysis.cash_flow.essential_expenses)}</strong>
      </div>
      <div class="mini-stat">
        EMIs + Insurance
        <strong>${formatCurrency(analysis.cash_flow.emi + analysis.cash_flow.insurance)}</strong>
      </div>
      <div class="mini-stat">
        Discretionary
        <strong>${formatCurrency(analysis.cash_flow.discretionary)}</strong>
      </div>
    </div>
    <div class="stack">
      ${createBarRows(
        [
          { name: "Essential", value: analysis.cash_flow.essential_expenses },
          { name: "EMIs", value: analysis.cash_flow.emi },
          { name: "Insurance", value: analysis.cash_flow.insurance },
          { name: "Discretionary", value: analysis.cash_flow.discretionary },
        ],
        "value",
        formatCurrency
      )}
    </div>
  `;
}

function fillEmergencyPanel(analysis) {
  const current = analysis.emergency_fund.current_amount;
  const target = analysis.emergency_fund.target_amount;
  const coverage = Math.min((current / Math.max(target, 1)) * 100, 100);
  document.getElementById("emergency-panel").innerHTML = `
    <p class="mini-label">Emergency Readiness</p>
    <h3 class="big-number">${analysis.emergency_fund.months_target} months</h3>
    <div class="inline-metrics">
      <div class="mini-stat">
        Current Reserve
        <strong>${formatCurrency(current)}</strong>
      </div>
      <div class="mini-stat">
        Target Reserve
        <strong>${formatCurrency(target)}</strong>
      </div>
      <div class="mini-stat">
        Gap
        <strong>${formatCurrency(analysis.emergency_fund.gap)}</strong>
      </div>
    </div>
    <div class="bar-chart">
      <div class="bar-row">
        <div class="bar-label">
          <span>Reserve Coverage</span>
          <span>${formatPercent(coverage)}</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill warn" style="width: ${coverage}%;"></div>
        </div>
      </div>
    </div>
    <p class="footer-note">
      Reserve-first planning avoids pushing the full monthly surplus straight into market risk.
    </p>
  `;
}

function fillRiskPanel(analysis) {
  document.getElementById("risk-panel").innerHTML = `
    <p class="mini-label">Risk Classification</p>
    <h3 class="big-number">${analysis.risk_profile.label}</h3>
    <div class="pill-row">
      <span class="signal-pill">Score ${analysis.risk_profile.score}</span>
      <span class="signal-pill">Volatility ${analysis.recommendation.expected_annual_volatility_pct}%</span>
      <span class="signal-pill">Return ${analysis.recommendation.expected_annual_return_pct}%</span>
    </div>
    <div class="stack">
      ${analysis.risk_profile.reasoning
        .map((reason) => `<div class="mini-stat"><strong>${reason}</strong></div>`)
        .join("")}
    </div>
  `;
}

function fillAllocationPanel(analysis) {
  const allocationItems = Object.entries(analysis.recommendation.target_allocation_pct).map(([name, value]) => ({
    name,
    value,
  }));
  document.getElementById("allocation-panel").innerHTML = `
    <p class="mini-label">Target Allocation</p>
    <h3 class="big-number">${formatCurrency(analysis.recommendation.suggested_monthly_investment)}</h3>
    <p class="muted">Suggested monthly investment after reserves: ${formatCurrency(
      analysis.recommendation.reserve_priority
    )} to emergency and near-term buffers.</p>
    ${createBarRows(allocationItems, "value", formatPercent)}
    <div class="tableish">
      ${allocationItems
        .map(
          (item) => `
            <div class="table-row">
              <span>${item.name}</span>
              <span>${formatPercent(item.value)}</span>
              <strong>${formatCurrency(analysis.recommendation.target_monthly_amounts[item.name])}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function fillMarketPanel(market) {
  document.getElementById("market-panel").innerHTML = `
    <p class="mini-label">Snapshot</p>
    <h3 class="big-number">${market.derived.market_regime}</h3>
    <div class="tableish">
      ${market.indices
        .map(
          (index) => `
            <div class="table-row">
              <span>${index.name}</span>
              <span>${index.value.toLocaleString("en-IN")}</span>
              <strong class="${index.change_pct >= 0 ? "status-positive" : "status-alert"}">
                ${index.change_pct >= 0 ? "+" : ""}${formatPercent(index.change_pct)}
              </strong>
            </div>
          `
        )
        .join("")}
    </div>
    <p class="footer-note">Market data timestamp: ${new Date(market.timestamp).toLocaleString("en-IN")}.</p>
  `;
}

function fillSectorPanel(market) {
  const sectorBars = createBarRows(market.sectors, "return_pct", formatPercent, "risk");
  document.getElementById("sector-panel").innerHTML = `
    <p class="mini-label">Sector Comparison</p>
    <h3 class="big-number">Top Sectors</h3>
    ${sectorBars}
    <div class="inline-metrics">
      ${market.macro
        .map(
          (item) => `
            <div class="mini-stat">
              ${item.label}
              <strong class="${statusClass(item.signal)}">${item.value}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function fillPortfolioPanels(analysis) {
  document.getElementById("portfolio-panel").innerHTML = `
    <p class="mini-label">Portfolio Health</p>
    <h3 class="big-number">${analysis.portfolio.health_score}/100</h3>
    <div class="inline-metrics">
      <div class="mini-stat">
        Total Value
        <strong>${formatCurrency(analysis.portfolio.total_value)}</strong>
      </div>
      <div class="mini-stat">
        Return
        <strong>${formatPercent(analysis.portfolio.portfolio_return_pct)}</strong>
      </div>
      <div class="mini-stat">
        Volatility
        <strong>${formatPercent(analysis.portfolio.portfolio_volatility_pct)}</strong>
      </div>
      <div class="mini-stat">
        Alignment
        <strong>${analysis.portfolio.alignment_score}/100</strong>
      </div>
    </div>
    ${createBarRows(
      analysis.portfolio.asset_allocation.map((item) => ({
        name: item.category,
        value: item.weight_pct,
      })),
      "value",
      formatPercent
    )}
  `;

  document.getElementById("portfolio-observations-panel").innerHTML = `
    <p class="mini-label">Review Notes</p>
    <h3 class="big-number">${analysis.portfolio.concentration_risk} Risk</h3>
    <div class="stack">
      ${analysis.portfolio.observations
        .map((note) => `<div class="mini-stat"><strong>${note}</strong></div>`)
        .join("")}
    </div>
    <p class="footer-note">
      Sector spread: ${analysis.portfolio.sector_allocation
        .slice(0, 3)
        .map((item) => `${item.sector} ${item.weight_pct}%`)
        .join(" • ")}
    </p>
  `;
}

function fillGoalsPanel(analysis) {
  document.getElementById("goals-panel").innerHTML = `
    <p class="mini-label">Goal Funding</p>
    <div class="stack">
      ${analysis.goals
        .map(
          (goal) => `
            <article class="goal-card">
              <p class="mini-label">${goal.priority} Priority</p>
              <h3>${goal.name}</h3>
              <div class="inline-metrics">
                <div class="mini-stat">
                  Target
                  <strong>${formatCurrency(goal.target_amount)}</strong>
                </div>
                <div class="mini-stat">
                  Progress
                  <strong>${formatPercent(goal.progress_pct)}</strong>
                </div>
                <div class="mini-stat">
                  Required SIP
                  <strong>${formatCurrency(goal.required_monthly_investment)}</strong>
                </div>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function fillSimulationPanel(analysis) {
  const pathBars = createBarRows(
    analysis.simulation.path.map((item) => ({
      name: `Year ${item.year}`,
      value: item.base,
    })),
    "value",
    formatCompactCurrency
  );

  document.getElementById("simulation-panel").innerHTML = `
    <p class="mini-label">Scenario Analysis</p>
    <h3 class="big-number">${formatCurrency(analysis.simulation.base_outcome)}</h3>
    <div class="inline-metrics">
      <div class="mini-stat">
        Conservative
        <strong>${formatCurrency(analysis.simulation.conservative_outcome)}</strong>
      </div>
      <div class="mini-stat">
        Base
        <strong>${formatCurrency(analysis.simulation.base_outcome)}</strong>
      </div>
      <div class="mini-stat">
        Optimistic
        <strong>${formatCurrency(analysis.simulation.optimistic_outcome)}</strong>
      </div>
    </div>
    ${pathBars}
  `;
}

function fillAssistantPanel(analysis) {
  document.getElementById("assistant-panel").innerHTML = `
    <strong>Explanation</strong>
    <p>${analysis.assistant_explanation}</p>
    <p class="footer-note">
      Educational use only. Historical return assumptions and simulated scenarios are uncertain and should not be
      treated as guaranteed outcomes.
    </p>
  `;
}

function populateForm(analysis) {
  const profile = analysis.profile;
  const mapping = {
    monthly_income: profile.monthly_income,
    age: profile.age,
    dependents: profile.dependents,
    rent: profile.monthly_expenses.rent,
    food: profile.monthly_expenses.food,
    transportation: profile.monthly_expenses.transportation,
    emis: profile.monthly_expenses.emis,
    emergency_fund: profile.emergency_fund,
    existing_savings: profile.existing_savings,
    investment_horizon_years: profile.risk_inputs.investment_horizon_years,
    loss_tolerance: profile.risk_inputs.loss_tolerance,
    volatility_comfort: profile.risk_inputs.volatility_comfort,
    income_stability: profile.risk_inputs.income_stability,
    market_knowledge: profile.risk_inputs.market_knowledge,
  };

  Object.entries(mapping).forEach(([key, value]) => {
    const input = document.querySelector(`[name="${key}"]`);
    if (input) {
      input.value = value;
    }
  });
  updateRangeLabels();
}

function updateRangeLabels() {
  document.querySelectorAll("[data-range-for]").forEach((node) => {
    const input = document.querySelector(`[name="${node.dataset.rangeFor}"]`);
    node.textContent = input ? input.value : "";
  });
}

function render() {
  fillSummaryGrid(state.analysis, state.market);
  fillCashFlowPanel(state.analysis);
  fillEmergencyPanel(state.analysis);
  fillRiskPanel(state.analysis);
  fillAllocationPanel(state.analysis);
  fillMarketPanel(state.market);
  fillSectorPanel(state.market);
  fillPortfolioPanels(state.analysis);
  fillGoalsPanel(state.analysis);
  fillSimulationPanel(state.analysis);
  fillAssistantPanel(state.analysis);
}

async function loadBootstrap() {
  const response = await fetch("/api/bootstrap");
  const payload = await response.json();
  state.analysis = payload.analysis;
  state.market = payload.market;
  populateForm(payload.analysis);
  render();
}

function buildPayload() {
  const form = document.getElementById("planner-form");
  const data = new FormData(form);
  return {
    age: Number(data.get("age")),
    dependents: Number(data.get("dependents")),
    monthly_income: Number(data.get("monthly_income")),
    emergency_fund: Number(data.get("emergency_fund")),
    existing_savings: Number(data.get("existing_savings")),
    monthly_expenses: {
      rent: Number(data.get("rent")),
      food: Number(data.get("food")),
      transportation: Number(data.get("transportation")),
      emis: Number(data.get("emis")),
    },
    risk_inputs: {
      investment_horizon_years: Number(data.get("investment_horizon_years")),
      loss_tolerance: Number(data.get("loss_tolerance")),
      volatility_comfort: Number(data.get("volatility_comfort")),
      income_stability: Number(data.get("income_stability")),
      market_knowledge: Number(data.get("market_knowledge")),
    },
  };
}

async function handleSubmit(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  button.textContent = "Recalculating...";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildPayload()),
    });
    const analysis = await response.json();
    state.analysis = analysis;
    render();
  } finally {
    button.disabled = false;
    button.textContent = "Recalculate Plan";
  }
}

document.getElementById("planner-form").addEventListener("submit", handleSubmit);
document.querySelectorAll('input[type="range"]').forEach((input) => {
  input.addEventListener("input", updateRangeLabels);
});

loadBootstrap().catch((error) => {
  document.body.innerHTML = `<main class="layout"><section class="section-block glass"><h2>Unable to load dashboard</h2><p>${error.message}</p></section></main>`;
});
