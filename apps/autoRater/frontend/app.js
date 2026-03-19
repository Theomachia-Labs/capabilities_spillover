// State
let models = [];
let currentResult = null;
let activeUncertaintyType = 1;

// DOM refs
const costTotal = document.getElementById('cost-total');
const arxivInput = document.getElementById('arxiv-url');
const arxivUrlsInput = document.getElementById('arxiv-urls');
const attemptCountInput = document.getElementById('attempt-count');
const modelCheckboxes = document.getElementById('model-checkboxes');
const rateBtn = document.getElementById('rate-btn');
const runReliabilityBtn = document.getElementById('run-reliability-btn');
const progressPanel = document.getElementById('progress-panel');
const progressBars = document.getElementById('progress-bars');
const statusLog = document.getElementById('status-log');
const resultsPanel = document.getElementById('results-panel');
const resultsContent = document.getElementById('results-content');
const historyList = document.getElementById('history-list');

// Tab switching
const modeTabs = document.querySelectorAll('.mode-tab');
const singleModeUi = document.getElementById('single-mode-ui');
const reliabilityModeUi = document.getElementById('reliability-mode-ui');
const reliabilityHistoryUi = document.getElementById('reliability-history-ui');
const modelsSection = document.querySelector('.models-section');
const sectionsSelection = document.getElementById('sections-selection');
const calibrationModeUi = document.getElementById('calibration-mode-ui');

modeTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const mode = tab.dataset.mode;
    modeTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    singleModeUi.classList.add('hidden');
    reliabilityModeUi.classList.add('hidden');
    reliabilityHistoryUi.classList.add('hidden');
    calibrationModeUi.classList.add('hidden');
    rateBtn.classList.add('hidden');
    runReliabilityBtn.classList.add('hidden');
    modelsSection.classList.add('hidden');
    sectionsSelection.classList.add('hidden');

    if (mode === 'single') {
      singleModeUi.classList.remove('hidden');
      rateBtn.classList.remove('hidden');
      modelsSection.classList.remove('hidden');
      sectionsSelection.classList.remove('hidden');
    } else if (mode === 'reliability') {
      reliabilityModeUi.classList.remove('hidden');
      runReliabilityBtn.classList.remove('hidden');
      modelsSection.classList.remove('hidden');
      sectionsSelection.classList.remove('hidden');
    } else if (mode === 'calibration') {
      calibrationModeUi.classList.remove('hidden');
      loadCalibrationRunPicker();
    } else {
      reliabilityHistoryUi.classList.remove('hidden');
    }
  });
});

const relHistorySelect = document.getElementById('rel-history-select');
relHistorySelect.addEventListener('change', async (e) => {
  if (!e.target.value) return;
  loadReliabilityResult(e.target.value);
});

// API key management
const openrouterKeyInput = document.getElementById('openrouter-key');
const geminiKeyInput = document.getElementById('gemini-key');
const saveKeysBtn = document.getElementById('save-keys');

function loadKeys() {
  openrouterKeyInput.value = localStorage.getItem('openrouter_key') || '';
  geminiKeyInput.value = localStorage.getItem('gemini_key') || '';
}

saveKeysBtn.addEventListener('click', () => {
  localStorage.setItem('openrouter_key', openrouterKeyInput.value);
  localStorage.setItem('gemini_key', geminiKeyInput.value);
  saveKeysBtn.textContent = 'Saved!';
  setTimeout(() => saveKeysBtn.textContent = 'Save Keys', 1500);
});

// List Gemini models
const listGeminiBtn = document.getElementById('list-gemini-models');
const geminiModelsList = document.getElementById('gemini-models-list');

listGeminiBtn.addEventListener('click', async () => {
  const key = geminiKeyInput.value || localStorage.getItem('gemini_key') || '';
  if (!key) return alert('Enter a Gemini API key first');
  listGeminiBtn.textContent = 'Loading...';
  listGeminiBtn.disabled = true;
  try {
    const res = await fetch(`/api/gemini-models?key=${encodeURIComponent(key)}`);
    const data = await res.json();
    if (data.error) {
      geminiModelsList.innerHTML = `<p class="error-msg">${escapeHtml(data.error)}</p>`;
    } else {
      geminiModelsList.innerHTML = '<h4 style="margin:8px 0 4px;color:#aaa">Available Gemini Models (generateContent)</h4>' +
        '<div style="max-height:200px;overflow-y:auto;font-size:13px;font-family:monospace;color:#ccc">' +
        data.map(m => `<div style="padding:2px 0">${escapeHtml(m.id)} <span style="color:#666">- ${escapeHtml(m.displayName)}</span></div>`).join('') +
        '</div>';
    }
    geminiModelsList.classList.remove('hidden');
  } catch (err) {
    geminiModelsList.innerHTML = `<p class="error-msg">${err.message}</p>`;
    geminiModelsList.classList.remove('hidden');
  }
  listGeminiBtn.textContent = 'List Gemini Models';
  listGeminiBtn.disabled = false;
});

// Load models
async function loadModels() {
  const res = await fetch('/api/models');
  models = await res.json();
  renderModelCheckboxes();
}

function renderModelCheckboxes() {
  const groups = {};

  models.forEach(m => {
    let group;
    if (m.provider === 'gemini') {
      group = 'Google';
    } else {
      if (m.id.startsWith('claude')) group = 'Anthropic';
      else if (m.id.startsWith('gpt') || m.id.startsWith('o3')) group = 'OpenAI';
      else if (m.id.startsWith('grok')) group = 'xAI';
      else group = 'Other';
    }
    if (!groups[group]) groups[group] = [];
    groups[group].push(m);
  });

  modelCheckboxes.innerHTML = '';
  for (const [groupName, groupModels] of Object.entries(groups)) {
    const div = document.createElement('div');
    div.className = 'provider-group';
    div.innerHTML = `<h4>${groupName}</h4>`;
    groupModels.forEach(m => {
      const label = document.createElement('label');
      label.className = 'model-checkbox';
      
      let toggleHtml = '';
      if (m.provider === 'gemini') {
        const useOR = localStorage.getItem(`use_or_${m.id}`) === 'true';
        toggleHtml = `
          <div class="model-toggle" onclick="event.stopPropagation()">
            <input type="checkbox" class="or-toggle" id="or-toggle-${m.id}" data-model-id="${m.id}" ${useOR ? 'checked' : ''} />
            <label for="or-toggle-${m.id}" style="font-size:10px;color:#888;margin-left:4px;cursor:pointer">OR</label>
          </div>
        `;
      }

      label.innerHTML = `
        <input type="checkbox" value="${m.id}" />
        <span style="flex:1">${m.displayName}</span>
        ${toggleHtml}
        <span class="price">$${m.inputPricePer1M}/$${m.outputPricePer1M}</span>
      `;
      div.appendChild(label);
    });
    modelCheckboxes.appendChild(div);
  }
}

// Delegate OR toggle changes
modelCheckboxes.addEventListener('change', (e) => {
  if (e.target.classList.contains('or-toggle')) {
    const modelId = e.target.dataset.modelId;
    localStorage.setItem(`use_or_${modelId}`, e.target.checked);
  }
});

function getSelectedModels() {
  return [...modelCheckboxes.querySelectorAll('.model-checkbox > input[type="checkbox"]:checked')]
    .map(cb => {
      const id = cb.value;
      const model = models.find(m => m.id === id);
      const toggle = cb.parentElement.querySelector('.or-toggle');
      const useOpenRouter = toggle && toggle.checked;
      return {
        id,
        providerPreference: (model && model.provider === 'gemini') ? (useOpenRouter ? 'openrouter' : 'gemini') : undefined
      };
    });
}

function getSelectedSections() {
  return [...document.querySelectorAll('#section-checkboxes input[type="checkbox"]:checked')]
    .map(cb => cb.value);
}

function getMaxSectionChars() {
  return parseInt(document.getElementById('max-section-chars').value) || 8000;
}

function getApiKeys() {
  return {
    openrouterKey: localStorage.getItem('openrouter_key') || '',
    geminiKey: localStorage.getItem('gemini_key') || '',
  };
}

async function readSSEStream(response, progressState) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let eventType = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7);
      } else if (line.startsWith('data: ') && eventType) {
        try {
          const data = JSON.parse(line.slice(6));
          handleSSEEvent(eventType, data, progressState);
        } catch {}
        eventType = '';
      }
    }
  }
}

// Cost ticker
async function updateCost() {
  try {
    const res = await fetch('/api/costs');
    const data = await res.json();
    costTotal.textContent = data.total.toFixed(6);
  } catch {}
}

// Rate paper
rateBtn.addEventListener('click', startRating);
runReliabilityBtn.addEventListener('click', startReliabilityTest);

