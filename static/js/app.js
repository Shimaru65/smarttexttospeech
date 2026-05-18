'use strict';

/* =====================================================
   SmartTextToSpeech — Frontend Application
   ===================================================== */

const App = (() => {
  // ── State ────────────────────────────────────────────
  let languages    = {};
  let currentLang  = 'th-TH';
  let currentGender = 'female';
  let currentAudioUrl = null;
  let currentFilename = null;

  // ── DOM refs ─────────────────────────────────────────
  const $ = id => document.getElementById(id);

  const el = {
    themeBtn:     $('themeBtn'),
    langSelect:   $('langSelect'),
    voiceSelect:  $('voiceSelect'),
    genderBtns:   document.querySelectorAll('.gender-tab'),
    speedSlider:  $('speedSlider'),
    speedVal:     $('speedVal'),
    pitchSlider:  $('pitchSlider'),
    pitchVal:     $('pitchVal'),
    textInput:    $('textInput'),
    charCount:    $('charCount'),
    generateBtn:  $('generateBtn'),
    btnText:      $('btnText'),
    btnIcon:      $('btnIcon'),
    statusBar:    $('statusBar'),
    statusIcon:   $('statusIcon'),
    statusMsg:    $('statusMsg'),
    progressWrap: $('progressWrap'),
    playerCard:   $('playerCard'),
    audioEl:      $('audioEl'),
    fileInfo:     $('fileInfo'),
    downloadBtn:  $('downloadBtn'),
    statChars:    $('statChars'),
    statWords:    $('statWords'),
    statSize:     $('statSize'),
  };

  // ── Theme ─────────────────────────────────────────────
  function initTheme() {
    const saved = localStorage.getItem('tts-theme') || 'dark';
    applyTheme(saved);
    el.themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    el.themeBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
    localStorage.setItem('tts-theme', theme);
  }

  // ── Load languages from API ───────────────────────────
  async function loadLanguages() {
    try {
      const res  = await fetch('/api/languages');
      languages  = await res.json();
      populateLangSelect();
      updateVoiceList();
    } catch (err) {
      showStatus('error', '⚠️ ไม่สามารถโหลดข้อมูลภาษาได้ — ' + err.message);
    }
  }

  function populateLangSelect() {
    el.langSelect.innerHTML = '';
    for (const [code, info] of Object.entries(languages)) {
      const opt = document.createElement('option');
      opt.value = code;
      opt.textContent = `${info.flag}  ${info.name}`;
      if (code === 'th-TH') opt.selected = true;
      el.langSelect.appendChild(opt);
    }
  }

  // ── Voice List ────────────────────────────────────────
  function updateVoiceList() {
    currentLang = el.langSelect.value;
    const voices = getFilteredVoices();
    el.voiceSelect.innerHTML = '';
    if (!voices.length) {
      const opt = document.createElement('option');
      opt.textContent = '— No voices available —';
      el.voiceSelect.appendChild(opt);
      return;
    }
    voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = v.display;
      el.voiceSelect.appendChild(opt);
    });
  }

  function getFilteredVoices() {
    const langData = languages[currentLang];
    if (!langData) return [];
    return langData.voices.filter(v => v.gender === currentGender);
  }

  // ── Gender tabs ───────────────────────────────────────
  function initGenderTabs() {
    el.genderBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        el.genderBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentGender = btn.dataset.gender;
        updateVoiceList();
      });
    });
  }

  // ── Sliders ───────────────────────────────────────────
  function initSliders() {
    el.speedSlider.addEventListener('input', () => {
      const v = parseInt(el.speedSlider.value);
      el.speedVal.textContent = v > 0 ? `+${v}%` : `${v}%`;
    });
    el.pitchSlider.addEventListener('input', () => {
      const v = parseInt(el.pitchSlider.value);
      el.pitchVal.textContent = v > 0 ? `+${v}Hz` : `${v}Hz`;
    });
  }

  // ── Character Counter ─────────────────────────────────
  function initCharCounter() {
    el.textInput.addEventListener('input', updateCharCount);
  }

  function updateCharCount() {
    const len  = el.textInput.value.length;
    const max  = 5000;
    el.charCount.textContent = `${len.toLocaleString()} / ${max.toLocaleString()}`;
    el.charCount.className   = 'char-count';
    if (len > max * 0.9) el.charCount.classList.add('warn');
    if (len > max)       el.charCount.classList.add('error');
    const words = el.textInput.value.trim().split(/\s+/).filter(Boolean).length;
    el.statChars.textContent = len.toLocaleString();
    el.statWords.textContent = words.toLocaleString();
  }

  // ── Status Bar ────────────────────────────────────────
  function showStatus(type, msg, showProgress = false) {
    el.statusBar.className  = `status-bar show ${type}`;
    el.statusMsg.textContent = msg;
    el.progressWrap.style.display = showProgress ? 'block' : 'none';

    const icons = { loading: '⏳', success: '✅', error: '❌' };
    el.statusIcon.textContent = icons[type] || '';
  }

  function hideStatus() {
    el.statusBar.classList.remove('show');
  }

  // ── Generate Speech ───────────────────────────────────
  async function generateSpeech() {
    const text = el.textInput.value.trim();
    if (!text) {
      showStatus('error', '⚠️ กรุณาพิมพ์หรือวางข้อความก่อน');
      el.textInput.focus();
      return;
    }

    const voice = el.voiceSelect.value;
    const rate  = parseInt(el.speedSlider.value);
    const pitch = parseInt(el.pitchSlider.value);

    // UI: loading state
    el.generateBtn.disabled = true;
    el.btnText.textContent  = 'กำลังสร้างเสียง...';
    el.btnIcon.innerHTML    = '<div class="spinner"></div>';
    showStatus('loading', 'กำลังประมวลผลข้อความ — โปรดรอสักครู่...', true);

    try {
      const res  = await fetch('/api/generate', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text, voice, rate, pitch }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || 'เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ');
      }

      // Success
      currentAudioUrl  = data.url;
      currentFilename  = data.filename;
      const sizeKB     = Math.round(data.file_size / 1024);
      el.statSize.textContent  = `${sizeKB} KB`;
      el.fileInfo.textContent  = `MP3 · ${sizeKB} KB`;

      el.audioEl.src = data.url;
      el.audioEl.load();
      el.downloadBtn.href = data.download_url;
      el.playerCard.classList.add('show');
      el.playerCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      showStatus('success', '✨ สร้างไฟล์เสียงสำเร็จ! กดปุ่ม Play เพื่อฟัง หรือ Download เพื่อบันทึก');

    } catch (err) {
      showStatus('error', '❌ ' + err.message);
      el.playerCard.classList.remove('show');
    } finally {
      el.generateBtn.disabled = false;
      el.btnText.textContent  = 'สร้างเสียงพูด';
      el.btnIcon.textContent  = '🎙️';
    }
  }

  // ── Event Wiring ──────────────────────────────────────
  function bindEvents() {
    el.langSelect.addEventListener('change', updateVoiceList);
    el.generateBtn.addEventListener('click', generateSpeech);

    el.textInput.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        generateSpeech();
      }
    });

    el.textInput.addEventListener('paste', () => {
      setTimeout(updateCharCount, 0);
    });
  }

  // ── Init ──────────────────────────────────────────────
  function init() {
    initTheme();
    initGenderTabs();
    initSliders();
    initCharCounter();
    bindEvents();
    loadLanguages();
    updateCharCount();

    // Pre-fill demo text for Thai
    if (!el.textInput.value) {
      el.textInput.value = 'สวัสดีครับ ยินดีต้อนรับสู่แอปพลิเคชันแปลงข้อความเป็นเสียงพูด คุณสามารถพิมพ์ข้อความภาษาไทยหรือภาษาอื่นๆ แล้วกดปุ่มสร้างเสียงพูดได้เลย';
      updateCharCount();
    }
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', App.init);
