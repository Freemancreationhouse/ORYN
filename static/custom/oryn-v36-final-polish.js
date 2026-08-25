
(()=>{'use strict';

const q=(s,r=document)=>r.querySelector(s);
const qa=(s,r=document)=>[...r.querySelectorAll(s)];

function apiBase(){
  try{
    const s=localStorage.getItem('orynmotion_tables');
    const id=localStorage.getItem('orynmotion_active_table');
    if(s&&id){
      const d=JSON.parse(s);
      const t=(d.tables||[]).find(x=>x.id===id);
      if(t&&!t.isCurrent&&t.url)return t.url.replace(/\/$/,'');
    }
  }catch(_){}
  return '';
}
async function jsonReq(path,opts={}){
  const r=await fetch(apiBase()+path,opts);
  const raw=await r.text();
  let d={};
  try{d=raw?JSON.parse(raw):{}}catch(_){d={detail:raw}}
  if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`);
  return d;
}

/* ---------------- Theme ---------------- */
function syncTheme(){
  const dark=document.documentElement.classList.contains('dark');
  document.body.classList.toggle('oryn-theme-dark',dark);
  document.body.classList.toggle('oryn-theme-light',!dark);
}
new MutationObserver(syncTheme).observe(
  document.documentElement,
  {attributes:true,attributeFilter:['class']}
);
document.addEventListener('DOMContentLoaded',syncTheme);
setTimeout(syncTheme,30);

/* ---------------- Final footer ---------------- */
function installFooter(){
  q('#oryn-v35-footer')?.remove();
  if(q('#oryn-v36-footer'))return;
  const main=q('main');
  if(!main)return;
  const f=document.createElement('footer');
  f.id='oryn-v36-footer';
  f.innerHTML='<strong>ORYN</strong> — Designed to Move — by <strong>Studio Kinematics™</strong>';
  main.appendChild(f);
}

/* ---------------- Pattern Forge ---------------- */
let forge={
  file:null,
  preview:null,
  working:false,
  sourceUrl:null
};

function forgeStatus(text,error=false){
  const e=q('#oryn-forge-status');
  if(!e)return;
  e.textContent=text||'';
  e.classList.toggle('oryn-forge-error',!!error);
}

function forgeBusy(v){
  forge.working=v;
  qa('#oryn-forge-modal button').forEach(b=>b.disabled=v);
  const g=q('#oryn-forge-generate');
  if(g)g.textContent=v?'Generating…':'Generate Clean Route';
}

function closeForge(){
  if(forge.sourceUrl){
    try{URL.revokeObjectURL(forge.sourceUrl)}catch(_){}
  }
  forge={file:null,preview:null,working:false,sourceUrl:null};
  q('#oryn-forge-overlay')?.remove();
}

function forgeHtml(){
  return `
  <div id="oryn-forge-overlay">
    <div id="oryn-forge-modal">
      <div class="oryn-forge-head">
        <div>
          <div class="oryn-forge-title">Pattern Forge</div>
          <div class="oryn-forge-sub">PNG · JPG · JPEG · WEBP · BMP · SVG · DXF · THR → clean sand-table route</div>
        </div>
        <button class="oryn-forge-close" type="button">×</button>
      </div>

      <div class="oryn-forge-grid">
        <div class="oryn-forge-controls">
          <label class="oryn-forge-drop">
            <input id="oryn-forge-file" type="file" hidden
              accept=".svg,.dxf,.png,.jpg,.jpeg,.webp,.bmp,.thr">
            <b>Choose artwork</b>
            <small>Vector or high-contrast raster artwork</small>
            <div id="oryn-forge-file-name" class="oryn-forge-file">No file selected</div>
          </label>

          <div class="oryn-forge-field">
            <label>Pattern name</label>
            <input id="oryn-forge-name" type="text" placeholder="My ORYN pattern">
          </div>

          ${[
            ['fit','Fit inside table','.55','.98','.01','.94'],
            ['threshold','Image threshold','30','235','1','128'],
            ['smoothing','Smoothing','0','5','1','1'],
            ['simplify','Geometry simplify','0','.015','.0005','.0025'],
            ['rotation_deg','Rotation','-180','180','1','0'],
            ['offset_x','Horizontal offset','-.5','.5','.01','0'],
            ['offset_y','Vertical offset','-.5','.5','.01','0'],
            ['max_bridge','Max connector gap','0','.14','.005','.055']
          ].map(a=>`
            <div class="oryn-forge-field">
              <label>${a[1]} <span id="oryn-val-${a[0]}">${a[5]}</span></label>
              <input id="oryn-forge-${a[0]}" type="range"
                min="${a[2]}" max="${a[3]}" step="${a[4]}" value="${a[5]}">
            </div>`).join('')}

          <div class="oryn-forge-field">
            <label>Preferred route start</label>
            <select id="oryn-forge-start_mode"
              style="width:100%;height:39px;background:#0B0D10;color:#fff;border:1px solid #353A40;border-radius:9px;padding:0 10px">
              <option value="auto">Auto — lowest route cost</option>
              <option value="perimeter">Prefer perimeter</option>
              <option value="center">Prefer center</option>
            </select>
          </div>

          <label class="oryn-forge-toggle">
            <input id="oryn-forge-invert" type="checkbox">
            <div>
              <b>Invert raster artwork</b>
              <small>For light lines on a dark image</small>
            </div>
          </label>

          <div class="oryn-forge-note">
            Long disconnected islands are skipped instead of creating a large straight pass-line.
            Generate first, inspect the exact ball path, then save.
          </div>

          <div class="oryn-forge-actions">
            <button id="oryn-forge-generate" class="oryn-forge-btn primary" style="flex:1" type="button">
              Generate Clean Route
            </button>
            <button id="oryn-forge-save" class="oryn-forge-btn" type="button" disabled>
              Save to Library
            </button>
          </div>

          <div id="oryn-forge-status" class="oryn-forge-status"></div>
        </div>

        <div class="oryn-forge-preview">
          <div class="oryn-forge-source-wrap">
            <div class="oryn-forge-source-head">
              <b>SOURCE ARTWORK</b>
              <span id="oryn-forge-source-name">Nothing selected</span>
            </div>
            <div class="oryn-forge-source-box" id="oryn-forge-source-box">
              <div class="oryn-forge-source-placeholder">
                Select an image or SVG to preview the original artwork here.
              </div>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:12px">
            <div>
              <div style="font-size:10px;letter-spacing:.18em;color:#737674">ROUTE PREVIEW</div>
              <b>Exact ball path</b>
            </div>
            <div id="oryn-forge-stats" class="oryn-forge-stats"></div>
          </div>

          <div class="oryn-forge-canvas-wrap">
            <div class="oryn-forge-disc">
              <div id="oryn-forge-empty" class="oryn-forge-empty">
                Generate a route after selecting artwork.<br>
                <small>Nothing is saved until you approve it.</small>
              </div>
              <svg id="oryn-forge-svg" viewBox="0 0 360 360" style="display:none">
                <polyline id="oryn-forge-route"></polyline>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>`;
}

function showSourcePreview(file){
  const box=q('#oryn-forge-source-box');
  const name=q('#oryn-forge-source-name');
  if(!box||!name)return;

  name.textContent=file?.name||'Nothing selected';

  if(forge.sourceUrl){
    try{URL.revokeObjectURL(forge.sourceUrl)}catch(_){}
    forge.sourceUrl=null;
  }

  if(!file){
    box.innerHTML='<div class="oryn-forge-source-placeholder">Select an image or SVG to preview the original artwork here.</div>';
    return;
  }

  const ext=(file.name.split('.').pop()||'').toLowerCase();
  const previewable=file.type.startsWith('image/') || ['png','jpg','jpeg','webp','bmp','svg'].includes(ext);

  if(previewable){
    forge.sourceUrl=URL.createObjectURL(file);
    const img=document.createElement('img');
    img.alt='Uploaded source artwork';
    img.src=forge.sourceUrl;
    box.replaceChildren(img);
  }else{
    box.innerHTML=`<div class="oryn-forge-source-placeholder">
      <b>${file.name}</b><br><br>
      ${ext.toUpperCase()} geometry will appear in the route preview after Generate.
    </div>`;
  }
}

function openForge(){
  if(q('#oryn-forge-overlay'))return;
  document.body.insertAdjacentHTML('beforeend',forgeHtml());

  q('.oryn-forge-close').onclick=closeForge;
  q('#oryn-forge-overlay').onclick=e=>{
    if(e.target.id==='oryn-forge-overlay')closeForge();
  };

  q('#oryn-forge-file').onchange=e=>{
    forge.file=e.target.files?.[0]||null;
    forge.preview=null;

    q('#oryn-forge-file-name').textContent=forge.file?.name||'No file selected';
    showSourcePreview(forge.file);

    if(forge.file){
      q('#oryn-forge-name').value=forge.file.name.replace(/\.[^.]+$/,'');
    }

    q('#oryn-forge-save').disabled=true;
    q('#oryn-forge-svg').style.display='none';
    q('#oryn-forge-stats').innerHTML='';

    const empty=q('#oryn-forge-empty');
    if(empty){
      empty.style.display='';
      empty.innerHTML='Generate a route after selecting artwork.<br><small>Nothing is saved until you approve it.</small>';
    }
  };

  qa('#oryn-forge-modal input[type="range"]').forEach(el=>{
    const update=()=>{
      const v=q('#oryn-val-'+el.id.replace('oryn-forge-',''));
      if(v)v.textContent=el.id.endsWith('rotation_deg')?el.value+'°':el.value;
    };
    el.oninput=update;
    update();
  });

  q('#oryn-forge-generate').onclick=generateForge;
  q('#oryn-forge-save').onclick=saveForge;

  // Always start the controls at their top.
  const controls=q('.oryn-forge-controls');
  if(controls)controls.scrollTop=0;
}

async function generateForge(){
  if(!forge.file)return forgeStatus('Choose SVG, DXF, PNG, JPG or THR first.',true);

  forgeBusy(true);
  forgeStatus('');

  try{
    const fd=new FormData();
    fd.append('file',forge.file);

    ['fit','threshold','smoothing','simplify','rotation_deg','offset_x','offset_y','max_bridge']
      .forEach(k=>fd.append(k,q('#oryn-forge-'+k).value));

    fd.append('invert',String(q('#oryn-forge-invert').checked));
    fd.append('start_mode',q('#oryn-forge-start_mode').value);

    forge.preview=await jsonReq(
      '/api/v2/pattern-generator/preview',
      {method:'POST',body:fd}
    );

    const coords=forge.preview.coordinates||[];
    if(!coords.length)throw new Error('Generator returned an empty route.');

    const pts=coords.map(([t,r])=>
      `${(180+Math.cos(t)*r*160).toFixed(2)},${(180+Math.sin(t)*r*160).toFixed(2)}`
    ).join(' ');

    q('#oryn-forge-route').setAttribute('points',pts);
    q('#oryn-forge-svg').style.display='block';

    const empty=q('#oryn-forge-empty');
    if(empty)empty.style.display='none';

    const s=forge.preview.stats||{};
    q('#oryn-forge-stats').innerHTML=[
      `${forge.preview.points||0} route pts`,
      `${s.input_paths??'—'} input paths`,
      `${s.skipped_islands??0} long islands skipped`,
      `${s.clipped_points??0} clipped outside`,
      s.trace_mode?`${s.trace_mode} trace`:null,
      s.small_gaps_repaired!=null?`${s.small_gaps_repaired} tiny gaps repaired`:null
    ].filter(Boolean)
     .map(x=>`<span class="oryn-forge-chip">${x}</span>`).join('');

    forgeStatus('Clean route generated. Inspect the exact path, then Save to Library.');
    q('#oryn-forge-save').disabled=false;
  }catch(e){
    forgeStatus(e.message||String(e),true);
  }finally{
    forgeBusy(false);
    if(forge.preview)q('#oryn-forge-save').disabled=false;
  }
}

async function saveForge(){
  if(!forge.preview)return;

  const name=(q('#oryn-forge-name')?.value||'').trim();
  if(!name)return forgeStatus('Enter a pattern name.',true);

  forgeBusy(true);
  try{
    const d=await jsonReq('/api/v2/pattern-generator/save',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({token:forge.preview.token,name})
    });

    forgeStatus(`Saved to Library: ${d.name||name}`);
    setTimeout(()=>{
      closeForge();
      location.reload();
    },550);
  }catch(e){
    forgeStatus(e.message||String(e),true);
  }finally{
    forgeBusy(false);
  }
}

function installForge(){
  if(location.pathname!=='/'&&!location.pathname.includes('browse'))return;
  if(q('#oryn-pattern-forge-launch'))return;

  const h=qa('h1,h2').find(x=>(x.textContent||'').trim()==='Browse Patterns');
  if(!h)return;

  const row=h.parentElement?.parentElement;
  if(!row)return;

  const b=document.createElement('button');
  b.id='oryn-pattern-forge-launch';
  b.type='button';
  b.innerHTML='◇&nbsp; Pattern Forge';
  b.onclick=openForge;
  row.appendChild(b);
}

/* ---------------- Delete Pattern ---------------- */

function basenameNoExt(path){
  const name=String(path||'').replace(/\\/g,'/').split('/').pop()||'';
  return name.replace(/\.thr$/i,'');
}

async function allPatternPaths(){
  const d=await jsonReq('/list_theta_rho_files');
  return Array.isArray(d)?d:[];
}

function activePatternPanel(){
  const dialogs=qa('[role="dialog"]');
  return dialogs.find(d=>{
    const text=(d.textContent||'');
    return /Run Pattern|Clearing strategy|Add to Queue|Play Next|Queue/i.test(text);
  })||null;
}

async function selectedPatternPath(){
  const panel=activePatternPanel();
  if(!panel)return null;

  const panelText=(panel.textContent||'').replace(/\s+/g,' ').trim();
  const paths=await allPatternPaths();

  // Prefer longest matching basename so similarly named files don't collide.
  const matches=paths
    .map(path=>({path,base:basenameNoExt(path)}))
    .filter(x=>x.base && panelText.toLowerCase().includes(x.base.toLowerCase()))
    .sort((a,b)=>b.base.length-a.base.length);

  if(matches.length)return matches[0].path;

  // Try visible sheet title against path basenames.
  const titleCandidates=qa('h1,h2,h3,[data-radix-dialog-title],span',panel)
    .map(x=>(x.textContent||'').trim())
    .filter(x=>x && x.length<160 && !/Pattern Details|Clearing strategy/i.test(x));

  for(const title of titleCandidates){
    const normalized=title.toLowerCase();
    const found=paths.find(p=>basenameNoExt(p).toLowerCase()===normalized);
    if(found)return found;
  }
  return null;
}

async function doDelete(){
  try{
    const path=await selectedPatternPath();
    if(!path)throw new Error('Could not determine the selected pattern file.');

    // Protect the three system clearing patterns; normal/default/custom drawing
    // patterns can be deleted if the user explicitly confirms.
    const bn=path.replace(/\\/g,'/').split('/').pop()?.toLowerCase()||'';
    if(['clear_from_in.thr','clear_from_out.thr','clear_sideway.thr'].includes(bn)){
      throw new Error('System clearing patterns are protected and cannot be deleted.');
    }

    if(!confirm(`Delete "${basenameNoExt(path)}"?\n\nThis permanently removes the pattern from the ORYN Library.`)){
      return;
    }

    await jsonReq('/delete_theta_rho_file',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({file_name:path})
    });

    alert('Pattern deleted.');
    location.reload();
  }catch(e){
    alert('Delete failed: '+(e.message||e));
  }
}

function installDelete(){
  const panel=activePatternPanel();
  if(!panel)return;

  // Remove any stale button inserted outside the active panel.
  qa('#oryn-delete-pattern').forEach(b=>{
    if(!panel.contains(b))b.remove();
  });

  if(q('#oryn-delete-pattern',panel))return;

  const buttons=qa('button',panel);
  const run=buttons.find(b=>{
    const t=(b.textContent||'').replace(/\s+/g,' ').trim();
    return /Run Pattern|^Play$|Play Pattern|Starting/i.test(t);
  });

  if(!run)return;

  const actionRow=run.parentElement;
  if(!actionRow)return;

  const b=document.createElement('button');
  b.id='oryn-delete-pattern';
  b.type='button';
  b.title='Delete selected pattern';
  b.innerHTML='⌫&nbsp; Delete';
  b.onclick=doDelete;
  actionRow.appendChild(b);
}

/* ---------------- Install loop ---------------- */
function installAll(){
  syncTheme();
  installFooter();
  installForge();
  installDelete();
}

new MutationObserver(installAll).observe(
  document.documentElement,
  {childList:true,subtree:true}
);
document.addEventListener('DOMContentLoaded',installAll);
setInterval(installAll,650);

})();
