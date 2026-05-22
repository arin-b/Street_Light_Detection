const STEPS = [
  {id: 'lamp_boxes', label: 'Mark Lamps', card: 'taskLampBoxes', tool: 'box'},
  {id: 'surfaces', label: 'Mark Other Lights', card: 'taskSurfaces', tool: 'smart'},
  {id: 'public_space', label: 'Mark Road/Footpath', card: 'taskPublicSpace', tool: 'polygon'},
  {id: 'affected', label: 'Mark Lit Area', card: 'taskAffected', tool: 'polygon'},
  {id: 'visibility', label: 'Rate Visibility', card: 'taskVisibility', tool: 'box'},
  {id: 'lux_qa', label: 'Field Lux / Notes', card: 'taskLuxQa', tool: 'point'}
];

const LABELS = {
  building_facade: 'Building wall',
  shopfront: 'Shop light/front',
  window: 'Window light',
  sign_lightbox: 'Bright sign',
  reflective_glass: 'Reflective glass',
  wet_road_reflection: 'Wet road reflection',
  wall_compound_surface: 'Boundary wall',
  vehicle_headlight_region: 'Vehicle headlights',
  unknown_bright_source: 'Other bright thing',
  road: 'Road',
  footpath_sidewalk: 'Footpath/sidewalk',
  crossing: 'Crossing',
  curb: 'Curb',
  median: 'Median',
  verge: 'Road edge/verge',
  vegetation: 'Tree/vegetation',
  vehicle: 'Vehicle',
  building_frontage: 'Building front',
  sign_billboard: 'Sign/board',
  traffic_signal: 'Traffic signal',
  sky: 'Sky',
  wet_reflection_like_road: 'Wet shiny road',
  occluder: 'Blocker/occluder',
  unknown: 'Unknown',
  on: 'On',
  dim: 'Dim',
  off: 'Off',
  flicker: 'Flickering',
  occluded: 'Blocked',
  saturated: 'Too bright / blown out',
  good: 'Good',
  adequate: 'Okay',
  marginal: 'Barely okay',
  poor: 'Poor',
  dark: 'Too dark',
  certain: 'Yes, mostly this lamp',
  mixed: 'Mixed with other lights',
  uncertain: 'Not sure',
  impossible_due_to_confounding: 'Cannot tell',
  P1: 'P1 under lamp',
  P2: 'P2 between lamps',
  P3: 'P3 road point',
  P4: 'P4 footpath point',
  P5: 'P5 darkest patch',
  P6: 'P6 near other light',
  P7: 'P7 opposite side',
  P8: 'P8 shadow/blocked side'
};

const QA_FLAGS = [
  'no_lux_reference',
  'proxy_only',
  'glare',
  'headlight_confounder',
  'shopfront_confounder',
  'wet_reflection',
  'tree_occlusion',
  'exposure_problem'
];

const state = {
  bootstrap: null,
  current: null,
  review: null,
  image: null,
  scale: 1,
  step: 0,
  tool: 'box',
  selectedType: '',
  selectedIndex: -1,
  drawing: null,
  polygonDraft: [],
  previewPoint: null,
  selectedPoint: null,
  proposal: null,
  dirty: false
};

const $ = (id) => document.getElementById(id);

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function setMessage(text) {
  $('message').textContent = text || '';
  $('statusStrip').textContent = text || `${STEPS[state.step].label} ready`;
}

function markDirty() {
  state.dirty = true;
  renderSummary();
}

function populateSelect(id, values) {
  const select = $(id);
  select.innerHTML = '';
  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = LABELS[value] || value;
    select.appendChild(option);
  }
}

async function init() {
  state.bootstrap = await fetchJson('/api/bootstrap');
  $('workspaceStatus').textContent = `${state.bootstrap.reviewed}/${state.bootstrap.total} reviewed`;
  populateSelect('surfaceType', state.bootstrap.surface_types);
  populateSelect('lampStatus', state.bootstrap.lamp_status_classes);
  populateSelect('visibilityClass', state.bootstrap.visibility_classes);
  populateSelect('attributionClass', state.bootstrap.attribution_classes);
  populateSelect('luxType', state.bootstrap.lux_point_types);
  populateSelect('regionType', state.bootstrap.public_space_types);
  renderQaChips();
  renderStepper();
  setStep(0);
  await loadItemByIndex(0);
}

