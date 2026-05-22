// Stellar API wrapper — talks to the ERP SaaS backend
const STELLAR_API_BASE = window.STELLAR_API_BASE || 'http://localhost:8080';

const StellarAPI = {
  // Persist token + user info
  saveSession(token, orgId, userId, role) {
    localStorage.setItem('stellar_token', token);
    localStorage.setItem('stellar_org_id', orgId);
    localStorage.setItem('stellar_user_id', userId);
    localStorage.setItem('stellar_role', role);
  },

  getToken() {
    return localStorage.getItem('stellar_token');
  },

  clearSession() {
    ['stellar_token', 'stellar_org_id', 'stellar_user_id', 'stellar_role']
      .forEach(k => localStorage.removeItem(k));
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  async signup({ orgName, fullName, email, password, plan = 'starter', industry = 'manufacturing', country = 'Bangladesh' }) {
    const res = await fetch(`${STELLAR_API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        org_name: orgName,
        full_name: fullName,
        email,
        password,
        industry,
        country,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || 'Signup failed');
    }
    const data = await res.json();
    this.saveSession(data.access_token, data.org_id, data.user_id, data.role);
    // Save selected plan locally — billing module will handle real subscription
    localStorage.setItem('stellar_selected_plan', plan);
    return data;
  },

  async login({ email, password }) {
    // FastAPI's OAuth2PasswordRequestForm wants form-urlencoded
    const fd = new URLSearchParams();
    fd.append('username', email);
    fd.append('password', password);

    const res = await fetch(`${STELLAR_API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: fd,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid email or password');
    }
    const data = await res.json();
    this.saveSession(data.access_token, data.org_id, data.user_id, data.role);
    return data;
  },

  async me() {
    const token = this.getToken();
    if (!token) throw new Error('Not logged in');
    const res = await fetch(`${STELLAR_API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Session expired');
    return res.json();
  },

  // Where to send users after login (the ERP React app)
  appUrl() {
    return window.STELLAR_APP_URL || 'http://localhost:5174';
  },
};

window.StellarAPI = StellarAPI;
