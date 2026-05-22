document.querySelector('.nav-toggle')?.addEventListener('click', () => {
  document.querySelector('.nav-links')?.classList.toggle('open');
});
const yearEl = document.getElementById('year'); if (yearEl) yearEl.textContent = new Date().getFullYear();

const obs = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
}, { threshold: 0.15 });
document.querySelectorAll('.feature-card, .process-step, .pricing-card, .section-header').forEach(el => {
  el.classList.add('fade-in'); obs.observe(el);
});

// Live quantity calculator
const UNIT_PRICE = 10;
const qtyInput = document.getElementById('lead-qty');
const totalEl = document.getElementById('lead-total');
function updateTotal() {
  const q = parseInt(qtyInput.value) || 0;
  if (totalEl) totalEl.textContent = '$' + (q * UNIT_PRICE).toLocaleString();
}
if (qtyInput) {
  qtyInput.addEventListener('input', updateTotal);
  updateTotal();
}

// Sync calculator qty → order form qty when navigating to order
const calcQtyInput = document.getElementById('lead-qty');
const orderQtyInput = document.getElementById('qty');
document.querySelectorAll('a[href="#order"]').forEach(a => {
  a.addEventListener('click', () => {
    if (calcQtyInput && orderQtyInput && calcQtyInput.value) {
      orderQtyInput.value = calcQtyInput.value;
    }
  });
});

// Order form → redirect to Stripe checkout
const form = document.getElementById('contact-form');
const alertEl = document.getElementById('alert');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    const orig = btn.innerHTML;
    btn.innerHTML = 'Loading checkout...';

    try {
      const quantity = parseInt(form.qty?.value) || 0;
      if (quantity < 50) {
        throw new Error('Minimum order is 50 leads');
      }

      const orderData = {
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        phone: (form.phone.value || '').trim() || null,
        quantity: quantity,
        notes: form.message.value.trim(),
      };

      if (!orderData.name || !orderData.email || !orderData.notes) {
        throw new Error('Please fill in all required fields');
      }

      // Store in sessionStorage for checkout page
      sessionStorage.setItem('csit_lead_order', JSON.stringify(orderData));

      // Redirect to checkout
      window.location.href = '/checkout.html';
    } catch (err) {
      if (alertEl) {
        alertEl.textContent = err.message || 'Could not proceed. Please try again.';
        alertEl.className = 'alert alert-error';
      }
      btn.disabled = false;
      btn.innerHTML = orig;
    }
  });
}
