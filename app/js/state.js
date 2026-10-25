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
    }
  },

  computed: {
    salaryResult: null,
    cutoffSchedule: null,
    billsSummary: null,
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
    }
    await this.recalculateAll();
  },

  async recalculateAll() {
    // 1. Recalculate Salary
    const salRes = await Bridge.call('compute_salary', this.data.salary);
    if (salRes && salRes.success) {
      this.computed.salaryResult = salRes.data;
    }

    // 2. Recalculate Cutoff Schedule
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

    // 3. Recalculate Bills
    const billsRes = await Bridge.call('compute_bills_summary', {
      my_tenant_name: this.data.bills.my_tenant_name,
      round_up: this.data.bills.round_up,
      bills: this.data.bills.items
    });
    if (billsRes && billsRes.success) {
      this.computed.billsSummary = billsRes.data;
    }

    // 4. Recalculate Peer Settlements
    const settRes = await Bridge.call('compute_peer_settlement', {
      peer_name: this.data.settlements.peer_name,
      items: this.data.settlements.items
    });
    if (settRes && settRes.success) {
      this.computed.settlementSummary = settRes.data;
    }

    // 5. Recalculate Groceries
    const grocRes = await Bridge.call('compute_groceries_remittance', {
      recipient_name: this.data.groceries.recipient_name,
      items: this.data.groceries.items,
      deductions: this.data.groceries.deductions
    });
    if (grocRes && grocRes.success) {
      this.computed.groceriesSummary = grocRes.data;
    }

    // 6. Recalculate Executive Cash Flow
    const netSalary = this.computed.salaryResult ? this.computed.salaryResult.net_pay : "0.00";
    const billsShare = this.computed.billsSummary ? this.computed.billsSummary.my_total_share : "0.00";
    const livingBudget = this.computed.cutoffSchedule ? this.computed.cutoffSchedule.monthly_totals.living_budget : "0.00";
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
