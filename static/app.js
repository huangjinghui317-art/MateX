const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

let selectedElements = [];
let searchMode = 'only';
let materialClass = 'all';
let materials = [];
let currentMaterial = null;
let renderMaterial = null;
let renderUploadedCifText = "";
let renderUploadName = "";
let lastHofmannImages = [];
let cardHofmannCache = new Map();
let viewer = null;
let renderViewer = null;
let spin = false;
let renderSpin = false;
let renderParams = { atomSize: 9, bondWidth: 3, jitter: 3, palette: 'science' };
let viewerParams = { style: 'stick', supercell: [1, 1, 1], atomScale: 0.22, stickRadius: 0.12, background: '#f1f5f8' };
let renderViewerParams = { style: 'stick', supercell: [1, 1, 1], atomScale: 0.22, stickRadius: 0.12, background: '#f1f5f8' };

const elColors = {
  H:'#8fa6b5', C:'#111820', N:'#2d5b84', O:'#b14f4f', F:'#338c82', Cl:'#4c9a58',
  Li:'#7aa6c8', Na:'#9aa7c4', K:'#a8a5c9', Mg:'#879c7a', Ca:'#8ba885', Ba:'#708a62',
  Ti:'#5b7286', Fe:'#484e57', Co:'#4f6072', Ni:'#526a6a', Ga:'#6f7e8c', Si:'#2f3942',
  P:'#6d5778', S:'#8b7e49', Zn:'#758696', Zr:'#638296', default:'#1c2c38'
};

function toast(msg){
  const t = $('#toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(()=>t.classList.add('hidden'), 2400);
}

function fmt(v, unit=''){
  if(v === null || v === undefined || v === '') return '--';
  if(typeof v === 'number') return `${Number(v).toFixed(Math.abs(v) < 1 ? 4 : 3)}${unit}`;
  return `${v}${unit}`;
}

async function api(url, options={}){
  const res = await fetch(url, options);
  if(!res.ok){
    let text = await res.text();
    throw new Error(text || res.statusText);
  }
  return await res.json();
}

function switchView(view){
  const target = $(`#view-${view}`);
  if(!target) return;
  $$('.view').forEach(v=>v.classList.remove('active'));
  target.classList.add('active');
  $$('.rail-item').forEach(b=>b.classList.toggle('active', b.dataset.view === view));
  if(view === 'render') {
    renderCurrent();
    const m = renderMaterial || currentMaterial || materials[0];
    if(m && m.cif) requestHofmannRender(m, 'render');
  }
  window.scrollTo({top:0, behavior:'smooth'});
}

function initNav(){
  $$('.rail-item').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.view)));
}

async function initHealth(){
  try{
    const h = await api('/api/health');
    $('#backendState').textContent = h.mp_api_enabled ? 'MP API ON' : 'MOCK MODE';
  }catch(e){
    $('#backendState').textContent = 'OFFLINE';
  }
}

async function loadPeriodic(){
  const data = await api('/api/periodic_table');
  const table = $('#periodicTable');
  table.innerHTML = '';
  data.elements.forEach(e=>{
    const btn = document.createElement('button');
    btn.className = `el ${e.category}`;
    btn.textContent = e.symbol;
    btn.style.gridColumn = e.col;
    btn.style.gridRow = e.row;
    btn.title = `${e.symbol} · ${e.category}`;
    if(e.symbol.includes('-')) btn.disabled = true;
    btn.addEventListener('click',()=>toggleElement(e.symbol, btn));
    table.appendChild(btn);
  });
}

function toggleElement(symbol, btn){
  if(selectedElements.includes(symbol)) selectedElements = selectedElements.filter(x=>x!==symbol);
  else selectedElements.push(symbol);
  btn.classList.toggle('selected', selectedElements.includes(symbol));
  renderSelectedElements();
}

function renderSelectedElements(){
  $('#selectedElements').innerHTML = selectedElements.map(s=>`<span class="element-chip">${s}</span>`).join('') || '<span class="muted">None</span>';
}

