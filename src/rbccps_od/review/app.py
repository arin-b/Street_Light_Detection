from __future__ import annotations

import argparse
import json
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from rbccps_od.review.repository import MODE_ORDER, OUTPUT_ROOT, ReviewRepository

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Streetlight Review App</title>
  <style>
    :root {
      --bg: #f5efe5;
      --panel: rgba(255, 251, 245, 0.88);
      --ink: #171410;
      --muted: #6d6458;
      --accent: #0f5a4a;
      --accent2: #b14f2d;
      --line: rgba(114, 96, 79, 0.22);
      --ok: #2d6a4f;
      --warn: #a15c00;
      --bad: #9c2f2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(17, 90, 74, 0.10), transparent 26%),
        radial-gradient(circle at top right, rgba(177, 79, 45, 0.10), transparent 24%),
        linear-gradient(180deg, #f7f1e8 0%, #ece3d5 100%);
      color: var(--ink);
    }
    .shell {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 18px;
      padding: 18px;
      min-height: 100vh;
    }
    .panel {
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: 0 18px 50px rgba(20, 20, 20, 0.08);
      padding: 16px;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 {
      font-size: 32px;
      letter-spacing: -0.04em;
      margin-bottom: 10px;
    }
    .hero {
      padding: 12px 2px 14px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 14px;
    }
    .hero p {
      color: var(--muted);
      line-height: 1.45;
      margin-bottom: 0;
    }
    .mode-list button, .action-grid button, .secondary-grid button, .scene-grid button, .toolbar button, .signoff button {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 12px 14px;
      border-radius: 12px;
      text-align: left;
      cursor: pointer;
      margin-bottom: 8px;
      font-size: 14px;
    }
    .mode-list button.active, .action-grid button.active, .secondary-grid button.active, .scene-grid button.active, .toolbar button.active {
      background: #e5f1ed;
      border-color: var(--accent);
    }
    .mode-list button {
      padding: 14px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,246,241,0.95));
    }
    .mode-list button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .counts {
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }
    .canvas-wrap {
      background: #161616;
      border-radius: 20px;
      overflow: hidden;
      border: 1px solid #000;
      min-height: 420px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    canvas {
      max-width: 100%;
      display: block;
      cursor: crosshair;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 16px;
    }
    .meta-card {
      background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(248,241,232,0.94));
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 10px;
      font-size: 13px;
    }
    .meta-card strong {
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .workspace {
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 18px;
    }
    .review-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 14px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(247,240,232,0.95));
    }
    .review-title {
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.03em;
    }
    .review-subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .nav-strip {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .nav-strip button {
      border: 1px solid var(--line);
      background: white;
      border-radius: 12px;
      padding: 10px 12px;
      cursor: pointer;
      font-weight: 600;
    }
    .nav-strip button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .position-chip {
      font-size: 12px;
      color: var(--muted);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(255,255,255,0.85);
    }
    .hidden { display: none; }
    .section-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .toolbar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-top: 12px;
    }
    .toolbar button { text-align: center; }
    .status-pill {
      display: inline-block;
      font-size: 12px;
      border-radius: 999px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      margin-right: 6px;
      margin-bottom: 8px;
      background: #fff;
    }
    .footer {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 16px;
    }
    .footer button {
      flex: 1;
      border-radius: 12px;
      border: none;
      padding: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .save-btn { background: var(--accent); color: white; }
    .refresh-btn { background: #eee2d2; color: var(--ink); }
    .signoff button { background: #efe7da; font-weight: 600; }
    .message {
      min-height: 22px;
      color: var(--accent2);
      font-size: 13px;
      margin: 8px 0 0;
    }
    .hint-card {
      margin-top: 14px;
      padding: 12px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(15,90,74,0.08), rgba(15,90,74,0.02));
      border: 1px solid rgba(15,90,74,0.14);
      font-size: 13px;
      color: #284238;
      line-height: 1.45;
    }
    .hint-card strong {
      display: block;
      margin-bottom: 6px;
      color: var(--accent);
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="panel">
      <div class="hero">
        <h1>Streetlight Review</h1>
        <p>Click-only audit for full-visible-luminaire positives, hard negatives, and scene buckets.</p>
      </div>
      <div id="modeList" class="mode-list"></div>
      <div class="signoff hidden" id="signoffWrap">
        <button id="signoffBtn">Sign Off Current Mode</button>
      </div>
      <div class="message" id="modeMessage"></div>
    </div>
    <div class="panel">
      <div id="workspace" class="workspace hidden">
        <div>
          <div class="review-header">
            <div>
              <h2 class="review-title" id="reviewTitle">Loading</h2>
              <p class="review-subtitle" id="reviewSubtitle"></p>
            </div>
            <div class="nav-strip">
              <button id="prevBtn">Previous</button>
              <button id="nextBtn">Next</button>
              <span class="position-chip" id="positionChip">0 / 0</span>
            </div>
          </div>
          <div class="meta-grid" id="metaGrid"></div>
          <div class="canvas-wrap">
            <canvas id="reviewCanvas"></canvas>
          </div>
          <div id="boxTools" class="hidden">
            <div class="section-label">Fix Box Tools</div>
            <div class="toolbar">
              <button id="toggleDrawBtn">Enable Box Draw</button>
              <button id="undoBoxBtn">Undo Last</button>
              <button id="clearBoxesBtn">Clear Boxes</button>
              <button id="resetBoxesBtn">Reset Boxes</button>
            </div>
            <div class="hint-card">
              <strong>Fix workflow</strong>
              Choose `Fix`, pick the reason, select the scene bucket, then click `Enable Box Draw`. Drag new boxes on the image. Use `Clear Boxes` if you want to replace everything.
            </div>
          </div>
        </div>
        <div>
          <div class="section-label">Decision</div>
          <div class="action-grid" id="actionGrid"></div>
          <div id="secondarySection" class="hidden">
            <div class="section-label">Reason</div>
            <div class="secondary-grid" id="secondaryGrid"></div>
          </div>
          <div id="sceneSection" class="hidden">
            <div class="section-label">Scene Bucket</div>
            <div class="scene-grid" id="sceneGrid"></div>
          </div>
          <div class="footer">
            <button class="refresh-btn" id="reloadBtn">Reload Item</button>
            <button class="save-btn" id="saveBtn">Save Review</button>
          </div>
          <div class="message" id="itemMessage"></div>
        </div>
      </div>
      <div id="emptyState">
        <h2>Loading</h2>
      </div>
    </div>
  </div>
  <script>
    const state = {
      bootstrap: null,
      activeMode: null,
      currentItem: null,
      image: null,
      imageScale: 1,
      currentDecision: '',
      currentReason: '',
      currentScene: '',
      editBoxes: [],
      drawingEnabled: false,
      dragStart: null,
      dragCurrent: null,
    };

    const canvas = document.getElementById('reviewCanvas');
    const ctx = canvas.getContext('2d');

    async function fetchJson(url, options={}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: response.statusText}));
        throw new Error(payload.error || response.statusText);
      }
      return response.json();
    }

    function setMessage(id, text) {
      document.getElementById(id).textContent = text || '';
    }

    function syncCanvasCursor() {
      canvas.style.cursor = state.drawingEnabled ? 'crosshair' : 'default';
    }

    function getCanvasPoint(event) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return [
        (event.clientX - rect.left) * scaleX,
        (event.clientY - rect.top) * scaleY,
      ];
    }

    function buildModeList() {
      const wrap = document.getElementById('modeList');
      wrap.innerHTML = '';
      for (const mode of state.bootstrap.modes) {
        const btn = document.createElement('button');
        btn.disabled = !mode.unlocked;
        if (mode.mode === state.activeMode) {
          btn.classList.add('active');
        }
        const baselineNote = mode.baseline_completed ? ` - ${mode.baseline_completed} baseline` : '';
        const subsetNote = mode.subset_enabled ? ` - active ${mode.active_reviewed}/${mode.active_total}` : '';
        btn.innerHTML = `<strong>${mode.label}</strong><div class="counts">${mode.reviewed}/${mode.total} reviewed${subsetNote}${baselineNote}${mode.signed_off ? ' - signed off' : ''}</div>`;
        btn.onclick = () => {
          if (!mode.unlocked) return;
          state.activeMode = mode.mode;
          loadCurrentItem();
        };
        wrap.appendChild(btn);
      }
    }

    function buildButtons(containerId, options, currentValue, onClick) {
      const wrap = document.getElementById(containerId);
      wrap.innerHTML = '';
      for (const option of options) {
        const btn = document.createElement('button');
        btn.textContent = option.label;
        if (option.id === currentValue) {
          btn.classList.add('active');
        }
        btn.onclick = () => onClick(option.id);
        wrap.appendChild(btn);
      }
    }

    function renderMeta(item) {
      document.getElementById('reviewTitle').textContent = `${item.dataset_id} / ${item.clip_id}`;
      document.getElementById('reviewSubtitle').textContent = `${item.frame_id} - ${state.bootstrap.modes.find(m => m.mode === state.activeMode).label}`;
      document.getElementById('positionChip').textContent = `${item.position} / ${item.mode_status.total}`;
      document.getElementById('prevBtn').disabled = !item.prev_key;
      document.getElementById('nextBtn').disabled = !item.next_key;
      const meta = document.getElementById('metaGrid');
      const cards = [
        ['Mode', state.bootstrap.modes.find(m => m.mode === state.activeMode).label],
        ['Dataset', item.dataset_id],
        ['Clip', item.clip_id],
        ['Frame', item.frame_id],
        ['Queue Position', `${item.active_position} / ${item.active_total}`],
        ['Boxes', String(item.boxes.length || item.annotation_count || 0)],
        ['Baseline Completed', String(item.mode_status.baseline_completed || 0)],
        ['Current Split', item.current_split_v2 || item.source_pool || 'n/a'],
      ];
      meta.innerHTML = cards.map(([label, value]) => `<div class="meta-card"><strong>${label}</strong>${value}</div>`).join('');
    }

    function drawCanvas() {
      if (!state.image) return;
      const maxWidth = Math.min(1200, state.image.naturalWidth);
      const scale = maxWidth / state.image.naturalWidth;
      const width = Math.round(state.image.naturalWidth * scale);
      const height = Math.round(state.image.naturalHeight * scale);
      state.imageScale = scale;
      canvas.width = width;
      canvas.height = height;
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(state.image, 0, 0, width, height);
      ctx.lineWidth = 2;
      ctx.font = '16px Segoe UI';
      for (const box of state.editBoxes) {
        ctx.strokeStyle = '#00c2ff';
        ctx.fillStyle = '#00c2ff';
        const [x, y, w, h] = box;
        ctx.strokeRect(x * scale, y * scale, w * scale, h * scale);
      }
      if (state.dragStart && state.dragCurrent) {
        const [sx, sy] = state.dragStart;
        const [cx, cy] = state.dragCurrent;
        ctx.strokeStyle = '#ffce45';
        ctx.strokeRect(sx, sy, cx - sx, cy - sy);
      }
    }

    async function loadImage() {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          state.image = img;
          drawCanvas();
          resolve();
        };
        img.onerror = reject;
        img.src = `/image?mode=${encodeURIComponent(state.activeMode)}&key=${encodeURIComponent(state.currentItem.key)}&t=${Date.now()}`;
      });
    }

    function updateDecisionUI() {
      const isNegative = state.activeMode === 'negative_review';
      const keepDrawingState = state.currentDecision === 'fix' && state.drawingEnabled;
      buildButtons('actionGrid', isNegative ? state.bootstrap.negative_decisions : state.bootstrap.positive_decisions, state.currentDecision, (value) => {
        const changed = state.currentDecision !== value;
        state.currentDecision = value;
        state.currentReason = '';
        if (changed) {
          state.currentScene = '';
          state.drawingEnabled = false;
        }
        updateDecisionUI();
      });
      const secondarySection = document.getElementById('secondarySection');
      const sceneSection = document.getElementById('sceneSection');
      const boxTools = document.getElementById('boxTools');
      secondarySection.classList.add('hidden');
      sceneSection.classList.add('hidden');
      boxTools.classList.add('hidden');

      if (!state.currentDecision) return;

      if (isNegative) {
        state.drawingEnabled = false;
        document.getElementById('toggleDrawBtn').classList.remove('active');
        document.getElementById('toggleDrawBtn').textContent = 'Enable Box Draw';
        syncCanvasCursor();
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
        return;
      }

      if (state.currentDecision === 'keep') {
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
        return;
      }

      secondarySection.classList.remove('hidden');
      if (state.currentDecision === 'fix') {
        buildButtons('secondaryGrid', state.bootstrap.fix_reasons, state.currentReason, (value) => {
          state.currentReason = value;
          updateDecisionUI();
        });
      } else {
        buildButtons('secondaryGrid', state.bootstrap.exclude_reasons, state.currentReason, (value) => {
          state.currentReason = value;
          updateDecisionUI();
        });
      }
      if (state.currentReason) {
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
      }
      if (state.currentDecision === 'fix') {
        boxTools.classList.remove('hidden');
        state.drawingEnabled = keepDrawingState;
        document.getElementById('toggleDrawBtn').classList.toggle('active', state.drawingEnabled);
        document.getElementById('toggleDrawBtn').textContent = state.drawingEnabled ? 'Disable Box Draw' : 'Enable Box Draw';
      } else {
        state.drawingEnabled = false;
        document.getElementById('toggleDrawBtn').classList.remove('active');
        document.getElementById('toggleDrawBtn').textContent = 'Enable Box Draw';
      }
      syncCanvasCursor();
    }

    function clearSelectionsFromItem(item) {
      const existing = item.existing_review || null;
      state.currentDecision = existing ? existing.primary_decision || '' : '';
      state.currentReason = existing ? existing.secondary_reason || '' : '';
      state.currentScene = existing ? existing.scene_bucket || '' : '';
      if (existing && existing.updated_boxes_json) {
        try {
          state.editBoxes = JSON.parse(existing.updated_boxes_json);
        } catch (error) {
          state.editBoxes = JSON.parse(JSON.stringify(item.boxes || []));
        }
      } else {
        state.editBoxes = JSON.parse(JSON.stringify(item.boxes || []));
      }
      state.drawingEnabled = false;
      state.dragStart = null;
      state.dragCurrent = null;
      syncCanvasCursor();
    }

    async function loadCurrentItem(key = null) {
      setMessage('modeMessage', '');
      setMessage('itemMessage', '');
      document.getElementById('workspace').classList.add('hidden');
      document.getElementById('emptyState').innerHTML = '<h2>Loading</h2>';
      buildModeList();

      try {
        const params = new URLSearchParams({mode: state.activeMode});
        if (key) {
          params.set('key', key);
        }
        const payload = await fetchJson(`/api/item?${params.toString()}`);
        state.currentItem = payload.item;
        const status = payload.status;
        if (!state.currentItem) {
          const title = status.stage_complete ? `${status.label} stage complete` : `${status.label} complete`;
          const detail = status.subset_enabled
            ? `${status.reviewed}/${status.total} reviewed. Active queue: ${status.active_reviewed}/${status.active_total}.`
            : `${status.reviewed}/${status.total} reviewed.`;
          document.getElementById('emptyState').innerHTML = `<h2>${title}</h2><p>${detail}</p>`;
          const signoffWrap = document.getElementById('signoffWrap');
          if (status.stage_complete && status.unlocked && !status.signed_off) {
            signoffWrap.classList.remove('hidden');
          } else {
            signoffWrap.classList.add('hidden');
          }
          buildModeList();
          return;
        }
        document.getElementById('signoffWrap').classList.add('hidden');
        clearSelectionsFromItem(state.currentItem);
        renderMeta(state.currentItem);
        updateDecisionUI();
        await loadImage();
        document.getElementById('emptyState').innerHTML = '';
        document.getElementById('workspace').classList.remove('hidden');
        buildModeList();
      } catch (error) {
        document.getElementById('emptyState').innerHTML = `<h2>Failed to load</h2><p>${error.message}</p>`;
      }
    }

    async function saveCurrentReview() {
      if (!state.currentItem) return;
      const payload = {
        mode: state.activeMode,
        key: state.currentItem.key,
        primary_decision: state.currentDecision,
        secondary_reason: state.currentReason,
        scene_bucket: state.currentScene,
        updated_boxes: state.editBoxes,
      };
      try {
        await fetchJson('/api/review', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload),
        });
        await loadCurrentItem(state.currentItem.next_key);
      } catch (error) {
        setMessage('itemMessage', error.message);
      }
    }

    async function signoffCurrentMode() {
      try {
        const payload = await fetchJson('/api/signoff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({mode: state.activeMode}),
        });
        state.bootstrap = payload;
        state.activeMode = payload.current_mode;
        await loadCurrentItem();
      } catch (error) {
        setMessage('modeMessage', error.message);
      }
    }

    canvas.addEventListener('mousedown', (event) => {
      if (!state.drawingEnabled || state.activeMode === 'negative_review' || state.currentDecision !== 'fix') return;
      state.dragStart = getCanvasPoint(event);
      state.dragCurrent = state.dragStart.slice();
      drawCanvas();
    });

    canvas.addEventListener('mousemove', (event) => {
      if (!state.dragStart) return;
      state.dragCurrent = getCanvasPoint(event);
      drawCanvas();
    });

    canvas.addEventListener('mouseup', () => {
      if (!state.dragStart || !state.dragCurrent) return;
      const [sx, sy] = state.dragStart;
      const [cx, cy] = state.dragCurrent;
      const x1 = Math.min(sx, cx);
      const y1 = Math.min(sy, cy);
      const x2 = Math.max(sx, cx);
      const y2 = Math.max(sy, cy);
      const width = x2 - x1;
      const height = y2 - y1;
      state.dragStart = null;
      state.dragCurrent = null;
      if (width > 8 && height > 8) {
        state.editBoxes.push([
          x1 / state.imageScale,
          y1 / state.imageScale,
          width / state.imageScale,
          height / state.imageScale,
        ]);
      }
      drawCanvas();
    });

    document.getElementById('toggleDrawBtn').onclick = () => {
      state.drawingEnabled = !state.drawingEnabled;
      document.getElementById('toggleDrawBtn').classList.toggle('active', state.drawingEnabled);
      document.getElementById('toggleDrawBtn').textContent = state.drawingEnabled ? 'Disable Box Draw' : 'Enable Box Draw';
      syncCanvasCursor();
    };
    document.getElementById('undoBoxBtn').onclick = () => {
      state.editBoxes.pop();
      drawCanvas();
    };
    document.getElementById('clearBoxesBtn').onclick = () => {
      state.editBoxes = [];
      drawCanvas();
    };
    document.getElementById('resetBoxesBtn').onclick = () => {
      state.editBoxes = JSON.parse(JSON.stringify(state.currentItem.boxes || []));
      drawCanvas();
    };
    document.getElementById('reloadBtn').onclick = () => loadCurrentItem();
    document.getElementById('saveBtn').onclick = () => saveCurrentReview();
    document.getElementById('signoffBtn').onclick = () => signoffCurrentMode();
    document.getElementById('prevBtn').onclick = () => {
      if (state.currentItem && state.currentItem.prev_key) {
        loadCurrentItem(state.currentItem.prev_key);
      }
    };
    document.getElementById('nextBtn').onclick = () => {
      if (state.currentItem && state.currentItem.next_key) {
        loadCurrentItem(state.currentItem.next_key);
      }
    };

    async function init() {
      state.bootstrap = await fetchJson('/api/bootstrap');
      state.activeMode = state.bootstrap.current_mode;
      await loadCurrentItem();
    }

    init();
  </script>
