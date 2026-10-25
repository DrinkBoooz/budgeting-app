/**
 * View Controller: Tab 1 - Salary & Statutory Deductions
 */
window.SalaryView = {
  init() {
    this.bindInputs();
    window.addEventListener('state-updated', () => this.render());
  },

  bindInputs() {
    const chkSync = document.getElementById('chk-sync-schedule');
    const basicInput = document.getElementById('input-monthly-basic');
    const typeSelect = document.getElementById('select-employment-type');
    const taxModeSelect = document.getElementById('select-tax-mode');
    const taxSplitSelect = document.getElementById('select-tax-split');
    const allowTaxInput = document.getElementById('input-taxable-allowances');
    const allowNonTaxInput = document.getElementById('input-nontax-allowances');
    const dedOtherInput = document.getElementById('input-other-deductions');

    if (chkSync) {
      chkSync.checked = Boolean(AppState.data.pipeline && AppState.data.pipeline.sync_with_schedule);
      chkSync.addEventListener('change', (e) => {
        if (!AppState.data.pipeline) AppState.data.pipeline = {};
        AppState.data.pipeline.sync_with_schedule = e.target.checked;
        if (basicInput) basicInput.disabled = e.target.checked;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (basicInput) {
      basicInput.value = AppState.data.salary.monthly_basic;
      basicInput.disabled = Boolean(AppState.data.pipeline && AppState.data.pipeline.sync_with_schedule);
      basicInput.addEventListener('input', (e) => {
        AppState.data.salary.monthly_basic = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (typeSelect) {
      typeSelect.value = AppState.data.salary.employment_type;
      typeSelect.addEventListener('change', (e) => {
        AppState.data.salary.employment_type = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (taxModeSelect) {
      if (AppState.data.pipeline && AppState.data.pipeline.tax_mode) {
        taxModeSelect.value = AppState.data.pipeline.tax_mode;
      }
      taxModeSelect.addEventListener('change', (e) => {
        if (!AppState.data.pipeline) AppState.data.pipeline = {};
        AppState.data.pipeline.tax_mode = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (taxSplitSelect) {
      if (AppState.data.pipeline && AppState.data.pipeline.tax_split_method) {
        taxSplitSelect.value = AppState.data.pipeline.tax_split_method;
      }
      taxSplitSelect.addEventListener('change', (e) => {
        if (!AppState.data.pipeline) AppState.data.pipeline = {};
        AppState.data.pipeline.tax_split_method = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (allowTaxInput) {
      allowTaxInput.value = AppState.data.salary.taxable_allowances;
      allowTaxInput.addEventListener('input', (e) => {
        AppState.data.salary.taxable_allowances = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (allowNonTaxInput) {
      allowNonTaxInput.value = AppState.data.salary.non_taxable_allowances;
      allowNonTaxInput.addEventListener('input', (e) => {
        AppState.data.salary.non_taxable_allowances = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    if (dedOtherInput) {
      dedOtherInput.value = AppState.data.salary.other_deductions;
      dedOtherInput.addEventListener('input', (e) => {
        AppState.data.salary.other_deductions = e.target.value;
        AppState.recalculateAll();
        AppState.persistState();
      });
    }

    // 13th month trigger
    const btn13th = document.getElementById('btn-calc-13th');
    if (btn13th) {
      btn13th.addEventListener('click', async () => {
        const res = await Bridge.call('compute_13th_month', {
          monthly_basic: AppState.data.salary.monthly_basic,
          months_worked: 12
        });
        if (res && res.success) {
          const d = res.data;
          document.getElementById('m-13th-total').innerText = AppState.formatCurrency(d.total_bonus);
          document.getElementById('m-13th-exempt').innerText = AppState.formatCurrency(d.non_taxable_bonus);
          document.getElementById('m-13th-taxable').innerText = AppState.formatCurrency(d.taxable_bonus);
          Modal.open('modal-13th-month');
        }
      });
    }
  },

  render() {
    const res = AppState.computed.salaryResult;
    const sched = AppState.computed.cutoffSchedule;
    if (!res) return;

    // Sync banner rendering
    const isSynced = Boolean(AppState.data.pipeline && AppState.data.pipeline.sync_with_schedule);
    const badgeSync = document.getElementById('badge-sync-status');
    const basicInput = document.getElementById('input-monthly-basic');
    if (badgeSync) {
      badgeSync.innerText = isSynced ? 'Active' : 'Unlinked';
      badgeSync.className = `badge ${isSynced ? 'badge-success' : 'badge-secondary'}`;
    }
    if (basicInput) {
      basicInput.value = AppState.data.salary.monthly_basic;
      basicInput.disabled = isSynced;
    }
    if (sched) {
      const unitsEl = document.getElementById('txt-sync-units');
      const rateEl = document.getElementById('txt-sync-rate');
      const grossEl = document.getElementById('txt-sync-gross');
      if (unitsEl) unitsEl.innerText = `${sched.monthly_totals.total_units} units`;
      if (rateEl) rateEl.innerText = AppState.formatCurrency(AppState.data.schedule.hourly_rate);
      if (grossEl) grossEl.innerText = AppState.formatCurrency(sched.monthly_totals.gross_pay);
    }

    // Hero metrics
    document.getElementById('val-net-pay').innerText = AppState.formatCurrency(res.net_pay);
    document.getElementById('val-cutoff-net').innerText = AppState.formatCurrency(res.semi_monthly_net);
    document.getElementById('val-gross-income').innerText = AppState.formatCurrency(res.gross_income);
    document.getElementById('val-total-deductions').innerText = AppState.formatCurrency(res.total_ee_deductions);

    // Statutory Cards
    document.getElementById('val-sss-ee').innerText = AppState.formatCurrency(res.sss.total_ee);
    document.getElementById('val-sss-regular').innerText = AppState.formatCurrency(res.sss.ee_regular);
    document.getElementById('val-sss-mpf').innerText = AppState.formatCurrency(res.sss.ee_mpf);
    document.getElementById('val-sss-msc').innerText = AppState.formatCurrency(res.sss.msc);

    document.getElementById('val-philhealth-ee').innerText = AppState.formatCurrency(res.philhealth.ee_share);
    document.getElementById('val-philhealth-total').innerText = AppState.formatCurrency(res.philhealth.total);

    document.getElementById('val-pagibig-ee').innerText = AppState.formatCurrency(res.pagibig.ee_share);
    document.getElementById('val-pagibig-total').innerText = AppState.formatCurrency(res.pagibig.total);

    document.getElementById('val-tax-withholding').innerText = AppState.formatCurrency(res.withholding_tax_monthly);
    document.getElementById('val-annual-taxable').innerText = AppState.formatCurrency(res.taxable_income_annual);

    // Government / GSIS visibility
    const isGov = AppState.data.salary.employment_type === 'government';
    const gsisRow = document.getElementById('row-gsis-statutory');
    if (gsisRow) {
      gsisRow.style.display = isGov ? 'flex' : 'none';
      if (isGov) {
        document.getElementById('val-gsis-ee').innerText = AppState.formatCurrency(res.gsis.ee_share);
      }
    }
  }
};
