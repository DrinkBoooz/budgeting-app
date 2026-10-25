/**
 * PyWebView Bridge Client Wrapper.
 * Provides safe Promise-based communication with Python ScriptAPI with
 * fallback mock handling if run outside PyWebView.
 */

window.Bridge = {
  isAvailable() {
    return window.pywebview && window.pywebview.api;
  },

  async call(method, payload = {}) {
    if (this.isAvailable()) {
      try {
        const response = await window.pywebview.api[method](payload);
        return response;
      } catch (err) {
        console.error(`Bridge call ${method} failed:`, err);
        return { success: false, message: err.toString() };
      }
    } else {
      console.warn(`PyWebView bridge not available. Simulating ${method}`, payload);
      return this._mockResponse(method, payload);
    }
  },

  _mockResponse(method, payload) {
    if (method === 'get_app_info') {
      return { success: true, data: { app_name: 'Budgeting & Salary Suite', version: '0.1.0', version_badge: 'Release v0.1.0' } };
    }
    return { success: true, data: payload, message: 'Mock response' };
  }
};