async function startRating() {
  const arxivUrl = arxivInput.value.trim();
  if (!arxivUrl) return alert('Please enter an arxiv URL');

  const selectedModels = getSelectedModels();
  if (selectedModels.length === 0) return alert('Please select at least one model');

  rateBtn.disabled = true;
  progressPanel.classList.remove('hidden');
  resultsPanel.classList.add('hidden');
  progressBars.innerHTML = '';
  statusLog.innerHTML = '';

  // Init progress bars
  const progressState = {};
  selectedModels.forEach(mInput => {
    const id = mInput.id;
    const model = models.find(m => m.id === id);
    const name = model ? model.displayName : id;
    progressState[name] = { completed: 0, total: 4 };
    const div = document.createElement('div');
    div.className = 'progress-item';
    div.id = `progress-${id}`;
    div.innerHTML = `
      <div class="label">
        <span>${name}</span>
        <span class="count">0/4</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:0%"></div></div>
    `;
    progressBars.appendChild(div);
  });

  const body = {
    arxivUrl,
    modelIds: selectedModels,
    selectedSections: getSelectedSections(),
    maxSectionChars: getMaxSectionChars(),
    ...getApiKeys(),
  };

  try {
    const response = await fetch('/api/rate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    await readSSEStream(response, progressState);
  } catch (err) {
    addStatusLog(`Error: ${err.message}`, true);
  }

  rateBtn.disabled = false;
  updateCost();
  loadHistory();
}

async function startReliabilityTest() {
  const urlsText = arxivUrlsInput.value.trim();
  if (!urlsText) return alert('Please enter at least one arxiv URL');
  const arxivUrls = urlsText.split('\n').map(u => u.trim()).filter(Boolean);
  const attempts = parseInt(attemptCountInput.value);

  const selectedModels = getSelectedModels();
  if (selectedModels.length === 0) return alert('Please select at least one model');

  runReliabilityBtn.disabled = true;
  progressPanel.classList.remove('hidden');
  resultsPanel.classList.add('hidden');
  progressBars.innerHTML = '';
  statusLog.innerHTML = '';

  // Init overall progress bar
  const div = document.createElement('div');
  div.className = 'progress-item';
  div.id = `progress-overall`;
  div.innerHTML = `
    <div class="label">
      <span>Overall Progress</span>
      <span class="count">0/0</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" style="width:0%"></div></div>
  `;
  progressBars.appendChild(div);

  const body = {
    arxivUrls,
    modelIds: selectedModels,
    attempts,
    selectedSections: getSelectedSections(),
    maxSectionChars: getMaxSectionChars(),
    ...getApiKeys(),
  };

  try {
    const response = await fetch('/api/reliability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    await readSSEStream(response);
  } catch (err) {
    addStatusLog(`Error: ${err.message}`, true);
  }

  runReliabilityBtn.disabled = false;
  updateCost();
  loadHistory();
}

function handleSSEEvent(event, data, progressState) {
  switch (event) {
    case 'status':
      addStatusLog(data.message);
      break;
    case 'progress': {
      const modelName = data.model;
      if (progressState && progressState[modelName]) {
        progressState[modelName].completed = data.completed;
      }
      // Find progress bar by model name
      const items = progressBars.querySelectorAll('.progress-item');
      items.forEach(item => {
        const label = item.querySelector('.label span:first-child');
        if (label && label.textContent === modelName) {
          const pct = (data.completed / data.total) * 100;
          item.querySelector('.count').textContent = `${data.completed}/${data.total}`;
          item.querySelector('.progress-fill').style.width = `${pct}%`;
        }
      });
      break;
    }
    case 'overall-progress': {
      const item = document.getElementById('progress-overall');
      if (item) {
        const pct = (data.completed / data.total) * 100;
        item.querySelector('.count').textContent = `${data.completed}/${data.total}`;
        item.querySelector('.progress-fill').style.width = `${pct}%`;
      }
      break;
    }
    case 'error':
      addStatusLog(`Error: ${data.model ? data.model + ': ' : ''}${data.message}`, true);
      break;
    case 'complete':
      currentResult = data;
      if (data.type === 'reliability') {
        renderReliabilityResults(data);
      } else {
        renderResults(data);
      }
      break;
  }
}

function addStatusLog(message, isError = false) {
  const div = document.createElement('div');
  div.textContent = `${new Date().toLocaleTimeString()} ${message}`;
  if (isError) div.className = 'error-msg';
  statusLog.appendChild(div);
  statusLog.scrollTop = statusLog.scrollHeight;
}

// Results rendering
const DIMENSIONS = [
  { id: 'direct_capability_impact', name: 'Direct Capability Impact' },
  { id: 'technical_transferability', name: 'Technical Transferability' },
  { id: 'audience_venue_exposure', name: 'Audience & Venue Exposure' },
  { id: 'marginal_contribution', name: 'Marginal Contribution' },
  { id: 'strategic_leverage', name: 'Strategic Leverage' },
];

const UNCERTAINTY_LABELS = [
  'Type 1: Uncertainty (0-1)',
  'Type 2: Probability off by 2+',
  'Type 3: Plausible range',
  'Type 4: Evidence level',
];

function renderResults(result) {
  resultsPanel.classList.remove('hidden');
  activeUncertaintyType = 1;

  const modelNames = Object.keys(result.modelResults);

  let html = `
    <div class="results-header">
      <h2>${result.paperTitle}</h2>
      <div class="paper-info">${result.paperAuthors.join(', ')} | arxiv: ${result.arxivId} | Cost: $${result.totalCost.toFixed(4)}</div>
    </div>
    <div class="uncertainty-tabs">
      ${UNCERTAINTY_LABELS.map((label, i) =>
        `<button class="uncertainty-tab ${i === 0 ? 'active' : ''}" data-type="${i + 1}">${label}</button>`
      ).join('')}
    </div>
  `;

  // Build table for each uncertainty type (show active one)
  for (let uType = 1; uType <= 4; uType++) {
    html += `<div class="uncertainty-table" data-type="${uType}" style="${uType !== 1 ? 'display:none' : ''}">`;
    html += `<table class="results-table">
      <thead>
        <tr>
          <th>Dimension</th>
          ${modelNames.map(m => `<th>${m}</th>`).join('')}
        </tr>
      </thead>
      <tbody>`;

    for (const dim of DIMENSIONS) {
      html += `<tr><td>${dim.name}</td>`;
      for (const mName of modelNames) {
        const uResults = result.modelResults[mName].uncertaintyResults[uType];
        if (uResults && uResults.ratings && uResults.ratings[dim.id]) {
          const r = uResults.ratings[dim.id];
          const score = r.score ?? '?';
          const unc = formatUncertainty(r.uncertainty, uType);
          html += `<td class="score-cell score-${score}">
            <span class="score">${score}</span>
            <span class="uncertainty">${unc}</span>
            <div class="justification">${escapeHtml(r.justification || '')}</div>
          </td>`;
        } else {
          html += `<td class="score-cell">-</td>`;
        }
      }
      html += `</tr>`;
    }

    html += `</tbody></table>`;

    // Justification summaries
    html += `<div class="justification-summaries">`;
    for (const mName of modelNames) {
      const uResults = result.modelResults[mName].uncertaintyResults[uType];
      if (uResults) {
        const usage = uResults.tokenUsage;
        html += `<div class="summary-card">
          <h4>${mName} <span style="color:#666;font-weight:normal;font-size:12px">(${usage.input} in / ${usage.output} out / $${usage.cost.toFixed(4)})</span></h4>
          <p>${escapeHtml(uResults.justificationSummary)}</p>
        </div>`;
      }
    }
    html += `</div></div>`;
  }

  resultsContent.innerHTML = html;

  // Tab switching
  resultsContent.querySelectorAll('.uncertainty-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const type = tab.dataset.type;
      resultsContent.querySelectorAll('.uncertainty-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      resultsContent.querySelectorAll('.uncertainty-table').forEach(t => {
        t.style.display = t.dataset.type === type ? '' : 'none';
      });
    });
  });
}

