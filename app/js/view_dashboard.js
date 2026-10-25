/**
 * View Controller: Tab 5 - Executive Cash Flow Waterfall & Savings Rate
 */
window.DashboardView = {
  init() {
    window.addEventListener('state-updated', () => this.render());
  },

  render() {
    const cf = AppState.computed.cashFlowSummary;
    if (!cf) return;

    // Hero metrics
    document.getElementById('val-dash-inflows').innerText = AppState.formatCurrency(cf.total_inflow);
    document.getElementById('val-dash-outflows').innerText = AppState.formatCurrency(cf.total_outflow);
    
    const surplusEl = document.getElementById('val-dash-surplus');
    const netSurplus = parseFloat(cf.net_surplus);
    surplusEl.innerText = AppState.formatCurrency(cf.net_surplus);
    surplusEl.className = `metric-value ${netSurplus >= 0 ? 'emerald' : 'text-danger'}`;

    const savingsRate = Math.max(0, Math.min(100, parseFloat(cf.savings_rate_pct)));
    document.getElementById('val-dash-savings-rate').innerText = `${savingsRate.toFixed(1)}%`;
    
    const progressBar = document.getElementById('dash-savings-progress');
    if (progressBar) {
      progressBar.style.width = `${savingsRate}%`;
    }

    // Waterfall components
    document.getElementById('wf-net-salary').innerText = AppState.formatCurrency(cf.net_salary);
    document.getElementById('wf-living-budget').innerText = `-${AppState.formatCurrency(cf.living_budget)}`;
    document.getElementById('wf-bills-share').innerText = `-${AppState.formatCurrency(cf.monthly_bills_share)}`;
    document.getElementById('wf-groceries-remit').innerText = `-${AppState.formatCurrency(cf.groceries_remittance)}`;
    document.getElementById('wf-net-surplus').innerText = AppState.formatCurrency(cf.net_surplus);
  }
};