function initFilters(){
  $$('.mode-btn').forEach(btn=>btn.addEventListener('click',()=>{
    $$('.mode-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    searchMode = btn.dataset.mode;
  }));
  $$('.class-btn').forEach(btn=>btn.addEventListener('click',()=>{
    $$('.class-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    materialClass = btn.dataset.class;
  }));
  $('#clearElements').addEventListener('click',()=>{
    selectedElements = [];
    $$('.el').forEach(b=>b.classList.remove('selected'));
    renderSelectedElements();
  });
  $('#sortSelect').addEventListener('change',()=>renderMaterials(sortMaterials([...materials])));
}

function sortMaterials(arr){
  const s = $('#sortSelect').value;
  if(s === 'gap') return arr.sort((a,b)=>(b.band_gap ?? -1)-(a.band_gap ?? -1));
  if(s === 'density') return arr.sort((a,b)=>(b.density ?? -1)-(a.density ?? -1));
  return arr.sort((a,b)=>(b.is_stable === true)-(a.is_stable === true));
}

async function searchMaterials(){
  const btn = $('#searchBtn');
  btn.textContent = 'Searching...';
  btn.disabled = true;
  $('#materialGrid').innerHTML = Array.from({length:8}).map(()=>'<div class="material-card loading-card"></div>').join('');
  try{
    const data = await api('/api/search_mp', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:$('#searchInput').value.trim(), mode:searchMode, elements:selectedElements, material_class:materialClass, limit:36})
    });
    materials = sortMaterials(data.materials || []);
    $('#resultCount').textContent = `全部的 ${data.total ?? materials.length} 条结果 · ${data.source === 'mock' ? 'Demo Data' : 'Materials Project'}`;
    renderMaterials(materials);
    if(data.warning) toast('MP API 不可用，已切换 demo 数据');
  }catch(e){
    toast('检索失败：' + e.message.slice(0,90));
    $('#materialGrid').innerHTML = '';
  }finally{
    btn.textContent = 'Search';
    btn.disabled = false;
  }
}

function renderMaterials(list){
  const grid = $('#materialGrid');
  grid.innerHTML = '';
  list.forEach(m=>{
    const card = document.createElement('article');
    card.className = 'material-card';
    card.innerHTML = `
      <div class="stable-badge ${m.is_stable ? '' : 'unstable'}">${m.is_stable ? 'STABLE' : 'SCREEN'}</div>
      <div class="card-name">${m.formula_pretty || '--'}</div>
      <div class="card-id">${m.material_id || '--'}</div>
      <div class="sg">${m.spacegroup || 'Space group --'} · ${m.crystal_system || 'system --'}</div>
      <div class="card-hofmann-slot">
        <div class="card-hof-loading">Hofmann rendering...</div>
        <svg class="hof-preview" viewBox="0 0 260 140"></svg>
      </div>
      <div class="prop-line">
        <span>Density</span><b>${fmt(m.density,'')}</b>
        <span>Band gap</span><b>${fmt(m.band_gap,' eV')}</b>
        <span>E hull</span><b>${fmt(m.energy_above_hull,'')}</b>
        <span>Elements</span><b>${(m.elements||[]).join(' ')}</b>
      </div>`;
    card.addEventListener('click',()=>openMaterial(m));
    grid.appendChild(card);
    drawProjection(card.querySelector('svg'), m.sites || [], 'ab', {preview:true});
    requestCardHofmann(card, m);
  });
}

async function requestCardHofmann(card, m){
  const slot = card.querySelector('.card-hofmann-slot');
  if(!slot || !m || !m.cif) {
    slot?.classList.add('fallback');
    return;
  }
  const key = `${m.material_id || m.formula_pretty || 'material'}::${m.cif.length}`;
  if(cardHofmannCache.has(key)){
    setCardHofmannImage(slot, cardHofmannCache.get(key));
    return;
  }
  try{
    const data = await api('/api/render_hofmann', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({cif_text:m.cif, zoom:1.08, bond_scale:1.12, perspective:0.0}),
    });
    const img = data.images && data.images[0];
    if(img){
      cardHofmannCache.set(key, img.url);
      setCardHofmannImage(slot, img.url);
    }else{
      slot.classList.add('fallback');
      const loading = slot.querySelector('.card-hof-loading');
      if(loading) loading.textContent = 'SVG fallback';
    }
  }catch(e){
    slot.classList.add('fallback');
    const loading = slot.querySelector('.card-hof-loading');
    if(loading) loading.textContent = 'SVG fallback';
  }
}

