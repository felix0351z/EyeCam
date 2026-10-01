// Markiert den aktiven Navigationspunkt anhand der aktuellen Seite
(function highlightNav() {
  const current = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.site-header nav a').forEach((link) => {
    if (link.getAttribute('href') === current) {
      link.classList.add('active');
    }
  });
})();

// Kontaktformular: sendet die Daten per REST-API (POST /api/contact) an das Backend
// Passt die Basis-URL an, sobald ihr die API deployed habt.
const API_BASE_URL = '[Platzhalter: z. B. http://localhost:3000]';

const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const statusEl = document.getElementById('form-status');
    const submitBtn = contactForm.querySelector('button[type="submit"]');

    const payload = {
      name: contactForm.name.value.trim(),
      email: contactForm.email.value.trim(),
      message: contactForm.message.value.trim(),
    };

    statusEl.textContent = 'Wird gesendet ...';
    statusEl.className = '';
    submitBtn.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server antwortete mit Status ${response.status}`);
      }

      const data = await response.json();
      statusEl.textContent = data.message || 'Danke! Eure Nachricht wurde verschickt.';
      statusEl.className = 'ok';
      contactForm.reset();
    } catch (err) {
      statusEl.textContent =
        'Nachricht konnte nicht gesendet werden. Laeuft die API? (' + err.message + ')';
      statusEl.className = 'err';
    } finally {
      submitBtn.disabled = false;
    }
  });
}
