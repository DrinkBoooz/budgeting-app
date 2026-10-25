/**
 * Reactive Client State Management
 */
window.AppState = {
  data: {
    salary: {
      monthly_basic: "30000.00",
      employment_type: "private",
      taxable_allowances: "0.00",
      non_taxable_allowances: "0.00",
      other_deductions: "0.00",
      withholding_method: "annualized",
      freelance_mode: "eight"
    },
    schedule: {
      year: 2026,
      month: 10,
      hourly_rate: "198.85",
      daily_food_rate: "200.00",
      daily_transport_rate: "150.00",
      daily_units: { Mon: "4", Tue: "4", Wed: "5", Thu: "4", Fri: "4", Sat: "0", Sun: "0" },
      holidays: []
    },
    bills: {
      tenants: ["Dan", "Jaco", "Troy"],
      my_tenant_name: "Dan",
      round_up: false,
      items: [
        { name: "Rent", category: "Rent", total_amount: "6000.00", is_active: true, active_tenants: ["Dan", "Jaco"] },
        { name: "Water", category: "Water", total_amount: "300.00", is_active: true, active_tenants: ["Dan", "Jaco", "Troy"] },
        { name: "Electricity", category: "Electricity", total_amount: "1600.00", is_active: true, active_tenants: ["Dan", "Jaco", "Troy"] },
        { name: "Internet", category: "Internet", total_amount: "1600.00", is_active: true, active_tenants: ["Dan", "Jaco"] }
      ],
      history: []
    },
    settlements: {
      peer_name: "Troy",
      items: []
    },
    groceries: {
      recipient_name: "Mama",
      items: [],
      deductions: []
    },
    apt_expenses: {
      house_expenditures: { items: [] },
      application_expenses: { items: [] },
      dentist_tracker: { billed_items: [], deductibles: [] },
      expedition: { items: [] }
    },
    chores: {
      month: "2026-07",
      entries: []
    },
    pajah: {
      owners: []
    },
    budget_extras: {
      additionals: [],
      payables: []
    },
    pipeline: {
      sync_with_schedule: true,
      tax_mode: "mode_a_private",
      tax_split_method: "equal_split",
      living_expense_option: "one_week",
      rent_perceived: "2500.00",
      utilities_perceived: "3175.00",
      include_13th_month: false,
      custom_tax_rate: "0.00"
    }
  },

  computed: {
    salaryResult: null,
    cutoffSchedule: null,
    unifiedBudget: null,
    billsSummary: null,
    billsYtdSummary: null,
    settlementSummary: null,
    groceriesSummary: null,
    cashFlowSummary: null
  },

  formatCurrency(val) {
    const num = parseFloat(val) || 0;
    return '₱' + num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },

  formatNumber(val, decimals = 2) {
    const num = parseFloat(val) || 0;
    return num.toLocaleString('en-PH', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  },

  async loadInitialData() {
    const res = await Bridge.call('get_user_data');
    if (res && res.success && res.data) {
      // Merge with defaults
      if (res.data.salary) Object.assign(this.data.salary, res.data.salary);
      if (res.data.schedule) Object.assign(this.data.schedule, res.data.schedule);
      if (res.data.bills) {
        if (res.data.bills.items && res.data.bills.items.length) this.data.bills.items = res.data.bills.items;
        if (res.data.bills.tenants) this.data.bills.tenants = res.data.bills.tenants;
        if (res.data.bills.history) this.data.bills.history = res.data.bills.history;
      }
      if (res.data.settlements && res.data.settlements.items) {
        this.data.settlements.items = res.data.settlements.items;
      }
      if (res.data.groceries) {
        if (res.data.groceries.items) this.data.groceries.items = res.data.groceries.items;
        if (res.data.groceries.deductions) this.data.groceries.deductions = res.data.groceries.deductions;
      }
      if (res.data.apt_expenses) Object.assign(this.data.apt_expenses, res.data.apt_expenses);
      if (res.data.chores) Object.assign(this.data.chores, res.data.chores);
      if (res.data.pajah) Object.assign(this.data.pajah, res.data.pajah);
      if (res.data.budget_extras) Object.assign(this.data.budget_extras, res.data.budget_extras);
      if (res.data.pipeline) Object.assign(this.data.pipeline, res.data.pipeline);
    }
    await this.recalculateAll();
  },

  async recalculateAll() {
    // 1. Recalculate Cutoff Schedule First (Teaching units define Gross!)
    const schedRes = await Bridge.call('compute_cutoff_schedule', {
      year: this.data.schedule.year,
      month: this.data.schedule.month,
      daily_units: this.data.schedule.daily_units,
      hourly_rate: this.data.schedule.hourly_rate,
      daily_food_rate: this.data.schedule.daily_food_rate,
      daily_transport_rate: this.data.schedule.daily_transport_rate,
      holidays: this.data.schedule.holidays
    });
    if (schedRes && schedRes.success) {
      this.computed.cutoffSchedule = schedRes.data;
    }

    // 2. Schedule Sync: Auto-derive basic salary from Tab 2 gross if enabled
    if (this.data.pipeline && this.data.pipeline.sync_with_schedule && this.computed.cutoffSchedule) {
      this.data.salary.monthly_basic = this.computed.cutoffSchedule.monthly_totals.gross_pay;
      if (this.data.pipeline.tax_mode === 'mode_a_private') {
        this.data.salary.employment_type = 'private';
      } else if (this.data.pipeline.tax_mode === 'mode_b_8percent') {
        this.data.salary.employment_type = 'freelancer';
        this.data.salary.freelance_mode = 'eight';
      } else if (this.data.pipeline.tax_mode === 'mode_c_govt') {
        this.data.salary.employment_type = 'government';
      }
    }

    // 3. Recalculate Salary (Pinasweldo Engine)
    const salRes = await Bridge.call('compute_salary', this.data.salary);
    if (salRes && salRes.success) {
      this.computed.salaryResult = salRes.data;
    }

    // 4. Recalculate Unified Budget Pipeline (Schedule -> Pinasweldo -> Current Budget)
    const p = this.data.pipeline || {};
    const uniRes = await Bridge.call('compute_unified_budget', {
      year: this.data.schedule.year,
      month: this.data.schedule.month,
      daily_units: this.data.schedule.daily_units,
      hourly_rate: this.data.schedule.hourly_rate,
      daily_food_rate: this.data.schedule.daily_food_rate,
      daily_transport_rate: this.data.schedule.daily_transport_rate,
      holidays: this.data.schedule.holidays,
      tax_mode: p.tax_mode || 'mode_a_private',
      tax_split_method: p.tax_split_method || 'equal_split',
      living_expense_option: p.living_expense_option || 'one_week',
      rent_perceived: p.rent_perceived || '2500.00',
      utilities_perceived: p.utilities_perceived || '3175.00',
      additionals: (this.data.budget_extras && this.data.budget_extras.additionals && this.data.budget_extras.additionals.length)
        ? this.data.budget_extras.additionals
        : [
            { label: "September", amount: "4000.00" },
            { label: "additional transfer", amount: "4700.00" }
          ],
      payables: (this.data.budget_extras && this.data.budget_extras.payables) || [],
      include_13th_month: Boolean(p.include_13th_month),
      custom_tax_rate: p.custom_tax_rate || '0.00'
    });
    if (uniRes && uniRes.success) {
      this.computed.unifiedBudget = uniRes.data;
    }

    // 5. Recalculate Bills
    const billsRes = await Bridge.call('compute_bills_summary', {
      my_tenant_name: this.data.bills.my_tenant_name,
      round_up: this.data.bills.round_up,
      bills: this.data.bills.items
    });
    if (billsRes && billsRes.success) {
      this.computed.billsSummary = billsRes.data;
    }

    // 6. Recalculate Bills YTD Summary
    const ytdRes = await Bridge.call('compute_ytd_summary', {
      history: this.data.bills.history || []
    });
    if (ytdRes && ytdRes.success) {
      this.computed.billsYtdSummary = ytdRes.data;
    }

    // 7. Recalculate Peer Settlements
    const settRes = await Bridge.call('compute_peer_settlement', {
      peer_name: this.data.settlements.peer_name,
      items: this.data.settlements.items
    });
    if (settRes && settRes.success) {
      this.computed.settlementSummary = settRes.data;
    }

    // 8. Recalculate Groceries
    const grocRes = await Bridge.call('compute_groceries_remittance', {
      recipient_name: this.data.groceries.recipient_name,
      items: this.data.groceries.items,
      deductions: this.data.groceries.deductions
    });
    if (grocRes && grocRes.success) {
      this.computed.groceriesSummary = grocRes.data;
    }

    // 9. Recalculate Executive Cash Flow
    let netSalary = this.computed.salaryResult ? this.computed.salaryResult.net_pay : "0.00";
    let livingBudget = this.computed.cutoffSchedule ? this.computed.cutoffSchedule.monthly_totals.living_budget : "0.00";
    if (this.computed.unifiedBudget) {
      netSalary = this.computed.unifiedBudget.net_take_home;
      livingBudget = this.computed.unifiedBudget.perceived_spending.living_expenses;
    }
    const billsShare = this.computed.billsSummary ? this.computed.billsSummary.my_total_share : "0.00";
    const groceriesRemit = this.computed.groceriesSummary ? this.computed.groceriesSummary.net_transfer_amount : "0.00";

    const cfRes = await Bridge.call('compute_cash_flow_waterfall', {
      net_salary: netSalary,
      other_income: "0.00",
      monthly_bills_share: billsShare,
      living_budget: livingBudget,
      peer_settlement_payable: "0.00",
      groceries_remittance: groceriesRemit
    });
    if (cfRes && cfRes.success) {
      this.computed.cashFlowSummary = cfRes.data;
    }

    // Trigger UI render updates
    window.dispatchEvent(new CustomEvent('state-updated'));
  },

  async persistState() {
    await Bridge.call('save_user_data', this.data);
  }
};

window.State = {
  get: () => window.AppState.data
};

