/**
 * View Controller: Pajah Graduation & Pictorial Toga Rentals
 */

const ViewPajah = {
  init() {
    this.bindEvents();
    this.render();
  },

  bindEvents() {
    const btnRefresh = document.getElementById("btn-refresh-pajah");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => this.render());
    }
  },

  async render() {
    const data = State.get();
    const pajahData = data.pajah || {};

    const res = await Bridge.call("compute_pajah_summary", {
      owners: pajahData.owners
    });

    if (!res || !res.success) return;

    const summary = res.data;

    // Totals
    const elOwned = document.getElementById("pajah-total-owned");
    if (elOwned) elOwned.textContent = summary.total_owned;

    const elRentals = document.getElementById("pajah-total-rentals");
    if (elRentals) elRentals.textContent = summary.total_rentals;

    const elRevenue = document.getElementById("pajah-total-revenue");
    if (elRevenue) elRevenue.textContent = `₱${Number(summary.total_active_revenue).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

    const elPotential = document.getElementById("pajah-total-potential");
    if (elPotential) elPotential.textContent = `₱${Number(summary.total_potential_sum).toLocaleString('en-PH', {minimumFractionDigits: 2})}`;

    // Table
    const tbody = document.getElementById("pajah-owners-tbody");
    if (tbody && summary.owners) {
      tbody.innerHTML = summary.owners.map(o => `
        <tr>
          <td><strong>${o.owner_name}</strong></td>
          <td class="text-center">${o.owned}</td>
          <td class="text-right mono">₱${Number(o.price_pictorial).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-right mono">₱${Number(o.price_grad).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-right mono text-warning">+₱${Number(o.dan_addon).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-right mono">₱${Number(o.pictorial_fprice).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-right mono">₱${Number(o.grad_fprice).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-right mono font-bold">₱${Number(o.sum).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
          <td class="text-center"><span class="badge ${o.active_rentals > 0 ? 'badge-success' : 'badge-secondary'}">${o.active_rentals}</span></td>
          <td class="text-right mono font-bold text-accent">₱${Number(o.total_revenue).toLocaleString('en-PH', {minimumFractionDigits: 2})}</td>
        </tr>
      `).join('');
    }
  }
};