function renderReliabilityResults(result) {
  resultsPanel.classList.remove('hidden');
  
  const modelNames = Object.keys(result.modelResults);
  const paperIds = result.papers.map(p => p.arxivId);
  let activePaperId = paperIds[0];
  let showUncertaintyMode = false;
  let analysisStats = {};

  function computeStats() {
    const stats = {
      modelStats: {},
      uTypeStats: {},
      modelDimAvg: {},
      modelUncStats: {},
      uTypeUncStats: {},
      modelDimUncAvg: {},
      dimUncStats: {}
    };

    for (const mName of modelNames) {
      stats.modelStats[mName] = { scoreSum: 0, scoreCount: 0, withinVarSum: 0, withinVarCount: 0 };
      stats.modelDimAvg[mName] = {};
      stats.modelUncStats[mName] = { uncSum: 0, uncCount: 0 };
      stats.modelDimUncAvg[mName] = {};
      for (const dim of DIMENSIONS) {
        stats.modelDimAvg[mName][dim.id] = { sum: 0, count: 0 };
        stats.modelDimUncAvg[mName][dim.id] = { sum: 0, count: 0 };
      }
    }
    for (let uType = 1; uType <= 4; uType++) {
      stats.uTypeStats[uType] = { scoreSum: 0, scoreCount: 0, withinVarSum: 0, withinVarCount: 0, betweenScores: [] };
      stats.uTypeUncStats[uType] = { uncSum: 0, uncCount: 0 };
    }
    for (const dim of DIMENSIONS) {
      stats.dimUncStats[dim.id] = { sum: 0, count: 0 };
    }

    for (let uType = 1; uType <= 4; uType++) {
      for (const paperId of paperIds) {
        for (const dim of DIMENSIONS) {
          const modelAveragesForDim = [];
          for (const mName of modelNames) {
            const attempts = result.modelResults[mName].paperResults[paperId]?.uncertaintyResults[uType] || [];
            
            // Score stats
            const scores = attempts.map(a => a.ratings[dim.id]?.score).filter(s => typeof s === 'number');
            if (scores.length > 0) {
              const avgScore = scores.reduce((a,b) => a+b, 0) / scores.length;
              stats.modelStats[mName].scoreSum += avgScore;
              stats.modelStats[mName].scoreCount += 1;
              stats.uTypeStats[uType].scoreSum += avgScore;
              stats.uTypeStats[uType].scoreCount += 1;
              stats.modelDimAvg[mName][dim.id].sum += avgScore;
              stats.modelDimAvg[mName][dim.id].count += 1;
              
              modelAveragesForDim.push(avgScore);
              
              if (scores.length > 1) {
                const variance = scores.reduce((acc, s) => acc + Math.pow(s - avgScore, 2), 0) / scores.length;
                stats.uTypeStats[uType].withinVarSum += variance;
                stats.uTypeStats[uType].withinVarCount += 1;
                stats.modelStats[mName].withinVarSum += variance;
                stats.modelStats[mName].withinVarCount += 1;
              }
            }

            // Uncertainty stats
            const uncertainties = attempts.map(a => a.ratings[dim.id]?.uncertainty).filter(u => u !== undefined && u !== null);
            if (uncertainties.length > 0) {
               const mags = uncertainties.map(u => {
                  if (typeof u === 'number') return u;
                  if (Array.isArray(u) && u.length === 2) return (u[1] - u[0]);
                  if (typeof u === 'string') {
                    const lower = u.toLowerCase();
                    if (lower.includes('strong direct')) return 0.2;
                    if (lower.includes('some indirect')) return 0.6;
                    if (lower.includes('weak') || lower.includes('no evidence')) return 0.9;
                    return 0.5;
                  }
                  return 0;
               });
               const avgMag = mags.reduce((a,b) => a+b, 0) / mags.length;
               
               stats.modelUncStats[mName].uncSum += avgMag;
               stats.modelUncStats[mName].uncCount += 1;
               stats.uTypeUncStats[uType].uncSum += avgMag;
               stats.uTypeUncStats[uType].uncCount += 1;
               stats.modelDimUncAvg[mName][dim.id].sum += avgMag;
               stats.modelDimUncAvg[mName][dim.id].count += 1;
               stats.dimUncStats[dim.id].sum += avgMag;
               stats.dimUncStats[dim.id].count += 1;
            }
          }
          if (modelAveragesForDim.length > 1) {
            const overallAvg = modelAveragesForDim.reduce((a,b)=>a+b,0) / modelAveragesForDim.length;
            const betweenVar = modelAveragesForDim.reduce((acc, s) => acc + Math.pow(s - overallAvg, 2), 0) / modelAveragesForDim.length;
            stats.uTypeStats[uType].betweenScores.push(betweenVar);
          }
        }
      }
    }
    return stats;
  }

  function buildAnalysisHtml() {
    let html = `<div class="analysis-section" style="margin-top: 30px; padding: 20px; background: #2a2a2a; border: 1px solid #444; border-radius: 8px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin-top:0; color: #4ecdc4; margin-bottom: 0;">Comparisons & Analysis (Across All Papers)</h3>
        <label style="color: #ccc; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; background: #1e1e1e; padding: 8px 12px; border-radius: 6px; border: 1px solid #555;">
          <input type="checkbox" id="analysis-mode-toggle" ${showUncertaintyMode ? 'checked' : ''}>
          Analyze Stated Uncertainty Instead of Scores
        </label>
      </div>`;
      
    html += `<div id="charts-container" style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div style="background: #1e1e1e; padding: 15px; border-radius: 8px; display:flex; justify-content:center;"><canvas id="chart-1" style="max-height: 350px;"></canvas></div>
      <div style="background: #1e1e1e; padding: 15px; border-radius: 8px; display:flex; justify-content:center;"><canvas id="chart-2" style="max-height: 350px;"></canvas></div>
      <div style="background: #1e1e1e; padding: 15px; border-radius: 8px; display:flex; justify-content:center;"><canvas id="chart-3" style="max-height: 350px;"></canvas></div>
      <div style="background: #1e1e1e; padding: 15px; border-radius: 8px; display:flex; justify-content:center;"><canvas id="chart-4" style="max-height: 350px;"></canvas></div>
    </div>`;
    
    html += `</div>`;
    return html;
  }

  function renderCharts(stats) {
    const colors = ['#4ecdc4', '#ff6b6b', '#ffe66d', '#1a535c', '#8ca8d9', '#f0a202'];
    
    if (window.myCharts) {
      window.myCharts.forEach(c => c.destroy());
    }
    window.myCharts = [];

    const ctx1 = document.getElementById('chart-1');
    const ctx2 = document.getElementById('chart-2');
    const ctx3 = document.getElementById('chart-3');
    const ctx4 = document.getElementById('chart-4');

    if (!showUncertaintyMode) {
      // MODE: SCORES
      if (ctx1) {
        const datasets = modelNames.map((mName, i) => {
          return {
            label: mName,
            data: DIMENSIONS.map(dim => {
              const d = stats.modelDimAvg[mName][dim.id];
              return d.count > 0 ? d.sum / d.count : 0;
            }),
            backgroundColor: colors[i % colors.length] + '40',
            borderColor: colors[i % colors.length],
            pointBackgroundColor: colors[i % colors.length],
          };
        });

        window.myCharts.push(new Chart(ctx1, {
          type: 'radar',
          data: { labels: DIMENSIONS.map(d => d.name), datasets: datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: { display: true, text: 'Average Score by Dimension & Model', color: '#fff' },
              legend: { labels: { color: '#ccc' } }
            },
            scales: {
              r: { min: 0, max: 5, grid: { color: '#555' }, pointLabels: { color: '#ccc', font: { size: 11 } }, ticks: { backdropColor: 'transparent', color: '#888' } }
            }
          }
        }));
      }

      if (ctx2) {
        const data = [1, 2, 3, 4].map(uType => {
          const d = stats.uTypeStats[uType];
          return d.scoreCount > 0 ? d.scoreSum / d.scoreCount : 0;
        });

        window.myCharts.push(new Chart(ctx2, {
          type: 'bar',
          data: {
            labels: ['Type 1 (0-1)', 'Type 2 (Off by 2+)', 'Type 3 (Range)', 'Type 4 (Evidence)'],
            datasets: [{ label: 'Avg Rating Score', data: data, backgroundColor: '#ff6b6b' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Average Rating Score by Uncertainty Type (Bias Check)', color: '#fff' }, legend: { display: false } },
            scales: { y: { min: 0, max: 5, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc' } } }
          }
        }));
      }

      if (ctx3) {
        const data = modelNames.map(mName => {
          const d = stats.modelStats[mName];
          return d.withinVarCount > 0 ? d.withinVarSum / d.withinVarCount : 0;
        });

        window.myCharts.push(new Chart(ctx3, {
          type: 'bar',
          data: {
            labels: modelNames,
            datasets: [{ label: 'Avg Variance across Attempts', data: data, backgroundColor: '#ffe66d' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Self-Consistency (Within-Model Score Variance)', color: '#fff' }, legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc' } } }
          }
        }));
      }

      if (ctx4) {
        const data = [1, 2, 3, 4].map(uType => {
          const scores = stats.uTypeStats[uType].betweenScores;
          return scores.length > 0 ? scores.reduce((a,b)=>a+b,0)/scores.length : 0;
        });

        window.myCharts.push(new Chart(ctx4, {
          type: 'bar',
          data: {
            labels: ['Type 1', 'Type 2', 'Type 3', 'Type 4'],
            datasets: [{ label: 'Avg Inter-Model Variance', data: data, backgroundColor: '#4ecdc4' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Inter-Model Agreement by Uncertainty Type', color: '#fff' }, legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc' } } }
          }
        }));
      }

    } else {
      // MODE: UNCERTAINTY
      if (ctx1) {
        const datasets = modelNames.map((mName, i) => {
          return {
            label: mName,
            data: DIMENSIONS.map(dim => {
              const d = stats.modelDimUncAvg[mName][dim.id];
              return d.count > 0 ? d.sum / d.count : 0;
            }),
            backgroundColor: colors[i % colors.length] + '40',
            borderColor: colors[i % colors.length],
            pointBackgroundColor: colors[i % colors.length],
          };
        });

        window.myCharts.push(new Chart(ctx1, {
          type: 'radar',
          data: { labels: DIMENSIONS.map(d => d.name), datasets: datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Average Stated Uncertainty by Dimension & Model', color: '#fff' }, legend: { labels: { color: '#ccc' } } },
            scales: { r: { beginAtZero: true, grid: { color: '#555' }, pointLabels: { color: '#ccc', font: { size: 11 } }, ticks: { backdropColor: 'transparent', color: '#888' } } }
          }
        }));
      }

      if (ctx2) {
        const data = modelNames.map(mName => {
          const d = stats.modelUncStats[mName];
          return d.uncCount > 0 ? d.uncSum / d.uncCount : 0;
        });

        window.myCharts.push(new Chart(ctx2, {
          type: 'bar',
          data: {
            labels: modelNames,
            datasets: [{ label: 'Avg Uncertainty', data: data, backgroundColor: '#8ca8d9' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Overall Stated Uncertainty by Model', color: '#fff' }, legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc' } } }
          }
        }));
      }

      if (ctx3) {
        const data = DIMENSIONS.map(dim => {
          const d = stats.dimUncStats[dim.id];
          return d.count > 0 ? d.sum / d.count : 0;
        });

        window.myCharts.push(new Chart(ctx3, {
          type: 'bar',
          data: {
            labels: DIMENSIONS.map(d => d.name),
            datasets: [{ label: 'Avg Uncertainty', data: data, backgroundColor: '#1a535c' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Average Stated Uncertainty by Dimension', color: '#fff' }, legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc', maxRotation: 45, minRotation: 45 } } }
          }
        }));
      }

      if (ctx4) {
        const data = [1, 2, 3, 4].map(uType => {
          const d = stats.uTypeUncStats[uType];
          return d.uncCount > 0 ? d.uncSum / d.uncCount : 0;
        });

        window.myCharts.push(new Chart(ctx4, {
          type: 'bar',
          data: {
            labels: ['Type 1 (0-1)', 'Type 2 (Prob)', 'Type 3 (Range size)', 'Type 4 (Evidence)'],
            datasets: [{ label: 'Avg Uncertainty Magnitude', data: data, backgroundColor: '#f0a202' }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: 'Average Uncertainty Magnitude by Type', color: '#fff' }, legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: '#444' }, ticks: { color: '#ccc' } }, x: { grid: { color: '#444' }, ticks: { color: '#ccc' } } }
          }
        }));
      }
    }
  }

  function buildHtml() {
    let html = `
      <div class="results-header">
        <h2>Reliability Test Results</h2>
        <div class="paper-info">
          ${result.papers.length} papers, ${result.attempts || '?'} attempts per configuration | Cost: $${(result.totalCost || 0).toFixed(4)}
        </div>
      </div>
      <div class="paper-selector" style="margin-bottom: 16px;">
        <label>Select Paper: </label>
        <select id="rel-paper-select">
          ${result.papers.map(p => `<option value="${p.arxivId}" ${p.arxivId === activePaperId ? 'selected' : ''}>${escapeHtml(p.paperTitle)} (${p.arxivId})</option>`).join('')}
        </select>
      </div>
      <div class="uncertainty-tabs">
        ${UNCERTAINTY_LABELS.map((label, i) =>
          `<button class="uncertainty-tab ${i === 0 ? 'active' : ''}" data-type="${i + 1}">${label}</button>`
        ).join('')}
      </div>
      <div id="rel-table-container"></div>
      <div id="rel-analysis-container">${buildAnalysisHtml()}</div>
    `;
    return html;
  }

  function renderTable(uType) {
    let html = `<table class="results-table">
      <thead>
        <tr>
          <th>Dimension</th>
          ${modelNames.map(m => `<th>${m}</th>`).join('')}
        </tr>
      </thead>
      <tbody>`;

    for (const dim of DIMENSIONS) {
      html += `<tr><td>${dim.name}</td>`;
      for (const mName of modelNames) {
        const paperRes = result.modelResults[mName].paperResults[activePaperId];
        const attempts = paperRes?.uncertaintyResults[uType] || [];
        
        if (attempts.length > 0) {
          const scores = attempts.map(a => a.ratings[dim.id]?.score).filter(s => s !== undefined);
          
          const avgScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '?';
          
          html += `<td class="score-cell rel-cell">
            <div class="avg-score">Avg: ${avgScore}</div>
            <div class="attempts-mini">
              ${attempts.map(a => {
                const s = a.ratings[dim.id]?.score ?? '?';
                const u = formatUncertainty(a.ratings[dim.id]?.uncertainty, uType);
                return `<div class="attempt-tiny" title="Justification: ${escapeHtml(a.ratings[dim.id]?.justification || '')}">
                  S:${s} U:${u}
                </div>`;
              }).join('')}
            </div>
          </td>`;
        } else {
          html += `<td>-</td>`;
        }
      }
      html += `</tr>`;
    }

    html += `</tbody></table>`;
    document.getElementById('rel-table-container').innerHTML = html;
  }

  analysisStats = computeStats();
  resultsContent.innerHTML = buildHtml();
  renderTable(1);
  
  setTimeout(() => renderCharts(analysisStats), 0);

  const paperSelect = document.getElementById('rel-paper-select');
  if (paperSelect) {
    paperSelect.addEventListener('change', (e) => {
      activePaperId = e.target.value;
      const activeTab = resultsContent.querySelector('.uncertainty-tab.active');
      renderTable(parseInt(activeTab.dataset.type));
    });
  }

  resultsContent.querySelectorAll('.uncertainty-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const type = tab.dataset.type;
      resultsContent.querySelectorAll('.uncertainty-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderTable(parseInt(type));
    });
  });

  const modeToggle = document.getElementById('analysis-mode-toggle');
  if (modeToggle) {
    modeToggle.addEventListener('change', (e) => {
      showUncertaintyMode = e.target.checked;
      renderCharts(analysisStats);
    });
  }
}

function formatUncertainty(value, type) {
  if (value === undefined || value === null) return '';
  if (type === 3 && Array.isArray(value)) return `[${value.join(', ')}]`;
  if (typeof value === 'number') return value.toFixed(2);
  return String(value);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// History
async function loadHistory() {
  try {
    const [resSingle, resRel] = await Promise.all([
      fetch('/api/results'),
      fetch('/api/reliability-results')
    ]);
    const singleResults = await resSingle.json();
    const relResults = await resRel.json();
    
    historyList.innerHTML = '';
    
    const allResults = [
      ...singleResults.map(r => ({ ...r, type: 'single' })),
      ...relResults.map(r => ({ ...r, type: 'reliability' }))
    ];
    
    if (allResults.length === 0) {
      historyList.innerHTML = '<p style="color:#666;font-size:14px">No previous ratings</p>';
      return;
    }
    
    allResults.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    
    // Populate reliability history select
    if (typeof relHistorySelect !== 'undefined') {
      relHistorySelect.innerHTML = '<option value="">Select a past test...</option>';
      allResults.filter(r => r.type === 'reliability').forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        const partialTag = r.status === 'partial' ? ' [PARTIAL]' : '';
        opt.textContent = `${new Date(r.timestamp).toLocaleString()} - ${r.papers} papers${partialTag}`;
        relHistorySelect.appendChild(opt);
      });
    }

    allResults.forEach(r => {
      const div = document.createElement('div');
      div.className = 'history-item';
      const isRel = r.type === 'reliability';
      const label = isRel ? '<span style="color:#4ecdc4;margin-right:5px">[REL]</span>' : '';
      const partialLabel = (isRel && r.status === 'partial') ? '<span style="color:#e74c3c;margin-left:4px;font-size:11px">[PARTIAL]</span>' : '';
      div.innerHTML = `
        <span class="title">${label}${escapeHtml(r.paperTitle || r.arxivId || `Batch (${r.papers} papers)`)}${partialLabel}</span>
        <span class="date">${new Date(r.timestamp).toLocaleDateString()}</span>
      `;
      div.addEventListener('click', () => {
        if (isRel) {
          loadReliabilityResult(r.id);
        } else {
          loadResult(r.id);
        }
      });
      historyList.appendChild(div);
    });
  } catch {}
}

async function loadResult(id) {
  try {
    const res = await fetch(`/api/results/${id}`);
    const result = await res.json();
    currentResult = result;
    renderResults(result);
    resultsPanel.classList.remove('hidden');
    resultsPanel.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert('Failed to load result');
  }
}

async function loadReliabilityResult(id) {
  try {
    const res = await fetch(`/api/results/${id}`);
    const result = await res.json();
    currentResult = result;
    renderReliabilityResults(result);
    resultsPanel.classList.remove('hidden');
    resultsPanel.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert('Failed to load reliability result');
  }
}

// ============================================================
// Calibration Analysis
// ============================================================

let calCharts = [];
let calDataPoints = [];
let calLoadedResults = [];

async function loadCalibrationRunPicker() {
  const runList = document.getElementById('cal-run-list');
  try {
    const res = await fetch('/api/reliability-results');
    const runs = await res.json();
    runList.innerHTML = '';
    if (runs.length === 0) {
      runList.innerHTML = '<div style="color:#666;font-size:13px;padding:6px">No reliability runs found</div>';
      return;
    }
    runs.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    runs.forEach(r => {
      const label = document.createElement('label');
      label.className = 'run-picker-item';
      const statusBadge = r.status === 'partial' ? '<span style="color:#e74c3c;font-weight:600;margin-left:4px">[PARTIAL]</span>' : '';
      label.innerHTML = `<input type="checkbox" class="cal-run-cb" value="${r.id}" />
        ${new Date(r.timestamp).toLocaleString()} &mdash; ${r.papers} papers, ${r.attempts || '?'} attempts${statusBadge}`;
      runList.appendChild(label);
    });
  } catch {
    runList.innerHTML = '<div class="error-msg">Failed to load runs</div>';
  }
}

document.getElementById('cal-select-all').addEventListener('change', (e) => {
  document.querySelectorAll('.cal-run-cb').forEach(cb => cb.checked = e.target.checked);
});

document.getElementById('cal-analyze-btn').addEventListener('click', runCalibrationAnalysis);
document.getElementById('cal-variance-toggle').addEventListener('change', () => renderCalibrationCharts());
document.getElementById('cal-color-by').addEventListener('change', () => renderCalibrationCharts());
document.getElementById('cal-model-filter').addEventListener('change', () => renderCalibrationCharts());

async function runCalibrationAnalysis() {
  const selectedIds = [...document.querySelectorAll('.cal-run-cb:checked')].map(cb => cb.value);
  if (selectedIds.length === 0) return alert('Select at least one reliability run');

  const btn = document.getElementById('cal-analyze-btn');
  btn.disabled = true;
  btn.textContent = 'Loading...';

  try {
    calLoadedResults = await Promise.all(
      selectedIds.map(id => fetch(`/api/results/${id}`).then(r => r.json()))
    );

    // Populate paper filter
    const paperFilter = document.getElementById('cal-paper-filter');
    const papers = new Map();
    calLoadedResults.forEach(result => {
      result.papers.forEach(p => {
        if (!papers.has(p.arxivId)) papers.set(p.arxivId, p.paperTitle || p.arxivId);
      });
    });
    paperFilter.innerHTML = '<option value="">All Papers</option>';
    papers.forEach((title, id) => {
      paperFilter.innerHTML += `<option value="${id}">${escapeHtml(title)} (${id})</option>`;
    });
    paperFilter.onchange = () => {
      calDataPoints = computeCalibrationData(calLoadedResults, paperFilter.value);
      renderCalibrationCharts();
    };

    calDataPoints = computeCalibrationData(calLoadedResults, '');

    // Populate model filter
    const modelFilter = document.getElementById('cal-model-filter');
    const allModels = [...new Set(calDataPoints.map(p => p.model))].sort();
    modelFilter.innerHTML = '<option value="">All Models (pooled)</option><option value="__per_model__">All Models (per-model overlay)</option>';
    allModels.forEach(m => {
      modelFilter.innerHTML += `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`;
    });

    document.getElementById('cal-results').classList.remove('hidden');
    renderCalibrationCharts();
  } catch (err) {
    alert('Failed to load data: ' + err.message);
  }

  btn.disabled = false;
  btn.textContent = 'Analyze Calibration';
}

function normalizeUncertainty(value, uType) {
  if (value === undefined || value === null) return null;
  if (uType === 1) {
    // Subjective 0-1
    return typeof value === 'number' ? Math.max(0, Math.min(1, value)) : null;
  }
  if (uType === 2) {
    // Probability 0-1
    return typeof value === 'number' ? Math.max(0, Math.min(1, value)) : null;
  }
  if (uType === 3) {
    // Plausible range [low, high] -> range/5
    if (Array.isArray(value) && value.length === 2) {
      return Math.max(0, Math.min(1, (value[1] - value[0]) / 5));
    }
    return null;
  }
  if (uType === 4) {
    // Evidence level string
    if (typeof value === 'string') {
      const lower = value.toLowerCase();
      if (lower.includes('strong direct')) return 0.1;
      if (lower.includes('some indirect')) return 0.4;
      if (lower.includes('very little') || lower.includes('weak')) return 0.7;
      if (lower.includes('pure guess') || lower.includes('no evidence')) return 0.9;
      return 0.5;
    }
    return null;
  }
  return null;
}

function resolveDimId(ratings, dimId) {
  // Handle audience_exposure vs audience_venue_exposure
  if (ratings[dimId] !== undefined) return dimId;
  if (dimId === 'audience_venue_exposure' && ratings['audience_exposure'] !== undefined) return 'audience_exposure';
  if (dimId === 'audience_exposure' && ratings['audience_venue_exposure'] !== undefined) return 'audience_venue_exposure';
  return dimId;
}

function computeCalibrationData(results, paperFilter) {
  const points = [];

  for (const result of results) {
    const modelNames = Object.keys(result.modelResults);
    const paperIds = result.papers.map(p => p.arxivId).filter(id => !paperFilter || id === paperFilter);

    for (const paperId of paperIds) {
      for (const dim of DIMENSIONS) {
        // Collect combined scores across all types and attempts for this (model, paper, dim)
        const modelCombinedScores = {};
        const modelTypeData = {}; // modelName -> uType -> { scores[], uncertainties[] }

        for (const mName of modelNames) {
          modelCombinedScores[mName] = [];
          modelTypeData[mName] = {};

          for (let uType = 1; uType <= 4; uType++) {
            const attempts = result.modelResults[mName]?.paperResults?.[paperId]?.uncertaintyResults?.[uType] || [];
            const scores = [];
            const uncertainties = [];

            for (const attempt of attempts) {
              const resolvedDim = resolveDimId(attempt.ratings, dim.id);
              const rating = attempt.ratings[resolvedDim];
              if (!rating) continue;
              if (typeof rating.score === 'number') {
                scores.push(rating.score);
                modelCombinedScores[mName].push(rating.score);
              }
              const normU = normalizeUncertainty(rating.uncertainty, uType);
              if (normU !== null) uncertainties.push(normU);
            }

            modelTypeData[mName][uType] = { scores, uncertainties };
          }
        }

        // Now produce data points per (model, paper, dim, uType)
        for (const mName of modelNames) {
          const combined = modelCombinedScores[mName];
          const combinedVariance = combined.length > 1 ? variance(combined) : null;

          for (let uType = 1; uType <= 4; uType++) {
            const td = modelTypeData[mName][uType];
            if (td.uncertainties.length === 0) continue;

            const meanUncertainty = mean(td.uncertainties);
            const withinTypeVariance = td.scores.length > 1 ? variance(td.scores) : null;

            points.push({
              statedUncertainty: meanUncertainty,
              withinTypeVariance,
              combinedVariance,
              meanScore: td.scores.length > 0 ? mean(td.scores) : null,
              model: mName,
              paper: paperId,
              dimension: dim.id,
              dimensionName: dim.name,
              uncertaintyType: uType,
            });
          }
        }
      }
    }
  }

  return points;
}

function computeBetweenModelPointsFromResults(results, paperFilter) {
  // For each (paper, dim, uType): collect per-model mean score and per-model mean uncertainty
  // Then: betweenModelVariance = variance of model mean scores
  //        statedUncertainty = mean of all model uncertainties
  const groups = {}; // key -> { modelScores: {model: [scores]}, modelUncertainties: {model: [uncertainties]} }

  for (const result of results) {
    const modelNames = Object.keys(result.modelResults);
    const paperIds = result.papers.map(p => p.arxivId).filter(id => !paperFilter || id === paperFilter);

    for (const paperId of paperIds) {
      for (const dim of DIMENSIONS) {
        for (const mName of modelNames) {
          for (let uType = 1; uType <= 4; uType++) {
            const attempts = result.modelResults[mName]?.paperResults?.[paperId]?.uncertaintyResults?.[uType] || [];
            for (const attempt of attempts) {
              const resolvedDim = resolveDimId(attempt.ratings, dim.id);
              const rating = attempt.ratings[resolvedDim];
              if (!rating) continue;
              const key = `${paperId}|${dim.id}|${uType}`;
              if (!groups[key]) groups[key] = { paper: paperId, dimension: dim.id, dimensionName: dim.name, uncertaintyType: uType, modelScores: {}, modelUncertainties: {} };
              if (!groups[key].modelScores[mName]) groups[key].modelScores[mName] = [];
              if (!groups[key].modelUncertainties[mName]) groups[key].modelUncertainties[mName] = [];
              if (typeof rating.score === 'number') groups[key].modelScores[mName].push(rating.score);
              const normU = normalizeUncertainty(rating.uncertainty, uType);
              if (normU !== null) groups[key].modelUncertainties[mName].push(normU);
            }
          }
        }
      }
    }
  }

  const points = [];
  for (const [, g] of Object.entries(groups)) {
    const modelNames = Object.keys(g.modelScores);
    if (modelNames.length < 2) continue;

    // Mean score per model
    const modelMeanScores = modelNames.map(m => g.modelScores[m].length > 0 ? mean(g.modelScores[m]) : null).filter(v => v !== null);
    if (modelMeanScores.length < 2) continue;

    const betweenModelVar = variance(modelMeanScores);

    // Mean uncertainty across all models
    const allUncertainties = modelNames.flatMap(m => g.modelUncertainties[m]);
    if (allUncertainties.length === 0) continue;
    const meanUnc = mean(allUncertainties);

    points.push({
      statedUncertainty: meanUnc,
      betweenModelVariance: betweenModelVar,
      combinedVariance: betweenModelVar,
      withinTypeVariance: betweenModelVar,
      paper: g.paper,
      dimension: g.dimension,
      dimensionName: g.dimensionName,
      uncertaintyType: g.uncertaintyType,
      model: '(between-model)',
    });
  }

  return points;
}

function mean(arr) {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function variance(arr) {
  const m = mean(arr);
  return arr.reduce((acc, v) => acc + (v - m) ** 2, 0) / arr.length;
}

function pearsonCorrelation(xs, ys) {
  const n = xs.length;
  if (n < 3) return { r: NaN, p: NaN };
  const mx = mean(xs), my = mean(ys);
  let num = 0, dx2 = 0, dy2 = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx, dy = ys[i] - my;
    num += dx * dy;
    dx2 += dx * dx;
    dy2 += dy * dy;
  }
  const denom = Math.sqrt(dx2 * dy2);
  if (denom === 0) return { r: 0, p: 1 };
  const r = num / denom;
  // Approximate p-value using t-distribution
  const t = r * Math.sqrt((n - 2) / (1 - r * r));
  const p = tDistPValue(t, n - 2);
  return { r, p };
}

function spearmanCorrelation(xs, ys) {
  const n = xs.length;
  if (n < 3) return NaN;
  const rankX = ranks(xs), rankY = ranks(ys);
  return pearsonCorrelation(rankX, rankY).r;
}

function ranks(arr) {
  const sorted = arr.map((v, i) => ({ v, i })).sort((a, b) => a.v - b.v);
  const r = new Array(arr.length);
  for (let i = 0; i < sorted.length;) {
    let j = i;
    while (j < sorted.length && sorted[j].v === sorted[i].v) j++;
    const avgRank = (i + j - 1) / 2 + 1;
    for (let k = i; k < j; k++) r[sorted[k].i] = avgRank;
    i = j;
  }
  return r;
}

function tDistPValue(t, df) {
  // Approximation of two-tailed p-value using incomplete beta function
  if (df <= 0 || isNaN(t)) return NaN;
  const x = df / (df + t * t);
  return incompleteBeta(df / 2, 0.5, x);
}

function incompleteBeta(a, b, x) {
  // Simple continued fraction approximation
  if (x < 0 || x > 1) return NaN;
  if (x === 0) return 0;
  if (x === 1) return 1;
  const lnBeta = lgamma(a) + lgamma(b) - lgamma(a + b);
  const front = Math.exp(Math.log(x) * a + Math.log(1 - x) * b - lnBeta);
  // Use Lentz's continued fraction
  let f = 1, c = 1, d = 1 - (a + 1) * x / (a + 1);
  if (Math.abs(d) < 1e-30) d = 1e-30;
  d = 1 / d;
  f = d;
  for (let m = 1; m <= 200; m++) {
    let num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m));
    d = 1 + num * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
    c = 1 + num / c; if (Math.abs(c) < 1e-30) c = 1e-30;
    f *= d * c;
    num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1));
    d = 1 + num * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
    c = 1 + num / c; if (Math.abs(c) < 1e-30) c = 1e-30;
    const delta = d * c;
    f *= delta;
    if (Math.abs(delta - 1) < 1e-8) break;
  }
  return front * f / a;
}

function lgamma(x) {
  // Lanczos approximation
  const c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
    -1.231739572450155, 0.001208650973866179, -0.000005395239384953];
  let y = x, tmp = x + 5.5;
  tmp -= (x + 0.5) * Math.log(tmp);
  let ser = 1.000000000190015;
  for (let j = 0; j < 6; j++) ser += c[j] / ++y;
  return -tmp + Math.log(2.5066282746310005 * ser / x);
}

