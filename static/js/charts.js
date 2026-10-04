window.ServerEyeCharts = (function () {
  function maxOf(values, fallback) {
    let m = fallback;
    for (let i = 0; i < values.length; i += 1) {
      if (values[i] > m) m = values[i];
    }
    return m;
  }

  function drawLineChart(svg, values, color) {
    if (!svg) return;
    const w = 640;
    const h = 220;
    const pad = 24;
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const axis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    axis.setAttribute('x1', String(pad));
    axis.setAttribute('y1', String(h - pad));
    axis.setAttribute('x2', String(w - pad));
    axis.setAttribute('y2', String(h - pad));
    axis.setAttribute('stroke', '#c5d0dc');
    axis.setAttribute('stroke-width', '1');
    svg.appendChild(axis);

    if (!values || values.length === 0) {
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('x', String(w / 2));
      t.setAttribute('y', String(h / 2));
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('fill', '#5b6b7c');
      t.setAttribute('font-size', '14');
      t.textContent = 'لا توجد بيانات في هذه الفترة';
      svg.appendChild(t);
      return;
    }

    const ymax = Math.max(maxOf(values, 1), 1);
    const usableW = w - pad * 2;
    const usableH = h - pad * 2;
    const step = values.length === 1 ? 0 : usableW / (values.length - 1);
    const points = values.map((v, i) => {
      const x = pad + step * i;
      const y = pad + usableH - (v / ymax) * usableH;
      return `${x},${y}`;
    }).join(' ');

    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    poly.setAttribute('fill', 'none');
    poly.setAttribute('stroke', color);
    poly.setAttribute('stroke-width', '2.2');
    poly.setAttribute('points', points);
    svg.appendChild(poly);

    values.forEach((v, i) => {
      const x = pad + step * i;
      const y = pad + usableH - (v / ymax) * usableH;
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('cx', String(x));
      c.setAttribute('cy', String(y));
      c.setAttribute('r', values.length > 80 ? '1.5' : '2.5');
      c.setAttribute('fill', color);
      svg.appendChild(c);
    });
  }

  return { drawLineChart: drawLineChart };
})();
