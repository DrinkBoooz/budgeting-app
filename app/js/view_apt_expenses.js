/**
 * View Controller: Apartment Expenses, Dentist & Braces Tracker, Expedition Splits
 */

const ViewAptExpenses = {
  init() {
    this.bindEvents();
    this.render();
  },

  bindEvents() {
    const btnRefresh = document.getElementById("btn-refresh-apt");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => this.render());
    }
  },

  async render() {
    const data = State.get();
    const apt = data.apt_expenses || {};

    // 1. House Expenditures
    const houseItems = apt.house_expenditures?.items || [
      { item: "BDO 50% promo item", count: "1", price: "1000.00", discount: "500.00", note: "BDO promo" },
      { item: "IKEA Storage Box", count: "3", price: "500.00", discount: "0.00", note: "Cabinet storage" },
      { item: "Desk Lamp", count: "1", price: "2675.00", discount: "0.00", note: "Work setup" },
    ];
    const houseRes = await Bridge.call("compute_house_expenditures", { items: houseItems });
    if (houseRes && houseRes.success) {
      const houseTbody = document.getElementById("house-expenditures-tbody");
      if (houseTbody) {
        houseTbody.innerHTML = houseRes.data.items.map(it => `
          <tr>
            <td><strong>${it.item}</strong></td>
            <td class="text-right mono">${it.count}</td>
            <td class="text-right mono">₱${Number(it.price).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-right mono text-warning">-₱${Number(it.discount).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-right mono font-bold">₱${Number(it.total_price).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-secondary small">${it.note || '—'}</td>
          </tr>
        `).join('');
      }
      const elHouseTotal = document.getElementById("house-expenditures-total");
      if (elHouseTotal) elHouseTotal.textContent = `₱${Number(houseRes.data.grand_total).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;
    }

    // 2. Application Expenses
    const appItems = apt.application_expenses?.items || [
      { label: "Drug Test", count: "1", price: "300.00", note: "Requirement" },
      { label: "Neuro Psych", count: "1", price: "1000.00", note: "Requirement" },
      { label: "NBI Clearance", count: "1", price: "160.00", note: "Clearance" },
      { label: "TOR Transcript", count: "1", price: "460.00", note: "CvSU Registrar" },
      { label: "Medical Exam", count: "1", price: "500.00", note: "Clinic" },
    ];
    const appRes = await Bridge.call("compute_application_expenses", { items: appItems });
    if (appRes && appRes.success) {
      const appTbody = document.getElementById("app-expenses-tbody");
      if (appTbody) {
        appTbody.innerHTML = appRes.data.items.map(it => `
          <tr>
            <td><strong>${it.label}</strong></td>
            <td class="text-right mono">${it.count}</td>
            <td class="text-right mono">₱${Number(it.price).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-right mono font-bold">₱${Number(it.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-secondary small">${it.note || '—'}</td>
          </tr>
        `).join('');
      }
      const elAppTotal = document.getElementById("app-expenses-total");
      if (elAppTotal) elAppTotal.textContent = `₱${Number(appRes.data.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;
    }

    // 3. Dentist & Braces Tracker
    const billedItems = apt.dentist_tracker?.billed_items || [
      { label: "Initial Downpayment", count: "1", price: "10000.00", note: "Clinic kickoff" },
      { label: "Adjustments (Batch 1)", count: "1", price: "4500.00", note: "3 sessions" },
      { label: "Adjustments (Batch 2)", count: "1", price: "20000.00", note: "Treatment series" },
      { label: "Dental Cleaning", count: "1", price: "3000.00", note: "Prophylaxis" },
    ];
    const deductibles = apt.dentist_tracker?.deductibles || [
      { label: "Nov 11 Payment", count: "1", price: "2000.00", note: "BDO Transfer" },
      { label: "Dec 5 Payment", count: "1", price: "4000.00", note: "GCash" },
      { label: "Jan 29 Payment", count: "1", price: "2000.00", note: "Cash" },
    ];
    const dentistRes = await Bridge.call("compute_dentist_tracker", {
      billed_items: billedItems,
      deductibles: deductibles,
      app_expenses_subtotal: appRes?.data?.subtotal || "2420.00"
    });

    if (dentistRes && dentistRes.success) {
      const d = dentistRes.data;
      const elBilled = document.getElementById("dentist-total-billed");
      if (elBilled) elBilled.textContent = `₱${Number(d.total_billed).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

      const elPaid = document.getElementById("dentist-total-paid");
      if (elPaid) elPaid.textContent = `-₱${Number(d.total_paid).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

      const elPure = document.getElementById("dentist-pure-remaining");
      if (elPure) elPure.textContent = `₱${Number(d.pure_dentist_remaining).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

      const elCombined = document.getElementById("dentist-combined-balance");
      if (elCombined) elCombined.textContent = `₱${Number(d.combined_grand_total).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

      const elBar = document.getElementById("dentist-progress-bar-display");
      if (elBar) elBar.textContent = d.progress_bar;

      const elPct = document.getElementById("dentist-progress-pct-display");
      if (elPct) elPct.textContent = `${d.progress_pct}% Paid (${d.payments_made_count} payments)`;

      const dentistTbody = document.getElementById("dentist-ledger-tbody");
      if (dentistTbody) {
        let rowsHtml = d.billed_items.map(b => `
          <tr>
            <td><span class="badge badge-primary">Billed</span> <strong>${b.label}</strong></td>
            <td class="text-right mono text-primary font-bold">₱${Number(b.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-secondary small">${b.note || '—'}</td>
          </tr>
        `).join('');

        rowsHtml += d.deductible_items.map(ded => `
          <tr class="table-row-deductible">
            <td><span class="badge badge-success">Payment</span> <strong>${ded.label}</strong></td>
            <td class="text-right mono text-success font-bold">-₱${Number(ded.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-secondary small">${ded.note || '—'}</td>
          </tr>
        `).join('');

        dentistTbody.innerHTML = rowsHtml;
      }
    }

    // 4. Expedition with dynamic Divisors
    const expItems = apt.expedition?.items || [
      { label: "Gas Split (5 people)", count: "1", price: "1500.00", divisor: "5", note: "Roadtrip gas" },
      { label: "Toll Fee (3 people)", count: "1", price: "455.00", divisor: "3", note: "CALAX Toll" },
      { label: "Solo Snack (1 person)", count: "1", price: "516.00", divisor: "1", note: "Personal drive-thru" },
    ];
    const expRes = await Bridge.call("compute_expedition_expenses", { items: expItems });
    if (expRes && expRes.success) {
      const expTbody = document.getElementById("expedition-tbody");
      if (expTbody) {
        expTbody.innerHTML = expRes.data.items.map(it => `
          <tr>
            <td><strong>${it.label}</strong></td>
            <td class="text-right mono">₱${Number(it.price).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-center mono"><span class="badge badge-info">÷ ${it.divisor}</span></td>
            <td class="text-right mono font-bold text-accent">₱${Number(it.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
            <td class="text-secondary small">${it.note || '—'}</td>
          </tr>
        `).join('');
      }
      const elExpTotal = document.getElementById("expedition-total");
      if (elExpTotal) elExpTotal.textContent = `₱${Number(expRes.data.subtotal).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;
    }
  }
};
