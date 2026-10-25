/**
 * View Controller: Tab 4 - Peer Settlements & Family Remittances
 */
window.SettlementsView = {
  init() {
    this.bindEvents();
    window.addEventListener('state-updated', () => this.render());
  },

  bindEvents() {
    // Add Calumpang Peer Item
    const btnAddPeer = document.getElementById('btn-add-peer-item');
    if (btnAddPeer) {
      btnAddPeer.addEventListener('click', () => {
        document.getElementById('form-add-peer-item').reset();
        Modal.open('modal-add-peer-item');
      });
    }

    const formPeer = document.getElementById('form-add-peer-item');
    if (formPeer) {
      formPeer.addEventListener('submit', (e) => {
        e.preventDefault();
        const desc = document.getElementById('modal-peer-desc').value.trim();
        const amount = document.getElementById('modal-peer-amount').value;
        if (!desc || !amount) return;

        AppState.data.settlements.items.push({
          description: desc,
          total_amount: amount,
          paid_by: "Dan",
          status: "pending"
        });

        Modal.close('modal-add-peer-item');
        AppState.recalculateAll();
        AppState.persistState();
        Toast.show(`Added peer item: ${desc}`, 'success');
      });
    }

    // Add Mama Grocery Item
    const btnAddGrocery = document.getElementById('btn-add-grocery-item');
    if (btnAddGrocery) {
      btnAddGrocery.addEventListener('click', () => {
        document.getElementById('form-add-grocery').reset();
        Modal.open('modal-add-grocery');
      });
    }

    const formGrocery = document.getElementById('form-add-grocery');
    if (formGrocery) {
      formGrocery.addEventListener('submit', (e) => {
        e.preventDefault();
        const desc = document.getElementById('modal-grocery-desc').value.trim();
        const amount = document.getElementById('modal-grocery-amount').value;
        const isDeduction = document.getElementById('modal-grocery-is-deduction').checked;
        if (!desc || !amount) return;

        if (isDeduction) {
          AppState.data.groceries.deductions.push({ description: desc, amount: amount });
        } else {
          AppState.data.groceries.items.push({ description: desc, amount: amount });
        }

        Modal.close('modal-add-grocery');
        AppState.recalculateAll();
        AppState.persistState();
        Toast.show(`Added grocery: ${desc}`, 'success');
      });
    }
  },

  render() {
    const peerSum = AppState.computed.settlementSummary;
    const grocSum = AppState.computed.groceriesSummary;

    // Calumpang Summary
    if (peerSum) {
      document.getElementById('val-calumpang-total').innerText = AppState.formatCurrency(peerSum.total_expenses);
      document.getElementById('val-calumpang-peer-owes').innerText = AppState.formatCurrency(peerSum.net_peer_owes_dan);
      document.getElementById('val-calumpang-dan-share').innerText = AppState.formatCurrency(peerSum.dan_total_share);

      const tbodyPeer = document.getElementById('tbody-calumpang');
      if (tbodyPeer && peerSum.items) {
        tbodyPeer.innerHTML = peerSum.items.map((it, idx) => `
          <tr>
            <td><strong>${it.description}</strong></td>
            <td class="currency-cell">${AppState.formatCurrency(it.total_amount)}</td>
            <td class="currency-cell text-emerald-400">${AppState.formatCurrency(it.dan_share)}</td>
            <td class="currency-cell text-cyan-400">${AppState.formatCurrency(it.peer_share)}</td>
            <td class="text-center">
              <button class="btn btn-secondary btn-sm btn-del-peer" data-idx="${idx}">🗑️</button>
            </td>
          </tr>
        `).join('');

        tbodyPeer.querySelectorAll('.btn-del-peer').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
            AppState.data.settlements.items.splice(idx, 1);
            AppState.recalculateAll();
            AppState.persistState();
          });
        });
      }
    }

    // Mama Groceries Summary
    if (grocSum) {
      document.getElementById('val-mama-gross').innerText = AppState.formatCurrency(grocSum.gross_amount);
      document.getElementById('val-mama-deductions').innerText = AppState.formatCurrency(grocSum.total_deductions);
      document.getElementById('val-mama-net-transfer').innerText = AppState.formatCurrency(grocSum.net_transfer_amount);

      // Groceries items table
      const tbodyGroc = document.getElementById('tbody-groceries');
      if (tbodyGroc) {
        tbodyGroc.innerHTML = AppState.data.groceries.items.map((it, idx) => `
          <tr>
            <td>${it.description}</td>
            <td class="currency-cell">${AppState.formatCurrency(it.amount)}</td>
            <td class="text-center">
              <button class="btn btn-secondary btn-sm btn-del-groc" data-idx="${idx}">🗑️</button>
            </td>
          </tr>
        `).join('');

        tbodyGroc.querySelectorAll('.btn-del-groc').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
            AppState.data.groceries.items.splice(idx, 1);
            AppState.recalculateAll();
            AppState.persistState();
          });
        });
      }

      // Deductions table
      const tbodyDed = document.getElementById('tbody-deductions');
      if (tbodyDed) {
        tbodyDed.innerHTML = AppState.data.groceries.deductions.map((d, idx) => `
          <tr>
            <td>${d.description}</td>
            <td class="currency-cell text-danger">-${AppState.formatCurrency(d.amount)}</td>
            <td class="text-center">
              <button class="btn btn-secondary btn-sm btn-del-ded" data-idx="${idx}">🗑️</button>
            </td>
          </tr>
        `).join('');

        tbodyDed.querySelectorAll('.btn-del-ded').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
            AppState.data.groceries.deductions.splice(idx, 1);
            AppState.recalculateAll();
            AppState.persistState();
          });
        });
      }
    }
  }
};