function setCardHofmannImage(slot, url){
  slot.classList.add('real');
  slot.innerHTML = `<img class="card-hof-img" src="${url}?t=${Date.now()}" alt="Hofmann preview">`;
}

async function openMaterial(m){
  switchView('detail');
  $('#detailTitle').textContent = `${m.formula_pretty || '--'} · ${m.material_id || ''}`;
  $('#detailSub').textContent = 'Loading Materials Project properties...';
  $('#viewer3d').innerHTML = '<div class="viewer-loading">Loading structure viewer...</div>';
  currentMaterial = m;
  try{
    const detail = await api(`/api/material/${encodeURIComponent(m.material_id)}`);
    currentMaterial = {...m, ...detail};
  }catch(e){
    currentMaterial = m;
    toast('详情数据获取失败，已展示卡片缓存信息');
  }
  $('#detailTitle').textContent = `${currentMaterial.formula_pretty || '--'} · ${currentMaterial.material_id || ''}`;
  $('#detailSub').textContent = `${currentMaterial.spacegroup || 'Unknown space group'} · ${(currentMaterial.elements||[]).join(', ')}`;
  renderDetail(currentMaterial);
}

function renderDetail(m){
  render3D(m);
  drawProjection($('#detailTop'), m.sites || [], 'ab');
  drawProjection($('#detailFront'), m.sites || [], 'ac');
  drawProjection($('#detailSide'), m.sites || [], 'bc');
  requestHofmannRender(m, 'detail');
  renderPropertyGroups(m);
  drawRadar(m);
  drawBars(m);
}

function renderPropertyGroups(m){
  const groups = m.property_groups || {
    Structure:{'Space group':m.spacegroup,'Crystal system':m.crystal_system,'Density':m.density,'Sites':(m.sites||[]).length},
    Thermodynamic:{'Formation energy / atom':m.formation_energy_per_atom,'Energy above hull':m.energy_above_hull,'Stable':m.is_stable},
    Electronic:{'Band gap':m.band_gap,'Metal':m.is_metal},
    Magnetic:{'Total magnetization':m.total_magnetization || '--'}
  };
  $('#propertyGroups').innerHTML = Object.entries(groups).map(([name, vals])=>`
    <div class="prop-group"><h3>${name}</h3>
      ${Object.entries(vals || {}).map(([k,v])=>`<div class="prop-row"><span>${k}</span><b>${typeof v === 'object' ? 'Object' : fmt(v)}</b></div>`).join('')}
    </div>`).join('');
}

function render3D(m, style=viewerParams.style, targetId='viewer3d', params=viewerParams, shouldSpin=spin){
  const el = $('#' + targetId);
  if(!el) return;
  el.style.position = 'relative';
  el.style.overflow = 'hidden';
  if(!window.$3Dmol || !m.cif){
    el.innerHTML = `<div style="height:100%;display:grid;place-items:center;color:#607080;text-align:center;padding:20px">3Dmol viewer will render here when CIF data is available.<br/>Current fallback uses Hofmann projections.</div>`;
    return;
  }
  el.innerHTML = '';
  const localViewer = $3Dmol.createViewer(el, {backgroundColor: params.background});
  if(targetId === 'viewer3d') viewer = localViewer;
  if(targetId === 'renderViewer3d') renderViewer = localViewer;

  const model = localViewer.addModel(m.cif, 'cif');
  const [nx, ny, nz] = params.supercell || [1,1,1];
  if((nx * ny * nz) > 1){
    try{
      if(typeof localViewer.replicateUnitCell === 'function') localViewer.replicateUnitCell(nx, ny, nz, model);
    }catch(err){
      console.warn('3Dmol supercell replication failed:', err);
    }
  }
  const atomColor = '#143f63';
  const stickColor = '#405466';
  const lineColor = params.background === '#0e1822' ? '#dce8f0' : '#143f63';
  if(style === 'sphere') localViewer.setStyle({}, {sphere:{scale:params.atomScale, color:atomColor}});
  else if(style === 'line') localViewer.setStyle({}, {line:{color:lineColor}});
  else localViewer.setStyle({}, {stick:{radius:params.stickRadius, color:stickColor}, sphere:{scale:params.atomScale, color:atomColor}});
  localViewer.addUnitCell({box:{color:'#0f2f4a'}, alabel:'', blabel:'', clabel:''});
  localViewer.zoomTo();
  localViewer.render();
  requestAnimationFrame(()=>{
    try{
      localViewer.resize();
      localViewer.zoomTo();
      localViewer.render();
      if(shouldSpin) localViewer.spin(true);
    }catch(err){ console.warn('3D viewer resize failed:', err); }
  });
}

