/**
 * View Controller: Tab 3 - Monthly Bills & Roommate Utility Splitter
 */
window.BillsView = {
  init() {
    this.bindEvents();
    window.addEventListener('state-updated', () => this.render());
  },

  bindEvents() {
    // Add bill button
    const btnAdd = document.getElementById('btn-add-bill');
    if (btnAdd) {
      btnAdd.addEventListener('click', () => {
        document.getElementById('form-add-bill').reset();
        Modal.open('modal-add-bill');
      });
    }

    // Save new bill
    const formAdd = document.getElementById('form-add-bill');
    if (formAdd) {
      formAdd.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('modal-bill-name').value.trim();
        const category = document.getElementById('modal-bill-category').value;
        const amount = document.getElementById('modal-bill-amount').value;
        
        if (!name || !amount) return;

        AppState.data.bills.items.push({
          name: name,
          category: category,
          total_amount: amount,
          is_active: true,
          active_tenants: [...AppState.data.bills.tenants]
        });

        Modal.close('modal-add-bill');
        AppState.recalculateAll();
        AppState.persistState();
        Toast.show(`Added bill: ${name}`, 'success');
      });
    }
  },

  render() {
    const summary = AppState.computed.billsSummary;
    if (!summary) return;

    // Header metrics
    document.getElementById('val-bills-grand-total').innerText = AppState.formatCurrency(summary.grand_total);
    document.getElementById('val-bills-my-share').innerText = AppState.formatCurrency(summary.my_total_share);
    document.getElementById('val-bills-active-count').innerText = `${summary.active_bills_count} Active`;

    // Render YTD Summary (A408:B413)
    const ytd = AppState.computed.billsYtdSummary;
    if (ytd) {
      const mPaidEl = document.getElementById('val-ytd-months-paid');
      const gTotalEl = document.getElementById('val-ytd-grand-total');
      const avgPersonEl = document.getElementById('val-ytd-avg-person');
      const highMonthEl = document.getElementById('val-ytd-highest-month');

      if (mPaidEl) mPaidEl.innerText = ytd.months_paid;
      if (gTotalEl) gTotalEl.innerText = AppState.formatCurrency(ytd.grand_total);
      if (avgPersonEl) avgPersonEl.innerText = AppState.formatCurrency(ytd.average_per_person);
      if (highMonthEl) {
        highMonthEl.innerText = AppState.formatCurrency(ytd.highest_month ? ytd.highest_month.amount : "0.00");
        if (ytd.highest_month && ytd.highest_month.month) {
          highMonthEl.title = `Month: ${ytd.highest_month.month}`;
        }
      }
    }

    // Render Bills Table
    const tbody = document.getElementById('tbody-bills');
    if (!tbody) return;

    const tenants = AppState.data.bills.tenants || ["Dan", "Jaco", "Troy"];
    const myName = AppState.data.bills.my_tenant_name || "Dan";

    tbody.innerHTML = AppState.data.bills.items.map((item, idx) => {
      const activeTenants = item.active_tenants || [];
      const computedBill = summary.bills ? summary.bills[idx] : null;
      const myShare = computedBill ? computedBill.my_share : "0.00";

      // Render tenant checkbox pills
      const tenantPillsHtml = tenants.map(t => {
        const isChecked = activeTenants.includes(t);
        return `
          <label class="tenant-pill ${isChecked ? 'active' : ''}">
            <input type="checkbox"
                   data-bill-idx="${idx}"
                   data-tenant="${t}"
                   ${isChecked ? 'checked' : ''}
                   class="chk-bill-tenant">
            <span>${t}</span>
          </label>
        `;
      }).join(' ');

      return `
        <tr>
          <td>
            <div style="font-weight: 600;">${item.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${item.category}</div>
          </td>
          <td class="currency-cell">${AppState.formatCurrency(item.total_amount)}</td>
          <td>${tenantPillsHtml}</td>
          <td class="currency-cell text-emerald-400 font-bold">${AppState.formatCurrency(myShare)}</td>
          <td class="text-center">
            <button class="btn btn-secondary btn-sm btn-delete-bill" data-idx="${idx}">🗑️</button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach tenant pill checkbox toggles
    tbody.querySelectorAll('.chk-bill-tenant').forEach(chk => {
      chk.addEventListener('change', (e) => {
        const bIdx = parseInt(e.target.getAttribute('data-bill-idx'));
        const tenant = e.target.getAttribute('data-tenant');
        const bill = AppState.data.bills.items[bIdx];
        
        if (e.target.checked) {
          if (!bill.active_tenants.includes(tenant)) bill.active_tenants.push(tenant);
        } else {
          bill.active_tenants = bill.active_tenants.filter(t => t !== tenant);
        }

        AppState.recalculateAll();
        AppState.persistState();
      });
    });

    // Attach delete button listeners
    tbody.querySelectorAll('.btn-delete-bill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
        const removed = AppState.data.bills.items.splice(idx, 1);
        AppState.recalculateAll();
        AppState.persistState();
        Toast.show(`Removed ${removed[0].name}`, 'info');
      });
    });
  }
};