function renderStepper() {
  const wrap = $('stepper');
  wrap.innerHTML = '';
  STEPS.forEach((step, index) => {
    const button = document.createElement('button');
    button.className = `step-button ${index === state.step ? 'active' : ''}`;
    button.innerHTML = `<span class="step-number">${index + 1}</span><span>${step.label}</span>`;
    button.onclick = () => setStep(index);
    wrap.appendChild(button);
  });
}

function renderQaChips() {
  const wrap = $('qaChips');
  wrap.innerHTML = '';
  for (const flag of QA_FLAGS) {
    const button = document.createElement('button');
    button.className = 'chip';
    button.textContent = LABELS[flag] || flag.replaceAll('_', ' ');
    button.onclick = () => {
      $('qaFlag').value = flag;
      addQa();
    };
    wrap.appendChild(button);
  }
}

function setStep(index) {
  state.step = Math.max(0, Math.min(index, STEPS.length - 1));
  for (const step of STEPS) $(step.card).classList.add('hidden');
  $(STEPS[state.step].card).classList.remove('hidden');
  renderStepper();
  setTool(STEPS[state.step].tool);
  setMessage('');
}

async function loadItemByIndex(index) {
  await loadPayload(await fetchJson(`/api/item?index=${index}`));
}

async function loadItemByKey(key) {
  await loadPayload(await fetchJson(`/api/item?key=${encodeURIComponent(key)}`));
}

async function loadPayload(payload) {
  state.current = payload;
  state.review = payload.review;
  state.selectedIndex = -1;
  state.selectedType = '';
  state.polygonDraft = [];
  state.previewPoint = null;
  state.selectedPoint = null;
  state.proposal = null;
  state.dirty = false;
  $('itemTitle').textContent = payload.item.key;
  $('itemSubtitle').textContent = `${payload.index + 1} / ${payload.total} | ${payload.item.clip_id || 'clip'} | frame ${payload.item.frame_id || ''}`;
  $('prevBtn').disabled = !payload.prev_key;
  $('nextBtn').disabled = !payload.next_key;
  $('prevBtn').onclick = () => payload.prev_key && loadItemByKey(payload.prev_key);
  $('nextBtn').onclick = () => payload.next_key && loadItemByKey(payload.next_key);
  await loadImage(payload.item.key);
  renderLists();
  renderSummary();
}

function loadImage(key) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      state.image = img;
      resizeCanvas();
      draw();
      resolve();
    };
    img.onerror = reject;
    img.src = `/image?key=${encodeURIComponent(key)}&t=${Date.now()}`;
  });
}

function resizeCanvas() {
  const canvas = $('canvas');
  const maxWidth = Math.max(620, document.querySelector('.canvas-wrap').clientWidth - 24);
  state.scale = Math.min(1, maxWidth / state.image.naturalWidth);
  canvas.width = Math.round(state.image.naturalWidth * state.scale);
  canvas.height = Math.round(state.image.naturalHeight * state.scale);
}

function imageCoords(event) {
  const rect = $('canvas').getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) / state.scale,
    y: (event.clientY - rect.top) / state.scale
  };
}

function draw() {
  const canvas = $('canvas');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!state.image) return;
  ctx.drawImage(state.image, 0, 0, canvas.width, canvas.height);
  drawPolygons(ctx);
  drawBoxes(ctx);
  drawLuxPoints(ctx);
  if (state.proposal) drawProposal(ctx, state.proposal.points, state.proposal.bbox_xyxy);
  if (state.polygonDraft.length) {
    drawPolyline(ctx, state.polygonDraft, '#ffd166', false);
    if (state.previewPoint) drawPolyline(ctx, [state.polygonDraft[state.polygonDraft.length - 1], [state.previewPoint.x, state.previewPoint.y]], '#ffd166', false);
    drawStartPoint(ctx);
  }
  if (state.drawing && (state.drawing.kind === 'box' || state.drawing.kind === 'smart')) {
    drawBox(ctx, state.drawing.box, '#ffd166', state.drawing.kind === 'smart' ? 'smart' : 'new');
  }
}

function drawBoxes(ctx) {
  for (const [index, box] of (state.review.boxes || []).entries()) {
    const color = state.selectedType === 'box' && state.selectedIndex === index ? '#ffd166' : '#4cc9f0';
    drawBox(ctx, box.bbox_xyxy, color, `${index + 1}:${box.status || 'box'}`);
  }
}

