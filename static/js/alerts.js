(function () {
  function refreshBadge() {
    fetch('/api/alerts/live', { credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('fail');
        return r.json();
      })
      .then((data) => {
        const title = document.querySelector('.page-title');
        if (title && typeof data.unresolved === 'number') {
          title.setAttribute('data-open-count', String(data.unresolved));
        }
      })
      .catch(() => {});
  }

  setInterval(refreshBadge, 8000);
})();
