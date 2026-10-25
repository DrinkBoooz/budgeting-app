/**
 * View Controller: Tab 2 - Bi-Weekly Cutoff & Living Budget
 */
window.ScheduleView = {
  days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],

  init() {
    this.renderWeekdayInputs();
    this.bindInputs();
    window.addEventListener('state-updated', () => this.render());
  },

  renderWeekdayInputs() {
    const container = document.getElementById('weekday-units-grid');
    if (!container) return;

    container.innerHTML = this.days.map(d => `
      <div class="stat-card">
        <span class="lbl">${d} Units</span>
        <input type="number" step="0.5" min="0" max="24"
               class="form-control mono text-center input-day-unit"
               data-day="${d}"
               value="${AppState.data.schedule.daily_units[d] || 0}">
      </div>
    `).join('');

    container.querySelectorAll('.input-day-unit').forEach(inp => {
      inp.addEventListener('input', (e) => {
        const day = e.target.getAttribute('data-day');
        AppState.data.schedule.daily_units[day] = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    });
  },

  bindInputs() {
    const rateInput = document.getElementById('input-hourly-rate');
    const foodInput = document.getElementById('input-daily-food');
    const transpoInput = document.getElementById('input-daily-transpo');
    const monthSelect = document.getElementById('select-schedule-month');

    if (rateInput) {
      rateInput.value = AppState.data.schedule.hourly_rate;
      rateInput.addEventListener('input', (e) => {
        AppState.data.schedule.hourly_rate = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (foodInput) {
      foodInput.value = AppState.data.schedule.daily_food_rate;
      foodInput.addEventListener('input', (e) => {
        AppState.data.schedule.daily_food_rate = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (transpoInput) {
      transpoInput.value = AppState.data.schedule.daily_transport_rate;
      transpoInput.addEventListener('input', (e) => {
        AppState.data.schedule.daily_transport_rate = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (monthSelect) {
      monthSelect.value = AppState.data.schedule.month;
      monthSelect.addEventListener('change', (e) => {
        AppState.data.schedule.month = parseInt(e.target.value);
        AppState.recalculateAll();
        AppState.persistState();
      });
    }
  },

  render() {
    const sched = AppState.computed.cutoffSchedule;
    if (!sched) return;

    // Cutoff 1 (1-15)
    document.getElementById('val-c1-days').innerText = sched.cutoff1.working_days;
    document.getElementById('val-c1-units').innerText = AppState.formatNumber(sched.cutoff1.total_units, 1);
    document.getElementById('val-c1-gross').innerText = AppState.formatCurrency(sched.cutoff1.gross_pay);
    document.getElementById('val-c1-living').innerText = AppState.formatCurrency(sched.cutoff1.living_budget);

    // Cutoff 2 (16-EOM)
    document.getElementById('val-c2-days').innerText = sched.cutoff2.working_days;
    document.getElementById('val-c2-units').innerText = AppState.formatNumber(sched.cutoff2.total_units, 1);
    document.getElementById('val-c2-gross').innerText = AppState.formatCurrency(sched.cutoff2.gross_pay);
    document.getElementById('val-c2-living').innerText = AppState.formatCurrency(sched.cutoff2.living_budget);

    // Month Totals
    document.getElementById('val-month-workdays').innerText = sched.monthly_totals.working_days;
    document.getElementById('val-month-units').innerText = AppState.formatNumber(sched.monthly_totals.total_units, 1);
    document.getElementById('val-month-gross-est').innerText = AppState.formatCurrency(sched.monthly_totals.gross_pay);
    document.getElementById('val-month-living-budget').innerText = AppState.formatCurrency(sched.monthly_totals.living_budget);

    // Day-by-day table
    const tbody = document.getElementById('tbody-schedule-breakdown');
    if (tbody && sched.day_breakdowns) {
      tbody.innerHTML = sched.day_breakdowns.map(d => `
        <tr>
          <td><strong>${d.day_name}</strong></td>
          <td class="text-center">${d.units_per_day}</td>
          <td class="text-center">${d.c1_workdays}</td>
          <td class="text-center">${d.c2_workdays}</td>
          <td class="text-center font-semibold text-emerald-400">${d.total_month_units}</td>
        </tr>
      `).join('');
    }
  }
};
