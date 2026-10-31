// MasterBike Data Pipeline - Frontend Logic
// Versión 2.0 - Consume datos reales desde GET /api/pipeline/status
const API = '';  // mismo origen

let selectedSource = 'ventas';
let isRunning = false;
let pollingInterval = null;
let currentRunData = null;

const SOURCES = [
  { id: 'ventas',     icon: '💰', color: '#3B82F6', label: 'Ventas' },
  { id: 'usuarios',   icon: '👤', color: '#8B5CF6', label: 'Usuarios' },
  { id: 'inventario', icon: '📦', color: '#F59E0B', label: 'Inventario' },
  { id: 'arriendos',  icon: '🚲', color: '#10B981', label: 'Arriendos' },
  { id: 'bicicletas', icon: '🔧', color: '#F97316', label: 'Bicicletas' },
  { id: 'despachos',  icon: '🚚', color: '#0EA5E9', label: 'Despachos' },
];

const STAGE_COLORS = {
  source:         '#3B82F6',
  ingestion:      '#8B5CF6',
  validation:     '#F59E0B',
  transformation: '#F97316',
  database:       '#0EA5E9',
  clean:          '#10B981',
  error:          '#EF4444',
};

// ── Inicialización ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderSourceButtons();
  drawPipeline({ total: 0, validos: 0, errores: 0 }, null);
  loadRuns();
  loadLogs();
  startPolling();
  selectSource('ventas');
});

function startPolling() {
  pollingInterval = setInterval(() => {
    if (!isRunning) {
      refreshStatus();
      loadLogs();
    }
  }, 5000);
}

// ── Source Buttons ────────────────────────────────────────────
function renderSourceButtons() {
  const container = document.getElementById('source-list');
  container.innerHTML = '';
  SOURCES.forEach(src => {
    const btn = document.createElement('button');
    btn.className = `source-btn${selectedSource === src.id ? ' active' : ''}`;
    btn.id = `source-btn-${src.id}`;
    btn.onclick = () => selectSource(src.id);
    btn.innerHTML = `
      <div class="source-icon" style="background:${src.color}22;color:${src.color}">${src.icon}</div>
      <div class="source-info">
        <div class="source-name">${src.label}</div>
        <div class="source-count" id="source-count-${src.id}">Sin datos</div>
      </div>
    `;
    container.appendChild(btn);
  });
}

