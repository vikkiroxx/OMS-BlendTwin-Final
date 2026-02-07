const API = '/api';

let editor = null;
let chart = null;
let currentTrend = null;

// --- DOM Elements ---
const trendSelect = document.getElementById('trend-select');
const trendInfo = document.getElementById('trend-info');
const paramsContainer = document.getElementById('params-container');
const sqlEditorEl = document.getElementById('sql-editor');
const btnExecute = document.getElementById('btn-execute');
const btnSave = document.getElementById('btn-save');
const btnNew = document.getElementById('btn-new');
const dataGridContainer = document.getElementById('data-grid-container');
const dataGrid = document.getElementById('data-grid');
const resultsError = document.getElementById('results-error');
const resultsEmpty = document.getElementById('results-empty');
const plotContainer = document.getElementById('plot-container');
const plotEmpty = document.getElementById('plot-empty');
const modalNew = document.getElementById('modal-new');
const btnCreate = document.getElementById('btn-create');
const btnCancelNew = document.getElementById('btn-cancel-new');

// --- Init CodeMirror ---
editor = CodeMirror.fromTextArea(sqlEditorEl, {
  mode: 'text/x-sql',
  theme: 'default',
  lineNumbers: true,
  indentUnit: 2,
  lineWrapping: true,
});

// --- API Helpers ---
async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    const msg = typeof d === 'string' ? d : (Array.isArray(d) ? d.map((e) => e?.msg || JSON.stringify(e)).join('; ') : JSON.stringify(data || res.statusText));
    throw new Error(msg);
  }
  return data;
}

// --- Load Trends ---
async function loadTrends() {
  const { trends } = await api('/trends');
  trendSelect.innerHTML = '<option value="">-- Select a trend --</option>';
  trends.forEach((t) => {
    const opt = document.createElement('option');
    opt.value = t.template_id;
    opt.textContent = `${t.trend_code} - ${t.trend_name || t.trend_code}`;
    trendSelect.appendChild(opt);
  });
}

// --- Load Single Trend ---
async function loadTrend(templateId) {
  const trend = await api(`/trends/by-id/${templateId}`);
  currentTrend = trend;
  editor.setValue(trend.sql_template || '');

  // Parameters
  paramsContainer.innerHTML = '';
  if (trend.parameters && trend.parameters.length) {
    trend.parameters
      .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
      .forEach((p) => {
        const div = document.createElement('div');
        div.className = 'param-field';
        div.innerHTML = `
          <label>${p.ui_label || p.param_name}${p.is_required ? ' *' : ''}</label>
          <input type="${p.param_type === 'number' ? 'number' : 'text'}" 
                 data-param="${p.param_name}" 
                 placeholder="${p.default_value || ''}"
                 value="${(p.default_value || '').replace(/"/g, '&quot;')}">
        `;
        paramsContainer.appendChild(div);
      });
  } else {
    paramsContainer.innerHTML = '<p class="muted">No parameters defined</p>';
  }

  trendInfo.textContent = trend.trend_name ? `${trend.trend_name} (${trend.trend_code})` : trend.trend_code;
  btnSave.disabled = false;
}

// --- Get Parameter Values ---
function getParams() {
  const params = {};
  paramsContainer.querySelectorAll('input[data-param]').forEach((inp) => {
    const v = inp.value.trim();
    if (v !== '') {
      params[inp.dataset.param] = inp.type === 'number' ? parseFloat(v) : v;
    }
  });
  return params;
}

// --- Execute ---
async function execute() {
  const sql = editor.getValue();
  if (!sql.trim()) {
    showError('Please enter SQL');
    return;
  }

  const params = getParams();
  resultsError.classList.add('hidden');
  resultsEmpty.classList.add('hidden');
  dataGridContainer.classList.add('hidden');

  try {
    const result = await api('/execute', {
      method: 'POST',
      body: JSON.stringify({ sql, params }),
    });

    if (result.error) {
      showError(result.error);
      return;
    }

    renderTable(result.columns, result.rows);
    renderPlot(result.columns, result.rows);
    dataGridContainer.classList.remove('hidden');
    plotEmpty.classList.add('hidden');
  } catch (e) {
    showError(e.message);
  }
}

function showError(msg) {
  resultsError.textContent = msg;
  resultsError.classList.remove('hidden');
  resultsEmpty.classList.add('hidden');
  dataGridContainer.classList.add('hidden');
}