function drawBox(ctx, rawBox, color, label) {
  const [x1, y1, x2, y2] = rawBox.map(v => v * state.scale);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
  ctx.fillStyle = color;
  ctx.font = '12px Segoe UI';
  ctx.fillText(label, x1 + 4, Math.max(14, y1 - 4));
}

function drawPolygons(ctx) {
  for (const [index, polygon] of (state.review.polygons || []).entries()) {
    const color = state.selectedType === 'polygon' && state.selectedIndex === index ? '#ffd166' : '#80ed99';
    drawPolyline(ctx, polygon.points || [], color, true, `${index + 1}:${polygon.surface_type || 'polygon'}`);
  }
  for (const row of state.review.measurement?.public_space_regions || []) {
    drawPolyline(ctx, row.points || [], '#9cc8ff', true, row.region_type || 'public');
  }
  for (const row of state.review.measurement?.affected_regions || []) {
    drawPolyline(ctx, row.points || [], '#f28482', true, row.region_type || 'affected');
  }
}

function drawProposal(ctx, points, bbox) {
  ctx.save();
  ctx.globalAlpha = 0.35;
  drawFilledPolygon(ctx, points, '#ffd166');
  ctx.globalAlpha = 1;
  drawPolyline(ctx, points, '#ffd166', true, 'proposal');
  if (bbox) drawBox(ctx, bbox, '#ffd166', 'prompt');
  ctx.restore();
}

function drawFilledPolygon(ctx, points, color) {
  if (!points || points.length < 3) return;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(points[0][0] * state.scale, points[0][1] * state.scale);
  for (const point of points.slice(1)) ctx.lineTo(point[0] * state.scale, point[1] * state.scale);
  ctx.closePath();
  ctx.fill();
}

function drawPolyline(ctx, points, color, closed, label) {
  if (!points || !points.length) return;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(points[0][0] * state.scale, points[0][1] * state.scale);
  for (const point of points.slice(1)) ctx.lineTo(point[0] * state.scale, point[1] * state.scale);
  if (closed && points.length > 2) ctx.closePath();
  ctx.stroke();
  for (const point of points) {
    ctx.beginPath();
    ctx.arc(point[0] * state.scale, point[1] * state.scale, 3, 0, Math.PI * 2);
    ctx.fill();
  }
  if (label) ctx.fillText(label, points[0][0] * state.scale + 4, points[0][1] * state.scale - 4);
}