function selectSource(sourceId) {
  selectedSource = sourceId;
  document.querySelectorAll('.source-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`source-btn-${sourceId}`);
  if (btn) btn.classList.add('active');

  const src = SOURCES.find(s => s.id === sourceId);
  document.getElementById('active-source-badge').textContent = src ? src.label.toUpperCase() : sourceId;

  loadGraphForSource(sourceId);
}

// ── Pipeline Graph (consume /api/pipeline/status) ─────────────
async function loadGraphForSource(source) {
  try {
    const res = await fetch(`${API}/api/pipeline/status?source=${source}`);
    if (!res.ok) {
      drawPipeline({ total: 0, validos: 0, errores: 0 }, null);
      return;
    }
    const statusData = await res.json();

    const totales = {
      total:   statusData.registros_procesados || 0,
      validos: statusData.registros_validos    || 0,
      errores: statusData.registros_error      || 0,
    };

    drawPipeline(totales, statusData);
    updateStatCards(totales, statusData);

  } catch (_) {
    drawPipeline({ total: 0, validos: 0, errores: 0 }, null);
  }
}

// ── Dibujo del grafo SVG ─────────────────────────────────────
function drawPipeline(totales, statusData = null) {
  const svg = document.getElementById('pipeline-svg');

  // Dimensiones del nodo
  const nodeW  = 168;   // ancho del nodo
  const nodeH  = 62;    // alto del nodo (3 líneas de texto)
  const cx     = 330;   // centro horizontal (viewBox 660)

  const etapas = statusData ? statusData.etapas : null;
  const estado = statusData ? statusData.estado : 'SIN_DATOS';
  const hasDatos = totales.total > 0;

  // ── Función para sublabels con datos reales ──────────────────
  function sub(etapa, fallback) {
    if (!etapas || !etapas[etapa]) return fallback;
    const e = etapas[etapa];
    switch (etapa) {
      case 'fuente':
        return hasDatos
          ? `${e.registros} registros · ${statusData.fuente}.json`
          : 'Sin datos cargados';
      case 'ingesta':
        return hasDatos
          ? `${e.registros} registros procesados`
          : 'Sin registros leídos';
      case 'validacion':
        return hasDatos
          ? `✓ ${e.validos} válidos  ✗ ${e.errores} errores`
          : 'Sin validaciones';
      case 'transformacion':
        return hasDatos
          ? `${e.registros} registros transformados`
          : 'Sin transformaciones';
      case 'postgresql':
        return hasDatos
          ? (e.estado === 'guardado' ? '✓ Guardado correctamente' : '✗ Error al guardar')
          : 'Sin datos guardados';
      case 'clean':
        return hasDatos
          ? `${e.registros} registros válidos`
          : '0 registros';
      case 'error':
        return hasDatos
          ? `${e.registros} registros con errores`
          : '0 registros';
      default:
        return fallback;
    }
  }

  function detail(etapa) {
    if (!statusData) return '';
    switch (etapa) {
      case 'fuente':
        return estado !== 'SIN_DATOS' ? `Estado: ${estado}` : '';
      case 'ingesta':
        return hasDatos ? `Duración total: ${statusData.tiempo_ejecucion}s` : '';
      case 'validacion':
        return hasDatos ? `Calidad: ${etapas.validacion.tasa_calidad}%` : '';
      case 'transformacion':
        return hasDatos ? `Registros válidos procesados` : '';
      case 'postgresql':
        return hasDatos ? `clean + error tables` : '';
      case 'clean':
        return hasDatos ? `Tabla ${statusData.fuente}_clean` : '';
      case 'error':
        return hasDatos ? `Tabla ${statusData.fuente}_error` : '';
      default:
        return '';
    }
  }

  // ── Layout de nodos ─────────────────────────────────────────
  const layout = [
    {
      id: 'source', x: cx, y: 15,
      label: 'FUENTE',
      sublabel: sub('fuente', selectedSource.toUpperCase()),
      detail:   detail('fuente'),
      color: STAGE_COLORS.source,
    },
    {
      id: 'ingestion', x: cx, y: 85,
      label: 'INGESTA',
      sublabel: sub('ingesta', 'Sin registros leídos'),
      detail:   detail('ingesta'),
      color: STAGE_COLORS.ingestion,
    },
    {
      id: 'validation', x: cx, y: 155,
      label: 'VALIDACIÓN',
      sublabel: sub('validacion', 'Sin validaciones'),
      detail:   detail('validacion'),
      color: STAGE_COLORS.validation,
    },
    {
      id: 'transformation', x: cx, y: 225,
      label: 'TRANSFORMACIÓN',
      sublabel: sub('transformacion', 'Sin transformaciones'),
      detail:   detail('transformacion'),
      color: STAGE_COLORS.transformation,
    },
    {
      id: 'postgresql', x: cx, y: 315,
      label: 'POSTGRESQL',
      sublabel: sub('postgresql', 'Sin datos guardados'),
      detail:   detail('postgresql'),
      color: STAGE_COLORS.database,
    },
    {
      id: 'clean', x: cx - 110, y: 415,
      label: 'CLEAN DATA',
      sublabel: sub('clean', '0 registros'),
      detail:   detail('clean'),
      color: STAGE_COLORS.clean,
    },
    {
      id: 'error', x: cx + 110, y: 415,
      label: 'ERROR DATA',
      sublabel: sub('error', '0 registros'),
      detail:   detail('error'),
      color: STAGE_COLORS.error,
    },
  ];

  const edges = [
    { from: 'source',         to: 'ingestion',      color: STAGE_COLORS.ingestion,      label: hasDatos ? `${totales.total}` : '' },
    { from: 'ingestion',      to: 'validation',     color: STAGE_COLORS.validation,     label: hasDatos ? `${totales.total}` : '' },
    { from: 'validation',     to: 'transformation', color: STAGE_COLORS.transformation, label: hasDatos ? `${totales.validos} válidos` : '' },
    { from: 'transformation', to: 'postgresql',     color: STAGE_COLORS.database,       label: hasDatos ? `${totales.validos}` : '' },
    { from: 'postgresql',     to: 'clean',          color: STAGE_COLORS.clean,          label: hasDatos ? `${totales.validos}` : '' },
    { from: 'postgresql',     to: 'error',          color: STAGE_COLORS.error,          label: hasDatos ? `${totales.errores} err` : '' },
  ];

  // También hay un edge de validación a error (registros inválidos van directo a error)
  // (no pasan por transformación)
  const extraEdge = {
    from: 'validation', to: 'error',
    color: STAGE_COLORS.error,
    label: hasDatos ? `${totales.errores} errores` : '',
    dashed: true,
  };

  const positions = {};
  layout.forEach(n => { positions[n.id] = n; });

  let svgContent = '';

  // ── Defs ─────────────────────────────────────────────────────
  svgContent += `<defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <marker id="arrow-clean" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="${STAGE_COLORS.clean}" opacity="0.7"/>
    </marker>
    <marker id="arrow-error" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="${STAGE_COLORS.error}" opacity="0.7"/>
    </marker>`;

  layout.forEach(n => {
    svgContent += `
    <linearGradient id="grad-${n.id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   style="stop-color:${n.color};stop-opacity:0.92"/>
      <stop offset="100%" style="stop-color:${n.color};stop-opacity:0.60"/>
    </linearGradient>`;
  });

  svgContent += `</defs>`;

  // ── Fondo del grafo ──────────────────────────────────────────
  svgContent += `<rect x="0" y="0" width="660" height="560" rx="16" fill="#12141f" opacity="0.3"/>`;

  // ── Edges normales ───────────────────────────────────────────
  const allEdges = [...edges, { ...extraEdge }];

  allEdges.forEach(e => {
    const from = positions[e.from];
    const to   = positions[e.to];
    if (!from || !to) return;

    // Desde el borde inferior del nodo origen
    const x1 = from.x;
    const y1 = from.y + nodeH;
    // Al borde superior del nodo destino
    const x2 = to.x;
    const y2 = to.y;

    const midY = (y1 + y2) / 2;
    const animated = hasDatos ? 'active' : '';
    const dashStyle = e.dashed ? 'stroke-dasharray="5 5"' : '';

    svgContent += `
    <path d="M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}"
      class="pipeline-edge ${animated}"
      stroke="${e.color}"
      stroke-opacity="0.55"
      ${dashStyle}/>`;

    // Etiqueta en el centro del edge (si hay datos)
    if (e.label) {
      const labelX = (x1 + x2) / 2;
      const labelY = midY;
      svgContent += `
    <rect x="${labelX - 28}" y="${labelY - 9}" width="56" height="14" rx="4" fill="#12141f" opacity="0.85"/>
    <text x="${labelX}" y="${labelY + 2}" class="edge-label" fill="${e.color}" font-size="9" text-anchor="middle" font-family="Inter,sans-serif" font-weight="600" opacity="0.9">${e.label}</text>`;
    }
  });

  // ── Nodos ────────────────────────────────────────────────────
  layout.forEach(n => {
    const nx     = n.x - nodeW / 2;
    const ny     = n.y;
    const isActive = hasDatos;
    const glowAttr = isActive ? 'filter="url(#glow)"' : '';

    svgContent += `
    <g class="pipeline-node" onclick="nodeClick('${n.id}', event)">
      <!-- Sombra exterior -->
      <rect x="${nx + 2}" y="${ny + 4}" width="${nodeW}" height="${nodeH}" rx="11"
        fill="${n.color}" opacity="${isActive ? 0.18 : 0.06}"/>
      <!-- Rectángulo principal -->
      <rect x="${nx}" y="${ny}" width="${nodeW}" height="${nodeH}" rx="10"
        fill="url(#grad-${n.id})"
        stroke="${n.color}"
        stroke-width="${isActive ? 1.8 : 0.8}"
        stroke-opacity="${isActive ? 0.9 : 0.35}"
        ${glowAttr}/>
      <!-- Línea superior de acento -->
      <rect x="${nx + 8}" y="${ny + 2}" width="${nodeW - 16}" height="2" rx="1"
        fill="${n.color}" opacity="${isActive ? 0.6 : 0.2}"/>
      <!-- Título del nodo -->
      <text x="${n.x}" y="${ny + 20}"
        fill="white"
        font-family="Inter,sans-serif"
        font-size="11"
        font-weight="700"
        text-anchor="middle"
        letter-spacing="0.5">${n.label}</text>
      <!-- Métrica principal -->
      <text x="${n.x}" y="${ny + 37}"
        fill="rgba(255,255,255,${isActive ? 0.92 : 0.45})"
        font-family="Inter,sans-serif"
        font-size="9.5"
        font-weight="500"
        text-anchor="middle">${truncate(n.sublabel, 30)}</text>
      <!-- Detalle secundario -->
      <text x="${n.x}" y="${ny + 52}"
        fill="rgba(255,255,255,${isActive ? 0.55 : 0.28})"
        font-family="'Fira Code',monospace"
        font-size="8.5"
        text-anchor="middle">${truncate(n.detail || '', 28)}</text>
    </g>`;
  });

  // ── Indicador de estado global (esquina superior derecha) ────
  if (statusData && statusData.estado !== 'SIN_DATOS') {
    const estadoColor = statusData.estado === 'COMPLETED' ? '#10B981'
                      : statusData.estado === 'FAILED'    ? '#EF4444'
                      : '#F59E0B';
    const estadoLabel = statusData.estado === 'COMPLETED' ? '✓ COMPLETADO'
                      : statusData.estado === 'FAILED'    ? '✗ FALLIDO'
                      : '⟳ ' + statusData.estado;
    svgContent += `
    <rect x="490" y="8" width="160" height="24" rx="6" fill="${estadoColor}" opacity="0.15"/>
    <rect x="490" y="8" width="160" height="24" rx="6" stroke="${estadoColor}" stroke-width="1" fill="none" opacity="0.4"/>
    <text x="570" y="24" fill="${estadoColor}" font-family="Inter,sans-serif" font-size="10" font-weight="700" text-anchor="middle">${estadoLabel}</text>`;

    // Tiempo de ejecución
    if (statusData.tiempo_ejecucion > 0) {
      svgContent += `
    <text x="570" y="44" fill="rgba(255,255,255,0.45)" font-family="'Fira Code',monospace" font-size="9" text-anchor="middle">⏱ ${statusData.tiempo_ejecucion}s</text>`;
    }
  }

  // Sin datos: mostrar mensaje guía
  if (!hasDatos) {
    svgContent += `
    <text x="330" y="550" fill="rgba(255,255,255,0.25)" font-family="Inter,sans-serif" font-size="11" text-anchor="middle">
      Ejecuta un pipeline para ver datos reales
    </text>`;
  }

  svg.innerHTML = svgContent;
}

// Trunca texto para que no desborde el nodo
function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max - 1) + '…' : str;
}

