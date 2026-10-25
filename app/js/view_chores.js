/**
 * View Controller: Roommate Chore Chart & Live COUNTIF Counters
 */

const ViewChores = {
  init() {
    this.bindEvents();
    this.render();
  },

  bindEvents() {
    const btnRefresh = document.getElementById("btn-refresh-chores");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => this.render());
    }
  },

  async render() {
    const data = State.get();
    const choresData = data.chores || {};

    const res = await Bridge.call("get_chores_summary", {
      month: choresData.month || "2026-07",
      entries: choresData.entries
    });

    if (!res || !res.success) return;

    const summary = res.data;

    // Roommate Counters
    const danCount = summary.counts?.Dan || 0;
    const jacoCount = summary.counts?.Jaco || 0;
    const troyCount = summary.counts?.Troy || 0;
    const totalCount = summary.total_completed || (danCount + jacoCount + troyCount);

    const elDan = document.getElementById("chore-count-dan");
    if (elDan) elDan.textContent = danCount;

    const elJaco = document.getElementById("chore-count-jaco");
    if (elJaco) elJaco.textContent = jacoCount;

    const elTroy = document.getElementById("chore-count-troy");
    if (elTroy) elTroy.textContent = troyCount;

    const elTotal = document.getElementById("chore-count-total");
    if (elTotal) elTotal.textContent = totalCount;

    // Render Chores Table
    const tbody = document.getElementById("chores-matrix-tbody");
    if (tbody && summary.entries) {
      tbody.innerHTML = summary.entries.map((c, idx) => {
        const assignments = c.daily_assignments || {};
        const daysActive = Object.entries(assignments).filter(([d, val]) => val && val.trim());
        const tags = daysActive.map(([d, val]) => {
          let badgeClass = "badge-secondary";
          if (val === 'D') badgeClass = "badge-primary";
          if (val === 'J') badgeClass = "badge-success";
          if (val === 'T') badgeClass = "badge-warning";
          return `<span class="badge ${badgeClass}" title="Day ${d}">Day ${d}: ${val}</span>`;
        }).join(' ');

        return `
          <tr>
            <td><span class="badge badge-outline">${c.zone}</span></td>
            <td><strong>${c.chore_name}</strong></td>
            <td><span class="text-secondary">${c.frequency}</span></td>
            <td>${tags || '<span class="text-muted small">No assignments logged</span>'}</td>
          </tr>
        `;
      }).join('');
    }
  }
};
