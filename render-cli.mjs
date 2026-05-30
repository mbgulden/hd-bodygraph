#!/usr/bin/env node
/**
 * CLI renderer: takes a ChartData JSON file path and theme,
 * outputs SVG bodygraph to stdout.
 * 
 * Usage: node render-cli.mjs <chart-json-path> [theme]
 */
import { readFileSync } from 'fs';
import { renderToSVG } from './dist/index.mjs';

const args = process.argv.slice(2);
const chartPath = args[0];
const theme = args[1] || 'canonical';

if (!chartPath) {
  console.error('Usage: node render-cli.mjs <chart.json> [theme]');
  process.exit(1);
}

try {
  const chartData = JSON.parse(readFileSync(chartPath, 'utf-8'));
  const svg = renderToSVG(chartData, { theme });
  process.stdout.write(svg);
} catch (err) {
  console.error('Render failed:', err.message);
  process.exit(1);
}
