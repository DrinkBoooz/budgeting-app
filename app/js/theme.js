/**
 * Theme Switcher: Emerald Dark & Light
 */
window.Theme = {
  current: 'dark',

  init() {
    const saved = localStorage.getItem('budget_app_theme') || 'dark';
    this.set(saved);
  },

  set(theme) {
    this.current = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('budget_app_theme', theme);
    const btn = document.getElementById('btn-theme-toggle');
    if (btn) {
      btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    }
  },

  toggle() {
    this.set(this.current === 'dark' ? 'light' : 'dark');
  }
};
