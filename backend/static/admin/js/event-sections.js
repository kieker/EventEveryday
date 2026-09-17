document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.event-section:not(.section-audit) > details').forEach(section => {
    section.open = true;
  });
  // Reveal collapsed fields before browser validation tries to focus them.
  document.addEventListener('invalid', event => {
    const section = event.target.closest('.event-section > details');
    if (section) section.open = true;
  }, true);
});