function getCalCorrelationsPerType(points, varianceKey) {
  const results = {};
  for (let uType = 1; uType <= 4; uType++) {
    const typePoints = points.filter(p => p.uncertaintyType === uType && p[varianceKey] !== null);
    const xs = typePoints.map(p => p.statedUncertainty);
    const ys = typePoints.map(p => p[varianceKey]);
    const pr = pearsonCorrelation(xs, ys);
    const sp = spearmanCorrelation(xs, ys);
    results[uType] = { pearsonR: pr.r, pValue: pr.p, spearmanRho: sp, n: typePoints.length };
  }
  return results;
}

function computeInterModelCalibration(points) {
  // Group by (paper, dimension, uType) -> aggregate across models
  const groups = {};
  for (const p of points) {
    const key = `${p.paper}|${p.dimension}|${p.uncertaintyType}`;
    if (!groups[key]) groups[key] = { uncertainties: [], scores: [], uType: p.uncertaintyType };
    groups[key].uncertainties.push(p.statedUncertainty);
    if (p.combinedVariance !== null) groups[key].scores.push(p.combinedVariance);
  }

  // For each (paper, dim, uType): between-model variance of mean scores (use statedUncertainty mean, combinedVariance variance)
  const results = {};
  for (let uType = 1; uType <= 4; uType++) {
    const xs = [], ys = [];
    for (const [, g] of Object.entries(groups)) {
      if (g.uType !== uType) continue;
      if (g.uncertainties.length < 2 || g.scores.length < 2) continue;
      xs.push(mean(g.uncertainties));
      ys.push(variance(g.scores));
    }
    const pr = pearsonCorrelation(xs, ys);
    results[uType] = { pearsonR: pr.r, pValue: pr.p, n: xs.length };
  }
  return results;
}