function nodeClick(nodeId) {
  showToast(`Etapa: ${nodeId.toUpperCase()}`, 'info');
}

// ── Run Pipeline ─────────────────────────────────────────────
async function runPipeline() {
  if (isRunning) return;
  setRunning(true);
  addLog('INFO', 'PIPELINE', `Ejecutando pipeline para: ${selectedSource.toUpperCase()}`);

  try {
    const res = await fetch(`${API}/api/v1/pipeline/run/${selectedSource}`, { method: 'POST' });
    const data = await res.json();

    if (!res.ok) {
      throw new Error((typeof data.detail === 'string' ? data.detail : data.detail?.error_mensaje) || 'La ejecución del pipeline falló');
    }

    currentRunData = data;
    handleRunResult(data);

    // Recargar el gráfico con datos reales del nuevo endpoint
    await loadGraphForSource(selectedSource);
    await loadRuns();
    updateSourceCount(selectedSource);

    showToast(
      `Pipeline ${selectedSource}: ${data.registros_validos} válidos / ${data.registros_error} errores`,
      data.estado === 'COMPLETED' ? 'success' : 'error'
    );
  } catch (err) {
    addLog('ERROR', 'PIPELINE', `Error: ${err.message}`);
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    setRunning(false);
  }
}

async function runAll() {
  if (isRunning) return;
  setRunning(true, true);
  addLog('INFO', 'PIPELINE', 'Ejecutando TODOS los pipelines...');

  try {
    const res = await fetch(`${API}/api/v1/pipeline/run-all`, { method: 'POST' });
    const data = await res.json();

    if (!res.ok) throw new Error((typeof data.detail === 'string' ? data.detail : data.detail?.estado) || 'Error');

    data.resultados?.forEach(r => handleRunResult(r));
    await loadRuns();
    await refreshStatus();

    showToast(
      `Completado: ${data.total_validos} válidos / ${data.total_errores} errores en ${data.duracion_total_segundos}s`,
      'success'
    );
    addLog('SUCCESS', 'PIPELINE', `Todos los pipelines completados en ${data.duracion_total_segundos}s`);
  } catch (err) {
    addLog('ERROR', 'PIPELINE', `Error: ${err.message}`);
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    setRunning(false, true);
    loadGraphForSource(selectedSource);
  }
}

