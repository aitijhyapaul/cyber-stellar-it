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
const form = document.getElementById('contact-form');
const alertEl = document.getElementById('alert');
const API_BASE = window.CSIT_API_BASE || 'http://localhost:8100';
const SERVICE_SLUG = window.CSIT_SERVICE_SLUG || 'digital-marketing';
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true; const orig = btn.innerHTML; btn.innerHTML = 'Sending...';
    try {
      const services = await fetch(`${API_BASE}/services`).then(r => r.json()).catch(() => []);
      const svc = services.find(s => s.slug === SERVICE_SLUG);
      const payload = {
        name: form.name.value, email: form.email.value, phone: form.phone.value || null,
        message: form.message.value, service_id: svc?.id || null,
      };
      const res = await fetch(`${API_BASE}/inquiries`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Could not send. Please try again.');
      alertEl.textContent = "Thanks! We'll be in touch within 24 hours.";
      alertEl.className = 'alert alert-success';
      form.reset();
    } catch (err) {
      alertEl.textContent = err.message || 'Could not send. Please try again.';
      alertEl.className = 'alert alert-error';
    } finally {
      btn.disabled = false; btn.innerHTML = orig;
    }
  });
}