// --- Render Table ---
function renderTable(columns, rows) {
  let html = '<thead><tr>';
  columns.forEach((c) => (html += `<th>${escapeHtml(c)}</th>`));
  html += '</tr></thead><tbody>';
  rows.forEach((row) => {
    html += '<tr>';
    columns.forEach((col) => {
      const val = row[col];
      html += `<td>${val != null ? escapeHtml(String(val)) : ''}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody>';
  dataGrid.innerHTML = html;
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

// --- Render Plot ---
function renderPlot(columns, rows) {
  const cyclenoIdx = columns.findIndex((c) => c.toLowerCase() === 'cycleno');
  const valueIdx = columns.findIndex((c) => c.toLowerCase() === 'value');
  const seriesIdx = columns.findIndex((c) => c.toLowerCase() === 'series');

  if (cyclenoIdx < 0 || valueIdx < 0 || seriesIdx < 0) {
    if (chart) chart.destroy();
    return;
  }

  const seriesMap = {};
  rows.forEach((row) => {
    const s = String(row[seriesIdx]);
    if (!seriesMap[s]) seriesMap[s] = { x: [], y: [] };
    seriesMap[s].x.push(Number(row[cyclenoIdx]));
    seriesMap[s].y.push(Number(row[valueIdx]));
  });

  const datasets = Object.entries(seriesMap).map(([label, d], i) => ({
    label,
    data: d.x.map((x, j) => ({ x, y: d.y[j] })),
    borderColor: getColor(i),
    backgroundColor: getColor(i) + '40',
    fill: false,
    tension: 0.2,
  }));

  const cfg = currentTrend?.plot_config || {};
  const ctx = document.getElementById('plot-canvas').getContext('2d');

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: !!cfg.title, text: cfg.title || 'Trend' },
        legend: { position: 'top' },
      },
      scales: {
        x: {
          title: { display: true, text: cfg.x_label || 'Cycle' },
          type: 'linear',
        },
        y: {
          title: { display: true, text: cfg.y_label || 'Value' },
        },
      },
    },
  });
}

function getColor(i) {
  const colors = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#a371f7', '#79c0ff'];
  return colors[i % colors.length];
}

// --- Save ---
async function save() {
  if (!currentTrend) return;
  const sql = editor.getValue();
  try {
    await api(`/trends/${currentTrend.template_id}`, {
      method: 'PUT',
      body: JSON.stringify({ sql_template: sql }),
    });
    alert('Saved successfully');
  } catch (e) {
    alert('Save failed: ' + e.message);
  }
}

// --- New Trend Modal ---
function showNewModal() {
  modalNew.classList.remove('hidden');
  document.getElementById('new-trend-code').value = '';
  document.getElementById('new-trend-name').value = '';
  document.getElementById('new-sql-template').value = 'SELECT cycleno, value, series FROM your_table WHERE blendid = :blendid';
}

function hideNewModal() {
  modalNew.classList.add('hidden');
}

async function createTrend() {
  const code = document.getElementById('new-trend-code').value.trim();
  const name = document.getElementById('new-trend-name').value.trim();
  const sql = document.getElementById('new-sql-template').value.trim();

  if (!code || !name || !sql) {
    alert('Please fill all fields');
    return;
  }

  try {
    await api('/trends', {
      method: 'POST',
      body: JSON.stringify({ trend_code: code, trend_name: name, sql_template: sql }),
    });
    hideNewModal();
    await loadTrends();
    alert('Trend created successfully');
  } catch (e) {
    alert('Create failed: ' + e.message);
  }
}

// --- Event Listeners ---
trendSelect.addEventListener('change', async () => {
  const id = trendSelect.value;
  if (!id) {
    currentTrend = null;
    editor.setValue('');
    paramsContainer.innerHTML = '<p class="muted">Select a trend to load parameters</p>';
    btnSave.disabled = true;
    return;
  }
  await loadTrend(id);
});

btnExecute.addEventListener('click', execute);
btnSave.addEventListener('click', save);
btnNew.addEventListener('click', showNewModal);
btnCancelNew.addEventListener('click', hideNewModal);
btnCreate.addEventListener('click', createTrend);

// --- Init ---
loadTrends().catch((e) => {
  console.error(e);
  trendSelect.innerHTML = '<option value="">Failed to load trends</option>';
});