const CAL_COLORS = {
  model: ['#4ecdc4', '#ff6b6b', '#ffe66d', '#1a535c', '#8ca8d9', '#f0a202', '#e056a0', '#56e0c8', '#d4a5ff', '#ff9f43'],
  dimension: ['#4ecdc4', '#ff6b6b', '#ffe66d', '#8ca8d9', '#f0a202'],
  paper: ['#4ecdc4', '#ff6b6b', '#ffe66d', '#1a535c', '#8ca8d9', '#f0a202', '#e056a0', '#56e0c8'],
};

const TYPE_LABELS = ['Type 1 (Subj. 0-1)', 'Type 2 (Prob off-by-2)', 'Type 3 (Range)', 'Type 4 (Evidence)'];
const TYPE_COLORS = ['#4ecdc4', '#ff6b6b', '#ffe66d', '#8ca8d9'];

function renderCalibrationCharts() {
  // Destroy old charts
  calCharts.forEach(c => c.destroy());
  calCharts = [];

  const varToggle = document.getElementById('cal-variance-toggle').value;
  const colorBy = document.getElementById('cal-color-by').value;
  const modelFilter = document.getElementById('cal-model-filter').value;

  let varianceKey, activePoints;

  if (varToggle === 'between') {
    varianceKey = 'betweenModelVariance';
    activePoints = computeBetweenModelPointsFromResults(calLoadedResults, document.getElementById('cal-paper-filter').value);
  } else {
    varianceKey = varToggle === 'combined' ? 'combinedVariance' : 'withinTypeVariance';
    if (modelFilter && modelFilter !== '__per_model__') {
      activePoints = calDataPoints.filter(p => p.model === modelFilter);
    } else {
      activePoints = calDataPoints;
    }
  }

  // Store active points for use by render functions
  window._calActivePoints = activePoints;
  window._calVarianceKey = varianceKey;
  window._calModelFilter = modelFilter;

  renderScatterChart(varianceKey, colorBy, activePoints);
  renderBarChart(varianceKey, activePoints);
  renderBinnedChart(varianceKey, activePoints);
  renderHeatmap(varianceKey, activePoints, modelFilter);
  renderICCTable();
  renderTypeRankingTable();
  renderCalibrationSummary();
}

function renderScatterChart(varianceKey, colorBy, points) {
  const ctx = document.getElementById('cal-chart-scatter');
  if (!ctx) return;
  points = points || calDataPoints;

  const datasets = [];
  for (let uType = 1; uType <= 4; uType++) {
    const typePoints = points.filter(p => p.uncertaintyType === uType && p[varianceKey] !== null);
    if (typePoints.length === 0) continue;

    const data = typePoints.map(p => ({
      x: p.statedUncertainty,
      y: p[varianceKey],
      label: `${p.model} | ${p.dimensionName} | ${p.paper}`,
    }));

    datasets.push({
      label: TYPE_LABELS[uType - 1],
      data,
      backgroundColor: TYPE_COLORS[uType - 1] + '80',
      borderColor: TYPE_COLORS[uType - 1],
      pointRadius: 4,
      pointHoverRadius: 6,
    });

    // Trend line
    if (typePoints.length >= 2) {
      const xs = typePoints.map(p => p.statedUncertainty);
      const ys = typePoints.map(p => p[varianceKey]);
      const { slope, intercept } = linearRegression(xs, ys);
      const xMin = Math.min(...xs), xMax = Math.max(...xs);
      datasets.push({
        label: `Trend (${TYPE_LABELS[uType - 1]})`,
        data: [{ x: xMin, y: slope * xMin + intercept }, { x: xMax, y: slope * xMax + intercept }],
        type: 'line',
        borderColor: TYPE_COLORS[uType - 1],
        borderWidth: 2,
        borderDash: [6, 3],
        pointRadius: 0,
        fill: false,
      });
    }
  }

  const corrs = getCalCorrelationsPerType(points, varianceKey);
  const titleParts = [1, 2, 3, 4].map(t => `T${t}: r=${isNaN(corrs[t].pearsonR) ? 'N/A' : corrs[t].pearsonR.toFixed(2)}`);

  calCharts.push(new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: ['Calibration Scatter', titleParts.join('  ')], color: '#fff', font: { size: 13 } },
        legend: { labels: { color: '#ccc', filter: (item) => !item.text.startsWith('Trend') } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const p = ctx.raw;
              return `${p.label || ''}: U=${ctx.parsed.x.toFixed(2)}, Var=${ctx.parsed.y.toFixed(3)}`;
            }
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Stated Uncertainty (normalized)', color: '#aaa' }, grid: { color: '#333' }, ticks: { color: '#ccc' } },
        y: { title: { display: true, text: 'Score Variance', color: '#aaa' }, beginAtZero: true, grid: { color: '#333' }, ticks: { color: '#ccc' } },
      }
    }
  }));
}

function linearRegression(xs, ys) {
  const n = xs.length;
  const mx = mean(xs), my = mean(ys);
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {
    num += (xs[i] - mx) * (ys[i] - my);
    den += (xs[i] - mx) ** 2;
  }
  const slope = den === 0 ? 0 : num / den;
  const intercept = my - slope * mx;
  return { slope, intercept };
}

function renderBarChart(varianceKey, points) {
  const ctx = document.getElementById('cal-chart-bars');
  if (!ctx) return;
  points = points || calDataPoints;

  const corrsCombined = getCalCorrelationsPerType(points, 'combinedVariance');
  const corrsPerType = getCalCorrelationsPerType(points, 'withinTypeVariance');
  const interModel = computeInterModelCalibration(points);

  const labels = TYPE_LABELS;
  const dataCombined = [1, 2, 3, 4].map(t => isNaN(corrsCombined[t].pearsonR) ? 0 : corrsCombined[t].pearsonR);
  const dataPerType = [1, 2, 3, 4].map(t => isNaN(corrsPerType[t].pearsonR) ? 0 : corrsPerType[t].pearsonR);
  const dataInter = [1, 2, 3, 4].map(t => isNaN(interModel[t].pearsonR) ? 0 : interModel[t].pearsonR);

  // Find best type (highest combined correlation)
  const bestIdx = dataCombined.indexOf(Math.max(...dataCombined));
  const bgCombined = dataCombined.map((_, i) => i === bestIdx ? '#4ecdc4' : '#4ecdc480');
  const bgPerType = dataPerType.map(() => '#ff6b6b80');
  const bgInter = dataInter.map(() => '#ffe66d80');

  calCharts.push(new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Intra-model r (combined var.)', data: dataCombined, backgroundColor: bgCombined, borderColor: '#4ecdc4', borderWidth: 1 },
        { label: 'Intra-model r (per-type var.)', data: dataPerType, backgroundColor: bgPerType, borderColor: '#ff6b6b', borderWidth: 1 },
        { label: 'Inter-model r', data: dataInter, backgroundColor: bgInter, borderColor: '#ffe66d', borderWidth: 1 },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: 'Calibration Comparison (Pearson r)', color: '#fff' },
        legend: { labels: { color: '#ccc' } },
      },
      scales: {
        y: { min: -1, max: 1, grid: { color: '#333' }, ticks: { color: '#ccc' }, title: { display: true, text: 'Pearson r', color: '#aaa' } },
        x: { grid: { color: '#333' }, ticks: { color: '#ccc', maxRotation: 30 } },
      }
    }
  }));
}