function drawLuxPoints(ctx) {
  const points = state.review.measurement?.lux_points || [];
  for (const [index, point] of points.entries()) {
    ctx.fillStyle = '#ff4d8d';
    ctx.beginPath();
    ctx.arc(point.x * state.scale, point.y * state.scale, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText(`${index + 1}:${point.point_type}`, point.x * state.scale + 6, point.y * state.scale - 5);
  }
  if (state.selectedPoint) {
    ctx.fillStyle = '#ffd166';
    ctx.beginPath();
    ctx.arc(state.selectedPoint.x * state.scale, state.selectedPoint.y * state.scale, 5, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawStartPoint(ctx) {
  if (!state.polygonDraft.length) return;
  const first = state.polygonDraft[0];
  ctx.save();
  ctx.strokeStyle = '#ffd166';
  ctx.fillStyle = 'rgba(255, 209, 102, 0.25)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(first[0] * state.scale, first[1] * state.scale, 9, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function renderLists() {
  renderBoxList();
  renderPolygonList();
  renderItemList();
}

function renderBoxList() {
  const wrap = $('boxList');
  wrap.innerHTML = '';
  for (const [index, box] of (state.review.boxes || []).entries()) {
    const row = document.createElement('div');
    row.className = `row ${state.selectedType === 'box' && state.selectedIndex === index ? 'active' : ''}`;
    row.textContent = `${index + 1}. ${box.status || 'candidate'} ${box.track_id || ''}`;
    row.onclick = () => selectBox(index);
    wrap.appendChild(row);
  }
}

function renderPolygonList() {
  const wrap = $('polygonList');
  wrap.innerHTML = '';
  for (const [index, polygon] of (state.review.polygons || []).entries()) {
    const row = document.createElement('div');
    row.className = `row ${state.selectedType === 'polygon' && state.selectedIndex === index ? 'active' : ''}`;
    const label = LABELS[polygon.surface_type] || polygon.surface_type || 'shape';
    row.innerHTML = `<span>${index + 1}. ${label}</span><button class="row-delete" title="Delete shape">X</button>`;
    row.onclick = () => selectPolygon(index);
    row.querySelector('.row-delete').onclick = (event) => {
      event.stopPropagation();
      deletePolygon(index);
    };
    wrap.appendChild(row);
  }
}

function renderItemList() {
  const wrap = $('itemList');
  wrap.innerHTML = '';
  const currentIndex = state.current?.index || 0;
  for (let delta = -4; delta <= 4; delta++) {
    const index = currentIndex + delta;
    if (index < 0 || index >= state.current.total) continue;
    const row = document.createElement('div');
    row.className = `row ${index === currentIndex ? 'active' : ''}`;
    row.textContent = `Item ${index + 1}`;
    row.onclick = () => loadItemByIndex(index);
    wrap.appendChild(row);
  }
}

function selectBox(index) {
  state.selectedType = 'box';
  state.selectedIndex = index;
  const box = state.review.boxes[index];
  $('boxStatus').value = box.status || 'candidate';
  $('boxTrackId').value = box.track_id || '';
  $('boxNotes').value = box.notes || '';
  $('measurementTrackId').value = box.track_id || $('measurementTrackId').value;
  renderLists();
  draw();
}

function selectPolygon(index) {
  state.selectedType = 'polygon';
  state.selectedIndex = index;
  const polygon = state.review.polygons[index];
  $('surfaceType').value = polygon.surface_type || state.bootstrap.surface_types[0];
  $('polyBright').checked = !!polygon.is_bright_source;
  $('polyReflective').checked = !!polygon.is_reflective;
  $('polyPublic').checked = !!polygon.is_public_space;
  $('polyConfounds').checked = polygon.can_confound_streetlight !== false;
  $('polyOverlaps').checked = !!polygon.overlaps_affected_region;
  $('polyAugAllowed').checked = !!polygon.augmentation_allowed;
  $('polyMargin').value = polygon.mask_exclusion_margin_px || 12;
  renderLists();
  draw();
}

function updateSelectedBox() {
  if (state.selectedType !== 'box' || state.selectedIndex < 0) return;
  const box = state.review.boxes[state.selectedIndex];
  box.status = $('boxStatus').value;
  box.track_id = $('boxTrackId').value.trim();
  box.notes = $('boxNotes').value.trim();
  markDirty();
  renderLists();
  draw();
}

function updateSelectedPolygon() {
  if (state.selectedType !== 'polygon' || state.selectedIndex < 0) return;
  Object.assign(state.review.polygons[state.selectedIndex], polygonMetadata());
  markDirty();
  renderLists();
  draw();
}

function polygonMetadata() {
  return {
    surface_type: $('surfaceType').value,
    is_bright_source: $('polyBright').checked,
    is_reflective: $('polyReflective').checked,
    is_public_space: $('polyPublic').checked,
    can_confound_streetlight: $('polyConfounds').checked,
    overlaps_affected_region: $('polyOverlaps').checked,
    augmentation_allowed: $('polyAugAllowed').checked,
    mask_exclusion_margin_px: Number($('polyMargin').value || 12)
  };
}

function ensureMeasurement() {
  if (!state.review.measurement) {
    state.review.measurement = {lamp_status: [], public_space_regions: [], affected_regions: [], visibility_labels: [], attribution_labels: [], lux_points: [], qa_flags: []};
  }
  return state.review.measurement;
}

function addLampStatus() {
  ensureMeasurement().lamp_status.push({track_id: $('measurementTrackId').value.trim(), status: $('lampStatus').value});
  markDirty();
}

function addVisibility() {
  ensureMeasurement().visibility_labels.push({track_id: $('measurementTrackId').value.trim(), visibility_class: $('visibilityClass').value});
  markDirty();
}

function addAttribution() {
  ensureMeasurement().attribution_labels.push({track_id: $('measurementTrackId').value.trim(), attribution_class: $('attributionClass').value, evidence: $('attributionEvidence').value.trim()});
  markDirty();
}

function selectedPolygonPoints() {
  if (state.selectedType !== 'polygon' || state.selectedIndex < 0) throw new Error('Select a polygon first.');
  return state.review.polygons[state.selectedIndex].points || [];
}

function addRegion(kind) {
  try {
    const measurement = ensureMeasurement();
    const row = {track_id: $('measurementTrackId').value.trim(), region_type: $('regionType').value, points: selectedPolygonPoints()};
    if (kind === 'public') measurement.public_space_regions.push(row);
    else measurement.affected_regions.push(row);
    markDirty();
    draw();
  } catch (error) {
    setMessage(error.message);
  }
}

function addLux() {
  if (!state.selectedPoint) {
    setMessage('Use the Point tool and click the image first.');
    return;
  }
  ensureMeasurement().lux_points.push({track_id: $('measurementTrackId').value.trim(), point_type: $('luxType').value, lux_value: $('luxValue').value, x: state.selectedPoint.x, y: state.selectedPoint.y});
  state.selectedPoint = null;
  markDirty();
  draw();
}

function addQa() {
  const flag = $('qaFlag').value.trim();
  if (!flag) return;
  ensureMeasurement().qa_flags.push({track_id: $('measurementTrackId').value.trim(), flag});
  $('qaFlag').value = '';
  markDirty();
}

function renderSummary() {
  $('reviewSummary').textContent = JSON.stringify({
    status: state.review?.review_status || 'unreviewed',
    dirty: state.dirty,
    boxes: state.review?.boxes?.length || 0,
    surfaces: state.review?.polygons?.length || 0,
    lamp_status: state.review?.measurement?.lamp_status?.length || 0,
    public_regions: state.review?.measurement?.public_space_regions?.length || 0,
    affected_regions: state.review?.measurement?.affected_regions?.length || 0,
    visibility: state.review?.measurement?.visibility_labels?.length || 0,
    attribution: state.review?.measurement?.attribution_labels?.length || 0,
    lux_points: state.review?.measurement?.lux_points?.length || 0,
    qa_flags: state.review?.measurement?.qa_flags?.length || 0
  }, null, 2);
}

async function saveReview() {
  try {
    await fetchJson('/api/save', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({key: state.current.item.key, review: state.review})
    });
    state.dirty = false;
    setMessage('Saved.');
    renderSummary();
  } catch (error) {
    setMessage(error.message);
  }
}

function markStatus(value) {
  state.review.review_status = value;
  if (value === 'needs_review' || value === 'unusable_frame') {
    ensureMeasurement().qa_flags.push({track_id: $('measurementTrackId').value.trim(), flag: value});
  }
  markDirty();
}

function setTool(tool) {
  state.tool = tool;
  for (const id of ['boxToolBtn', 'smartToolBtn', 'polygonToolBtn', 'pointToolBtn']) $(id).classList.remove('active');
  if (tool === 'box') $('boxToolBtn').classList.add('active');
  if (tool === 'smart') $('smartToolBtn').classList.add('active');
  if (tool === 'polygon') $('polygonToolBtn').classList.add('active');
  if (tool === 'point') $('pointToolBtn').classList.add('active');
}

function finishPolygon() {
  if (state.polygonDraft.length < 3) {
    setMessage('Add at least 3 corners before finishing the shape.');
    return;
  }
  if (!canCloseDraft()) {
    setMessage('That final line would cross the shape. Move the last point first.');
    return;
  }
  addPolygon([...state.polygonDraft], 'manual');
  state.polygonDraft = [];
  state.previewPoint = null;
}

function addPolygon(points, source) {
  state.review.polygons = state.review.polygons || [];
  const polygon = {
    polygon_id: `poly_${String(state.review.polygons.length + 1).padStart(3, '0')}`,
    points,
    source,
    ...polygonMetadata()
  };
  state.review.polygons.push(polygon);
  markDirty();
  selectPolygon(state.review.polygons.length - 1);
}

function deleteSelected() {
  if (state.proposal) {
    state.proposal = null;
  } else if (state.selectedType === 'box' && state.selectedIndex >= 0) {
    state.review.boxes.splice(state.selectedIndex, 1);
    markDirty();
  } else if (state.selectedType === 'polygon' && state.selectedIndex >= 0) {
    deletePolygon(state.selectedIndex);
    return;
  }
  state.selectedType = '';
  state.selectedIndex = -1;
  renderLists();
  draw();
}

function deletePolygon(index) {
  if (!state.review.polygons || index < 0 || index >= state.review.polygons.length) return;
  state.review.polygons.splice(index, 1);
  state.selectedType = '';
  state.selectedIndex = -1;
  markDirty();
  renderLists();
  draw();
  setMessage('Shape deleted.');
}

function undoLastShape() {
  if (state.review.polygons?.length) {
    deletePolygon(state.review.polygons.length - 1);
  } else {
    setMessage('No shape to undo.');
  }
}

function undoPoint() {
  if (!state.polygonDraft.length) {
    setMessage('No drawing point to undo.');
    return;
  }
  state.polygonDraft.pop();
  state.previewPoint = null;
  draw();
  setMessage('Last point removed.');
}

function cancelShape() {
  state.polygonDraft = [];
  state.previewPoint = null;
  state.proposal = null;
  draw();
  setMessage('Drawing cancelled.');
}

async function requestAutoPolygon(box) {
  setMessage('Finding the shape...');
  try {
    const payload = await fetchJson('/api/auto-polygon', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        item_key: state.current.item.key,
        bbox_xyxy: box,
        margin_px: Number($('polyMargin').value || 12)
      })
    });
    state.proposal = payload;
    const warningText = payload.warnings?.length ? ` ${payload.warnings.join(' ')}` : '';
    setMessage(`Shape found. Keep it or try again.${warningText}`);
    draw();
  } catch (error) {
    setMessage(error.message);
  }
}

