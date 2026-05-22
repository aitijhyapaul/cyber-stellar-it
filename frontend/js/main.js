// Cyber Stellar IT — main UI helpers
(function() {
  const { Auth } = window.CSIT;

  // Mobile nav toggle
  document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', () => links.classList.toggle('open'));
    }

    // Update nav based on auth state
    updateNav();
  });

  function updateNav() {
    const loggedIn = Auth.isLoggedIn();
    const isAdmin = Auth.isAdmin();

    document.querySelectorAll('[data-auth="logged-in"]').forEach(el => {
      el.style.display = loggedIn ? '' : 'none';
    });
    document.querySelectorAll('[data-auth="logged-out"]').forEach(el => {
      el.style.display = loggedIn ? 'none' : '';
    });
    document.querySelectorAll('[data-auth="admin"]').forEach(el => {
      el.style.display = isAdmin ? '' : 'none';
    });

    // Logout buttons
    document.querySelectorAll('[data-action="logout"]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        Auth.logout();
        window.location.href = '/';
      });
    });
  }

  window.updateNav = updateNav;

  // Alert helper
  window.showAlert = function(msg, type = 'info', containerSel = '#alerts') {
    const container = document.querySelector(containerSel);
    if (!container) return alert(msg);
    container.innerHTML = `<div class="alert alert-${type} fade-in">${escapeHtml(msg)}</div>`;
    if (type === 'success') {
      setTimeout(() => { container.innerHTML = ''; }, 4000);
    }
  };

  window.escapeHtml = function(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  window.formatPrice = function(amount, currency) {
    if (amount == null) return '—';
    const cur = (currency || 'bdt').toLowerCase();
    const num = Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (cur === 'usd') return '$' + num;
    return '৳' + num;
  };

  // Get the JWT token (used by invoice download links).
  window.getAuthToken = function() {
    return localStorage.getItem('csit_token');
  };

  window.formatDate = function(s) {
    if (!s) return '—';
    const d = new Date(s);
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  };

  window.requireAuth = function() {
    if (!Auth.isLoggedIn()) {
      window.location.href = '/login.html?next=' + encodeURIComponent(window.location.pathname);
      return false;
    }
    return true;
  };

  window.requireAdmin = function() {
    if (!Auth.isLoggedIn() || !Auth.isAdmin()) {
      window.location.href = '/login.html?next=' + encodeURIComponent(window.location.pathname);
      return false;
    }
    return true;
  };
})();