function handleRunResult(data) {
  const level = data.estado === 'COMPLETED' ? 'SUCCESS' : 'ERROR';
  addLog(level, data.fuente?.toUpperCase() || 'PIPELINE',
    `${data.estado} | ${data.total_registros} total | ${data.registros_validos} válidos | ${data.registros_error} errores | ${data.duracion_segundos}s`
  );

  if (data.stages) {
    data.stages.forEach(s => {
      addLog('INFO', s.stage,
        `entrada:${s.registros_entrada} → salida:${s.registros_salida} (${s.duracion_ms}ms)`
      );
    });
  }
}

function setRunning(running, all = false) {
  isRunning = running;
  const btn     = document.getElementById(all ? 'btn-run-all' : 'btn-run');
  const spinner = document.getElementById(all ? 'spinner-all' : 'spinner-run');
  const label   = document.getElementById(all ? 'label-all' : 'label-run');

  if (btn)     btn.disabled = running;
  if (spinner) spinner.style.display = running ? 'block' : 'none';
  if (label)   label.textContent = running
    ? 'Procesando...'
    : (all ? 'Ejecutar Todos' : 'Ejecutar Pipeline');
}

// ── Stats Cards ───────────────────────────────────────────────
function updateStatCards(totales, statusData = null) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set('stat-total',   totales.total);
  set('stat-validos', totales.validos);
  set('stat-errores', totales.errores);

  const rate = totales.total > 0
    ? Math.round(totales.validos / totales.total * 100)
    : 0;
  set('stat-rate', `${rate}%`);

  // Actualizar label de duración si existe el elemento
  const elTime = document.getElementById('stat-time');
  if (elTime && statusData && statusData.tiempo_ejecucion != null) {
    elTime.textContent = `${statusData.tiempo_ejecucion}s`;
  }
}