function acceptProposal() {
  if (!state.proposal || !state.proposal.points?.length) {
    setMessage('No proposal to accept.');
    return;
  }
  addPolygon(state.proposal.points, `auto:${state.proposal.engine}`);
  state.proposal = null;
  setMessage('Shape kept.');
}

function discardProposal() {
  state.proposal = null;
  draw();
  setMessage('Try again: drag a new box around the surface.');
}

function canvasMouseDown(event) {
  const point = imageCoords(event);
  if (state.tool === 'box' || state.tool === 'smart') {
    state.drawing = {kind: state.tool === 'smart' ? 'smart' : 'box', start: point, box: [point.x, point.y, point.x, point.y]};
  } else if (state.tool === 'polygon') {
    addDraftPoint(point);
  } else if (state.tool === 'point') {
    const selected = polygonIndexAt(point);
    if (selected >= 0) {
      selectPolygon(selected);
    } else {
      state.selectedPoint = point;
      draw();
    }
  }
}

function canvasMouseMove(event) {
  const point = imageCoords(event);
  if (state.tool === 'polygon' && state.polygonDraft.length) {
    state.previewPoint = point;
    draw();
  }
  if (!state.drawing || !['box', 'smart'].includes(state.drawing.kind)) return;
  const start = state.drawing.start;
  state.drawing.box = [Math.min(start.x, point.x), Math.min(start.y, point.y), Math.max(start.x, point.x), Math.max(start.y, point.y)];
  draw();
}