function initDetailControls(){
  $('#closeDetail').addEventListener('click',()=>switchView('explore'));
  $$('.view-style[data-style]').forEach(btn=>btn.addEventListener('click',()=>{
    $$('.view-style[data-style]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    viewerParams.style = btn.dataset.style;
    if(currentMaterial) render3D(currentMaterial);
  }));
  $('#spinBtn').addEventListener('click',()=>{
    spin = !spin;
    $('#spinBtn').classList.toggle('active', spin);
    if(viewer) viewer.spin(spin);
  });
  $('#supercellSelect').addEventListener('change',()=>{
    viewerParams.supercell = $('#supercellSelect').value.split(',').map(Number);
    if(currentMaterial) render3D(currentMaterial);
    toast(`Supercell: ${viewerParams.supercell.join(' × ')}`);
  });
  $('#viewerAtomScale').addEventListener('input',()=>{
    viewerParams.atomScale = +$('#viewerAtomScale').value / 100;
    if(currentMaterial) render3D(currentMaterial);
  });
  $('#viewerStickRadius').addEventListener('input',()=>{
    viewerParams.stickRadius = +$('#viewerStickRadius').value / 100;
    if(currentMaterial) render3D(currentMaterial);
  });
  $('#viewerBg').addEventListener('change',()=>{
    viewerParams.background = $('#viewerBg').value;
    if(currentMaterial) render3D(currentMaterial);
  });
}

function coord(site, axis){
  const f = site.frac_coords || [Math.random(),Math.random(),Math.random()];
  if(axis==='ab') return [f[0], f[1]];
  if(axis==='ac') return [f[0], f[2]];
  return [f[1], f[2]];
}
function drawProjection(svg, sites, axis='ab', opts={}){
  if(!svg) return;
  const size = opts.preview ? {w:260,h:140} : {w:320,h:230};
  const atomSize = opts.preview ? 5 : renderParams.atomSize;
  const jitter = opts.preview ? 0 : renderParams.jitter;
  svg.innerHTML = '';
  const ns = 'http://www.w3.org/2000/svg';
  const bg = document.createElementNS(ns,'rect');
  bg.setAttribute('x','20');bg.setAttribute('y','18');bg.setAttribute('width',size.w-40);bg.setAttribute('height',size.h-36);bg.setAttribute('fill','none');bg.setAttribute('stroke','#aebdca');bg.setAttribute('stroke-width','1');
  svg.appendChild(bg);
  // grid
  for(let i=1;i<4;i++){
    const l1=document.createElementNS(ns,'line');l1.setAttribute('x1',20+i*(size.w-40)/4);l1.setAttribute('y1',18);l1.setAttribute('x2',20+i*(size.w-40)/4);l1.setAttribute('y2',size.h-18);l1.setAttribute('stroke','#edf1f5');svg.appendChild(l1);
    const l2=document.createElementNS(ns,'line');l2.setAttribute('x1',20);l2.setAttribute('y1',18+i*(size.h-36)/4);l2.setAttribute('x2',size.w-20);l2.setAttribute('y2',18+i*(size.h-36)/4);l2.setAttribute('stroke','#edf1f5');svg.appendChild(l2);
  }
  const pts = (sites && sites.length ? sites : [{element:'X',frac_coords:[.5,.5,.5]}]).map((s,i)=>{
    const [u,v]=coord(s,axis);
    return {s,x:20+u*(size.w-40)+(Math.sin(i*1.7)*jitter), y:18+(1-v)*(size.h-36)+(Math.cos(i*2.1)*jitter)};
  });
  pts.forEach((p,i)=>{
    for(let j=i+1;j<pts.length;j++){
      const q=pts[j]; const d=Math.hypot(p.x-q.x,p.y-q.y);
      if(d < (opts.preview?75:105)){
        const line=document.createElementNS(ns,'line');
        line.setAttribute('x1',p.x);line.setAttribute('y1',p.y);line.setAttribute('x2',q.x);line.setAttribute('y2',q.y);
        line.setAttribute('stroke','#738394');line.setAttribute('stroke-width',opts.preview?1:renderParams.bondWidth/2);line.setAttribute('opacity','.55');svg.appendChild(line);
      }
    }
  });
  pts.forEach((p)=>{
    const c=document.createElementNS(ns,'circle');
    c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r',atomSize);
    const col = renderParams.palette==='mono' ? '#111' : (elColors[p.s.element] || elColors.default);
    c.setAttribute('fill', col);c.setAttribute('stroke','#fff');c.setAttribute('stroke-width','1.3');svg.appendChild(c);
    if(!opts.preview){
      const t=document.createElementNS(ns,'text');t.setAttribute('x',p.x+atomSize+3);t.setAttribute('y',p.y+4);t.setAttribute('font-size','10');t.setAttribute('fill','#53616d');t.textContent=p.s.element;svg.appendChild(t);
    }
  });
}

function drawRadar(m){
  const c = $('#radarChart'); if(!c) return;
  const ctx = c.getContext('2d'); ctx.clearRect(0,0,c.width,c.height);
  const vals = [
    Math.min((m.band_gap||0)/5,1), Math.min((m.density||0)/10,1),
    Math.max(0,1-Math.min((m.energy_above_hull||0)/0.2,1)), Math.min(((m.sites||[]).length||1)/20,1),
    m.is_stable ? 1 : .45
  ];
  const labels=['Gap','Density','Stability','Sites','Stable'];
  const cx=220, cy=135, r=90;
  ctx.strokeStyle='#d5dee6'; ctx.fillStyle='#60717e'; ctx.font='11px Arial';
  for(let ring=1; ring<=4; ring++){
    ctx.beginPath();
    for(let i=0;i<5;i++){const a=-Math.PI/2+i*2*Math.PI/5; const x=cx+Math.cos(a)*r*ring/4; const y=cy+Math.sin(a)*r*ring/4; i?ctx.lineTo(x,y):ctx.moveTo(x,y)}
    ctx.closePath();ctx.stroke();
  }
  labels.forEach((lab,i)=>{const a=-Math.PI/2+i*2*Math.PI/5;ctx.fillText(lab,cx+Math.cos(a)*(r+18)-15,cy+Math.sin(a)*(r+18)+4)});
  ctx.beginPath();
  vals.forEach((v,i)=>{const a=-Math.PI/2+i*2*Math.PI/5; const x=cx+Math.cos(a)*r*v; const y=cy+Math.sin(a)*r*v; i?ctx.lineTo(x,y):ctx.moveTo(x,y)});
  ctx.closePath();ctx.fillStyle='rgba(0,169,200,.22)';ctx.fill();ctx.strokeStyle='#00a9c8';ctx.lineWidth=2;ctx.stroke();
}

function drawBars(m){
  const c = $('#barChart'); if(!c) return;
  const ctx = c.getContext('2d'); ctx.clearRect(0,0,c.width,c.height);
  const entries=[['Band gap',m.band_gap||0,5],['Density',m.density||0,10],['E hull',m.energy_above_hull||0,.2],['Sites',(m.sites||[]).length||0,20]];
  ctx.font='12px Arial';
  entries.forEach((e,i)=>{
    const y=30+i*42; ctx.fillStyle='#60717e';ctx.fillText(e[0],18,y+11);
    ctx.fillStyle='#e5edf2';ctx.fillRect(105,y,280,15);
    ctx.fillStyle=i===2?'#143f63':'#00a9c8';ctx.fillRect(105,y,Math.min(e[1]/e[2],1)*280,15);
    ctx.fillStyle='#243444';ctx.fillText(fmt(e[1]),395,y+12);
  });
}

function hofmannParams(){
  const val = (id, fallback) => $('#'+id) ? +$('#'+id).value : fallback;
  return {
    zoom: val('hofZoom', 120) / 100,
    bond_scale: val('hofBondScale', 112) / 100,
    // Perspective is intentionally fixed by backend at 0.0 to match the previous Hofmann script.
    perspective: 0.0,
  };
}

function applyRenderEffects(){
  const contrast = $('#renderContrast') ? +$('#renderContrast').value : 106;
  const shadow = $('#renderShadow') ? +$('#renderShadow').value : 18;
  const alpha = Math.min(0.38, (shadow + 8) / 100).toFixed(2);
  document.documentElement.style.setProperty('--render-contrast', `${contrast}%`);
  document.documentElement.style.setProperty('--render-shadow', `0 ${Math.round(shadow/2)}px ${shadow}px rgba(8,28,44,${alpha})`);
}

function setHofmannImages(scope, images){
  const realGrid = scope === 'detail' ? $('#detailRealHofmannGrid') : $('#realHofmannGrid');
  const fallbackGrid = scope === 'detail' ? $('#detailFallbackHofmannGrid') : $('#fallbackHofmannGrid');
  if(!realGrid || !fallbackGrid) return;
  if(images && images.length){
    realGrid.innerHTML = images.map((img, idx)=>{
      const labels = ['[100]', '[010]', '[001]'];
      return `<div class="real-hof-card"><span>${labels[idx] || img.name}</span><img src="${img.url}?t=${Date.now()}" alt="Hofmann ${img.name}"></div>`;
    }).join('');
    realGrid.classList.remove('hidden');
    fallbackGrid.classList.add('hidden');
    applyRenderEffects();
  }else{
    realGrid.classList.add('hidden');
    fallbackGrid.classList.remove('hidden');
  }
}

async function requestHofmannRender(m, scope='render'){
  if(!m || !m.cif){
    setHofmannImages(scope, []);
    return null;
  }
  if(scope === 'render') $('#renderProgress')?.classList.remove('hidden');
  try{
    const payload = {cif_text:m.cif, ...hofmannParams()};
    const data = await api('/api/render_hofmann', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload),
    });
    if(data.material){
      const normalized = data.material;
      normalized.cif = normalized.cif || m.cif;
      normalized.formula_pretty = normalized.formula_pretty || normalized.formula || m.formula_pretty;
      normalized.material_id = m.material_id || normalized.material_id || 'uploaded-cif';
      const sgObj = normalized.spacegroup;
      normalized.spacegroup = sgObj?.space_group_symbol || m.spacegroup || normalized.spacegroup;
      normalized.crystal_system = sgObj?.crystal_system || m.crystal_system || normalized.crystal_system;
      if(scope === 'render') renderMaterial = {...m, ...normalized};
    }
    if(data.images && data.images.length){
      lastHofmannImages = data.images;
      setHofmannImages(scope, data.images);
      if(scope === 'render') toast('Hofmann rendering completed');
    }else{
      setHofmannImages(scope, []);
      if(scope === 'render') toast(data.warning || 'Hofmann package unavailable, using fallback projection');
    }
    return data;
  }catch(e){
    setHofmannImages(scope, []);
    if(scope === 'render') toast('Hofmann 渲染失败：' + e.message.slice(0,100));
    return null;
  }finally{
    if(scope === 'render') $('#renderProgress')?.classList.add('hidden');
  }
}

