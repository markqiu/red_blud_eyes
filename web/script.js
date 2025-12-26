/*
  红蓝眼谜题可视化

  当前模式：本地后端驱动（/api/*），前端仅负责展示。
  - 后端负责：村民类型（dummy/openai）、推理与离开规则、日志
  - 前端负责：渲染视角/日志/验证结果
*/

/** @typedef {'RED'|'BLUE'} EyeColor */

/**
 * @typedef {Object} Villager
 * @property {number} id
 * @property {string} name
 * @property {EyeColor} eyeColor
 * @property {string} villagerType
 * @property {boolean} hasLeft
 * @property {number|null} leftOnDay
 * @property {number} observedRedEyes
 * @property {string[]} reasoningLog
 */

/**
 * @typedef {Object} VillageState
 * @property {number} numRed
 * @property {number} numBlue
 * @property {boolean} announcementMade
 * @property {number} currentDay
 * @property {number} knowledgeLevel  // -1 means common knowledge (infinite)
 * @property {Villager[]} villagers
 * @property {string[]} dailyLog
 */

const $ = (id) => document.getElementById(id);

/** @type {VillageState|null} */
let state = null;

/** @type {boolean} */
let isAdvancingDay = false;

function nextPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

async function apiFetch(path, options) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  const data = await res.json().catch(() => null);
  if (!res.ok || !data || data.ok !== true) {
    const message = (data && data.error) ? data.error : `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data;
}

async function refreshState() {
  try {
    const data = await apiFetch('/api/state', { method: 'GET' });
    state = data.state;
  } catch (e) {
    state = null;
  }
  render();
}

function clampInt(value, min, max) {
  const n = Number.parseInt(String(value), 10);
  if (Number.isNaN(n)) return min;
  return Math.max(min, Math.min(max, n));
}

function buildVillage(numRed, numBlue) {
  /** @type {Villager[]} */
  const villagers = [];

  for (let i = 0; i < numRed; i++) {
    villagers.push({
      id: villagers.length + 1,
      name: `红${i + 1}`,
      eyeColor: 'RED',
      hasLeft: false,
      leftOnDay: null,
      observedRedEyes: 0,
      reasoningLog: [],
    });
  }

  for (let i = 0; i < numBlue; i++) {
    villagers.push({
      id: villagers.length + 1,
      name: `蓝${i + 1}`,
      eyeColor: 'BLUE',
      hasLeft: false,
      leftOnDay: null,
      observedRedEyes: 0,
      reasoningLog: [],
    });
  }

  /** @type {VillageState} */
  const s = {
    numRed,
    numBlue,
    announcementMade: false,
    currentDay: 0,
    knowledgeLevel: 0,
    villagers,
    dailyLog: [],
  };

  updateObservations(s);
  s.dailyLog.push(`初始化：红眼睛 ${numRed} 人，蓝眼睛 ${numBlue} 人`);
  s.dailyLog.push(describeKnowledgeBeforeAnnouncement(s));
  return s;
}

function describeKnowledgeBeforeAnnouncement(s) {
  const n = s.numRed;
  if (n === 0) return '宣布前：没有红眼睛，命题 p₀ 不成立。';
  if (n === 1) return '宣布前：唯一红眼睛看不到红眼睛，无法知道 p₀（存在红眼睛）。';
  return `宣布前：p₀ 被所有人知道，但最大知识阶数有限（约为 ${n - 1} 阶）。`;
}

function describeKnowledgeAfterAnnouncement() {
  return '宣布后：命题“至少有一个红眼睛”成为公共知识（无限阶）。';
}

function updateObservations(s) {
  for (const v of s.villagers) {
    if (v.hasLeft) {
      v.observedRedEyes = 0;
      continue;
    }
    let count = 0;
    for (const other of s.villagers) {
      if (other.id === v.id) continue;
      if (other.hasLeft) continue;
      if (other.eyeColor === 'RED') count++;
    }
    v.observedRedEyes = count;
  }
}

function makeAnnouncement(s) {
  if (s.announcementMade) return;

  s.announcementMade = true;
  s.knowledgeLevel = -1;
  s.dailyLog.push(`🎤 游客公开宣布：'村庄里至少有一个红眼睛的人！'`);
  s.dailyLog.push('💡 变量变化：announcementMade = true');
  s.dailyLog.push('💡 变量变化：knowledgeLevel = -1（公共知识）');
  s.dailyLog.push(describeKnowledgeAfterAnnouncement());
}

/**
 * 复刻当前 Python 版的核心推理结构（但在日志里强调“第N天离开”来自归纳推导）
 * @param {Villager} v
 * @param {number} day
 * @param {boolean} announcementMade
 * @returns {boolean}
 */
function reasonAndDecide(v, day, announcementMade) {
  if (v.hasLeft) return false;

  if (!announcementMade) {
    v.reasoningLog.push(
      `第${day}天：没有公开宣布。我仍会尝试推理，但缺少“至少一人红眼”的公共知识基准，` +
        `归纳链条无法闭合，所以无法确定自己该不该离开。`
    );
    return false;
  }

  if (v.eyeColor === 'BLUE') {
    v.reasoningLog.push(`第${day}天：我看到 ${v.observedRedEyes} 个红眼睛。我是蓝眼睛，不需要离开。`);
    return false;
  }

  // 红眼睛：归纳基础 + 归纳步骤
  if (v.observedRedEyes === 0) {
    if (day === 1) {
      v.reasoningLog.push(
        `第${day}天：[归纳基础] 我看到0个红眼睛，但游客说至少有一个。只能是我 → 我是红眼睛，今晚离开。`
      );
      return true;
    }
    // day>1 的情况下其实不会发生（因为 day=1 就会走）
    v.reasoningLog.push(`第${day}天：我看到0个红眼睛（理论上第1天就应离开）。`);
    return false;
  }

  const k = v.observedRedEyes;
  const myLeaveDay = k + 1;

  if (day < myLeaveDay) {
    v.reasoningLog.push(
      `第${day}天：[归纳推理] 我看到${k}个红眼睛。假设我是蓝眼睛，则只有${k}个红眼睛；` +
        `按归纳链条，这${k}个红眼睛会在第${k}天离开。我继续等待。`
    );
    return false;
  }

  if (day === myLeaveDay) {
    v.reasoningLog.push(
      `第${day}天：[归纳推理完成] 昨天（第${k}天）没人离开。若只有${k}个红眼睛，按归纳链条他们应在第${k}天离开；` +
        `既然没离开，说明“我是蓝眼睛”的假设错误 → 我也是红眼睛，今晚离开。`
    );
    return true;
  }

  // 理论上到不了这里（因为到 myLeaveDay 就离开）
  return false;
}

function simulateDay(s) {
  if (isFinished(s)) {
    s.dailyLog.push('✅ 已结束：所有红眼睛已离开。');
    return;
  }

  s.currentDay += 1;
  s.dailyLog.push(`\n=== 第 ${s.currentDay} 天 ===`);

  if (!s.announcementMade) {
    s.dailyLog.push(
      '🚫 无游客宣布：大家仍会思考，但缺少“至少一人红眼”的公共知识基准，' +
        '归纳链条无法闭合（预期无人离开）。'
    );
  }

  updateObservations(s);

  /** @type {Villager[]} */
  const leaving = [];
  for (const v of s.villagers) {
    if (v.hasLeft) continue;
    const shouldLeave = reasonAndDecide(v, s.currentDay, s.announcementMade);
    if (shouldLeave) leaving.push(v);
  }

  if (leaving.length === 0) {
    s.dailyLog.push('😴 今天没有人离开。');
  } else {
    for (const v of leaving) {
      v.hasLeft = true;
      v.leftOnDay = s.currentDay;
      s.dailyLog.push(`🚶 ${v.name}（红眼睛）离开了村庄。`);
    }
  }

  updateObservations(s);

  if (isFinished(s)) {
    const expected = s.numRed;
    s.dailyLog.push('\n=== 验证 ===');
    if (expected === 0) {
      s.dailyLog.push('ℹ️ 没有红眼睛：没有人需要离开。');
    } else if (!s.announcementMade) {
      s.dailyLog.push('ℹ️ 未进行游客宣布：预期现象是永远不会有人离开。');
    } else {
      s.dailyLog.push(`预期：所有 ${expected} 个红眼睛在第 ${expected} 天离开。`);
      s.dailyLog.push(`实际：第 ${s.currentDay} 天红眼睛全部离开。`);
    }
  }
}

function isFinished(s) {
  if (s.numRed === 0) return true;
  for (const v of s.villagers) {
    if (v.eyeColor === 'RED' && !v.hasLeft) return false;
  }
  return true;
}

function computeVerification(s) {
  if (s == null) return { status: '—', ok: null };
  if (s.numRed === 0) return { status: '无需离开', ok: true };

  const allRedLeft = s.villagers.every((v) => (v.eyeColor !== 'RED') || v.hasLeft);
  if (!allRedLeft) return { status: '进行中', ok: null };

  const leftDays = s.villagers
    .filter((v) => v.eyeColor === 'RED')
    .map((v) => v.leftOnDay)
    .filter((d) => typeof d === 'number');

  if (leftDays.length !== s.numRed) return { status: '异常', ok: false };

  const uniqueDays = new Set(leftDays);
  const sameDay = uniqueDays.size === 1;
  const day = leftDays[0] ?? null;
  const expected = s.numRed;
  const ok = sameDay && day === expected;
  return { status: ok ? '验证通过' : '验证失败', ok };
}

function render() {
  // Controls
  const btnInit = $('btnInit');
  const btnAnnounce = $('btnAnnounce');
  const btnNext = $('btnNext');
  const btnRunAll = $('btnRunAll');
  const btnReset = $('btnReset');

  // KPI
  const kpiDay = $('kpiDay');
  const kpiAnnounce = $('kpiAnnounce');
  const kpiKnowledge = $('kpiKnowledge');
  const kpiVerify = $('kpiVerify');

  // Panels
  const villagersEl = $('villagers');
  const dailyLogEl = $('dailyLog');
  const villagerSelect = $('villagerSelect');
  const reasoningLogEl = $('reasoningLog');

  if (!state) {
    kpiDay.textContent = '0';
    kpiAnnounce.textContent = '未宣布';
    kpiKnowledge.textContent = '0';
    kpiVerify.textContent = '—';

    villagersEl.innerHTML = '';
    dailyLogEl.textContent = '请先点击“初始化村庄”。（需要先启动后端：uv run python -m src.web_server）';
    villagerSelect.innerHTML = '';
    reasoningLogEl.textContent = '';

    btnAnnounce.disabled = true;
    btnNext.disabled = true;
    btnRunAll.disabled = true;
    btnReset.disabled = false;
    return;
  }

  kpiDay.textContent = String(state.currentDay);
  kpiAnnounce.textContent = state.announcementMade ? '已宣布' : '未宣布';
  kpiKnowledge.textContent = state.knowledgeLevel === -1 ? '∞（公共知识）' : String(state.knowledgeLevel);

  const verify = computeVerification(state);
  if (verify.ok === true) {
    kpiVerify.innerHTML = '<span class="ok">验证通过</span>';
  } else if (verify.ok === false) {
    kpiVerify.innerHTML = '<span class="warn">验证失败</span>';
  } else {
    kpiVerify.textContent = verify.status;
  }

  // Buttons state
  btnAnnounce.disabled = state.announcementMade;
  // 允许“未宣布”也能推进天数，用于演示“无宣布则无人离开”
  btnNext.disabled = isFinished(state) || isAdvancingDay;
  btnRunAll.disabled = isFinished(state);
  btnReset.disabled = false;

  // Progress indicator for slow backends (e.g., all-OpenAI mode)
  btnNext.textContent = isAdvancingDay ? '下一天（请求中…）' : '下一天';

  // Villagers cards (show remaining, but also keep left ones visible as status)
  const cards = [];
  for (const v of state.villagers) {
    const dotClass = v.eyeColor === 'RED' ? 'red' : 'blue';
    const eyeText = v.eyeColor === 'RED' ? '红眼睛' : '蓝眼睛';
    const status = v.hasLeft ? `已离开（第${v.leftOnDay}天）` : '在村庄中';
    const sees = v.hasLeft ? '—' : `${v.observedRedEyes} 个红眼睛`;
    const typeText = v.villagerType || 'dummy';
    const typePill = typeText === 'openai'
      ? '<span class="pill" style="margin-left:6px;">🧠 OpenAI</span>'
      : '<span class="pill" style="margin-left:6px;">🧩 dummy</span>';

    cards.push(`
      <div class="v">
        <div class="top">
          <div>
            <div class="name">${escapeHtml(v.name)}</div>
            <div style="margin-top:6px;">
              <span class="pill"><span class="dot ${dotClass}"></span>${eyeText}</span>
              ${typePill}
            </div>
          </div>
          <div class="pill"><span class="dot ok"></span>视角</div>
        </div>
        <div class="meta">我看到：<strong>${escapeHtml(sees)}</strong></div>
        <div class="status">状态：<strong>${escapeHtml(status)}</strong></div>
      </div>
    `);
  }
  villagersEl.innerHTML = cards.join('');

  // Logs
  dailyLogEl.textContent = state.dailyLog.join('\n');

  // Villager select
  const selected = villagerSelect.value ? Number(villagerSelect.value) : null;
  villagerSelect.innerHTML = state.villagers
    .map((v) => {
      const t = v.villagerType || 'dummy';
      const tLabel = t === 'openai' ? 'OpenAI' : 'dummy';
      return `<option value="${v.id}">${escapeHtml(v.name)}（${v.eyeColor === 'RED' ? '红' : '蓝'}，${tLabel}）</option>`;
    })
    .join('');

  // Restore selection if possible
  if (selected && state.villagers.some((v) => v.id === selected)) {
    villagerSelect.value = String(selected);
  }

  const currentId = Number(villagerSelect.value);
  const villager = state.villagers.find((v) => v.id === currentId);
  reasoningLogEl.textContent = villager ? villager.reasoningLog.join('\n') : '';
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function wireEvents() {
  $('btnInit').addEventListener('click', () => {
    const n = clampInt($('numRed').value, 0, 200);
    const m = clampInt($('numBlue').value, 0, 200);
    const villagerMode = String($('villagerMode')?.value || 'mixed_ends');
    const openaiStyle = String($('openaiStyle')?.value || 'social');

    apiFetch('/api/init', {
      method: 'POST',
      body: JSON.stringify({ numRed: n, numBlue: m, villagerMode, openaiStyle }),
    })
      .then((data) => {
        state = data.state;
        render();
      })
      .catch((e) => {
        state = null;
        render();
        alert(`初始化失败：${e.message}`);
      });
  });

  $('btnAnnounce').addEventListener('click', () => {
    if (!state) return;
    apiFetch('/api/announce', { method: 'POST', body: '{}' })
      .then((data) => {
        state = data.state;
        render();
      })
      .catch((e) => alert(`宣布失败：${e.message}`));
  });

  $('btnNext').addEventListener('click', async () => {
    if (!state) return;
    // Strict check: if already advancing, completely ignore this click.
    if (isAdvancingDay) return;
    
    isAdvancingDay = true;
    render();

    // Yield once so the "busy" UI state is painted before a slow request.
    await nextPaint();

    try {
      const data = await apiFetch('/api/next', { method: 'POST', body: '{}' });
      state = data.state;
    } catch (e) {
      alert(`推进失败：${e.message}`);
    } finally {
      isAdvancingDay = false;
      render();
    }
  });

  $('btnRunAll').addEventListener('click', () => {
    if (!state) return;
    apiFetch('/api/run_all', { method: 'POST', body: '{}' })
      .then((data) => {
        state = data.state;
        render();
      })
      .catch((e) => alert(`跑到结束失败：${e.message}`));
  });

  $('btnReset').addEventListener('click', () => {
    apiFetch('/api/reset', { method: 'POST', body: '{}' })
      .then((data) => {
        state = data.state;
        render();
      })
      .catch(() => {
        state = null;
        render();
      });
  });

  $('villagerSelect').addEventListener('change', () => {
    render();
  });
}

async function setupPasswordVerification() {
  const passwordPrompt = document.getElementById('passwordPrompt');
  const passwordInput = document.getElementById('passwordInput');
  const passwordBtn = document.getElementById('passwordBtn');
  const passwordError = document.getElementById('passwordError');
  const mainEl = document.querySelector('main');

  // 检查是否已通过密码验证
  const isAuthenticated = sessionStorage.getItem('authenticated') === 'true';
  if (isAuthenticated) {
    passwordPrompt.style.display = 'none';
    mainEl.style.display = 'block';
    return; // 密码已验证，直接初始化应用
  }

  // 显示密码提示框
  passwordPrompt.style.display = 'flex';
  mainEl.style.display = 'none';

  const checkPassword = async () => {
    const password = passwordInput.value.trim();
    if (!password) {
      passwordError.style.display = 'block';
      return;
    }

    try {
      const response = await fetch('/api/verify_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      const data = await response.json();
      if (data.valid) {
        sessionStorage.setItem('authenticated', 'true');
        passwordPrompt.style.display = 'none';
        mainEl.style.display = 'block';
        init(); // 初始化应用
      } else {
        passwordError.style.display = 'block';
        passwordInput.value = '';
      }
    } catch (error) {
      console.error('Password verification failed:', error);
      passwordError.style.display = 'block';
    }
  };

  passwordBtn.addEventListener('click', checkPassword);
  passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') checkPassword();
  });
}

function init() {
  wireEvents();
  refreshState();
}

// Setup password verification first, then init app after authentication
setupPasswordVerification().catch(console.error);