function canvasMouseUp() {
  if (!state.drawing || !['box', 'smart'].includes(state.drawing.kind)) return;
  const box = state.drawing.box;
  const kind = state.drawing.kind;
  state.drawing = null;
  if (Math.abs(box[2] - box[0]) < 4 || Math.abs(box[3] - box[1]) < 4) return;
  if (kind === 'smart') {
    requestAutoPolygon(box);
    return;
  }
  state.review.boxes = state.review.boxes || [];
  state.review.boxes.push({box_id: `box_${String(state.review.boxes.length + 1).padStart(3, '0')}`, class_name: 'streetlight', bbox_xyxy: box, track_id: $('measurementTrackId').value.trim(), status: 'fixed', source: 'manual', notes: ''});
  markDirty();
  selectBox(state.review.boxes.length - 1);
}

function addDraftPoint(point) {
  const pointArray = [point.x, point.y];
  if (state.polygonDraft.length >= 3 && distance(pointArray, state.polygonDraft[0]) < 12 / state.scale) {
    finishPolygon();
    return;
  }
  if (!canAddPoint(pointArray)) {
    setMessage('That line crosses the shape. Pick another point.');
    return;
  }
  state.polygonDraft.push(pointArray);
  state.previewPoint = null;
  draw();
}

function canAddPoint(point) {
  const draft = state.polygonDraft;
  if (draft.length < 2) return true;
  const nextSegment = [draft[draft.length - 1], point];
  for (let index = 0; index < draft.length - 2; index++) {
    if (segmentsIntersect(nextSegment[0], nextSegment[1], draft[index], draft[index + 1])) return false;
  }
  return true;
}

