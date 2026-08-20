
(() => {
  'use strict';

  const CARD_ID = 'oryn-perimeter-calibration-card';
  let timer = null;
  let working = false;

  function apiBase() {
    try {
      const saved = localStorage.getItem('orynmotion_tables');
      const activeId = localStorage.getItem('orynmotion_active_table');
      if (!saved || !activeId) return '';
      const data = JSON.parse(saved);
      const table = (data.tables || []).find(t => t.id === activeId);
      if (table && !table.isCurrent && table.url) return table.url.replace(/\/$/, '');
    } catch (_) {}
    return '';
  }

  async function request(path, method='GET', body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(apiBase() + path, options);
    const raw = await response.text();
    let data = {};
    try { data = raw ? JSON.parse(raw) : {}; }
    catch (_) { data = { detail: raw }; }
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    return data;
  }

  function setMessage(text, isError=false) {
    const el = document.getElementById('oryn-pc-message');
    if (!el) return;
    el.textContent = text || '';
    el.classList.toggle('oryn-pc-error', !!isError);
  }

  function setWorking(value) {
    working = value;
    document.querySelectorAll(`#${CARD_ID} button`).forEach(btn => {
      btn.disabled = value;
    });
  }

  async function refreshCalibration() {
    const card = document.getElementById(CARD_ID);
    if (!card) return;

    try {
      // IMPORTANT: this is the actual backend state contract.
      const c = await request('/api/perimeter-calibration');

      const calibrated = !!c.calibrated;
      const active = !!c.active;
      const savedUnits = c.rho_travel_units == null ? null : Number(c.rho_travel_units);
      const effectiveUnits = Number(c.effective_units);
      const currentUnits = Number(c.current_units || 0);

      const badge = document.getElementById('oryn-pc-badge');
      if (badge) {
        badge.textContent = calibrated ? 'CALIBRATED' : 'SOURCE DEFAULT';
        badge.classList.toggle('calibrated', calibrated);
      }

      const idle = document.getElementById('oryn-pc-idle');
      const activeBox = document.getElementById('oryn-pc-active');
      if (idle) idle.style.display = active ? 'none' : '';
      if (activeBox) activeBox.style.display = active ? '' : 'none';

      const saved = document.getElementById('oryn-pc-saved');
      if (saved) {
        saved.textContent = calibrated && Number.isFinite(savedUnits)
          ? `${savedUnits.toFixed(3)} units`
          : `Source ${Number.isFinite(effectiveUnits) ? effectiveUnits.toFixed(3) : '—'} units`;
      }

      const input = document.getElementById('oryn-pc-units');
      if (input && document.activeElement !== input && !active) {
        input.value = calibrated && Number.isFinite(savedUnits) ? savedUnits.toFixed(3) : '';
      }

      const current = document.getElementById('oryn-pc-current');
      if (current) current.textContent = `${currentUnits.toFixed(3)} units`;

      const saveBtn = document.getElementById('oryn-pc-save');
      if (saveBtn) saveBtn.disabled = working || !active || currentUnits < 1;

      const resetBtn = document.getElementById('oryn-pc-reset');
      if (resetBtn) resetBtn.style.display = calibrated && !active ? '' : 'none';

      // Only disable all controls while a command is actually in flight.
      if (!working) {
        card.querySelectorAll('button').forEach(btn => {
          if (btn.id !== 'oryn-pc-save') btn.disabled = false;
        });
        if (saveBtn) saveBtn.disabled = !active || currentUnits < 1;
      }
    } catch (e) {
      setMessage(`Calibration status unavailable: ${e.message || e}`, true);
    }
  }

  async function execute(path, body, success) {
    if (working) return;
    setWorking(true);
    setMessage('');
    try {
      const result = await request(path, 'POST', body);
      setMessage(success instanceof Function ? success(result) : success);
      return result;
    } catch (e) {
      setMessage(e.message || String(e), true);
      return null;
    } finally {
      working = false;
      await refreshCalibration();
    }
  }

  async function start() {
    await execute(
      '/api/perimeter-calibration/start',
      undefined,
      'Calibration started. Use OUT buttons until the ball reaches the exact physical perimeter.'
    );
  }

  async function jog(units) {
    await execute(
      '/api/perimeter-calibration/jog',
      { units, speed: 60 },
      `Jog ${units > 0 ? 'OUT' : 'IN'} ${Math.abs(units)} units complete.`
    );
  }

  async function save() {
    const r = await execute(
      '/api/perimeter-calibration/save',
      undefined,
      data => `Perimeter saved: ${Number(data.rho_travel_units).toFixed(3)} controller units.`
    );
    if (r && Number.isFinite(Number(r.rho_travel_units))) {
      const input = document.getElementById('oryn-pc-units');
      if (input) input.value = Number(r.rho_travel_units).toFixed(3);
    }
  }

  async function update() {
    const input = document.getElementById('oryn-pc-units');
    const units = Number(input?.value);
    if (!Number.isFinite(units) || units <= 0) {
      setMessage('Enter a valid controller-unit travel.', true);
      return;
    }
    await execute(
      '/api/perimeter-calibration/set',
      { units },
      `Perimeter travel updated to ${units.toFixed(3)} units.`
    );
  }

  async function reset() {
    await execute(
      '/api/perimeter-calibration/reset',
      undefined,
      'Original source radial scale restored.'
    );
  }

  function cardMarkup() {
    return `
      <div class="oryn-pc-head">
        <div>
          <h3 class="oryn-pc-title">Perimeter Calibration</h3>
          <div class="oryn-pc-sub">Teach exact Center → Perimeter travel once for this table</div>
        </div>
        <span id="oryn-pc-badge" class="oryn-pc-badge">SOURCE DEFAULT</span>
      </div>

      <div class="oryn-pc-note">
        HOME is rho=0. Start from the physical center, jog OUT to the exact edge,
        then Save. The existing theta, gear and coupling mathematics are not changed.
      </div>

      <div id="oryn-pc-idle">
        <button id="oryn-pc-start" class="oryn-pc-btn primary">
          Start From Current Center
        </button>

        <div class="oryn-pc-row">
          <input id="oryn-pc-units" class="oryn-pc-input"
                 type="number" min="0.001" step="0.001"
                 placeholder="Saved controller units">
          <button id="oryn-pc-update" class="oryn-pc-btn">Update</button>
        </div>

        <div class="oryn-pc-meta">
          <span>Saved travel</span>
          <strong id="oryn-pc-saved">Loading…</strong>
        </div>

        <button id="oryn-pc-reset" class="oryn-pc-btn oryn-pc-reset" style="display:none">
          Reset to Source Default
        </button>
      </div>

      <div id="oryn-pc-active" style="display:none">
        <div class="oryn-pc-current">
          <span>Center → Edge travel</span>
          <strong id="oryn-pc-current">0.000 units</strong>
        </div>

        <div class="oryn-pc-jogs">
          <button class="oryn-pc-btn" data-jog="-0.2">IN 0.2</button>
          <button class="oryn-pc-btn" data-jog="0.2">OUT 0.2</button>
          <button class="oryn-pc-btn" data-jog="1">OUT 1</button>
          <button class="oryn-pc-btn" data-jog="-1">IN 1</button>
          <button class="oryn-pc-btn" data-jog="2">OUT 2</button>
          <button class="oryn-pc-btn" data-jog="5">OUT 5</button>
        </div>

        <button id="oryn-pc-save" class="oryn-pc-btn primary" style="margin-top:10px">
          Save This Physical Position as Perimeter
        </button>
      </div>

      <div id="oryn-pc-message" class="oryn-pc-message"></div>
    `;
  }

  function findPositionCard() {
    const exact = [...document.querySelectorAll('h1,h2,h3,h4,h5,div,span')]
      .find(el => (el.textContent || '').trim() === 'Position');
    if (!exact) return null;

    let node = exact;
    for (let i=0; i<8 && node; i++, node=node.parentElement) {
      const text = (node.textContent || '');
      if (text.includes('Center') && text.includes('Perimeter') && text.includes('Align')) {
        return node;
      }
    }
    return exact.parentElement?.parentElement || null;
  }

  function mount() {
    if (location.pathname !== '/table-control') {
      document.getElementById(CARD_ID)?.remove();
      if (timer) { clearInterval(timer); timer = null; }
      return;
    }

    if (document.getElementById(CARD_ID)) {
      if (!timer) timer = setInterval(refreshCalibration, 800);
      return;
    }

    const positionCard = findPositionCard();
    if (!positionCard || !positionCard.parentElement) return;

    const card = document.createElement('section');
    card.id = CARD_ID;
    card.innerHTML = cardMarkup();

    // Put calibration immediately after Position, matching the intended locked UI.
    positionCard.insertAdjacentElement('afterend', card);

    document.getElementById('oryn-pc-start')?.addEventListener('click', start);
    document.getElementById('oryn-pc-update')?.addEventListener('click', update);
    document.getElementById('oryn-pc-reset')?.addEventListener('click', reset);
    document.getElementById('oryn-pc-save')?.addEventListener('click', save);
    card.querySelectorAll('[data-jog]').forEach(button => {
      button.addEventListener('click', () => jog(Number(button.dataset.jog)));
    });

    refreshCalibration();
    if (!timer) timer = setInterval(refreshCalibration, 800);
  }

  const observer = new MutationObserver(() => mount());
  observer.observe(document.documentElement, { childList:true, subtree:true });

  document.addEventListener('DOMContentLoaded', mount);
  window.addEventListener('popstate', mount);
  setInterval(mount, 1200);
})();
