// Cyber Stellar IT — API client
const API_BASE = window.location.origin;

function getToken() {
  return localStorage.getItem('csit_token');
}

function setToken(token) {
  localStorage.setItem('csit_token', token);
}

function clearToken() {
  localStorage.removeItem('csit_token');
  localStorage.removeItem('csit_user');
}

function getUser() {
  const u = localStorage.getItem('csit_user');
  return u ? JSON.parse(u) : null;
}

function setUser(user) {
  localStorage.setItem('csit_user', JSON.stringify(user));
}

async function api(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : await res.text();

  if (!res.ok) {
    const err = new Error(data.detail || data.message || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

// ============================
// Auth API
// ============================
const Auth = {
  async register(email, full_name, password) {
    const data = await api('/api/auth/register', {
      method: 'POST',
      body: { email, full_name, password },
    });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  },

  async login(email, password) {
    const data = await api('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  },

  async me() {
    return api('/api/auth/me');
  },

  logout() {
    clearToken();
  },

  isLoggedIn() {
    return !!getToken();
  },

  isAdmin() {
    const u = getUser();
    return u && u.is_admin;
  },
};

// ============================
// Services API
// ============================
const Services = {
  list() { return api('/api/services/'); },
  get(slug) { return api(`/api/services/${slug}`); },
};

// ============================
// Orders API
// ============================
const Orders = {
  create(service_id, customer_notes) {
    return api('/api/orders/', {
      method: 'POST',
      body: { service_id, customer_notes },
    });
  },
  myOrders() { return api('/api/orders/my'); },
  get(id) { return api(`/api/orders/${id}`); },
  all() { return api('/api/orders/admin/all'); },
  updateStatus(id, payload) {
    return api(`/api/orders/${id}`, { method: 'PATCH', body: payload });
  },
};

// ============================
// Payments API (bank / wire transfer)
// ============================
const Payments = {
  bankDetails() { return api('/api/payments/bank-details'); },
  exchangeRate() { return api('/api/payments/exchange-rate'); },
  submit(order_id, payment_method, transfer_reference, transfer_date, notes) {
    return api('/api/payments/submit', {
      method: 'POST',
      body: { order_id, payment_method, transfer_reference, transfer_date, notes },
    });
  },
  verify(order_id, approve, rejection_reason) {
    return api(`/api/payments/${order_id}/verify`, {
      method: 'POST',
      body: { approve, rejection_reason },
    });
  },
  invoiceUrl(order_id) {
    const token = getToken();
    return `/api/payments/${order_id}/invoice?token=${encodeURIComponent(token || '')}`;
  },
};

// ============================
// Inquiries API
// ============================
const Inquiries = {
  create(payload) {
    return api('/api/inquiries/', { method: 'POST', body: payload });
  },
  all() { return api('/api/inquiries/admin/all'); },
  updateStatus(id, status) {
    return api(`/api/inquiries/admin/${id}`, { method: 'PATCH', body: { status } });
  },
};

// ============================
// Admin API
// ============================
const Admin = {
  stats() { return api('/api/admin/stats'); },
  users() { return api('/api/admin/users'); },
  toggleUserActive(id) {
    return api(`/api/admin/users/${id}/toggle-active`, { method: 'PATCH' });
  },
  makeAdmin(id) {
    return api(`/api/admin/users/${id}/make-admin`, { method: 'PATCH' });
  },
};

// Make available globally
window.CSIT = { Auth, Services, Orders, Payments, Inquiries, Admin, api, getToken, getUser };
