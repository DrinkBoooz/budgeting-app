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

    const livingSelect = document.getElementById('select-living-mode');
    if (livingSelect) {
      if (AppState.data.pipeline && AppState.data.pipeline.living_expense_option) {
        livingSelect.value = AppState.data.pipeline.living_expense_option;
      }
      livingSelect.addEventListener('change', (e) => {
        if (!AppState.data.pipeline) AppState.data.pipeline = {};
        AppState.data.pipeline.living_expense_option = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    const chk13th = document.getElementById('chk-include-13th-month');
    if (chk13th) {
      chk13th.checked = Boolean(AppState.data.pipeline && AppState.data.pipeline.include_13th_month);
      chk13th.addEventListener('change', (e) => {
        if (!AppState.data.pipeline) AppState.data.pipeline = {};
        AppState.data.pipeline.include_13th_month = e.target.checked;
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

    // Holiday Loss (A5:C5)
    const lostUnitsEl = document.getElementById('val-lost-units');
    const lostCashEl = document.getElementById('val-lost-cash');
    if (lostUnitsEl) lostUnitsEl.innerText = AppState.formatNumber(sched.lost_units_due_to_holidays, 1);
    if (lostCashEl) lostCashEl.innerText = AppState.formatCurrency(sched.lost_cash_due_to_holidays);

    // Current Budget Waterfall & Take-Home Engine
    const uni = AppState.computed.unifiedBudget;
    if (uni) {
      const b8GrossEl = document.getElementById('val-cb-b8-gross');
      const b9DedEl = document.getElementById('val-cb-b9-deductions');
      const b10NetEl = document.getElementById('val-cb-b10-net');
      const b22SpentEl = document.getElementById('val-cb-b22-spent');
      const c1NetEl = document.getElementById('val-cb-c1-net');
      const c2NetEl = document.getElementById('val-cb-c2-net');
      const b23UtilsEl = document.getElementById('val-cb-b23-after-utils');
      const b32AddEl = document.getElementById('val-cb-b32-after-add');
      const modeBadge = document.getElementById('badge-active-mode');
      const livingDesc = document.getElementById('txt-cb-living-desc');

      if (b8GrossEl) b8GrossEl.innerText = AppState.formatCurrency(uni.gross_income);
      if (b9DedEl) b9DedEl.innerText = `${AppState.formatCurrency(uni.total_deductions)} (${uni.effective_deduction_rate_pct}%)`;
      if (b10NetEl) b10NetEl.innerText = AppState.formatCurrency(uni.net_take_home);
      if (b22SpentEl) b22SpentEl.innerText = AppState.formatCurrency(uni.total_perceived_spent);
      if (c1NetEl) c1NetEl.innerText = AppState.formatCurrency(uni.cutoff1_net_take_home);
      if (c2NetEl) c2NetEl.innerText = AppState.formatCurrency(uni.cutoff2_net_take_home);
      if (b23UtilsEl) b23UtilsEl.innerText = AppState.formatCurrency(uni.money_available_after_utilities);
      if (b32AddEl) b32AddEl.innerText = AppState.formatCurrency(uni.money_after_additionals);

      if (modeBadge) {
        const modeLabels = {
          'mode_a_private': 'Private (Mode A)',
          'mode_b_8percent': '8% COS (Mode B)',
          'mode_c_govt': 'GSIS Gov (Mode C)',
          'mode_d_legacy': 'Excel Legacy 0% (Mode D)',
        };
        modeBadge.innerText = modeLabels[uni.tax_mode] || uni.tax_mode;
      }

      if (livingDesc) {
        livingDesc.innerText = uni.living_expense_option === 'full_month'
          ? `Full-Month ${AppState.formatCurrency(uni.perceived_spending.living_expenses)}`
          : `1-Week ${AppState.formatCurrency(uni.perceived_spending.living_expenses)}`;
      }

      // Render Side-by-Side Comparison Table
      const cmpTbody = document.getElementById('tbody-mode-comparison');
      if (cmpTbody && uni.comparison_matrix) {
        const m = uni.comparison_matrix;
        const rows = [
          { label: "B8 Gross Monthly Income", key: "gross" },
          { label: "SSS Contribution (Reg + MPF)", key: "sss" },
          { label: "PhilHealth Contribution", key: "philhealth" },
          { label: "Pag-IBIG Contribution", key: "pagibig" },
          { label: "BIR Withholding Tax", key: "tax" },
          { label: "B9 Total Deductions", key: "total_deductions", isDanger: true },
          { label: "B10 Net Take-Home Pay", key: "net_pay", isEmerald: true, isBold: true },
          { label: "B22 Total Perceived Spent", key: "total_spent", isWarning: true },
          { label: "B23 Money Available After Utilities", key: "money_after_utilities", isAccent: true, isBold: true },
          { label: "B32 Money After Additionals (+₱8.7k)", key: "money_after_additionals", isEmerald: true, isBold: true },
        ];

        cmpTbody.innerHTML = rows.map(r => {
          const valA = m.mode_a_private[r.key];
          const valB = m.mode_b_8percent[r.key];
          const valC = m.mode_c_govt[r.key];
          const valD = m.mode_d_legacy[r.key];

          let cls = 'mono text-right';
          if (r.isEmerald) cls += ' text-emerald-400';
          if (r.isDanger) cls += ' text-danger';
          if (r.isWarning) cls += ' text-warning';
          if (r.isAccent) cls += ' text-cyan-400';
          if (r.isBold) cls += ' font-bold';

          return `
            <tr>
              <td><strong>${r.label}</strong></td>
              <td class="${cls}">${AppState.formatCurrency(valA)}</td>
              <td class="${cls}">${AppState.formatCurrency(valB)}</td>
              <td class="${cls}">${AppState.formatCurrency(valC)}</td>
              <td class="${cls}">${AppState.formatCurrency(valD)}</td>
            </tr>
          `;
        }).join('');
      }
    }

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
