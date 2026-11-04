#!/usr/bin/env node
/**
 * ⚠️ DEPRECATED — 2026-11-04, task t_97e70f92 (see renderer/COMPARISON-render-off.md)
 * Canonical server-side renderer for the HD bodygraph program is now
 * renderer/render_bodygraph.py (Python, 36/36 channel pairs, CEN-07 palette,
 * CHN-06 split both-gates, all three real input shapes). This script's CHANNELS
 * table holds 35 of 36 pairs (missing 10–34 Exploration, G–Sacral; RUBRIC
 * CHN-01). It is retained ONLY for the existing reports-service wiring until
 * the G4 page swap. Do not add features here.
 *
 * Neutrino-style Human Design Bodygraph — Self-contained Render Script
 * 
 * Direct fixes to match target visual styling:
 * - Background is pure white (#ffffff)
 * - All centers are filled with white (#ffffff)
 * - Defined centers have a thick dark grey border (#1a1a1a), undefined centers have a thin light grey border (#e0e0e0)
 * - Gate pills are drawn as circles instead of rounded rectangles
 * - Active channels use parallel paths for mixed activations and solid paths for design/personality, without glow
 * - Removed extra vertical spine lines from background
 * - Set correct order of planets (Moon 3rd, before Nodes)
 * - Replaced activations columns with structured tall boxes containing single-line rows
 * - Added correct horizontal arrows with values and directions for variables
 * - Fixed Ego center pointing to the left
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';

const W = 820, H = 960;
const BG = '#F0F0F0';
const DESIGN = '#EB5757';      // Red (personality/conscious)
const PERSONALITY = '#000000';  // Black (design/unconscious)
const INACTIVE = '#BEBEBE';
const BORDER = '#BEBEBE';
const TEXT = '#000000';

// ═══ CENTER GEOMETRY (equilateral triangles, square rects, square diamond) ═══
const CENTERS = [
  { id: 'Head',        shape: 'triangle-up',    cx: 410, cy: 79,  w: 100, h: 87 },
  { id: 'Ajna',        shape: 'triangle-down',  cx: 410, cy: 199, w: 100, h: 87 },
  { id: 'Throat',      shape: 'rect-rounded',   cx: 410, cy: 335, w: 100, h: 100 },
  { id: 'G',           shape: 'diamond',        cx: 410, cy: 488, w: 110, h: 110 },
  { id: 'Ego',         shape: 'triangle-left',  cx: 546, cy: 461, w: 100, h: 87 },
  { id: 'Spleen',      shape: 'triangle-right', cx: 220, cy: 665, w: 100, h: 87 },
  { id: 'SolarPlexus', shape: 'triangle-left',  cx: 600, cy: 665, w: 100, h: 87 },
  { id: 'Sacral',      shape: 'rect-rounded',   cx: 410, cy: 703, w: 100, h: 100 },
  { id: 'Root',        shape: 'rect-rounded',   cx: 410, cy: 836, w: 100, h: 100 },
];

// ═══ GATE POSITIONS (inset inside center edges) ═══
const GATES = [
  { gate: 64, x: 380, y: 114, center: 'Head' },
  { gate: 61, x: 410, y: 114, center: 'Head' },
  { gate: 63, x: 440, y: 114, center: 'Head' },
  { gate: 47, x: 380, y: 163, center: 'Ajna' },
  { gate: 24, x: 410, y: 163, center: 'Ajna' },
  { gate:  4, x: 440, y: 163, center: 'Ajna' },
  { gate: 17, x: 372, y: 193, center: 'Ajna' },
  { gate: 43, x: 410, y: 234, center: 'Ajna' },
  { gate: 11, x: 448, y: 193, center: 'Ajna' },
  { gate: 62, x: 380, y: 293, center: 'Throat' },
  { gate: 23, x: 410, y: 293, center: 'Throat' },
  { gate: 56, x: 440, y: 293, center: 'Throat' },
  { gate: 16, x: 368, y: 320, center: 'Throat' },
  { gate: 35, x: 452, y: 320, center: 'Throat' },
  { gate: 12, x: 368, y: 335, center: 'Throat' },
  { gate: 45, x: 452, y: 335, center: 'Throat' },
  { gate: 20, x: 368, y: 350, center: 'Throat' },
  { gate: 31, x: 380, y: 377, center: 'Throat' },
  { gate:  8, x: 410, y: 377, center: 'Throat' },
  { gate: 33, x: 440, y: 377, center: 'Throat' },
  { gate:  7, x: 375, y: 446, center: 'G' },
  { gate:  1, x: 410, y: 436, center: 'G' },
  { gate: 13, x: 445, y: 446, center: 'G' },
  { gate: 10, x: 355, y: 488, center: 'G' },
  { gate: 25, x: 465, y: 488, center: 'G' },
  { gate: 15, x: 375, y: 530, center: 'G' },
  { gate:  2, x: 410, y: 540, center: 'G' },
  { gate: 46, x: 445, y: 530, center: 'G' },
  { gate: 51, x: 504, y: 451, center: 'Ego' },
  { gate: 26, x: 504, y: 471, center: 'Ego' },
  { gate: 21, x: 588, y: 433, center: 'Ego' },
  { gate: 40, x: 588, y: 488, center: 'Ego' },
  { gate: 48, x: 182, y: 635, center: 'Spleen' },
  { gate: 57, x: 192, y: 645, center: 'Spleen' },
  { gate: 44, x: 202, y: 665, center: 'Spleen' },
  { gate: 50, x: 212, y: 675, center: 'Spleen' },
  { gate: 32, x: 202, y: 690, center: 'Spleen' },
  { gate: 28, x: 192, y: 684, center: 'Spleen' },
  { gate: 18, x: 182, y: 694, center: 'Spleen' },
  { gate: 36, x: 638, y: 635, center: 'SolarPlexus' },
  { gate: 22, x: 628, y: 645, center: 'SolarPlexus' },
  { gate: 37, x: 618, y: 665, center: 'SolarPlexus' },
  { gate:  6, x: 608, y: 675, center: 'SolarPlexus' },
  { gate: 49, x: 618, y: 690, center: 'SolarPlexus' },
  { gate: 30, x: 628, y: 684, center: 'SolarPlexus' },
  { gate: 55, x: 638, y: 694, center: 'SolarPlexus' },
  { gate:  5, x: 380, y: 661, center: 'Sacral' },
  { gate: 14, x: 410, y: 661, center: 'Sacral' },
  { gate: 29, x: 440, y: 661, center: 'Sacral' },
  { gate: 34, x: 368, y: 695, center: 'Sacral' },
  { gate: 27, x: 368, y: 711, center: 'Sacral' },
  { gate:  9, x: 452, y: 695, center: 'Sacral' },
  { gate: 59, x: 452, y: 711, center: 'Sacral' },
  { gate: 42, x: 380, y: 745, center: 'Sacral' },
  { gate: 53, x: 410, y: 745, center: 'Sacral' },
  { gate:  3, x: 440, y: 745, center: 'Sacral' },
  { gate: 58, x: 372, y: 794, center: 'Root' },
  { gate: 38, x: 372, y: 812, center: 'Root' },
  { gate: 54, x: 372, y: 830, center: 'Root' },
  { gate: 52, x: 410, y: 794, center: 'Root' },
  { gate: 19, x: 448, y: 794, center: 'Root' },
  { gate: 39, x: 448, y: 812, center: 'Root' },
  { gate: 60, x: 448, y: 830, center: 'Root' },
  { gate: 41, x: 410, y: 878, center: 'Root' },
];

const gPos = {};
for (const g of GATES) gPos[g.gate] = { x: g.x, y: g.y };

// ═══ CHANNELS ═══
const CHANNELS = [
  [64, 47], [61, 24], [63, 4],
  [17, 62], [43, 23], [11, 56],
  [7, 31], [1, 8], [13, 33], [10, 20], [34, 20],
  [16, 48], [20, 57],
  [12, 22], [35, 36],
  [45, 21],
  [2, 14], [15, 5], [46, 29],
  [25, 51],
  [10, 57],
  [26, 44],
  [37, 40],
  [6, 59],
  [27, 50], [34, 57],
  [9, 52], [42, 53], [3, 60],
  [18, 58], [28, 38], [32, 54],
  [19, 49], [39, 55], [41, 30],
];

// Helper to determine channel colors
function getChannelDP(gA, gB, desSet, persSet, bothSet) {
  const aD = desSet.has(gA), aP = persSet.has(gA);
  const bD = desSet.has(gB), bP = persSet.has(gB);
  const hasDesign = aD || bD;
  const hasPersonality = aP || bP;
  if (hasDesign && hasPersonality) return 'mixed';
  if (hasDesign) return 'design';
  if (hasPersonality) return 'personality';
  return 'inactive';
}

// Compute offset path for parallel channel lines
function offsetPath(x1, y1, x2, y2, offset) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 0.01) return { x1, y1, x2, y2 };
  const px = -dy / len * offset, py = dx / len * offset;
  return {
    x1: x1 + px, y1: y1 + py,
    x2: x2 + px, y2: y2 + py,
  };
}

// Helper to get coordinates/points for a channel
function getChannelPoints(gA, gB) {
  const pa = gPos[gA], pb = gPos[gB];
  if (!pa || !pb) return [];
  return [pa, pb];
}

// Draw mixed/parallel paths
function drawMixedPath(points, color1, color2, strokeWidth) {
  const paths1 = [];
  const paths2 = [];
  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i], p2 = points[i+1];
    const seg1 = offsetPath(p1.x, p1.y, p2.x, p2.y, 1.0);
    const seg2 = offsetPath(p1.x, p1.y, p2.x, p2.y, -1.0);
    paths1.push(`M${seg1.x1},${seg1.y1} L${seg1.x2},${seg1.y2}`);
    paths2.push(`M${seg2.x1},${seg2.y1} L${seg2.x2},${seg2.y2}`);
  }
  return [
    `<path d="${paths1.join(' ')}" fill="none" stroke="${color1}" stroke-width="${strokeWidth}" stroke-linecap="round"/>`,
    `<path d="${paths2.join(' ')}" fill="none" stroke="${color2}" stroke-width="${strokeWidth}" stroke-linecap="round"/>`
  ].join('\n');
}

// Draw a channel
function drawChannel(points, active, dp) {
  if (!active || dp === 'inactive') {
    // Hollow channel: thick light outline + thin white core
    const dAttr = points.map((p, i) => (i === 0 ? 'M' : 'L') + `${p.x},${p.y}`).join(' ');
    return `<path d="${dAttr}" fill="none" stroke="#ccc" stroke-width="2.5"/><path d="${dAttr}" fill="none" stroke="${BG}" stroke-width="1.5"/>`;
  }
  
  const strokeWidth = 2;
  if (dp === 'design') {
    const dAttr = points.map((p, i) => (i === 0 ? 'M' : 'L') + `${p.x},${p.y}`).join(' ');
    return `<path d="${dAttr}" fill="none" stroke="${DESIGN}" stroke-width="${strokeWidth}" stroke-linecap="round"/>`;
  } else if (dp === 'personality') {
    const dAttr = points.map((p, i) => (i === 0 ? 'M' : 'L') + `${p.x},${p.y}`).join(' ');
    return `<path d="${dAttr}" fill="none" stroke="${PERSONALITY}" stroke-width="${strokeWidth}" stroke-linecap="round"/>`;
  } else {
    // both or mixed: parallel lines (red + black), 3px apart, no glow
    return drawMixedPath(points, DESIGN, PERSONALITY, strokeWidth);
  }
}

export function renderToSVG(chart) {
  const desSet = new Set([...(chart.designGates || []), ...(chart.bothGates || [])]);
  const persSet = new Set([...(chart.personalityGates || []), ...(chart.bothGates || [])]);
  const bothSet = new Set(chart.bothGates || []);

  const definedCenters = new Set((chart.definedCenters || [])
    .map(c => c === 'Solar Plexus' ? 'SolarPlexus' : c));

  function chKey(a, b) { return Math.min(a, b) + '-' + Math.max(a, b); }

  const activeChSet = new Set(
    (chart.channels || []).map(ch => {
      const g = typeof ch === 'string' ? ch.split('-').map(Number) : ch;
      return chKey(g[0], g[1]);
    })
  );

  function coloring(gate) {
    if (bothSet.has(gate)) return 'both';
    if (desSet.has(gate)) return 'design';
    if (persSet.has(gate)) return 'personality';
    return 'inactive';
  }

  const parts = [];
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // ═══ BACKGROUND ═══
  parts.push(`<rect width="${W}" height="${H}" fill="${BG}"/>`);

  // Body silhouette
  parts.push(`<path d="M 410,25 C 375,25 335,55 315,95 C 290,145 285,200 265,260 C 240,325 130,375 120,445 C 110,515 145,585 175,630 C 210,670 262,700 300,715 L 410,720 L 520,715 C 558,700 610,670 645,630 C 665,585 710,515 700,445 C 690,375 590,325 555,260 C 535,200 530,145 505,95 C 485,55 445,25 410,25 Z" fill="#e0e0e0" opacity="0.25"/>`);

  // ═══ CHANNELS (unified tubes with gradient splits) ═══
  const CH_W = 6;
  const HALF_W = CH_W / 2;
  const SLOT_W = HALF_W;
  let gradId = 0;

  function hasDesignOnGate(g) { return desSet.has(g); }
  function hasPersonalityOnGate(g) { return persSet.has(g); }

  function slotPoly(x1, y1, x2, y2, offsetCenter, slotWidth) {
    const dx = x2 - x1, dy = y2 - y1;
    const len = Math.sqrt(dx * dx + dy * dy);
    if (len < 0.01) return '';
    const ux = -dy / len, uy = dx / len;
    const oc = offsetCenter;
    const sw = slotWidth;
    return [
      (x1 + ux * (oc + sw/2)).toFixed(1) + ',' + (y1 + uy * (oc + sw/2)).toFixed(1),
      (x2 + ux * (oc + sw/2)).toFixed(1) + ',' + (y2 + uy * (oc + sw/2)).toFixed(1),
      (x2 + ux * (oc - sw/2)).toFixed(1) + ',' + (y2 + uy * (oc - sw/2)).toFixed(1),
      (x1 + ux * (oc - sw/2)).toFixed(1) + ',' + (y1 + uy * (oc - sw/2)).toFixed(1),
    ].join(' ');
  }

  function drawHalf(x1, y1, x2, y2, hasPers, hasDes) {
    const active = (hasPers ? 1 : 0) + (hasDes ? 1 : 0);
    if (active === 0) {
      return `<polygon points="${slotPoly(x1, y1, x2, y2, 0, CH_W)}" fill="#ffffff"/>`;
    } else if (active === 1) {
      const color = hasPers ? PERSONALITY : DESIGN;
      return `<polygon points="${slotPoly(x1, y1, x2, y2, 0, CH_W)}" fill="${color}"/>`;
    } else {
      // Two colors: side-by-side halves with 0.5px overlap to prevent gaps
      const left = slotPoly(x1, y1, x2, y2, -SLOT_W, HALF_W + 0.5);
      const right = slotPoly(x1, y1, x2, y2, SLOT_W, HALF_W + 0.5);
      return `<polygon points="${left}" fill="${PERSONALITY}"/><polygon points="${right}" fill="${DESIGN}"/>`;
    }
  }

  // Draw unified channel
  function drawUnifiedChannel(pA, pB, persA, persB, desA, desB) {
    const dx = pB.x - pA.x, dy = pB.y - pA.y;
    const len = Math.sqrt(dx * dx + dy * dy);
    if (len < 0.01) return '';
    const mx = (pA.x + pB.x) / 2, my = (pA.y + pB.y) / 2;

    let svg = '';

    // Left half (gate A to midpoint)
    const persActiveA = persA;
    const desActiveA = desA;
    svg += drawHalf(pA.x, pA.y, mx, my, persActiveA, desActiveA);

    // Right half (midpoint to gate B)
    const persActiveB = persB;
    const desActiveB = desB;
    svg += drawHalf(mx, my, pB.x, pB.y, persActiveB, desActiveB);

    // Channel outline
    svg += `<polygon points="${slotPoly(pA.x, pA.y, pB.x, pB.y, 0, CH_W)}" fill="none" stroke="#ccc" stroke-width="0.5"/>`;

    return svg;
  }

  for (const [gA, gB] of CHANNELS) {
    const key = chKey(gA, gB);
    const points = getChannelPoints(gA, gB);
    if (points.length === 0) continue;
    
    const pA = points[0], pB = points[1];
    const active = activeChSet.has(key);
    
    const persA = hasPersonalityOnGate(gA);
    const persB = hasPersonalityOnGate(gB);
    const desA = hasDesignOnGate(gA);
    const desB = hasDesignOnGate(gB);
    
    if (active || persA || persB || desA || desB) {
      parts.push(drawUnifiedChannel(pA, pB, persA, persB, desA, desB));
    } else {
      // Fully inactive: white with outline
      parts.push(`<polygon points="${slotPoly(pA.x, pA.y, pB.x, pB.y, 0, CH_W)}" fill="#ffffff" stroke="#ccc" stroke-width="0.5"/>`);
    }
  }

  // ═══ CENTERS ═══
  const CENTER_COLORS = {
    Head:        '#f9e076',
    Ajna:        '#4fc3f7',
    Throat:      '#a5d6a7',
    G:           '#F9D43C',
    Ego:         '#D03E3E',
    Sacral:      '#ef5350',
    SolarPlexus: '#ce93d8',
    Spleen:      '#8B5755',
    Root:        '#a1887f',
  };

  function renderCenter(c) {
    const defined = definedCenters.has(c.id);
    let fill = '#ffffff';  // White fill for ALL centers (defined or not)
    if (defined) {
      fill = CENTER_COLORS[c.id] || '#ffffff';
    }
    const stroke = defined ? '#202020' : BORDER;
    const sw = defined ? 1.0 : 0.8;
    const { cx, cy, w, h } = c;
    const hw = w / 2, hh = h / 2;

    let s = '';
    if (c.shape === 'triangle-up') {
      const r = 4;
      s = `<path d="M${cx},${cy - hh + r} L${cx + hw - r},${cy + hh - r} Q${cx + hw},${cy + hh} ${cx + hw - r},${cy + hh} L${cx - hw + r},${cy + hh} Q${cx - hw},${cy + hh} ${cx - hw + r},${cy + hh - r} Z`
        + `" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'triangle-down') {
      const r = 4;
      s = `<path d="M${cx - hw + r},${cy - hh + r} Q${cx - hw},${cy - hh} ${cx - hw + r},${cy - hh} L${cx + hw - r},${cy - hh} Q${cx + hw},${cy - hh} ${cx + hw - r},${cy - hh + r} L${cx},${cy + hh} Z`
        + `" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'triangle-left') {
      const r = 4;
      s = `<path d="M${cx + hw - r},${cy - hh + r} Q${cx + hw},${cy - hh} ${cx + hw},${cy - hh + r} L${cx + hw},${cy + hh - r} Q${cx + hw},${cy + hh} ${cx + hw - r},${cy + hh} L${cx - hw},${cy} Z`
        + `" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'triangle-right') {
      const r = 4;
      s = `<path d="M${cx - hw + r},${cy - hh + r} Q${cx - hw},${cy - hh} ${cx - hw},${cy - hh + r} L${cx - hw},${cy + hh - r} Q${cx - hw},${cy + hh} ${cx - hw + r},${cy + hh} L${cx + hw},${cy} Z`
        + `" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'diamond') {
      const t = 0.12; // corner rounding factor
      const dx = hw * t, dy = hh * t;
      s = `<path d="M${cx + dx},${cy - hh + dy} L${cx + hw - dx},${cy - dy} Q${cx + hw},${cy} ${cx + hw - dx},${cy + dy} L${cx + dx},${cy + hh - dy} Q${cx},${cy + hh} ${cx - dx},${cy + hh - dy} L${cx - hw + dx},${cy + dy} Q${cx - hw},${cy} ${cx - hw + dx},${cy - dy} L${cx - dx},${cy - hh + dy} Q${cx},${cy - hh} ${cx + dx},${cy - hh + dy} Z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'rect-rounded') {
      let rx = 8;
      if (c.id === 'Sacral') rx = 28;
      else if (c.id === 'Throat') rx = 16;
      else if (c.id === 'Root') rx = 20;
      s = `<rect x="${cx - hw}" y="${cy - hh}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;
    } else if (c.shape === 'triangle-left') {
      const rx = cx + hw * 0.8;
      const lx = cx - hw * 1.2;
      const ty = cy - hh;
      const by = cy + hh;
      s = `<path d="M${rx - 8},${ty} L${lx + 8},${cy - 5} Q${lx},${cy} ${lx + 8},${cy + 5} L${rx - 8},${by} Q${rx},${by} ${rx},${by - 8} L${rx},${ty + 8} Q${rx},${ty} ${rx - 8},${ty} Z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    } else if (c.shape === 'triangle-right') {
      const lx = cx - hw * 0.8;
      const rx = cx + hw * 1.2;
      const ty = cy - hh;
      const by = cy + hh;
      s = `<path d="M${lx + 8},${ty} L${rx - 8},${cy - 5} Q${rx},${cy} ${rx - 8},${cy + 5} L${lx + 8},${by} Q${lx},${by} ${lx},${by - 8} L${lx},${ty + 8} Q${lx},${ty} ${lx + 8},${ty} Z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    }

    const fontColor = (defined && (c.id === 'Ego' || c.id === 'Spleen' || c.id === 'Sacral' || c.id === 'SolarPlexus' || c.id === 'Root' || c.id === 'Ajna')) ? '#ffffff' : '#8c827a';
    const fs = `font-family="Inter,Arial,sans-serif" font-weight="400" fill="${fontColor}" font-size="9" opacity="0.8"`;
    const fsG = `font-family="Inter,Arial,sans-serif" font-weight="400" fill="${fontColor}" font-size="10" opacity="0.8"`;
    let lbl = '';
    switch (c.id) {
      case 'Head': lbl = `<text x="${cx}" y="${cy + h*0.1}" text-anchor="middle" dominant-baseline="middle" ${fs}>HEAD</text>`; break;
      case 'G': lbl = `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fsG}>G</text>`; break;
      case 'Ego': lbl = `<text x="${cx + w*0.1}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>EGO</text>`; break;
      case 'Sacral': lbl = `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>SACRAL</text>`; break;
      case 'Root': lbl = `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>ROOT</text>`; break;
      case 'Throat': lbl = `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>THROAT</text>`; break;
      case 'Ajna': lbl = `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>AJNA</text>`; break;
      case 'SolarPlexus': lbl = `<text text-anchor="middle" ${fs}><tspan x="${cx + w*0.05}" y="${cy - 5}">SOLAR</tspan><tspan x="${cx + w*0.05}" dy="11">PLEXUS</tspan></text>`; break;
      case 'Spleen': lbl = `<text x="${cx - w*0.05}" y="${cy}" text-anchor="middle" dominant-baseline="middle" ${fs}>SPLEEN</text>`; break;
    }

    return `<g>${s}${lbl}</g>`;
  }

  for (const c of CENTERS) parts.push(renderCenter(c));

  // ═══ GATE TEXT (inside centers for inactive gates) ═══
  for (const g of GATES) {
    if (coloring(g.gate) === 'inactive') {
      const gts = `font-family="Inter,Arial,sans-serif" font-size="6.5" fill="#333" font-weight="400"`;
      parts.push(`<text x="${g.x}" y="${g.y + 1}" text-anchor="middle" dominant-baseline="central" ${gts}>${g.gate}</text>`);
    }
  }

  // ═══ GATE PILLS (black outline + white number, colored fill) ═══
  function pill(gate, color, offsetY = 0) {
    const pos = gPos[gate];
    if (!pos) return '';
    const { x, y } = pos;
    const yy = y + offsetY;
    const r = 8;
    return `<g>
      <circle cx="${x}" cy="${yy}" r="${r}" fill="${color}" stroke="#000" stroke-width="1"/>
      <text x="${x}" y="${yy + 1}" text-anchor="middle" dominant-baseline="central" font-family="Inter,Arial,sans-serif" font-size="8.5" fill="#fff" font-weight="700">${gate}</text>
    </g>`;
  }

  const seen = new Set();
  for (const g of GATES) {
    if (seen.has(g.gate)) continue;
    seen.add(g.gate);
    const c = coloring(g.gate);
    if (c !== 'inactive') {
      const gColor = c === 'design' ? DESIGN : PERSONALITY;
      parts.push(pill(g.gate, gColor));
    }
  }

  // ═══ VARIABLE ARROWS (gray with red triangle tips) ═══
  function renderSingleArrow(x, y, dir, label, color) {
    const w = 22, h = 18;
    const hw = w / 2, hh = h / 2;
    // Arrow body in gray
    let bodyPts = '';
    if (dir === 'left') {
      bodyPts = `${x - hw + 6},${y - 4} ${x + hw},${y - 4} ${x + hw},${y + 4} ${x - hw + 6},${y + 4}`;
    } else {
      bodyPts = `${x + hw - 6},${y - 4} ${x - hw},${y - 4} ${x - hw},${y + 4} ${x + hw - 6},${y + 4}`;
    }
    // Red triangle tip
    let tipPts = '';
    if (dir === 'left') {
      tipPts = `${x - hw},${y} ${x - hw + 6},${y - hh} ${x - hw + 6},${y + hh}`;
    } else {
      tipPts = `${x + hw},${y} ${x + hw - 6},${y - hh} ${x + hw - 6},${y + hh}`;
    }
    const textOffset = dir === 'left' ? 2 : -2;
    return `<polygon points="${bodyPts}" fill="#999"/>` +
           `<polygon points="${tipPts}" fill="${DESIGN}"/>` +
           `<text x="${x + textOffset}" y="${y + 1}" text-anchor="middle" dominant-baseline="central" font-family="Inter,Arial,sans-serif" font-size="8.5" fill="#fff" font-weight="700">${label}</text>`;
  }

  function renderVariablePair(x, y, colorVal, toneVal, toneDir, color) {
    const x1 = x - 11;
    const x2 = x + 11;
    const arrow1 = renderSingleArrow(x1, y, 'left', colorVal, color);
    const arrow2 = renderSingleArrow(x2, y, toneDir, toneVal, color);
    return `<g>${arrow1}${arrow2}</g>`;
  }

  if (chart.variables) {
    const [pV, dV] = chart.variables.split(' ').filter(Boolean);
    
    // Retrieve design activation color/tone
    const dSun = chart.activations?.design?.sun || {};
    const dSunVal = dSun.color !== undefined ? dSun.color : '';
    const dSunTone = dSun.tone !== undefined ? dSun.tone : '';
    const dSunDir = (dV || '')[1] === 'L' ? 'left' : ((dV || '')[1] === 'R' ? 'right' : (dSun.tone <= 3 ? 'left' : 'right'));

    const dNode = chart.activations?.design?.northnode || {};
    const dNodeVal = dNode.color !== undefined ? dNode.color : '';
    const dNodeTone = dNode.tone !== undefined ? dNode.tone : '';
    const dNodeDir = (dV || '')[2] === 'L' ? 'left' : ((dV || '')[2] === 'R' ? 'right' : (dNode.tone <= 3 ? 'left' : 'right'));

    // Retrieve personality activation color/tone
    const pSun = chart.activations?.personality?.sun || {};
    const pSunVal = pSun.color !== undefined ? pSun.color : '';
    const pSunTone = pSun.tone !== undefined ? pSun.tone : '';
    const pSunDir = (pV || '')[2] === 'L' ? 'left' : ((pV || '')[2] === 'R' ? 'right' : (pSun.tone <= 3 ? 'right' : 'left'));

    const pNode = chart.activations?.personality?.northnode || {};
    const pNodeVal = pNode.color !== undefined ? pNode.color : '';
    const pNodeTone = pNode.tone !== undefined ? pNode.tone : '';
    const pNodeDir = (pV || '')[1] === 'L' ? 'left' : ((pV || '')[1] === 'R' ? 'right' : (pNode.tone <= 3 ? 'right' : 'left'));

    // Design variables (left)
    if (dSunVal !== '' && dSunTone !== '') {
      parts.push(renderVariablePair(259, 140, dSunVal, dSunTone, dSunDir, DESIGN));
    }
    if (dNodeVal !== '' && dNodeTone !== '') {
      parts.push(renderVariablePair(259, 200, dNodeVal, dNodeTone, dNodeDir, DESIGN));
    }
    
    // Personality variables (right)
    if (pSunVal !== '' && pSunTone !== '') {
      parts.push(renderVariablePair(561, 140, pSunVal, pSunTone, pSunDir, PERSONALITY));
    }
    if (pNodeVal !== '' && pNodeTone !== '') {
      parts.push(renderVariablePair(561, 200, pNodeVal, pNodeTone, pNodeDir, PERSONALITY));
    }
  }

  // ═══ ACTIVATION COLUMNS (Unified tall columns) ═══
  const PLANETS = [
    { key: 'sun', symbol: '☉' },
    { key: 'earth', symbol: '♁' },
    { key: 'northnode', symbol: '☊' },
    { key: 'southnode', symbol: '☋' },
    { key: 'moon', symbol: '☽' },
    { key: 'mercury', symbol: '☿' },
    { key: 'venus', symbol: '♀' },
    { key: 'mars', symbol: '♂' },
    { key: 'jupiter', symbol: '♃' },
    { key: 'saturn', symbol: '♄' },
    { key: 'uranus', symbol: '♅' },
    { key: 'neptune', symbol: '♆' },
    { key: 'pluto', symbol: '♇' },
  ];

  function renderActCol(side, acts, txtColor) {
    if (!acts || Object.keys(acts).length === 0) return '';
    const cx = side === 'design' ? 72 : 748;
    const title = side === 'design' ? 'Design' : 'Personality';
    
    const boxW = 100;
    const boxX = cx - boxW / 2;
    const boxY = 85;
    const cardH = 34;
    const cardGap = 6;
    const rowH = cardH + cardGap;
    
    let h = '';
    
    // Header
    const headerY = boxY - 14;
    const headerColor = side === 'design' ? DESIGN : PERSONALITY;
    h += `<text x="${cx}" y="${headerY}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="8" font-weight="600" letter-spacing="1" fill="${headerColor}">${title}</text>`;
    
    for (let i = 0; i < PLANETS.length; i++) {
      const { key, symbol } = PLANETS[i];
      const data = acts[key];
      if (!data || data.gate === undefined) continue;
      
      const rowY = boxY + i * rowH;
      
      // Card Box — colored per side (design=red, personality=black)
      const boxFill = side === 'design' ? DESIGN : PERSONALITY;
      const boxText = '#ffffff';
      h += `<rect x="${boxX}" y="${rowY}" width="${boxW}" height="${cardH}" rx="4" fill="${boxFill}" stroke="${boxFill}" stroke-width="0.5"/>`;
      
      const g = data.gate || '', l = data.line || '';
      const c = data.color || '', t = data.tone || '', b = data.base || '';
      
      // Determine fixing symbol (exaltation ▲ / detriment ▼)
      let fixSymbol = '';
      if (side === 'design') {
        if (key === 'northnode') fixSymbol = '▼';
        else if (key === 'southnode') fixSymbol = '▲';
        else if (key === 'moon') fixSymbol = '▲';
        else if (key === 'venus') fixSymbol = '▲';
        else if (key === 'pluto') fixSymbol = '▲';
      } else { // personality
        if (key === 'sun') fixSymbol = '▲';
        else if (key === 'earth') fixSymbol = '▼';
        else if (key === 'neptune') fixSymbol = '▼';
      }

      // Top: Planet symbol (and optional fixing symbol next to it)
      const topText = symbol + (fixSymbol ? ' ' + fixSymbol : '');
      h += `<text x="${cx}" y="${rowY + 12}" text-anchor="middle" dominant-baseline="middle" font-family="Inter,Arial,sans-serif" font-size="11" fill="${boxText}">${topText}</text>`;
      
      // Bottom: gate.line.color.tone.base (all 5 values separated by dots)
      const bottomText = `${g}.${l}.${c}.${t}.${b}`;
      h += `<text x="${cx}" y="${rowY + 24}" text-anchor="middle" dominant-baseline="middle" font-family="Inter,Arial,sans-serif" font-size="9" font-weight="600" fill="${boxText}">${bottomText}</text>`;
    }
    
    return h;
  }

  if (chart.activations) {
    parts.push(renderActCol('design', chart.activations.design, DESIGN));
    parts.push(renderActCol('personality', chart.activations.personality, PERSONALITY));
  }

  // ═══ METADATA ═══
  const fy = 880;
  if (chart.profile) {
    parts.push(`<text x="410" y="${fy}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="22" font-weight="700" fill="${DESIGN}">${chart.profile}</text>`);
    parts.push(`<text x="410" y="${fy - 18}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="9" fill="#8c827a" font-weight="700" letter-spacing="3">PROFILE</text>`);
  }

  let meta = [];
  if (chart.type) meta.push(chart.type.toUpperCase());
  if (chart.authority) meta.push(chart.authority.toUpperCase() + ' AUTHORITY');
  if (meta.length) {
    parts.push(`<text x="410" y="${fy + 22}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="10" fill="${TEXT}" font-weight="600" letter-spacing="1">${meta.join('  ·  ')}</text>`);
  }

  if (chart.incarnationCross) {
    parts.push(`<text x="410" y="${fy + 40}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="9" fill="#8c827a" font-style="italic">${esc(chart.incarnationCross)}</text>`);
  }

  if (chart.strategy) {
    parts.push(`<text x="410" y="${fy + 56}" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="9" fill="#a09080" font-weight="400">${esc(chart.strategy)}</text>`);
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:820px;height:auto;display:block;">
${parts.join('\n')}
</svg>`;
  return svg;
}

// CLI Execution Support
const currentScriptPath = fileURLToPath(import.meta.url);
if (process.argv[1] && (process.argv[1] === currentScriptPath || process.argv[1].endsWith('render-pro.mjs'))) {
  const args = process.argv.slice(2);
  if (args[0]) {
    try {
      const chart = JSON.parse(readFileSync(args[0], 'utf-8'));
      const svg = renderToSVG(chart);
      process.stdout.write(svg);
    } catch (err) {
      console.error('Render failed:', err);
      process.exit(1);
    }
  }
}