function canCloseDraft() {
  const draft = state.polygonDraft;
  if (draft.length < 3) return false;
  const closing = [draft[draft.length - 1], draft[0]];
  for (let index = 1; index < draft.length - 2; index++) {
    if (segmentsIntersect(closing[0], closing[1], draft[index], draft[index + 1])) return false;
  }
  return true;
}

function distance(a, b) {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function segmentsIntersect(a, b, c, d) {
  if (samePoint(a, c) || samePoint(a, d) || samePoint(b, c) || samePoint(b, d)) return false;
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);
  if (o1 !== o2 && o3 !== o4) return true;
  return false;
}

function orientation(a, b, c) {
  const value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]);
  if (Math.abs(value) < 1e-7) return 0;
  return value > 0 ? 1 : 2;
}

function samePoint(a, b) {
  return Math.abs(a[0] - b[0]) < 1e-7 && Math.abs(a[1] - b[1]) < 1e-7;
}

function polygonIndexAt(point) {
  const polygons = state.review.polygons || [];
  for (let index = polygons.length - 1; index >= 0; index--) {
    if (pointInPolygon([point.x, point.y], polygons[index].points || [])) return index;
  }
  return -1;
}

function pointInPolygon(point, polygon) {
  if (!polygon || polygon.length < 3) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1];
    const xj = polygon[j][0], yj = polygon[j][1];
    const intersect = ((yi > point[1]) !== (yj > point[1])) &&
      (point[0] < (xj - xi) * (point[1] - yi) / ((yj - yi) || 1e-9) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function bindEvents() {
  $('saveBtn').onclick = saveReview;
  $('acceptedBtn').onclick = () => markStatus('accepted');
  $('needsReviewBtn').onclick = () => markStatus('needs_review');
  $('unusableBtn').onclick = () => markStatus('unusable_frame');
  $('boxToolBtn').onclick = () => setTool('box');
  $('smartToolBtn').onclick = () => setTool('smart');
  $('polygonToolBtn').onclick = () => setTool('polygon');
  $('pointToolBtn').onclick = () => setTool('point');
  $('finishPolygonBtn').onclick = finishPolygon;
  $('deleteSelectedBtn').onclick = deleteSelected;
  $('deleteShapeBtn').onclick = deleteSelected;
  $('undoShapeBtn').onclick = undoLastShape;
  $('undoPointBtn').onclick = undoPoint;
  $('cancelShapeBtn').onclick = cancelShape;
  $('updateBoxBtn').onclick = updateSelectedBox;
  $('updatePolygonBtn').onclick = updateSelectedPolygon;
  $('acceptProposalBtn').onclick = acceptProposal;
  $('discardProposalBtn').onclick = discardProposal;
  $('addLampStatusBtn').onclick = addLampStatus;
  $('addVisibilityBtn').onclick = addVisibility;
  $('addAttributionBtn').onclick = addAttribution;
  $('addPublicRegionBtn').onclick = () => addRegion('public');
  $('addAffectedRegionBtn').onclick = () => addRegion('affected');
  $('addLuxBtn').onclick = addLux;
  $('addQaBtn').onclick = addQa;
  $('canvas').onmousedown = canvasMouseDown;
  $('canvas').onmousemove = canvasMouseMove;
  $('canvas').onmouseup = canvasMouseUp;
  window.onresize = () => { if (state.image) { resizeCanvas(); draw(); } };
  document.onkeydown = (event) => {
    if (event.target && ['INPUT', 'SELECT'].includes(event.target.tagName)) return;
    if (event.key.toLowerCase() === 's') saveReview();
    if (event.key.toLowerCase() === 'n' && state.current?.next_key) loadItemByKey(state.current.next_key);
    if (event.key.toLowerCase() === 'b') setTool('box');
    if (event.key.toLowerCase() === 'g') setTool('smart');
    if (event.key.toLowerCase() === 'p') setTool('polygon');
    if (event.key === 'Enter') acceptProposal();
    if (event.key === 'Escape') cancelShape();
    if (event.key === 'Backspace') {
      event.preventDefault();
      undoPoint();
    }
  };
}

bindEvents();
init().catch(error => setMessage(error.message));