// ── Refresh Status (sidebar botones) ─────────────────────────
async function refreshStatus() {
  try {
    const res = await fetch(`${API}/api/v1/pipeline/status`);
    if (!res.ok) return;
    const data = await res.json();

    SOURCES.forEach(src => {
      const info = data[src.id];
      if (info) {
        const el = document.getElementById(`source-count-${src.id}`);
        if (el) {
          el.textContent = info.total_runs > 0
            ? `${info.total_registros_procesados} regs · ${info.total_runs} runs`
            : 'Sin ejecutar';
        }
      }
    });

    // Actualizar el gráfico de la fuente activa
    if (selectedSource) {
      await loadGraphForSource(selectedSource);
    }
  } catch (_) {}
}

async function updateSourceCount(source) {
  try {
    const res = await fetch(`${API}/api/v1/pipeline/status`);
    if (!res.ok) return;
    const data = await res.json();
    const info = data[source];
    if (info) {
      const el = document.getElementById(`source-count-${source}`);
      if (el) el.textContent = `${info.total_registros_procesados} regs · ${info.total_runs} runs`;
    }
  } catch (_) {}
}

// ── Runs History ──────────────────────────────────────────────
async function loadRuns() {
  try {
    const res = await fetch(`${API}/api/v1/pipeline/runs?limit=20`);
    if (!res.ok) return;
    const runs = await res.json();
    renderRuns(runs);
  } catch (_) {}
}

