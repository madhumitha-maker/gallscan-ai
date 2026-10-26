/**
 * GallScan AI — Unified API Client
 */

const API_BASE = window.__BACKEND_URL__ 
  || (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
      ? (window.location.port === "8000" ? window.location.origin : "http://localhost:8000")
      : window.location.origin);

const API = {
  getToken() {
    return localStorage.getItem("gallscan_token");
  },

  setToken(token) {
    localStorage.setItem("gallscan_token", token);
  },

  removeToken() {
    localStorage.removeItem("gallscan_token");
    localStorage.removeItem("gallscan_user");
  },

  getUser() {
    try {
      const u = localStorage.getItem("gallscan_user");
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("gallscan_user", JSON.stringify(user));
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE}/api${endpoint}`;
    const headers = options.headers || {};
    
    // Attach JWT if available
    const token = this.getToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!options.isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      
      // If unauthorized, clear auth and redirect to login
      if (response.status === 401 && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/signup")) {
        this.removeToken();
        if (!window.location.pathname.endsWith("login.html") && !window.location.pathname.endsWith("index.html")) {
          window.location.href = "login.html?expired=1";
        }
        throw new Error("Session expired. Please log in again.");
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth endpoints
  login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },

  signup(name, email, password, role = "clinician") {
    return this.request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role })
    });
  },

  forgotPassword(email) {
    return this.request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  },

  resetPassword(token, new_password) {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password })
    });
  },

  // Profile endpoints
  getProfile() {
    return this.request("/users/me");
  },

  updateProfile(name, email) {
    return this.request("/users/me", {
      method: "PATCH",
      body: JSON.stringify({ name, email })
    });
  },

  changePassword(current_password, new_password) {
    return this.request("/users/me/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password })
    });
  },

  // Prediction & Scans
  predict(formData) {
    return this.request("/predict", {
      method: "POST",
      body: formData,
      isFormData: true
    });
  },

  getHistory(page = 1, limit = 10, classFilter = "", search = "") {
    const params = new URLSearchParams({ page, limit });
    if (classFilter) params.append("class_filter", classFilter);
    if (search) params.append("search", search);
    return this.request(`/history?${params.toString()}`);
  },

  getPredictionById(id) {
    return this.request(`/history/${id}`);
  },

  deletePrediction(id) {
    return this.request(`/history/${id}`, {
      method: "DELETE"
    });
  },

  // Notifications
  getNotifications(limit = 50) {
    return this.request(`/notifications?limit=${limit}`);
  },

  markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: "PATCH"
    });
  },

  markAllNotificationsRead() {
    return this.request("/notifications/read-all", {
      method: "PATCH"
    });
  },

  deleteNotification(id) {
    return this.request(`/notifications/${id}`, {
      method: "DELETE"
    });
  },

  // Health
  checkHealth() {
    return this.request("/health");
  }
};

window.API = API;