</body>
</html>
"""


class ReviewRequestHandler(BaseHTTPRequestHandler):
    repository: ReviewRepository | None = None

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_text(self, content: str, content_type: str = "text/html; charset=utf-8", status: int = HTTPStatus.OK) -> None:
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Image not found.")
            return
        content = path.read_bytes()
        suffix = path.suffix.lower()
        content_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        repository = self.repository
        if repository is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Repository not initialized.")
            return

        if parsed.path == "/":
            self._send_text(HTML_PAGE)
            return
        if parsed.path == "/api/bootstrap":
            self._send_json(repository.bootstrap())
            return
        if parsed.path == "/api/item":
            mode = params.get("mode", [""])[0]
            item = repository.get_item(mode, params.get("key", [None])[0])
            self._send_json({"item": item, "status": repository.mode_status(mode)})
            return
        if parsed.path == "/image":
            mode = params.get("mode", [""])[0]
            key = params.get("key", [""])[0]
            item = repository.get_item(mode, key)
            if not item:
                self.send_error(HTTPStatus.NOT_FOUND, "Review item not found.")
                return
            self._send_file(Path(item["image_path"]))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        repository = self.repository
        if repository is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Repository not initialized.")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        try:
            if parsed.path == "/api/review":
                status = repository.save_review(payload)
                self._send_json({"ok": True, "status": status})
                return
            if parsed.path == "/api/signoff":
                bootstrap = repository.signoff_mode(payload["mode"])
                self._send_json(bootstrap)
                return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the click-only streetlight review app.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the local reviewer.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind the local reviewer.")
    parser.add_argument("--build-only", action="store_true", help="Build app data and exit without starting the server.")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the local review app in a browser.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = ReviewRepository()
    if args.build_only:
        for mode in MODE_ORDER:
            status = repository.mode_status(mode)
            print(f"{mode}: {status['total']} items, {status['reviewed']} reviewed")
        print(f"Review outputs rooted at: {OUTPUT_ROOT}")
        return

    handler = ReviewRequestHandler
    handler.repository = repository
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Streetlight review app running at: {url}")
    print(f"Review outputs rooted at: {OUTPUT_ROOT}")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
