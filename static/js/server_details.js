(function () {
  const wrap = document.querySelector('.charts-grid');
  if (!wrap) return;
  const serverId = wrap.getAttribute('data-server-id');
  const tabs = document.getElementById('range-tabs');
  let currentRange = 'hour';

  function loadCharts(range) {
    fetch(`/api/servers/${serverId}/metrics?range=${encodeURIComponent(range)}`, {
      credentials: 'same-origin'
    })
      .then((r) => {
        if (!r.ok) throw new Error('fail');
        return r.json();
      })
      .then((data) => {
        const points = data.points || [];
        const cpu = points.map((p) => p.cpu);
        const ram = points.map((p) => p.ram);
        const disk = points.map((p) => p.disk);
        const rt = points.map((p) => p.rt);
        window.ServerEyeCharts.drawLineChart(document.getElementById('chart-cpu'), cpu, '#1e5a8a');
        window.ServerEyeCharts.drawLineChart(document.getElementById('chart-ram'), ram, '#2f7d4a');
        window.ServerEyeCharts.drawLineChart(document.getElementById('chart-disk'), disk, '#b7791f');
        window.ServerEyeCharts.drawLineChart(document.getElementById('chart-rt'), rt, '#2b7bb8');
      })
      .catch(() => {});
  }

  if (tabs) {
    tabs.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-range]');
      if (!btn) return;
      currentRange = btn.getAttribute('data-range');
      tabs.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      loadCharts(currentRange);
    });
  }

  loadCharts(currentRange);
  setInterval(() => { loadCharts(currentRange); }, 15000);
})();
