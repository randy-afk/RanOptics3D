
(function() {
  // Wait until the Plotly graph div is fully initialized — we need the
  // .on() event API (added by Plotly) AND the .data array (populated after
  // newPlot resolves). Polling avoids depending on Plotly's internal
  // post_script mechanism, which has version-specific quirks.
  function waitForPlotly(cb, attempts) {
    attempts = attempts || 0;
    var gd = document.querySelector('.plotly-graph-div');
    if (gd && typeof gd.on === 'function' && Array.isArray(gd.data)) {
      cb(gd);
    } else if (attempts < 200) {  // ~10 s @ 50 ms
      setTimeout(function(){ waitForPlotly(cb, attempts + 1); }, 50);
    } else {
      console.warn('RanOptics3D: Plotly graph div never ready — control panel disabled.');
    }
  }

  waitForPlotly(function(gd) {
  var SCENE = __SCENE_JSON__;

  // ── Helpers ────────────────────────────────────────────────────────────
  function tracesByName(names) {
    // Return numeric trace indices whose name matches any in `names`
    var out = [];
    var data = gd.data || [];
    for (var i = 0; i < data.length; i++) {
      if (names.indexOf(data[i].name) !== -1) out.push(i);
    }
    return out;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  // Convert wildcard glob (* and ?) to regex
  function globToRegex(pat) {
    var s = pat.replace(/[.+^${}()|[\]\\]/g, '\\$&')
               .replace(/\*/g, '.*').replace(/\?/g, '.');
    return new RegExp('^' + s + '$', 'i');
  }


  // ── Build element type controls ──────────────────────────────────────
  var typesDiv = document.getElementById('rop-types');
  Object.keys(SCENE.type_traces).forEach(function(typeName) {
    var traces = SCENE.type_traces[typeName];
    var color = SCENE.type_colors[typeName] || '#888';
    var row = document.createElement('div'); row.className = 'rop-chk';
    row.innerHTML =
      '<span class="rop-swatch" style="background:'+color+'"></span>' +
      '<input type="checkbox" data-rop-type-vis="'+typeName+'" checked>' +
      '<span style="flex:1;">' + escapeHtml(typeName) + '</span>' +
      '<input type="range" min="0" max="1" step="0.05" value="1" ' +
        'data-rop-type-op="'+typeName+'" title="Opacity">';
    typesDiv.appendChild(row);
  });

  // Visibility checkboxes
  document.querySelectorAll('[data-rop-type-vis]').forEach(function(cb) {
    cb.addEventListener('change', function() {
      var t = cb.getAttribute('data-rop-type-vis');
      var idxs = tracesByName(SCENE.type_traces[t] || []);
      if (!idxs.length) return;
      Plotly.restyle(gd, {visible: cb.checked ? true : 'legendonly'}, idxs);
    });
  });
  // Opacity sliders
  document.querySelectorAll('[data-rop-type-op]').forEach(function(sl) {
    sl.addEventListener('input', function() {
      var t = sl.getAttribute('data-rop-type-op');
      var idxs = tracesByName(SCENE.type_traces[t] || []);
      if (!idxs.length) return;
      Plotly.restyle(gd, {opacity: parseFloat(sl.value)}, idxs);
    });
  });

  // ── Twiss tube panel controls ────────────────────────────────────────
  (function() {
    var hasTube = (SCENE.overlay_traces['Twiss tube'] || []).length > 0;
    var hasSx   = (SCENE.overlay_traces['Twiss σ_x']  || []).length > 0;
    var hasSy   = (SCENE.overlay_traces['Twiss σ_y']  || []).length > 0;
    if (!hasTube && !hasSx && !hasSy) {
      var unavail = document.getElementById('rop-twiss-unavail');
      var ctrls   = document.getElementById('rop-twiss-controls');
      if (unavail) unavail.style.display = 'block';
      if (ctrls)   ctrls.style.display   = 'none';
      return;
    }
    function twissVis(key, visible) {
      var idxs = tracesByName(SCENE.overlay_traces[key] || []);
      if (idxs.length) Plotly.restyle(gd, {visible: visible ? true : 'legendonly'}, idxs);
    }
    function twissOp(key, op) {
      var idxs = tracesByName(SCENE.overlay_traces[key] || []);
      if (idxs.length) Plotly.restyle(gd, {opacity: op}, idxs);
    }
    var cbTube = document.getElementById('rop-twiss-tube');
    var cbSx   = document.getElementById('rop-twiss-sx');
    var cbSy   = document.getElementById('rop-twiss-sy');
    var slOp   = document.getElementById('rop-twiss-op');
    var spOp   = document.getElementById('rop-twiss-op-val');
    if (cbTube) cbTube.addEventListener('change', function() { twissVis('Twiss tube', cbTube.checked); });
    if (cbSx)   cbSx.addEventListener('change',   function() { twissVis('Twiss σ_x',  cbSx.checked);   });
    if (cbSy)   cbSy.addEventListener('change',   function() { twissVis('Twiss σ_y',  cbSy.checked);   });
    if (slOp)   slOp.addEventListener('input', function() {
      var v = parseFloat(slOp.value);
      spOp.textContent = v.toFixed(2);
      twissOp('Twiss tube', v);
    });
  })();

  // ── Build overlay controls ───────────────────────────────────────────
  var overlaysDiv = document.getElementById('rop-overlays');
  Object.keys(SCENE.overlay_traces).forEach(function(name) {
    var row = document.createElement('div'); row.className = 'rop-chk';
    row.innerHTML =
      '<input type="checkbox" data-rop-overlay="'+name+'" checked>' +
      '<span>' + escapeHtml(name) + '</span>';
    overlaysDiv.appendChild(row);
  });
  document.querySelectorAll('[data-rop-overlay]').forEach(function(cb) {
    cb.addEventListener('change', function() {
      var t = cb.getAttribute('data-rop-overlay');
      var idxs = tracesByName(SCENE.overlay_traces[t] || []);
      if (!idxs.length) return;
      Plotly.restyle(gd, {visible: cb.checked ? true : 'legendonly'}, idxs);
    });
  });

  // ── Grid toggle ──────────────────────────────────────────────────────
  var gridRow = document.createElement('div'); gridRow.className = 'rop-chk';
  gridRow.innerHTML = '<input type="checkbox" id="rop-grid-toggle" checked><span>Grid</span>';
  overlaysDiv.appendChild(gridRow);
  document.getElementById('rop-grid-toggle').addEventListener('change', function() {
    var show = this.checked;
    Plotly.relayout(gd, {
      'scene.xaxis.showgrid':        show,
      'scene.yaxis.showgrid':        show,
      'scene.zaxis.showgrid':        show,
      'scene.xaxis.showbackground':  show,
      'scene.yaxis.showbackground':  show,
      'scene.zaxis.showbackground':  show,
      'scene.xaxis.zeroline':        show,
      'scene.yaxis.zeroline':        show,
      'scene.zaxis.zeroline':        show,
    });
  });

  // ── Element name autocomplete ────────────────────────────────────────
  var datalist = document.getElementById('rop-elem-list');
  var seen = {};
  SCENE.elements.forEach(function(e) {
    if (seen[e.name]) return;
    seen[e.name] = true;
    var opt = document.createElement('option'); opt.value = e.name;
    datalist.appendChild(opt);
  });

  // ── Highlight system ─────────────────────────────────────────────────
  // Each call to addHighlight takes a pattern (may contain * and ?).
  // All matching elements get one colour; panel shows one tag per pattern.
  var highlightTraces = [];
  var highlightAnnots = [];
  var highlightDiv = document.getElementById('rop-highlights');
  var HIGHLIGHT_COLORS = [
    '#ffdd00','#ff6b6b','#69db7c','#74c0fc','#ffa94d',
    '#da77f2','#f783ac','#63e6be','#ff8787','#a9e34b'
  ];
  var hlColorIdx = 0;

  function findByPattern(pat) {
    var t = pat.trim();
    if (!t) return [];
    // Only match elements that have 3D floor coordinates
    var pool = SCENE.elements;
    if (t.indexOf('*') === -1 && t.indexOf('?') === -1) {
      var tl = t.toLowerCase();
      var exact = pool.filter(function(e){ return e.name.toLowerCase() === tl; });
      if (exact.length) return exact;
      return pool.filter(function(e){ return e.name.toLowerCase().indexOf(tl) === 0; });
    }
    var re = globToRegex(t);
    return pool.filter(function(e){ return re.test(e.name); });
  }

  function addHighlight(pat) {
    var matches = findByPattern(pat);
    if (!matches.length) return;
    var color = HIGHLIGHT_COLORS[hlColorIdx % HIGHLIGHT_COLORS.length];
    hlColorIdx++;
    var traceName = '__hl__' + hlColorIdx + '__' + pat;

    // One Scatter3d trace for all matched elements — marker only, no inline text
    var xs = matches.map(function(e){ return e.x; });
    var ys = matches.map(function(e){ return e.y; });
    var zs = matches.map(function(e){ return e.z; });
    Plotly.addTraces(gd, {
      type: 'scatter3d', mode: 'markers',
      x: xs, y: ys, z: zs,
      name: traceName, showlegend: false, hoverinfo: 'skip',
      marker: {
        size: 14, color: color, opacity: 0.9,
        line: {color: '#ffffff', width: 2},
        symbol: 'circle'
      }
    });
    highlightTraces.push(traceName);

    // Annotations — one per matched element
    matches.forEach(function(e) {
      highlightAnnots.push({
        x: e.x, y: e.y, z: e.z,
        text: '<b>' + escapeHtml(e.name) + '</b>',
        showarrow: true, arrowhead: 2, arrowsize: 1.2, arrowwidth: 1.5,
        arrowcolor: color, ax: 0, ay: -36,
        font: {size: SCENE.annot_font_size || 10, color: color},
        bgcolor: SCENE.dark_mode ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.8)',
        bordercolor: color, borderwidth: 1, borderpad: 3
      });
    });
    Plotly.relayout(gd, {'scene.annotations': highlightAnnots});

    // One tag in panel showing the pattern + match count
    var tag = document.createElement('span');
    var label = pat + (matches.length > 1 ? ' (' + matches.length + ')' : '');
    tag.style.cssText = 'display:inline-block;background:' + color +
      ';color:#111;border-radius:3px;padding:1px 6px;margin:2px;font-size:10px;' +
      'font-family:monospace;';
    tag.textContent = label;
    highlightDiv.appendChild(tag);
  }

  function clearHighlights() {
    var indices = [];
    var data = gd.data || [];
    for (var i = 0; i < data.length; i++) {
      if (highlightTraces.indexOf(data[i].name) !== -1) indices.push(i);
    }
    if (indices.length) Plotly.deleteTraces(gd, indices);
    highlightTraces = []; highlightAnnots = []; hlColorIdx = 0;
    Plotly.relayout(gd, {'scene.annotations': []});
    highlightDiv.innerHTML = '';
    updateAnnotations();
  }

  document.getElementById('rop-focus-go').addEventListener('click', function() {
    var pat = document.getElementById('rop-focus').value.trim();
    if (pat) { addHighlight(pat); document.getElementById('rop-focus').value = ''; }
  });
  document.getElementById('rop-focus').addEventListener('keydown', function(ev) {
    if (ev.key === 'Enter') { ev.preventDefault(); document.getElementById('rop-focus-go').click(); }
  });
  document.getElementById('rop-pivot-reset').addEventListener('click', clearHighlights);

  // Camera preset buttons
  document.querySelectorAll('[data-cam]').forEach(function(b) {
    b.addEventListener('click', function() {
      var preset = b.getAttribute('data-cam');
      var eye = SCENE.eyes[preset];
      if (eye) Plotly.relayout(gd, {'scene.camera.eye': eye});
    });
  });

  // ── Aspect sliders ───────────────────────────────────────────────────
  function applyAspect() {
    var sx = parseFloat(document.getElementById('rop-sx').value);
    var sy = parseFloat(document.getElementById('rop-sy').value);
    var sz = parseFloat(document.getElementById('rop-sz').value);
    document.getElementById('rop-sx-val').textContent = sx.toFixed(2);
    document.getElementById('rop-sy-val').textContent = sy.toFixed(2);
    document.getElementById('rop-sz-val').textContent = sz.toFixed(2);
    var de = SCENE.data_extent;
    var ex = de.x * sx, ey = de.y * sy, ez = de.z * sz;
    var m = Math.max(ex, ey, ez) || 1;
    var newAR = {x: ex/m, y: ey/m, z: ez/m};
    Plotly.relayout(gd, {
      'scene.aspectmode': 'manual',
      'scene.aspectratio': newAR
    });
    SCENE.aspect_ratio = newAR;
  }
  ['rop-sx','rop-sy','rop-sz'].forEach(function(id){
    document.getElementById(id).addEventListener('input', applyAspect);
  });
  document.getElementById('rop-aspect-reset').addEventListener('click', function(){
    document.getElementById('rop-sx').value = 1;
    document.getElementById('rop-sy').value = 1;
    document.getElementById('rop-sz').value = 1;
    applyAspect();
  });

  // ── Annotations (live) ────────────────────────────────────────────────
  var annotInput = document.getElementById('rop-annot');
  var annotCount = document.getElementById('rop-annot-count');

  function updateAnnotations() {
    var pat = annotInput.value.trim();
    if (!pat) {
      Plotly.relayout(gd, {'scene.annotations': []});
      annotCount.textContent = '';
      return;
    }
    var patterns = pat.split(',').map(function(s){return s.trim();})
                       .filter(function(s){return s.length;});
    var regs = patterns.map(globToRegex);
    var seen = {};
    var annots = [];
    SCENE.elements.forEach(function(e) {
      if (!regs.some(function(r){return r.test(e.name);})) return;
      var key = e.x.toFixed(6)+','+e.y.toFixed(6)+','+e.z.toFixed(6);
      if (seen[key]) return;
      seen[key] = true;
      annots.push({
        x: e.x, y: e.y, z: e.z, text: e.name,
        showarrow: true, arrowhead: 2, arrowsize: 1, arrowwidth: 1,
        ax: 0, ay: -25,
        font: {size: SCENE.annot_font_size || 10,
               color: SCENE.dark_mode ? '#fff' : '#222'},
        bgcolor: SCENE.dark_mode ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.7)',
        bordercolor: '#888', borderwidth: 1, borderpad: 2
      });
    });
    Plotly.relayout(gd, {'scene.annotations': annots});
    annotCount.textContent = annots.length + ' element' +
      (annots.length === 1 ? '' : 's') + ' annotated';
  }
  annotInput.addEventListener('input', updateAnnotations);

  // Helper: extract hovertext from a click point — works for both
  // Mesh3d (hovertext is an array on pt.data) and Scatter3d (pt.hovertext).
  function getHovertext(pt) {
    if (pt.hovertext) return String(pt.hovertext);
    if (pt.data && pt.data.hovertext) {
      var ht = pt.data.hovertext;
      if (Array.isArray(ht)) return String(ht[pt.pointNumber] || '');
      return String(ht);
    }
    return '';
  }

  // ── Twiss Inspector ───────────────────────────────────────────────────
  (function() {
    var startFld = document.getElementById('rop-twiss-start');
    var endFld   = document.getElementById('rop-twiss-end');
    var nextLbl  = document.getElementById('rop-twiss-next-field');
    var rangeInfo= document.getElementById('rop-twiss-range-info');
    // Guard — if any required element is missing, skip the whole block
    if (!startFld || !endFld || !nextLbl || !rangeInfo) return;
    var nextIsStart = true;

    // Clicking an element populates start then end alternately.
    // Debounce: ignore if the same event fires again within 100ms.
    var _lastClickTime = 0;
    gd.on('plotly_click', function(ev) {
      var now = Date.now();
      if (now - _lastClickTime < 100) return;
      _lastClickTime = now;
      if (!ev || !ev.points || !ev.points.length) return;
      var pt = ev.points[0];
      var ht = getHovertext(pt);
      if (!ht) return;
      var m = ht.match(/<b>([^<]+)<\/b>/);
      if (!m) return;
      var name = m[1];
      if (nextIsStart) {
        startFld.value = name;
        nextIsStart = false;
        nextLbl.textContent = 'End';
      } else {
        endFld.value = name;
        nextIsStart = true;
        nextLbl.textContent = 'Start';
      }
      _updateRangeInfo();
    });

    // Also update info when user types
    startFld.addEventListener('input', _updateRangeInfo);
    endFld.addEventListener('input',   _updateRangeInfo);

    document.getElementById('rop-twiss-clear-range').addEventListener('click', function() {
      startFld.value = ''; endFld.value = '';
      nextIsStart = true; nextLbl.textContent = 'Start';
      rangeInfo.textContent = '';
    });

    function _resolveS(tok) {
      tok = tok.trim();
      if (!tok) return null;
      var n = parseFloat(tok);
      if (!isNaN(n)) return n;
      // Search by element name (case-insensitive, exact then prefix)
      var tl = tok.toLowerCase();
      var elems = SCENE.elements;
      for (var i = 0; i < elems.length; i++) {
        if (elems[i].name.toLowerCase() === tl) return elems[i].s0;
      }
      for (var i = 0; i < elems.length; i++) {
        if (elems[i].name.toLowerCase().indexOf(tl) === 0) return elems[i].s0;
      }
      return null;
    }

    function _updateRangeInfo() {
      var s0 = _resolveS(startFld.value);
      var s1 = _resolveS(endFld.value);
      if (s0 !== null && s1 !== null) {
        if (s0 > s1) { var tmp = s0; s0 = s1; s1 = tmp; }
        var n = SCENE.elements.filter(function(e){ return e.s0 >= s0 && e.s1 <= s1; }).length;
        rangeInfo.textContent = 's = ' + s0.toFixed(1) + ' → ' + s1.toFixed(1) + ' m  (' + n + ' elements)';
      } else {
        rangeInfo.textContent = s0 !== null ? 'Start: s=' + s0.toFixed(1) + ' m' :
                                s1 !== null ? 'End: s=' + s1.toFixed(1) + ' m' : '';
      }
    }

    document.getElementById('rop-twiss-open').addEventListener('click', function() {
      var s0tok = startFld.value.trim();
      var s1tok = endFld.value.trim();
      var s0 = s0tok ? _resolveS(s0tok) : null;
      var s1 = s1tok ? _resolveS(s1tok) : null;

      // Default: full range from optics_series
      var series = SCENE.optics_series || {};
      var allS = [];
      Object.keys(series).forEach(function(u) {
        allS = allS.concat(series[u].s);
      });
      if (!allS.length) {
        alert('No optics data available. Check that the backend loaded Twiss data.');
        return;
      }
      if (s0 === null) s0 = Math.min.apply(null, allS);
      if (s1 === null) s1 = Math.max.apply(null, allS);
      if (s0 > s1) { var tmp = s0; s0 = s1; s1 = tmp; }

      _openTwissPopup(s0, s1);
    });

    function _openTwissPopup(s0, s1) {
      var emx = SCENE.emit_x;
      var emy = SCENE.emit_y;
      var hasEmit = emx != null && emy != null && emx > 0 && emy > 0;
      var plots  = SCENE.inspector_plots || ['beta', 'sigma'];
      var phNorm = SCENE.phase_normalized || false;
      var series = SCENE.optics_series || {};
      var uniKeys = Object.keys(series);

      // Filter each universe's series to the s-range
      var uniData = {};
      uniKeys.forEach(function(u) {
        var ops = series[u];
        var idx = [];
        for (var i = 0; i < ops.s.length; i++) {
          if (ops.s[i] >= s0 && ops.s[i] <= s1) idx.push(i);
        }
        if (!idx.length) return;
        var pick = function(arr) { return idx.map(function(i){ return arr[i]; }); };
        uniData[u] = {
          s:       pick(ops.s),
          beta_x:  pick(ops.beta_x),  beta_y:  pick(ops.beta_y),
          eta_x:   pick(ops.eta_x),   eta_y:   pick(ops.eta_y),
          mu_x:    pick(ops.mu_x),    mu_y:    pick(ops.mu_y),
          orbit_x: pick(ops.orbit_x), orbit_y: pick(ops.orbit_y),
          key:     pick(ops.key),
          k1:      pick(ops.k1),      angle:   pick(ops.angle),
          ref_tilt:pick(ops.ref_tilt),name:    pick(ops.name),
          s0:      pick(ops.s0),      s1:      pick(ops.s1),
        };
      });

      var activeUnis = Object.keys(uniData);
      if (!activeUnis.length) {
        alert('No optics data in this range.');
        return;
      }

      // Use first universe for element bar
      var barOps = uniData[activeUnis[0]];

      // Detect active panels from any universe
      var panels = [];
      var anyBeta = activeUnis.some(function(u){ return uniData[u].beta_x.some(function(v){ return v>0; }); });
      if (plots.indexOf('beta') !== -1 && anyBeta) panels.push('beta');
      if (plots.indexOf('sigma') !== -1 && hasEmit && anyBeta) panels.push('sigma');
      if (plots.indexOf('dispersion') !== -1 && activeUnis.some(function(u){
            return uniData[u].eta_x.some(function(v){ return v!==0; }); }))
        panels.push('dispersion');
      if (plots.indexOf('orbit') !== -1 && activeUnis.some(function(u){
            return uniData[u].orbit_x.some(function(v){ return v!==0; }); }))
        panels.push('orbit');
      if (plots.indexOf('phase') !== -1 && activeUnis.some(function(u){
            return uniData[u].mu_x.some(function(v){ return v>0; }); }))
        panels.push('phase');

      if (!panels.length) {
        alert('No data available for the selected plots in this range.\n' +
              'Check that the backend loaded optics data (see render log).');
        return;
      }

      var nPanels = panels.length;
      // Reserve bottom 12% for element bar, split rest equally
      var barH = 0.12;
      var plotH = (1.0 - barH - 0.02) / nPanels;

      var traces = [];
      var layout = {
        paper_bgcolor: '#1e1e1e', plot_bgcolor: '#1a1a1a',
        font: {color: '#ccc', family: 'monospace,sans-serif', size: 11},
        title: {
          text: 'Twiss Inspector  |  s = ' + s0.toFixed(1) + ' → ' + s1.toFixed(1) + ' m',
          font: {size: 13, color: '#fda769'}, x: 0.5
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {bgcolor:'rgba(0,0,0,0.5)',bordercolor:'#444',borderwidth:1,
                 x:1.01,y:1,xanchor:'left',yanchor:'top'},
        margin: {l:70,r:130,t:50,b:60},
        shapes: [],
        annotations: [],
        grid: {rows: nPanels, columns: 1, pattern: 'independent'}
      };

      // ── Lattice bar — matches 2D ranoptics style ──────────────────
      // Larger barH so elements are actually visible
      var barY0  = 0;
      var barCy  = barH * 0.5;
      var dipH   = barH * 0.38;   // dipoles: wide, moderate height, centred
      var quadH  = barH * 0.48;   // quads: taller than dipoles, above/below
      var sextH  = barH * 0.20;   // sextupoles: short thin marks
      var kickH  = barH * 0.18;   // kickers: thinner still

      // Grey background strip covering full s range — represents drifts/beampipe
      layout.shapes.push({
        type:'rect', xref:'x', yref:'paper',
        x0:s0, x1:s1, y0:barCy-barH*0.08, y1:barCy+barH*0.08,
        fillcolor:'rgba(120,120,120,0.25)', line:{width:0}, layer:'below'
      });

      // Baseline
      layout.shapes.push({
        type:'line', xref:'x', yref:'paper',
        x0:s0, x1:s1, y0:barCy, y1:barCy,
        line:{color:'#888', width:1}
      });

      for (var bi = 0; bi < barOps.s.length; bi++) {
        var bs0 = barOps.s0[bi], bs1 = barOps.s1[bi];
        if (bs1 <= bs0) continue;
        var kl = (barOps.key[bi]||'').toLowerCase();
        var color, y0r, y1r;

        if (kl.indexOf('bend') !== -1) {
          color = '#ff2222';
          y0r = barCy - dipH; y1r = barCy + dipH;
        } else if (kl.indexOf('quad') !== -1) {
          color = '#2288ff';
          if (barOps.k1[bi] >= 0) { y0r = barCy; y1r = barCy + quadH; }
          else { y0r = barCy - quadH; y1r = barCy; }
        } else if (kl.indexOf('sext') !== -1) {
          color = '#ffcc00';
          y0r = barCy - sextH; y1r = barCy + sextH;
        } else if (kl.indexOf('kick') !== -1) {
          color = '#ff8800';
          y0r = barCy - kickH; y1r = barCy + kickH;
        } else if (kl.indexOf('cav') !== -1) {
          color = '#00ddff';
          y0r = barCy - sextH; y1r = barCy + sextH;
        } else if (kl.indexOf('solenoid') !== -1) {
          color = '#e377c2';
          y0r = barCy - sextH; y1r = barCy + sextH;
        } else { continue; }

        layout.shapes.push({
          type:'rect', xref:'x', yref:'paper',
          x0:bs0, x1:bs1, y0:y0r, y1:y1r,
          fillcolor:color, line:{width:0}, layer:'above'
        });
      }

      // ── Magnet hover ────────────────────────────────────────────────────────
      var barHoverX = [], barHoverText = [];
      for (var bi = 0; bi < barOps.s.length; bi++) {
        var bs0 = barOps.s0[bi], bs1 = barOps.s1[bi];
        var kl = (barOps.key[bi]||'').toLowerCase();
        if (kl.indexOf('bend')  === -1 && kl.indexOf('quad') === -1 &&
            kl.indexOf('sext')  === -1 && kl.indexOf('kick') === -1 &&
            kl.indexOf('cav')   === -1) continue;
        barHoverX.push(0.5 * (bs0 + bs1));
        var k1str = barOps.k1[bi] !== 0 ? '<br>K1 = ' + barOps.k1[bi].toFixed(4) + ' m⁻²' : '';
        var angstr = barOps.angle[bi] !== 0 ?
          '<br>Angle = ' + (barOps.angle[bi] * 180 / Math.PI).toFixed(4) + '°' : '';
        barHoverText.push(
          '<b>' + escapeHtml(barOps.name[bi]) + '</b>' +
          '<br>' + escapeHtml(barOps.key[bi]) +
          '<br>L = ' + (bs1 - bs0).toFixed(4) + ' m' +
          '<br>s = ' + bs0.toFixed(2) + ' → ' + bs1.toFixed(2) + ' m' +
          k1str + angstr
        );
      }
      if (barHoverX.length) {
        traces.push({
          type: 'scatter', mode: 'markers',
          x: barHoverX, y: Array(barHoverX.length).fill(0.5),
          xaxis: 'x', yaxis: 'ybar',
          name: '', showlegend: false,
          hovertemplate: barHoverText.map(function(t){ return t + '<extra></extra>'; }),
          marker: { size: 14, opacity: 0, color: 'rgba(0,0,0,0)' },
        });
        layout['yaxis_bar'] = {
          overlaying: 'y', side: 'left',
          range: [0, 1], domain: [0, barH],
          visible: false, showgrid: false, zeroline: false,
          fixedrange: true,
        };
      }

      // Shared x-axis config
      var xcfg = {title:'s (m)', color:'#aaa', gridcolor:'#2a2a2a',
                  range:[s0,s1], zeroline:false};

      // Line styles per universe index
      var uniDashes = ['solid','dot','dash','dashdot'];
      var uniSuffix = activeUnis.length > 1;

      panels.forEach(function(panel, pi) {
        var axN  = pi === 0 ? '' : String(pi+1);
        var yKey = 'yaxis' + axN;
        var xKey = 'xaxis' + axN;
        var domY0 = barH + (nPanels - 1 - pi) * plotH + 0.01;
        var domY1 = domY0 + plotH - 0.02;

        layout[xKey] = Object.assign({}, xcfg, {
          domain: [0, 1],
          showticklabels: pi === nPanels - 1,
          anchor: 'y' + axN
        });

        if (panel === 'beta') {
          layout[yKey] = {title:'β (m)', color:'#aaa', gridcolor:'#2a2a2a',
                          zeroline:false, domain:[domY0,domY1], anchor:'x'+axN};
          activeUnis.forEach(function(u, ui) {
            var d = uniData[u];
            var dash = uniDashes[ui % uniDashes.length];
            var lbl = uniSuffix ? ' ('+u+')' : '';
            traces.push({x:d.s, y:d.beta_x, name:'β<sub>x</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#74c0fc',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
            traces.push({x:d.s, y:d.beta_y, name:'β<sub>y</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#69db7c',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
          });
        }
        else if (panel === 'sigma') {
          layout[yKey] = {title:'σ (mm)', color:'#aaa', gridcolor:'#2a2a2a',
                          zeroline:false, domain:[domY0,domY1], anchor:'x'+axN};
          activeUnis.forEach(function(u, ui) {
            var d = uniData[u];
            var dash = uniDashes[ui % uniDashes.length];
            var lbl = uniSuffix ? ' ('+u+')' : '';
            var sx = d.beta_x.map(function(b){ return Math.sqrt(emx*b)*1000; });
            var sy = d.beta_y.map(function(b){ return Math.sqrt(emy*b)*1000; });
            traces.push({x:d.s, y:sx, name:'σ<sub>x</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#74c0fc',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
            traces.push({x:d.s, y:sy, name:'σ<sub>y</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#69db7c',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
          });
        }
        else if (panel === 'dispersion') {
          layout[yKey] = {title:'η (m)', color:'#aaa', gridcolor:'#2a2a2a',
                          zeroline:true, zerolinecolor:'#444', domain:[domY0,domY1], anchor:'x'+axN};
          activeUnis.forEach(function(u, ui) {
            var d = uniData[u];
            var dash = uniDashes[ui % uniDashes.length];
            var lbl = uniSuffix ? ' ('+u+')' : '';
            traces.push({x:d.s, y:d.eta_x, name:'η<sub>x</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#ffa94d',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
            traces.push({x:d.s, y:d.eta_y, name:'η<sub>y</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#f783ac',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
          });
        }
        else if (panel === 'orbit') {
          layout[yKey] = {title:'orbit (m)', color:'#aaa', gridcolor:'#2a2a2a',
                          zeroline:true, zerolinecolor:'#444', domain:[domY0,domY1], anchor:'x'+axN};
          activeUnis.forEach(function(u, ui) {
            var d = uniData[u];
            var dash = uniDashes[ui % uniDashes.length];
            var lbl = uniSuffix ? ' ('+u+')' : '';
            traces.push({x:d.s, y:d.orbit_x, name:'x orbit'+lbl,
              type:'scatter', mode:'lines', line:{color:'#ff6b6b',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
            traces.push({x:d.s, y:d.orbit_y, name:'y orbit'+lbl,
              type:'scatter', mode:'lines', line:{color:'#da77f2',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
          });
        }
        else if (panel === 'phase') {
          var twoPi = 2 * Math.PI;
          var unit = phNorm ? '(2π)' : '(rad)';
          layout[yKey] = {title:'μ '+unit, color:'#aaa', gridcolor:'#2a2a2a',
                          zeroline:false, domain:[domY0,domY1], anchor:'x'+axN};
          activeUnis.forEach(function(u, ui) {
            var d = uniData[u];
            var dash = uniDashes[ui % uniDashes.length];
            var lbl = uniSuffix ? ' ('+u+')' : '';
            var mux = d.mu_x.map(function(v){ return phNorm ? v/twoPi : v; });
            var muy = d.mu_y.map(function(v){ return phNorm ? v/twoPi : v; });
            traces.push({x:d.s, y:mux, name:'μ<sub>x</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#a9e34b',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
            traces.push({x:d.s, y:muy, name:'μ<sub>y</sub>'+lbl,
              type:'scatter', mode:'lines', line:{color:'#63e6be',width:2,dash:dash},
              xaxis:'x'+axN, yaxis:'y'+axN});
          });
        }
      });

      // Open in new tab via Blob URL
      var plotlyScript = '<script src="https://cdn.plot.ly/plotly-latest.min.js"><\/script>';
      var html = '<!DOCTYPE html><html><head><meta charset="utf-8">' +
        '<title>Twiss Inspector</title>' + plotlyScript +
        '<style>body{margin:0;background:#1e1e1e;}</style></head>' +
        '<body><div id="plot" style="width:100vw;height:100vh;"></div>' +
        '<script>Plotly.newPlot("plot",' +
          JSON.stringify(traces) + ',' +
          JSON.stringify(layout) + ',' +
          '{responsive:true,displaylogo:false}' +
        ');<\/script></body></html>';

      var blob = new Blob([html], {type:'text/html'});
      var url  = URL.createObjectURL(blob);
      var a    = document.createElement('a');
      a.href   = url; a.target = '_blank'; a.rel = 'noopener';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function(){ URL.revokeObjectURL(url); }, 10000);
    }

  })();

  // ── Click events: pin info + optional camera focus ────────────────────
  var pinDiv = document.getElementById('rop-pin');
  gd.on('plotly_click', function(ev) {
    if (!ev || !ev.points || !ev.points.length) return;
    var pt = ev.points[0];
    var ht = getHovertext(pt);
    if (ht) {
      pinDiv.innerHTML = ht.replace(/<extra><\/extra>/g, '');
      pinDiv.style.color = SCENE.dark_mode ? '#eee' : '#222';
    }
  });

  // ── Reset all ─────────────────────────────────────────────────────────
  document.getElementById('rop-reset-all').addEventListener('click', function() {
    document.querySelectorAll('[data-rop-type-vis]').forEach(function(cb){
      cb.checked = true;
      var t = cb.getAttribute('data-rop-type-vis');
      var idxs = tracesByName(SCENE.type_traces[t] || []);
      if (idxs.length) Plotly.restyle(gd, {visible: true}, idxs);
    });
    document.querySelectorAll('[data-rop-type-op]').forEach(function(sl){
      sl.value = 1;
      var t = sl.getAttribute('data-rop-type-op');
      var idxs = tracesByName(SCENE.type_traces[t] || []);
      if (idxs.length) Plotly.restyle(gd, {opacity: 1}, idxs);
    });
    document.querySelectorAll('[data-rop-overlay]').forEach(function(cb){
      cb.checked = true;
      var t = cb.getAttribute('data-rop-overlay');
      var idxs = tracesByName(SCENE.overlay_traces[t] || []);
      if (idxs.length) Plotly.restyle(gd, {visible: true}, idxs);
    });
    document.getElementById('rop-sx').value = 1;
    document.getElementById('rop-sy').value = 1;
    document.getElementById('rop-sz').value = 1;
    applyAspect();
    annotInput.value = '';
    updateAnnotations();
    clearHighlights();
    var r = SCENE.axis_ranges;
    Plotly.relayout(gd, {
      'scene.xaxis.range': r.x,
      'scene.yaxis.range': r.y,
      'scene.zaxis.range': r.z,
      'scene.camera.center': {x:0, y:0, z:0}
    });
    pinDiv.innerHTML = 'Click any element to pin its info here.';
    pinDiv.style.color = SCENE.dark_mode ? '#888' : '#666';
  });

  // ── PNG screenshot ────────────────────────────────────────────────────
  document.getElementById('rop-screenshot').addEventListener('click', function() {
    Plotly.toImage(gd, {format:'png', width:1920, height:1080}).then(function(url) {
      var a = document.createElement('a');
      a.href = url;
      a.download = 'ranoptics3d.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
  });

  // ── Panel collapse → bottom-right tab ───────────────────────────────
  var hdr      = document.getElementById('rop-header');
  var body     = document.getElementById('rop-body');
  var expanded = document.getElementById('rop-expanded');
  var tab      = document.getElementById('rop-tab');
  var toggle   = document.getElementById('rop-toggle');

  function collapsePanel() {
    expanded.style.display = 'none';
    tab.style.display = 'block';
    toggle.textContent = '▸';
  }
  function expandPanel() {
    tab.style.display = 'none';
    expanded.style.display = 'flex';
    toggle.textContent = '▾';
  }

  hdr.addEventListener('click', function() {
    if (expanded.style.display === 'none') { expandPanel(); }
    else { collapsePanel(); }
  });
  tab.addEventListener('click', expandPanel);
  });  // end waitForPlotly callback
})();
