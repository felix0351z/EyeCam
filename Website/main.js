// Karten-Navigation: zeigt jeweils nur eine .page an und schaltet per
// Weiter/Zurueck-Button oder Klick auf einen Punkt um.
(function stepper() {
  const pages = Array.from(document.querySelectorAll('.page'));
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  if (!pages.length) return;

  let current = 0;

  function render() {
    pages.forEach((page, i) => {
      page.classList.toggle('is-active', i === current);
    });

    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === pages.length - 1;
    nextBtn.textContent = current === pages.length - 1 ? 'Ende' : ' \u2192';

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goTo(index) {
    current = Math.max(0, Math.min(pages.length - 1, index));
    render();
  }

  prevBtn.addEventListener('click', () => goTo(current - 1));
  nextBtn.addEventListener('click', () => goTo(current + 1));

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') goTo(current + 1);
    if (e.key === 'ArrowLeft') goTo(current - 1);
  });

  render();
})();