function renderBinnedChart(varianceKey, points) {
  const ctx = document.getElementById('cal-chart-binned');
  if (!ctx) return;
  points = points || calDataPoints;

  const bins = [
    { label: '0-0.2', min: 0, max: 0.2 },
    { label: '0.2-0.4', min: 0.2, max: 0.4 },
    { label: '0.4-0.6', min: 0.4, max: 0.6 },
    { label: '0.6-0.8', min: 0.6, max: 0.8 },
    { label: '0.8-1.0', min: 0.8, max: 1.01 },
  ];

  const datasets = [];
  for (let uType = 1; uType <= 4; uType++) {
    const typePoints = points.filter(p => p.uncertaintyType === uType && p[varianceKey] !== null);

    const binData = bins.map(bin => {
      const inBin = typePoints.filter(p => p.statedUncertainty >= bin.min && p.statedUncertainty < bin.max);
      if (inBin.length === 0) return null;
      const variances = inBin.map(p => p[varianceKey]);
      return mean(variances);
    });

    datasets.push({
      label: TYPE_LABELS[uType - 1],
      data: binData,
      borderColor: TYPE_COLORS[uType - 1],
      backgroundColor: TYPE_COLORS[uType - 1] + '30',
      fill: false,
      tension: 0.3,
      spanGaps: true,
      pointRadius: 5,
      pointHoverRadius: 7,
    });
  }

  calCharts.push(new Chart(ctx, {
    type: 'line',
    data: { labels: bins.map(b => b.label), datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: 'Binned Calibration Curves', color: '#fff' },
        legend: { labels: { color: '#ccc' } },
      },
      scales: {
        x: { title: { display: true, text: 'Stated Uncertainty Bin', color: '#aaa' }, grid: { color: '#333' }, ticks: { color: '#ccc' } },
        y: { title: { display: true, text: 'Mean Score Variance', color: '#aaa' }, beginAtZero: true, grid: { color: '#333' }, ticks: { color: '#ccc' } },
      }
    }
  }));
}

function renderHeatmap(varianceKey, points, modelFilter) {
  const container = document.getElementById('cal-heatmap-container');
  if (!container) return;
  points = points || calDataPoints;
  modelFilter = modelFilter || '';

  const isOverlay = modelFilter === '__per_model__';

  if (isOverlay) {
    renderHeatmapOverlay(varianceKey);
    return;
  }

  // Compute correlation per (dimension, uType)
  const cells = {};
  for (const dim of DIMENSIONS) {
    cells[dim.id] = {};
    for (let uType = 1; uType <= 4; uType++) {
      const pts = points.filter(p => p.dimension === dim.id && p.uncertaintyType === uType && p[varianceKey] !== null);
      if (pts.length < 3) {
        cells[dim.id][uType] = { r: NaN, n: pts.length };
      } else {
        const xs = pts.map(p => p.statedUncertainty);
        const ys = pts.map(p => p[varianceKey]);
        const pr = pearsonCorrelation(xs, ys);
        cells[dim.id][uType] = { r: pr.r, p: pr.p, n: pts.length };
      }
    }
  }

  // Store cells for Steiger popup
  window._calHeatmapCells = cells;
  window._calHeatmapPoints = points;
  window._calHeatmapVarKey = varianceKey;

  let html = `<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px;text-align:center;">Dimension x Type Heatmap (Pearson r)</div>`;
  html += `<div style="font-size:11px;color:#888;text-align:center;margin-bottom:6px;">Click a cell to compare vs other types (Steiger's Z)</div>`;
  html += `<table class="cal-heatmap"><thead><tr><th>Dimension</th>`;
  for (let t = 1; t <= 4; t++) html += `<th>Type ${t}</th>`;
  html += `</tr></thead><tbody>`;

  for (const dim of DIMENSIONS) {
    html += `<tr><td style="text-align:left;color:#ccc;font-weight:500">${dim.name}</td>`;
    for (let t = 1; t <= 4; t++) {
      const cell = cells[dim.id][t];
      const r = cell.r;
      const display = isNaN(r) ? 'N/A' : r.toFixed(2);
      const bg = isNaN(r) ? '#2a2d3a' : correlationColor(r);
      const textColor = isNaN(r) ? '#666' : '#fff';
      const clickable = !isNaN(r) ? 'clickable' : '';
      html += `<td class="${clickable}" style="background:${bg};color:${textColor}" data-dim="${dim.id}" data-type="${t}">${display}<br><span style="font-size:10px;opacity:0.7">n=${cell.n}</span></td>`;
    }
    html += `</tr>`;
  }
  html += `</tbody></table>`;
  html += `<div id="steiger-popup-anchor" style="position:relative;"></div>`;
  container.innerHTML = html;

  // Add click handlers for Steiger popup
  container.querySelectorAll('td.clickable').forEach(td => {
    td.addEventListener('click', (e) => {
      showSteigerPopup(td.dataset.dim, parseInt(td.dataset.type), e);
    });
  });
}

function renderHeatmapOverlay(varianceKey) {
  const container = document.getElementById('cal-heatmap-container');
  const allModels = [...new Set(calDataPoints.map(p => p.model))].sort();

  // Compute per-model correlations for each (dim, type)
  const perModelCells = {}; // dim -> type -> [{ model, r }]
  for (const dim of DIMENSIONS) {
    perModelCells[dim.id] = {};
    for (let uType = 1; uType <= 4; uType++) {
      perModelCells[dim.id][uType] = [];
      for (const m of allModels) {
        const pts = calDataPoints.filter(p => p.dimension === dim.id && p.uncertaintyType === uType && p.model === m && p[varianceKey] !== null);
        if (pts.length < 3) continue;
        const xs = pts.map(p => p.statedUncertainty);
        const ys = pts.map(p => p[varianceKey]);
        const pr = pearsonCorrelation(xs, ys);
        perModelCells[dim.id][uType].push({ model: m, r: pr.r });
      }
    }
  }

  let html = `<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px;text-align:center;">Per-Model Heatmap Overlay</div>`;
  html += `<table class="cal-heatmap"><thead><tr><th>Dimension</th>`;
  for (let t = 1; t <= 4; t++) html += `<th>Type ${t}</th>`;
  html += `</tr></thead><tbody>`;

  for (const dim of DIMENSIONS) {
    html += `<tr><td style="text-align:left;color:#ccc;font-weight:500">${dim.name}</td>`;
    for (let t = 1; t <= 4; t++) {
      const entries = perModelCells[dim.id][t];
      if (entries.length === 0) {
        html += `<td style="background:#2a2d3a;color:#666">N/A</td>`;
      } else {
        const rs = entries.map(e => e.r).filter(r => !isNaN(r));
        if (rs.length === 0) {
          html += `<td style="background:#2a2d3a;color:#666">N/A</td>`;
        } else {
          const meanR = mean(rs);
          const minR = Math.min(...rs);
          const maxR = Math.max(...rs);
          const bg = correlationColor(meanR);
          const tooltip = entries.map(e => `${e.model}: ${isNaN(e.r) ? 'N/A' : e.r.toFixed(2)}`).join('&#10;');
          html += `<td class="overlay-cell" style="background:${bg};color:#fff" title="${tooltip}">${meanR.toFixed(2)}<br><span class="overlay-range">[${minR.toFixed(2)}, ${maxR.toFixed(2)}]</span></td>`;
        }
      }
    }
    html += `</tr>`;
  }
  html += `</tbody></table>`;
  html += `<div style="font-size:11px;color:#888;text-align:center;margin-top:4px;">Cell shows mean r [min, max]. Hover for per-model breakdown.</div>`;
  container.innerHTML = html;
}

function correlationColor(r) {
  // Red (negative/poor) to green (positive/good)
  const clamped = Math.max(-1, Math.min(1, r));
  if (clamped >= 0) {
    const g = Math.round(80 + clamped * 120);
    const rb = Math.round(50 - clamped * 30);
    return `rgb(${rb}, ${g}, ${rb})`;
  } else {
    const red = Math.round(80 + Math.abs(clamped) * 120);
    const gb = Math.round(50 - Math.abs(clamped) * 30);
    return `rgb(${red}, ${gb}, ${gb})`;
  }
}

// ============================================================
// Steiger's Z-test for comparing dependent correlations
// Meng, Rosenthal & Rubin (1992)
// ============================================================
function steigerZ(r12, r13, r23, n) {
  // Compare correlation r12 vs r13, where variable 1 is shared (stated uncertainty)
  // r23 = correlation between the two predictors (the two uncertainty types' values)
  if (n < 4 || isNaN(r12) || isNaN(r13) || isNaN(r23)) return { z: NaN, p: NaN };
  const z12 = fisherZ(r12);
  const z13 = fisherZ(r13);
  const fbar = (r12 * r12 + r13 * r13) / 2;
  const denom1 = 2 * (1 - r23);
  const denom2 = (1 - fbar);
  if (denom1 <= 0 || denom2 <= 0) return { z: NaN, p: NaN };
  const h = (1 - fbar) / (1 - fbar * fbar);
  if (h <= 0) return { z: NaN, p: NaN };
  const zStar = (z12 - z13) * Math.sqrt((n - 3) / denom1) * Math.sqrt(h);
  // Two-tailed p-value from standard normal
  const p = 2 * (1 - normalCDF(Math.abs(zStar)));
  return { z: zStar, p };
}

function fisherZ(r) {
  r = Math.max(-0.999, Math.min(0.999, r));
  return 0.5 * Math.log((1 + r) / (1 - r));
}

function normalCDF(x) {
  // Approximation of standard normal CDF
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989422804014327;
  const p = d * Math.exp(-x * x / 2) * (t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.8212560 + t * 1.3302744)))));
  return x > 0 ? 1 - p : p;
}

function showSteigerPopup(dimId, clickedType, event) {
  // Remove existing popup
  document.querySelectorAll('.steiger-popup').forEach(el => el.remove());

  const points = window._calHeatmapPoints || calDataPoints;
  const varianceKey = window._calHeatmapVarKey || 'combinedVariance';

  // Get the shared variable (variance values) and per-type uncertainty values for this dimension
  // We need to compute r23 (correlation between uncertainty values of two types)
  // Points are per (model, paper, dim, type). We need to pair them.
  const dimPoints = points.filter(p => p.dimension === dimId && p[varianceKey] !== null);

  // Build lookup: (model, paper) -> { type -> { uncertainty, variance } }
  const lookup = {};
  for (const p of dimPoints) {
    const key = `${p.model}|${p.paper}`;
    if (!lookup[key]) lookup[key] = {};
    lookup[key][p.uncertaintyType] = { u: p.statedUncertainty, v: p[varianceKey] };
  }

  // For Steiger: we need paired observations where both types exist
  const results = [];
  for (let otherType = 1; otherType <= 4; otherType++) {
    if (otherType === clickedType) continue;

    // Find pairs where both types exist
    const pairs = [];
    for (const [, types] of Object.entries(lookup)) {
      if (types[clickedType] && types[otherType]) {
        pairs.push({
          u1: types[clickedType].u,
          u2: types[otherType].u,
          v: types[clickedType].v, // shared variance (same for both if using combined)
        });
      }
    }

    if (pairs.length < 4) {
      results.push({ otherType, z: NaN, p: NaN, n: pairs.length });
      continue;
    }

    // r12 = correlation between type1 uncertainty and variance
    const r12 = pearsonCorrelation(pairs.map(p => p.u1), pairs.map(p => p.v)).r;
    // r13 = correlation between type2 uncertainty and variance
    const r13 = pearsonCorrelation(pairs.map(p => p.u2), pairs.map(p => p.v)).r;
    // r23 = correlation between the two uncertainty types
    const r23 = pearsonCorrelation(pairs.map(p => p.u1), pairs.map(p => p.u2)).r;

    const sz = steigerZ(r12, r13, r23, pairs.length);
    results.push({ otherType, z: sz.z, p: sz.p, n: pairs.length, r1: r12, r2: r13 });
  }

  // Build popup HTML
  const dimName = DIMENSIONS.find(d => d.id === dimId)?.name || dimId;
  let html = `<div class="steiger-popup">`;
  html += `<h5>Steiger's Z: Type ${clickedType} vs others</h5>`;
  html += `<div style="margin-bottom:6px;color:#aaa;">${dimName}</div>`;
  html += `<table><thead><tr><th>Comparison</th><th>Z</th><th>p</th><th>n</th></tr></thead><tbody>`;

  for (const r of results) {
    const sig = !isNaN(r.p) && r.p < 0.05;
    const cls = sig ? 'steiger-sig' : 'steiger-nonsig';
    const zStr = isNaN(r.z) ? 'N/A' : r.z.toFixed(2);
    const pStr = isNaN(r.p) ? 'N/A' : (r.p < 0.001 ? '<0.001' : r.p.toFixed(3));
    html += `<tr><td>T${clickedType} vs T${r.otherType}</td><td class="${cls}">${zStr}</td><td class="${cls}">${pStr}</td><td>${r.n}</td></tr>`;
  }

  html += `</tbody></table>`;
  html += `<div style="margin-top:6px;font-size:10px;color:#666;">Z>0 means Type ${clickedType} has stronger correlation. p<0.05 = significant.</div>`;
  html += `</div>`;

  const anchor = document.getElementById('steiger-popup-anchor') || container;
  anchor.innerHTML = html;

  // Close on click outside
  const closeHandler = (e) => {
    if (!e.target.closest('.steiger-popup') && !e.target.closest('.clickable')) {
      document.querySelectorAll('.steiger-popup').forEach(el => el.remove());
      document.removeEventListener('click', closeHandler);
    }
  };
  setTimeout(() => document.addEventListener('click', closeHandler), 10);
}