function renderCurrent(){
  const m = renderMaterial || currentMaterial || materials[0];
  if(!m) return;
  drawProjection($('#renderTop'), m.sites || [], 'ab');
  drawProjection($('#renderFront'), m.sites || [], 'ac');
  drawProjection($('#renderSide'), m.sites || [], 'bc');
  render3D(m, renderViewerParams.style, 'renderViewer3d', renderViewerParams, renderSpin);
  applyRenderEffects();
}

async function readFileAsText(file){
  return await new Promise((resolve, reject)=>{
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result || '');
    reader.onerror = reject;
    reader.readAsText(file);
  });
}

function showRenderUploadSuccess(file){
  renderUploadName = file?.name || '';
  $('#renderUploadState').textContent = renderUploadName ? `Uploaded: ${renderUploadName}` : 'No CIF uploaded.';
  $('#renderUploadState').classList.toggle('ok', Boolean(renderUploadName));
  if(renderUploadName) toast(`上传成功：${renderUploadName}`);
}

async function handleRenderUploadFile(file){
  if(!file) return;
  if(!file.name.toLowerCase().endsWith('.cif') && !file.name.toLowerCase().endsWith('.txt')){
    toast('请上传 .cif 文件');
    return;
  }
  renderUploadedCifText = await readFileAsText(file);
  showRenderUploadSuccess(file);
}

