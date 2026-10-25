/**
 * Modal Dialog Controller
 */
window.Modal = {
  open(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('open');
  },

  close(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('open');
  },

  closeAll() {
    document.querySelectorAll('.modal-backdrop, .drawer-backdrop').forEach(el => {
      el.classList.remove('open');
    });
  }
};
