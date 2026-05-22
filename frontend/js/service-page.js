// Service detail page — loads service data based on data-service-slug attribute on body
(async function() {
  const slug = document.body.dataset.serviceSlug;
  const icon = document.body.dataset.serviceIcon || '✨';
  const container = document.getElementById('service-content');
  if (!slug || !container) return;

  try {
    const svc = await CSIT.Services.get(slug);
    let features = [];
    try { features = JSON.parse(svc.features); } catch {}

    // Is this a fixed-price service with a unit price set? → show quantity selector
    const isFixedQty = svc.service_type === 'fixed' && svc.price > 0;
    const unitLabel = (slug === 'lead-generation') ? 'leads' : 'units';

    // Map each service slug to its illustration
    const illustrationMap = {
      'website-development': '/assets/illustrations/website-dev.png',
      'erp-software': '/assets/illustrations/erp-gears.png',
      'digital-marketing': '/assets/illustrations/marketing-team.png',
      'lead-generation': '/assets/illustrations/leadgen-meeting.png',
    };
    const illustrationSrc = illustrationMap[slug];

    container.innerHTML = `
      <section class="hero-split hero-animated fade-in">
        <div class="floating-shapes">
          <div class="floating-shape s1"></div>
          <div class="floating-shape s2"></div>
          <div class="floating-shape s3"></div>
        </div>
        <div class="container">
          <div class="hero-split-inner">
            <div class="hero-split-text">
              <div class="service-hero-icon" style="margin:0 0 var(--space-md) 0;">${icon}</div>
              <h1>${escapeHtml(svc.name)}</h1>
              <p class="hero-subtitle">${escapeHtml(svc.short_description)}</p>
              <div class="service-price">${escapeHtml(svc.price_label || 'Contact for pricing')}</div>
              <div class="hero-actions mt-md">
                <a href="#order-form" class="btn btn-primary btn-lg">${svc.service_type === 'fixed' && svc.price > 0 ? 'Order Now' : 'Get Started'}</a>
              </div>
            </div>
            ${illustrationSrc ? `
              <div class="hero-illustration">
                <img src="${illustrationSrc}" alt="${escapeHtml(svc.name)} illustration">
              </div>
            ` : ''}
          </div>
        </div>
      </section>

      <section class="section container-narrow">
        <h2 class="text-center mb-md">What's included</h2>
        <ul class="features-list">
          ${features.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
        </ul>

        <div class="card mt-lg">
          <h3 class="mb-sm">About this service</h3>
          <p>${escapeHtml(svc.full_description)}</p>
        </div>

        <div class="text-center mt-lg">
          <h3 class="mb-md">Ready to get started?</h3>
          <div class="hero-actions">
            <a href="#order-form" class="btn btn-primary btn-lg">${isFixedQty ? 'Order Now' : 'Request This Service'}</a>
            <a href="/#contact" class="btn btn-ghost btn-lg">Have Questions?</a>
          </div>
        </div>
      </section>

      <section class="section container-narrow" id="order-form">
        <div class="section-header">
          <span class="section-eyebrow">${isFixedQty ? 'Place your order' : 'Get started'}</span>
          <h2 class="section-title">${isFixedQty ? 'How many do you need?' : 'Tell us about your project'}</h2>
        </div>

        <div id="alerts"></div>

        <div data-auth="logged-out" class="card text-center">
          <p class="mb-md">You need an account to ${isFixedQty ? 'place an order' : 'request a quote'}.</p>
          <div class="hero-actions">
            <a href="/signup.html?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary">Sign Up</a>
            <a href="/login.html?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-ghost">Login</a>
          </div>
        </div>

        ${isFixedQty ? renderFixedForm(svc, unitLabel) : renderQuoteForm(svc)}
      </section>
    `;

    // Re-trigger nav update for newly injected elements
    if (window.updateNav) window.updateNav();

    // Wire up quantity calculator (only for fixed services)
    if (isFixedQty) {
      const qtyInput = document.getElementById('quantity');
      const totalEl = document.getElementById('total-price');
      const updateTotal = () => {
        const q = parseInt(qtyInput.value) || 0;
        const total = q * svc.price;
        totalEl.textContent = formatPrice(total);
      };
      qtyInput.addEventListener('input', updateTotal);
      updateTotal();
    }

    // Wire up the form
    const form = document.getElementById('order-form-el');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!window.requireAuth()) return;
        const btn = e.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Submitting...';
        try {
          let notes = document.getElementById('customer_notes').value;
          if (isFixedQty) {
            const qty = parseInt(document.getElementById('quantity').value) || 0;
            if (qty < 1) throw new Error('Please enter a valid quantity');
            notes = `QUANTITY: ${qty} ${unitLabel} @ ${formatPrice(svc.price)} each = ${formatPrice(qty * svc.price)}\n\n${notes}`;
          }
          const order = await CSIT.Orders.create(svc.id, notes);
          // If fixed-price, immediately set the order amount via admin? No — customer can't set amount.
          // Backend uses service.price as initial amount, so for fixed services the amount will be svc.price (single unit).
          // Admin will need to update amount based on quantity. We pass quantity in customer_notes.
          showAlert('Order submitted! Redirecting to your dashboard...', 'success');
          setTimeout(() => {
            window.location.href = '/dashboard.html';
          }, 1500);
        } catch (err) {
          showAlert(err.message || 'Could not submit. Please try again.', 'error');
          btn.disabled = false;
          btn.textContent = isFixedQty ? 'Place Order' : 'Submit Request';
        }
      });
    }
  } catch (err) {
    container.innerHTML = `
      <section class="section container-narrow text-center">
        <h2>Service not found</h2>
        <p class="text-muted">${escapeHtml(err.message || 'Could not load this service.')}</p>
        <a href="/" class="btn btn-primary mt-md">Back home</a>
      </section>
    `;
  }

  function renderFixedForm(svc, unitLabel) {
    return `
      <form id="order-form-el" class="card" data-auth="logged-in">
        <div class="form-group">
          <label class="form-label" for="quantity">Number of ${unitLabel} <span class="text-accent">*</span></label>
          <input class="form-input" type="number" id="quantity" name="quantity" min="1" value="50" required>
          <small class="text-muted" style="display:block;margin-top:0.25rem;">Minimum 1 ${unitLabel.slice(0,-1)}. Bulk discounts available for 500+.</small>
        </div>

        <div class="card mb-md" style="background:var(--bg-secondary);padding:1rem 1.25rem;">
          <div class="flex-between" style="font-size:0.95rem;">
            <span class="text-muted">Unit price</span>
            <strong>${formatPrice(svc.price)} / ${unitLabel.slice(0,-1)}</strong>
          </div>
          <div class="flex-between mt-sm" style="padding-top:0.75rem;border-top:1px solid var(--border);">
            <strong>Total</strong>
            <strong id="total-price" style="font-size:1.5rem;color:var(--accent);">${formatPrice(svc.price * 50)}</strong>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="customer_notes">Targeting Details</label>
          <textarea class="form-textarea" id="customer_notes" name="customer_notes" rows="4" required
            placeholder="Describe your ideal lead: industry, job titles, company size, location, etc."></textarea>
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg">Place Order</button>
        <p class="text-muted text-center mt-sm" style="font-size:0.85rem;">
          We'll confirm your order and send a payment link within 1 business day.
        </p>
      </form>
    `;
  }

  function renderQuoteForm(svc) {
    return `
      <form id="order-form-el" class="card" data-auth="logged-in">
        <div class="form-group">
          <label class="form-label" for="customer_notes">Project Details</label>
          <textarea class="form-textarea" id="customer_notes" name="customer_notes" rows="5" required
            placeholder="Describe your project, requirements, timeline, budget range..."></textarea>
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg">Submit Request</button>
        <p class="text-muted text-center mt-sm" style="font-size:0.85rem;">
          We'll review your request and get back with a custom quote within 24-48 hours.
        </p>
      </form>
    `;
  }
})();