async function renderUploadedCif(){
  const file = $('#renderCifInput')?.files?.[0];
  if(file && !renderUploadedCifText) await handleRenderUploadFile(file);
  if(!renderUploadedCifText){ toast('请先上传 CIF 文件'); return; }
  renderMaterial = {material_id:'uploaded-cif', formula_pretty:renderUploadName || 'Uploaded CIF', cif:renderUploadedCifText, sites:[]};
  renderCurrent();
  const data = await requestHofmannRender(renderMaterial, 'render');
  if(data?.material){
    renderMaterial = {...renderMaterial, ...data.material, cif:data.material.cif || renderUploadedCifText};
    renderCurrent();
  }
}

function initRenderControls(){
  const updateFallback = ()=>{
    renderParams = {
      atomSize:+$('#atomSize').value,
      bondWidth:+$('#bondWidth').value,
      jitter:+$('#jitter').value,
      palette:$('#palette').value,
    };
    renderCurrent();
    applyRenderEffects();
  };
  ['atomSize','bondWidth','jitter','palette','renderContrast','renderShadow'].forEach(id=>{
    const node = $('#'+id);
    if(node) node.addEventListener('input', updateFallback);
  });
  ['hofZoom','hofBondScale'].forEach(id=>{
    const node = $('#'+id);
    if(node){
      node.addEventListener('input', ()=>{ applyRenderEffects(); });
      node.addEventListener('change', ()=>{
        const m = renderMaterial || currentMaterial || materials[0];
        if(m && m.cif) requestHofmannRender(m, 'render');
      });
    }
  });
  $('#render3dStyle').addEventListener('change',()=>{
    renderViewerParams.style = $('#render3dStyle').value;
    renderCurrent();
  });
  $('#render3dSupercell').addEventListener('change',()=>{
    renderViewerParams.supercell = $('#render3dSupercell').value.split(',').map(Number);
    renderCurrent();
    toast(`Render supercell: ${renderViewerParams.supercell.join(' × ')}`);
  });
  $('#render3dBg').addEventListener('change',()=>{
    renderViewerParams.background = $('#render3dBg').value;
    renderCurrent();
  });
  $('#render3dAtomScale').addEventListener('input',()=>{
    renderViewerParams.atomScale = +$('#render3dAtomScale').value / 100;
    renderCurrent();
  });
  $('#render3dBondRadius').addEventListener('input',()=>{
    renderViewerParams.stickRadius = +$('#render3dBondRadius').value / 100;
    renderCurrent();
  });
  $('#renderSpinBtn').addEventListener('click',()=>{
    renderSpin = !renderSpin;
    $('#renderSpinBtn').classList.toggle('active', renderSpin);
    if(renderViewer) renderViewer.spin(renderSpin);
  });
  $('#rerenderBtn').addEventListener('click',async ()=>{
    const m = currentMaterial || materials[0];
    if(!m){toast('请先在 Materials Explore 中选择一个材料'); return;}
    renderMaterial = m;
    renderCurrent();
    await requestHofmannRender(m, 'render');
  });
  $('#renderUploadBtn').addEventListener('click', renderUploadedCif);
  const renderInput = $('#renderCifInput');
  renderInput.addEventListener('change',()=>handleRenderUploadFile(renderInput.files[0]));
  const dz = $('#renderDropZone');
  ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('dragging');}));
  ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('dragging');}));
  dz.addEventListener('drop',async e=>{
    const file = e.dataTransfer.files[0];
    if(file){
      $('#renderCifInput').files = e.dataTransfer.files;
      await handleRenderUploadFile(file);
    }
  });
  applyRenderEffects();
}

