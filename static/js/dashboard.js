(function () {
  const grid = document.getElementById('server-grid');
  const alertsBody = document.getElementById('alerts-mini-body');
  const statServers = document.getElementById('stat-servers');
  const statAlerts = document.getElementById('stat-alerts');

  function esc(text) {
    const d = document.createElement('div');
    d.textContent = text == null ? '' : String(text);
    return d.innerHTML;
  }

  function renderServers(servers) {
    if (!grid) return;
    if (!servers.length) {
      grid.innerHTML = '<p class="empty-note" id="empty-servers">لا توجد سيرفرات مسجّلة بعد.</p>';
      return;
    }
    grid.innerHTML = servers.map((s) => {
      const cpu = s.cpu == null ? '--' : `${s.cpu}%`;
      const ram = s.ram == null ? '--' : `${s.ram}%`;
      const disk = s.disk == null ? '--' : `${s.disk}%`;
      const baseline = s.is_in_baseline ? '<p class="tile-note">فترة تعلّم أولية</p>' : '';
      return (
        `<a class="server-tile status-${esc(s.status)}" href="/servers/${s.id}" data-server-id="${s.id}">` +
        `<div class="tile-head"><h3>${esc(s.name)}</h3><span class="badge badge-${esc(s.status)}">${esc(s.status)}</span></div>` +
        `<p class="tile-meta">${esc(s.os_type)} · ${esc(s.host_address)}</p>${baseline}` +
        `<div class="metrics-mini">` +
        `<div><span>المعالج</span><strong class="m-cpu">${esc(cpu)}</strong></div>` +
        `<div><span>الذاكرة</span><strong class="m-ram">${esc(ram)}</strong></div>` +
        `<div><span>التخزين</span><strong class="m-disk">${esc(disk)}</strong></div>` +
        `</div></a>`
      );
    }).join('');
  }

  function renderAlerts(alerts) {
    if (!alertsBody) return;
    if (!alerts.length) {
      alertsBody.innerHTML = '<tr class="empty-row"><td colspan="5">لا توجد تنبيهات مفتوحة.</td></tr>';
      return;
    }
    alertsBody.innerHTML = alerts.map((a) => (
      `<tr>` +
      `<td>${esc(a.server_name)}</td>` +
      `<td>${esc(a.alert_type)}</td>` +
      `<td><span class="sev sev-${esc(a.severity)}">${esc(a.severity)}</span></td>` +
      `<td>${esc(a.message)}</td>` +
      `<td>${esc(a.created_at_fmt || '')}</td>` +
      `</tr>`
    )).join('');
  }

  function refresh() {
    fetch('/api/dashboard/live', { credentials: 'same-origin' })
      .then((r) => {
        if (!r.ok) throw new Error('fail');
        return r.json();
      })
      .then((data) => {
        if (statServers) statServers.textContent = String((data.servers || []).length);
        if (statAlerts) statAlerts.textContent = String(data.unresolved || 0);
        renderServers(data.servers || []);
        renderAlerts(data.recent_alerts || []);
      })
      .catch(() => {});
  }

  setInterval(refresh, 5000);
})();