// ============================================================
// ICC (Intraclass Correlation Coefficient) computation & rendering
// ============================================================
function computeICC(dimId, uType) {
  // ICC(1,1) one-way random effects
  // Groups = models, observations = scores across attempts for this (paper, dim, uType)
  // We pool all papers together: each model is a group, their scores are observations

  const groups = {}; // model -> [scores]
  for (const result of calLoadedResults) {
    const paperFilter = document.getElementById('cal-paper-filter').value;
    const paperIds = result.papers.map(p => p.arxivId).filter(id => !paperFilter || id === paperFilter);

    for (const paperId of paperIds) {
      for (const mName of Object.keys(result.modelResults)) {
        const attempts = result.modelResults[mName]?.paperResults?.[paperId]?.uncertaintyResults?.[uType] || [];
        for (const attempt of attempts) {
          const resolvedDim = resolveDimId(attempt.ratings, dimId);
          const rating = attempt.ratings[resolvedDim];
          if (!rating || typeof rating.score !== 'number') continue;
          if (!groups[mName]) groups[mName] = [];
          groups[mName].push(rating.score);
        }
      }
    }
  }

  const modelNames = Object.keys(groups);
  if (modelNames.length < 2) return { icc: NaN, msb: NaN, msw: NaN, k: 0, nGroups: modelNames.length };

  const allScores = modelNames.flatMap(m => groups[m]);
  const grandMean = mean(allScores);
  const k = mean(modelNames.map(m => groups[m].length)); // average group size

  // Between-group and within-group sum of squares
  let ssb = 0, ssw = 0;
  let dfb = modelNames.length - 1;
  let dfw = 0;
  for (const m of modelNames) {
    const groupMean = mean(groups[m]);
    ssb += groups[m].length * (groupMean - grandMean) ** 2;
    for (const score of groups[m]) {
      ssw += (score - groupMean) ** 2;
    }
    dfw += groups[m].length - 1;
  }

  if (dfb === 0 || dfw === 0) return { icc: NaN, msb: NaN, msw: NaN, k, nGroups: modelNames.length };

  const msb = ssb / dfb;
  const msw = ssw / dfw;

  const icc = (msb - msw) / (msb + (k - 1) * msw);

  return { icc, msb, msw, k, nGroups: modelNames.length };
}

function iccColor(icc) {
  if (isNaN(icc)) return '#2a2d3a';
  const clamped = Math.max(-1, Math.min(1, icc));
  if (clamped >= 0) {
    // Blue gradient for high ICC (between-model dominated)
    const b = Math.round(80 + clamped * 150);
    const rg = Math.round(50 + clamped * 30);
    return `rgb(${rg}, ${rg}, ${b})`;
  } else {
    // Orange gradient for negative ICC
    const r = Math.round(80 + Math.abs(clamped) * 150);
    const g = Math.round(60 + Math.abs(clamped) * 80);
    return `rgb(${r}, ${g}, 40)`;
  }
}

function renderICCTable() {
  const container = document.getElementById('cal-icc-container');
  if (!container) return;

  let html = `<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px;text-align:center;">ICC(1,1): Within vs Between Model Variance</div>`;
  html += `<div style="font-size:11px;color:#888;text-align:center;margin-bottom:6px;">High ICC (blue) = models disagree. Low ICC (orange) = models are self-inconsistent.</div>`;
  html += `<table class="cal-icc-table"><thead><tr><th>Dimension</th>`;
  for (let t = 1; t <= 4; t++) html += `<th>Type ${t}</th>`;
  html += `</tr></thead><tbody>`;

  for (const dim of DIMENSIONS) {
    html += `<tr><td style="text-align:left;color:#ccc;font-weight:500">${dim.name}</td>`;
    for (let t = 1; t <= 4; t++) {
      const result = computeICC(dim.id, t);
      const display = isNaN(result.icc) ? 'N/A' : result.icc.toFixed(2);
      const bg = iccColor(result.icc);
      const textColor = isNaN(result.icc) ? '#666' : '#fff';
      html += `<td style="background:${bg};color:${textColor}" title="MSB=${isNaN(result.msb)?'N/A':result.msb.toFixed(3)}, MSW=${isNaN(result.msw)?'N/A':result.msw.toFixed(3)}, k=${result.k.toFixed(1)}, groups=${result.nGroups}">${display}</td>`;
    }
    html += `</tr>`;
  }
  html += `</tbody></table>`;
  container.innerHTML = html;
}

// ============================================================
// Type Ranking Table + Kendall's W
// ============================================================
function computePerModelTypeCorrelations(varianceKey) {
  varianceKey = varianceKey || 'combinedVariance';
  const allModels = [...new Set(calDataPoints.map(p => p.model))].sort();
  const perModel = {}; // model -> { type -> { r, n } }

  for (const m of allModels) {
    perModel[m] = {};
    for (let uType = 1; uType <= 4; uType++) {
      const pts = calDataPoints.filter(p => p.model === m && p.uncertaintyType === uType && p[varianceKey] !== null);
      if (pts.length < 3) {
        perModel[m][uType] = { r: NaN, n: pts.length };
      } else {
        const xs = pts.map(p => p.statedUncertainty);
        const ys = pts.map(p => p[varianceKey]);
        const pr = pearsonCorrelation(xs, ys);
        perModel[m][uType] = { r: pr.r, n: pts.length };
      }
    }
  }

  return { allModels, perModel };
}

function computeKendallW(rankings) {
  // rankings: array of arrays, each inner array is one ranker's ranking of n items
  // rankings[i][j] = rank given by ranker i to item j
  const k = rankings.length; // number of rankers
  if (k < 2) return { W: NaN, chi2: NaN, p: NaN, df: NaN };

  const n = rankings[0].length; // number of items
  if (n < 2) return { W: NaN, chi2: NaN, p: NaN, df: NaN };

  // Column sums of ranks
  const colSums = new Array(n).fill(0);
  for (let j = 0; j < n; j++) {
    for (let i = 0; i < k; i++) {
      colSums[j] += rankings[i][j];
    }
  }

  const meanColSum = mean(colSums);
  const S = colSums.reduce((acc, cs) => acc + (cs - meanColSum) ** 2, 0);

  const W = (12 * S) / (k * k * (n * n * n - n));
  const chi2 = k * (n - 1) * W;
  const df = n - 1;

  // Chi-square p-value approximation
  const p = chi2PValue(chi2, df);

  return { W, chi2, p, df };
}

function chi2PValue(chi2, df) {
  // Upper tail probability of chi-square distribution
  // Using incomplete gamma function approximation
  if (chi2 <= 0 || df <= 0) return 1;
  return 1 - lowerIncompleteGamma(df / 2, chi2 / 2) / Math.exp(lgamma(df / 2));
}

function lowerIncompleteGamma(a, x) {
  // Series expansion for lower incomplete gamma function
  if (x < 0) return 0;
  if (x === 0) return 0;

  let sum = 0;
  let term = 1 / a;
  sum = term;
  for (let n = 1; n < 200; n++) {
    term *= x / (a + n);
    sum += term;
    if (Math.abs(term) < 1e-10 * Math.abs(sum)) break;
  }
  return sum * Math.exp(-x + a * Math.log(x) - lgamma(a));
}

function renderTypeRankingTable() {
  const container = document.getElementById('cal-ranking-container');
  if (!container) return;

  const varianceKey = window._calVarianceKey || 'combinedVariance';
  const { allModels, perModel } = computePerModelTypeCorrelations(varianceKey);

  // Compute ranks per model (1 = highest r = best)
  const rankings = []; // for Kendall's W
  const modelRanks = {}; // model -> [rank for type 1, 2, 3, 4]

  for (const m of allModels) {
    const rs = [1, 2, 3, 4].map(t => ({ type: t, r: perModel[m][t].r }));
    // Sort by r descending (highest = rank 1), NaN goes last
    const sorted = [...rs].sort((a, b) => {
      if (isNaN(a.r) && isNaN(b.r)) return 0;
      if (isNaN(a.r)) return 1;
      if (isNaN(b.r)) return -1;
      return b.r - a.r;
    });

    const rankArr = new Array(4).fill(NaN);
    sorted.forEach((item, idx) => {
      if (!isNaN(item.r)) rankArr[item.type - 1] = idx + 1;
    });

    modelRanks[m] = rankArr;

    // Only include in Kendall's W if model has all 4 types
    if (rankArr.every(r => !isNaN(r))) {
      rankings.push(rankArr);
    }
  }

  const kendall = computeKendallW(rankings);

  let html = `<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px;text-align:center;">Type Ranking by Model</div>`;
  html += `<div style="font-size:11px;color:#888;text-align:center;margin-bottom:6px;">Rank 1 = best calibrated type for that model. Kendall's W measures agreement.</div>`;
  html += `<table class="cal-ranking-table"><thead><tr><th>Model</th>`;
  for (let t = 1; t <= 4; t++) html += `<th>Type ${t}</th>`;
  html += `</tr></thead><tbody>`;

  for (const m of allModels) {
    html += `<tr><td style="text-align:left;color:#ccc;font-weight:500;font-size:12px;">${escapeHtml(m)}</td>`;
    for (let t = 0; t < 4; t++) {
      const rank = modelRanks[m][t];
      const r = perModel[m][t + 1].r;
      const display = isNaN(rank) ? 'N/A' : `#${rank}`;
      const rDisplay = isNaN(r) ? '' : ` (${r.toFixed(2)})`;
      const cls = isNaN(rank) ? '' : `rank-${rank}`;
      html += `<td class="${cls}" title="r=${isNaN(r)?'N/A':r.toFixed(3)}">${display}<span style="font-size:10px;opacity:0.7">${rDisplay}</span></td>`;
    }
    html += `</tr>`;
  }

  // Footer: Kendall's W
  html += `<tr class="footer-row"><td style="text-align:left;">Kendall's W</td>`;
  html += `<td colspan="4" style="text-align:center;">`;
  if (isNaN(kendall.W)) {
    html += `N/A (need ≥2 models with all 4 types)`;
  } else {
    const pStr = kendall.p < 0.001 ? '<0.001' : kendall.p.toFixed(3);
    const interpretation = kendall.W > 0.7 ? 'Strong agreement — one type likely dominates' :
      kendall.W > 0.4 ? 'Moderate agreement — some shared preferences' :
      'Weak agreement — models prefer different types';
    html += `W = ${kendall.W.toFixed(3)}, χ²(${kendall.df}) = ${kendall.chi2.toFixed(2)}, p = ${pStr} — ${interpretation}`;
  }
  html += `</td></tr>`;

  html += `</tbody></table>`;
  container.innerHTML = html;
}