async function evaluateCif(){
  const file = $('#cifInput').files[0];
  if(!file){ toast('请先选择 CIF 文件'); return; }
  $('#evalProgress').classList.remove('hidden');
  $('#evalState').textContent = 'Parsing CIF, then calling CHGNet / MatterSim predictors...';
  $('#evalCards').innerHTML = '';
  const fd = new FormData(); fd.append('file', file);
  try{
    const data = await api('/api/evaluate_cif', {method:'POST', body:fd});
    renderEval(data);
    $('#evalState').textContent = 'Finished';
  }catch(e){
    $('#evalState').textContent = 'Failed';
    toast('评估失败：' + e.message.slice(0,100));
  }finally{
    $('#evalProgress').classList.add('hidden');
  }
}

function renderEval(data){
  const st = data.structure || {};
  const sym = data.symmetry || {};
  const chg = data.chgnet || {};
  const mat = data.mattersim || {};
  const cards = [
    ['Formula', st.formula || '--', `Sites: ${st.nsites || '--'} · Density: ${fmt(st.density)}`],
    ['Symmetry', sym.space_group_symbol || '--', `No. ${sym.space_group_number || '--'} · ${sym.crystal_system || '--'}`],
    ['Volume', fmt(st.volume,' Å³'), `a=${fmt(st.lattice?.a)} b=${fmt(st.lattice?.b)} c=${fmt(st.lattice?.c)}`],
    ['Wyckoff', (sym.wyckoffs||[]).slice(0,8).join(' ') || '--', 'Extracted by pymatgen/spglib'],
    ['CHGNet', chg.available ? fmt(chg.energy_eV_per_atom,' eV/atom') : 'Unavailable', chg.available ? `Called · forces ${Array.isArray(chg.force_shape) ? chg.force_shape.join('×') : chg.force_shape || '--'} · stress/magmom returned` : (chg.message || 'Not installed')],
    ['MatterSim', mat.available ? fmt(mat.energy_eV,' eV') : 'Unavailable', mat.available ? 'ASE calculator output returned' : (mat.message || 'Not installed')],
  ];
  $('#evalCards').innerHTML = cards.map(c=>`<div class="eval-card"><h3>${c[0]}</h3><div class="big">${c[1]}</div><p>${c[2]}</p></div>`).join('');
}