function renderRuns(runs) {
  const container = document.getElementById('runs-list');
  if (!container) return;

  if (!runs.length) {
    container.innerHTML = `<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:2rem">Sin ejecuciones aún</div>`;
    return;
  }

  container.innerHTML = runs.map(r => `
    <div class="run-item" onclick="selectRunSource('${r.fuente}')">
      <div class="run-header">
        <span class="run-source">${r.fuente}</span>
        <span class="run-estado estado-${r.estado}">${r.estado}</span>
      </div>
      <div class="run-metrics">
        <span>Total: ${r.total_registros}</span>
        <span class="run-metric-ok">✓ ${r.registros_validos}</span>
        <span class="run-metric-err">✗ ${r.registros_error}</span>
        <span>${r.tasa_exito}%</span>
        <span>${r.duracion_segundos ?? '-'}s</span>
      </div>
      <div style="color:var(--text-muted);font-size:0.68rem;margin-top:2px">${formatDate(r.fecha_inicio)}</div>
    </div>
  `).join('');
}

function selectRunSource(fuente) {
  selectSource(fuente);
  document.querySelector('[data-tab="runs"]')?.click();
}

// ── Logs ──────────────────────────────────────────────────────
async function loadLogs() {
  try {
    const res = await fetch(`${API}/api/v1/monitoring/logs?limit=80`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.logs) {
      const container = document.getElementById('logs-list');
      if (container) renderLogs(data.logs, container);
    }
  } catch (_) {}
}

function renderLogs(logs, container) {
  const existing = container.children.length;
  if (logs.length === 0 && existing === 0) {
    container.innerHTML = `<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:2rem">Ejecuta un pipeline para ver los logs</div>`;
    return;
  }

  container.innerHTML = logs.map(l => `
    <div class="log-entry log-${l.level}">
      <span class="log-time">${l.timestamp?.slice(11, 19) || ''}</span>
      <span class="log-stage">[${l.stage || '?'}]</span>
      ${l.message}
    </div>
  `).join('');

  container.scrollTop = 0;
}

function addLog(level, stage, message) {
  const container = document.getElementById('logs-list');
  if (!container) return;

  if (container.querySelector('div[style]')) container.innerHTML = '';

  const entry = document.createElement('div');
  entry.className = `log-entry log-${level}`;
  const now = new Date().toTimeString().slice(0, 8);
  entry.innerHTML = `<span class="log-time">${now}</span> <span class="log-stage">[${stage}]</span> ${message}`;
  container.insertBefore(entry, container.firstChild);

  while (container.children.length > 150) container.removeChild(container.lastChild);
}

// ── Tabs ──────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tab}`)?.classList.add('active');
    });
  });
}

document.addEventListener('DOMContentLoaded', initTabs);

// ── Toast ─────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// ── Helpers ───────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleString('es-CL', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

// Redibuja al cambiar tamaño de ventana
window.addEventListener('resize', () => {
  loadGraphForSource(selectedSource);
});