// ============================================================
// Enhanced Calibration Summary with Scenario Diagnosis
// ============================================================
function renderCalibrationSummary() {
  const container = document.getElementById('cal-summary');
  if (!container) return;

  const activePoints = window._calActivePoints || calDataPoints;
  const varianceKey = window._calVarianceKey || 'combinedVariance';

  const corrsCombined = getCalCorrelationsPerType(calDataPoints, 'combinedVariance');
  const corrsPerType = getCalCorrelationsPerType(calDataPoints, 'withinTypeVariance');

  // Rank types by combined Pearson r
  const ranked = [1, 2, 3, 4]
    .map(t => ({ type: t, ...corrsCombined[t], perTypeR: corrsPerType[t].pearsonR, perTypeRho: corrsPerType[t].spearmanRho }))
    .sort((a, b) => {
      const ra = isNaN(a.pearsonR) ? -Infinity : a.pearsonR;
      const rb = isNaN(b.pearsonR) ? -Infinity : b.pearsonR;
      return rb - ra;
    });

  // Mean stated uncertainty per type
  const meanUncByType = {};
  for (let t = 1; t <= 4; t++) {
    const pts = calDataPoints.filter(p => p.uncertaintyType === t);
    meanUncByType[t] = pts.length > 0 ? mean(pts.map(p => p.statedUncertainty)) : NaN;
  }

  const best = ranked[0];
  let html = '';

  // Data adequacy panel
  html += renderDataAdequacy();

  // Scenario diagnosis
  html += renderScenarioDiagnosis();

  if (!isNaN(best.pearsonR)) {
    html += `<div class="cal-insight">Type ${best.type} (${TYPE_LABELS[best.type - 1]}) is the most well-calibrated uncertainty type (r = ${best.pearsonR.toFixed(3)}, p = ${best.pValue < 0.001 ? '<0.001' : best.pValue.toFixed(3)}, n = ${best.n})</div>`;
  }

  html += `<h3 style="color:#ccc;margin-bottom:12px">Calibration Summary by Type</h3>`;
  for (const entry of ranked) {
    const t = entry.type;
    html += `<div class="cal-summary-card">
      <h4>${TYPE_LABELS[t - 1]}</h4>
      <div class="metrics">
        <div>Pearson r (combined): <span class="metric-value">${isNaN(entry.pearsonR) ? 'N/A' : entry.pearsonR.toFixed(3)}</span></div>
        <div>p-value: <span class="metric-value">${isNaN(entry.pValue) ? 'N/A' : (entry.pValue < 0.001 ? '<0.001' : entry.pValue.toFixed(3))}</span></div>
        <div>Spearman rho: <span class="metric-value">${isNaN(entry.spearmanRho) ? 'N/A' : entry.spearmanRho.toFixed(3)}</span></div>
        <div>Pearson r (per-type): <span class="metric-value">${isNaN(entry.perTypeR) ? 'N/A' : entry.perTypeR.toFixed(3)}</span></div>
        <div>Mean uncertainty: <span class="metric-value">${isNaN(meanUncByType[t]) ? 'N/A' : meanUncByType[t].toFixed(3)}</span></div>
        <div>Data points: <span class="metric-value">${entry.n}</span></div>
      </div>
    </div>`;
  }

  container.innerHTML = html;
}

function renderDataAdequacy() {
  const uniqueModels = [...new Set(calDataPoints.map(p => p.model))];
  const uniquePapers = [...new Set(calDataPoints.map(p => p.paper))];

  const samplePoints = calDataPoints.filter(p => p.model === uniqueModels[0] && p.paper === uniquePapers[0] && p.dimension === DIMENSIONS[0].id && p.uncertaintyType === 1);
  const estimatedAttempts = samplePoints.length > 0 ? samplePoints.length : '?';

  const warnings = [];
  if (uniqueModels.length < 3) warnings.push(`Only ${uniqueModels.length} model(s) — need ≥3 for meaningful between-model analysis and ICC`);
  if (uniqueModels.length < 5) warnings.push(`Only ${uniqueModels.length} model(s) — Kendall's W is more reliable with ≥5 rankers`);
  if (uniquePapers.length < 3) warnings.push(`Only ${uniquePapers.length} paper(s) — between-model variance needs ≥3 papers for stable estimates`);
  if (uniquePapers.length < 10) warnings.push(`Only ${uniquePapers.length} paper(s) — ≥10 recommended for robust per-model correlations`);

  // Check min cell sizes
  let minCellN = Infinity;
  for (const dim of DIMENSIONS) {
    for (let t = 1; t <= 4; t++) {
      const n = calDataPoints.filter(p => p.dimension === dim.id && p.uncertaintyType === t).length;
      minCellN = Math.min(minCellN, n);
    }
  }
  if (minCellN < 10) warnings.push(`Smallest heatmap cell has only ${minCellN} data points — correlations are unstable below ~10`);

  const isOk = warnings.length === 0;
  let html = `<div class="cal-adequacy ${isOk ? 'ok' : ''}">`;
  html += `<strong>Data Adequacy:</strong> ${uniqueModels.length} models, ${uniquePapers.length} papers, ~${estimatedAttempts} attempts/cell`;
  if (warnings.length > 0) {
    html += `<ul>`;
    warnings.forEach(w => html += `<li>${w}</li>`);
    html += `</ul>`;
  } else {
    html += ` — sufficient data for all analyses.`;
  }
  html += `</div>`;
  return html;
}

function renderScenarioDiagnosis() {
  // Compute evidence for each of the 5 scenarios
  const varianceKey = 'combinedVariance';
  const corrsCombined = getCalCorrelationsPerType(calDataPoints, varianceKey);
  const interModel = computeInterModelCalibration(calDataPoints);
  const { allModels, perModel } = computePerModelTypeCorrelations(varianceKey);

  // Evidence for Scenario 1: One type strictly dominates
  // Check Kendall's W + whether one type is consistently #1
  const rankings = [];
  for (const m of allModels) {
    const rs = [1, 2, 3, 4].map(t => ({ type: t, r: perModel[m][t].r }));
    const sorted = [...rs].sort((a, b) => {
      if (isNaN(a.r) && isNaN(b.r)) return 0;
      if (isNaN(a.r)) return 1;
      if (isNaN(b.r)) return -1;
      return b.r - a.r;
    });
    const rankArr = new Array(4).fill(NaN);
    sorted.forEach((item, idx) => { if (!isNaN(item.r)) rankArr[item.type - 1] = idx + 1; });
    if (rankArr.every(r => !isNaN(r))) rankings.push(rankArr);
  }
  const kendall = computeKendallW(rankings);

  // Count how often each type is #1
  const wins = [0, 0, 0, 0];
  for (const rank of rankings) {
    const bestIdx = rank.indexOf(1);
    if (bestIdx >= 0) wins[bestIdx]++;
  }
  const maxWins = Math.max(...wins);
  const winnerType = wins.indexOf(maxWins) + 1;
  const winPct = rankings.length > 0 ? maxWins / rankings.length : 0;

  // Evidence for Scenario 2: Capability-dependent
  // Check if top-performing models have higher calibration than bottom-performing ones
  // Proxy for capability: average combined variance (lower = more consistent = more capable)
  const modelCapability = {};
  for (const m of allModels) {
    const pts = calDataPoints.filter(p => p.model === m && p.combinedVariance !== null);
    modelCapability[m] = pts.length > 0 ? mean(pts.map(p => p.combinedVariance)) : NaN;
  }
  const sortedByCapability = allModels.filter(m => !isNaN(modelCapability[m])).sort((a, b) => modelCapability[a] - modelCapability[b]);
  let capabilityGap = NaN;
  if (sortedByCapability.length >= 4) {
    const topHalf = sortedByCapability.slice(0, Math.floor(sortedByCapability.length / 2));
    const bottomHalf = sortedByCapability.slice(Math.floor(sortedByCapability.length / 2));
    const topMeanR = mean(topHalf.map(m => {
      const rs = [1,2,3,4].map(t => perModel[m][t].r).filter(r => !isNaN(r));
      return rs.length > 0 ? Math.max(...rs) : 0;
    }));
    const bottomMeanR = mean(bottomHalf.map(m => {
      const rs = [1,2,3,4].map(t => perModel[m][t].r).filter(r => !isNaN(r));
      return rs.length > 0 ? Math.max(...rs) : 0;
    }));
    capabilityGap = topMeanR - bottomMeanR;
  }

  // Evidence for Scenarios 4 & 5: Within vs between model
  const withinRs = [1, 2, 3, 4].map(t => isNaN(corrsCombined[t].pearsonR) ? 0 : corrsCombined[t].pearsonR);
  const betweenRs = [1, 2, 3, 4].map(t => isNaN(interModel[t].pearsonR) ? 0 : interModel[t].pearsonR);
  const avgWithinR = mean(withinRs);
  const avgBetweenR = mean(betweenRs);

  // Determine most likely scenario
  const scenarios = [];

  // Scenario 1: Strong W, clear winner
  if (!isNaN(kendall.W) && kendall.W > 0.6 && winPct > 0.6) {
    scenarios.push({ id: 1, score: kendall.W * winPct, label: `Scenario 1: Type ${winnerType} dominates`, detail: `Kendall's W=${kendall.W.toFixed(2)}, Type ${winnerType} wins ${(winPct*100).toFixed(0)}% of models` });
  }

  // Scenario 2: Capability gap
  if (!isNaN(capabilityGap) && Math.abs(capabilityGap) > 0.15) {
    const dir = capabilityGap > 0 ? 'More capable models calibrate better' : 'Less capable models calibrate better (unusual)';
    scenarios.push({ id: 2, score: Math.abs(capabilityGap), label: 'Scenario 2: Capability-dependent calibration', detail: `${dir} (gap=${capabilityGap.toFixed(2)})` });
  }

  // Scenario 3: Low W, no clear winner
  if (!isNaN(kendall.W) && kendall.W < 0.4) {
    scenarios.push({ id: 3, score: 1 - kendall.W, label: 'Scenario 3: Models prefer different types', detail: `Kendall's W=${kendall.W.toFixed(2)} (weak agreement)` });
  }

  // Scenario 4: High within-r, low between-r
  if (avgWithinR > 0.15 && avgBetweenR < 0.1) {
    scenarios.push({ id: 4, score: avgWithinR - avgBetweenR, label: 'Scenario 4: Good self-calibration, poor inter-model', detail: `Avg within r=${avgWithinR.toFixed(2)}, avg between r=${avgBetweenR.toFixed(2)}` });
  }

  // Scenario 5: Low within-r, high between-r
  if (avgBetweenR > 0.15 && avgWithinR < 0.1) {
    scenarios.push({ id: 5, score: avgBetweenR - avgWithinR, label: 'Scenario 5: Good inter-model, overconfident individually', detail: `Avg within r=${avgWithinR.toFixed(2)}, avg between r=${avgBetweenR.toFixed(2)}` });
  }

  // Sort by score
  scenarios.sort((a, b) => b.score - a.score);

  let html = `<div class="cal-scenario">`;
  html += `<strong>Scenario Diagnosis</strong><br>`;
  if (scenarios.length === 0) {
    html += `No clear scenario detected — data may be insufficient or results are mixed across all scenarios.`;
    html += `<br><span style="font-size:12px;color:#888;">Within-model avg r=${avgWithinR.toFixed(2)}, Between-model avg r=${avgBetweenR.toFixed(2)}`;
    if (!isNaN(kendall.W)) html += `, Kendall's W=${kendall.W.toFixed(2)}`;
    html += `</span>`;
  } else {
    html += `<strong>Most likely: ${scenarios[0].label}</strong><br>`;
    html += `<span style="font-size:13px;">${scenarios[0].detail}</span>`;
    if (scenarios.length > 1) {
      html += `<br><br>Other signals:`;
      for (let i = 1; i < scenarios.length; i++) {
        html += `<br>- ${scenarios[i].label}: ${scenarios[i].detail}`;
      }
    }
  }
  html += `</div>`;
  return html;
}

// Init
loadKeys();
loadModels();
updateCost();
loadHistory();