function showEvalUploadSuccess(file){
  const state = $('#evalUploadState');
  if(!state) return;
  if(file){
    state.textContent = `Uploaded: ${file.name}`;
    state.classList.add('ok');
    $('#evalState').textContent = `CIF uploaded: ${file.name}. Ready for evaluation.`;
    toast(`上传成功：${file.name}`);
  }else{
    state.textContent = 'No CIF uploaded.';
    state.classList.remove('ok');
  }
}

function initUpload(){
  $('#evalBtn').addEventListener('click', evaluateCif);
  const input = $('#cifInput');
  input.addEventListener('change',()=>showEvalUploadSuccess(input.files[0]));
  const dz = $('#dropZone');
  ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.style.borderColor='#00a9c8';dz.style.background='#effbfc';dz.classList.add('dragging');}));
  ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.style.borderColor='#9fb0bd';dz.style.background='#f7fafc';dz.classList.remove('dragging');}));
  dz.addEventListener('drop',e=>{
    if(e.dataTransfer.files[0]){
      $('#cifInput').files = e.dataTransfer.files;
      showEvalUploadSuccess(e.dataTransfer.files[0]);
    }
  });
}

async function init(){
  initNav(); initFilters(); initDetailControls(); initRenderControls(); initUpload();
  await initHealth(); await loadPeriodic();
  renderSelectedElements();
  $('#searchBtn').addEventListener('click', searchMaterials);
  $('#searchInput').addEventListener('keydown', e=>{if(e.key==='Enter') searchMaterials();});
  await searchMaterials();
}

document.addEventListener('DOMContentLoaded', init);
