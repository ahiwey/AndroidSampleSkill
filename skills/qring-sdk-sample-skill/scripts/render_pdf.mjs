import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const options = {};
for (let i = 2; i < process.argv.length; i += 2) options[process.argv[i].slice(2)] = process.argv[i + 1];
const escapeHtml = text => String(text).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

export function protectTableCodePipes(markdown) {
  let fence = null;
  return markdown.split('\n').map(line => {
    const marker = line.match(/^\s*(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length) fence = null;
      return line;
    }
    if (fence || !/^\s*\|/.test(line)) return line;
    // GFM splits table cells before inline code; protect literal bitwise/logical operators.
    return line.replace(/(`+)(.*?)\1/g, span => span.replace(/(?<!\\)\|/g, '\\|'));
  }).join('\n');
}

async function dependencies() {
  const roots = [options['node-modules'], process.env.QRING_NODE_MODULES,
    path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')].filter(Boolean);
  let error;
  for (const root of [null, ...roots]) {
    try {
      const req = createRequire(root ? path.join(path.resolve(root), '__qring_loader.cjs') : import.meta.url);
      const { marked } = await import(pathToFileURL(req.resolve('marked')).href);
      return {marked, playwright: req('playwright')};
    } catch (e) { error = e; }
  }
  throw new Error(`marked/playwright unavailable; use --node-modules with an existing runtime. ${error.message}`);
}

async function main() {
  const {marked, playwright} = await dependencies();
  const candidates = [options.browser, process.env.QRING_BROWSER_EXECUTABLE, playwright.chromium.executablePath(),
    ...['PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'].flatMap(key => process.env[key] ? [
      path.join(process.env[key], 'Google/Chrome/Application/chrome.exe'),
      path.join(process.env[key], 'Microsoft/Edge/Application/msedge.exe')] : [])];
  const executablePath = candidates.find(candidate => candidate && fs.existsSync(candidate));
  if (!executablePath) throw new Error('No local Chromium browser found. Supply --browser; no browser is downloaded automatically.');
  if (options.probe === 'true') {
    console.log(JSON.stringify({browser: executablePath, renderer: 'marked/playwright'}));
    return;
  }
  const source = path.resolve(options.source);
  const output = path.resolve(options.output);
  const sourceText = fs.readFileSync(source, 'utf8').replace(/^\uFEFF/, '');
  const renderer = new marked.Renderer();
  renderer.html = token => escapeHtml(typeof token === 'string' ? token : token.text);
  renderer.link = function(token) {
    const label = this.parser.parseInline(token.tokens);
    return /^(https?:|mailto:|#)/i.test(token.href) ? `<a href="${escapeHtml(token.href)}">${label}</a>` : label;
  };
  renderer.image = token => {
    if (/^[a-z]+:|^[/\\]/i.test(token.href)) throw new Error('Only local relative document images are supported.');
    const imagePath = fs.realpathSync(path.resolve(path.dirname(source), decodeURIComponent(token.href)));
    const relative = path.relative(fs.realpathSync(path.dirname(source)), imagePath);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('Image escapes the document directory.');
    const mime = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[path.extname(imagePath).toLowerCase()];
    if (!mime) throw new Error(`Unsupported document image: ${token.href}`);
    return `<img alt="${escapeHtml(token.text)}" src="data:${mime};base64,${fs.readFileSync(imagePath).toString('base64')}">`;
  };
  const body = marked.parse(protectTableCodePipes(sourceText), {renderer, gfm: true, breaks: false});
  const browser = await playwright.chromium.launch({executablePath, headless: true});
  try {
    const context = await browser.newContext({javaScriptEnabled: false, viewport: {width: 794, height: 1123}});
    await context.route('**/*', route => route.abort());
    const page = await context.newPage();
    await page.setContent(`<!doctype html><html lang="${source.endsWith('_cn.md') ? 'zh-CN' : 'en'}"><head><meta charset="utf-8"><style>
      @page { size: A4; }
      * { box-sizing: border-box; }
      body { margin: 0; color: #182332; font-family: "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif; font-size: 9pt; line-height: 1.55; overflow-wrap: anywhere; }
      h1 { font-size: 22pt; color: #163c62; line-height: 1.35; margin: 0 0 18pt; }
      h2 { font-size: 15pt; color: #163c62; border-bottom: 1px solid #cbd5e1; padding-bottom: 4pt; margin-top: 20pt; }
      h3 { font-size: 12pt; margin-top: 15pt; } h4 { font-size: 10pt; }
      h1,h2,h3,h4,h5,h6 { break-after: avoid-page; }
      p { margin: 6pt 0; orphans: 3; widows: 3; }
      a { color: #145d94; text-decoration: none; }
      ul,ol { padding-left: 19pt; } li { margin: 3pt 0; }
      pre { white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; background: #f1f5f9; padding: 8pt; border: 1px solid #dbe3eb; border-radius: 3pt; font-size: 7.5pt; line-height: 1.45; }
      code { font-family: Consolas, "Microsoft YaHei", monospace; font-size: 0.93em; }
      p code,li code,td code { color: #254d70; }
      table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 7.4pt; margin: 9pt 0; }
      thead { display: table-header-group; } th { background: #e9eff5; text-align: left; }
      th,td { border: 1px solid #cbd5e1; padding: 5pt; vertical-align: top; overflow-wrap: anywhere; }
      tr { break-inside: avoid; } blockquote { border-left: 3px solid #cbd5e1; margin-left: 0; padding-left: 12pt; color: #475569; }
      img { max-width: 100%; height: auto; } hr { border: 0; border-top: 1px solid #cbd5e1; }
      main { width: 180mm; margin: 0 auto; }
    </style></head><body><main>${body}</main></body></html>`, {waitUntil: 'load'});
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => Array.from(document.querySelectorAll('main *')).filter(e => e.scrollWidth > e.clientWidth + 2 && e.clientWidth > 0 && getComputedStyle(e).display !== 'inline').map(e => ({tag:e.tagName,text:e.textContent.slice(0,80)})).slice(0,10));
    if (overflow.length) throw new Error(`Document width overflow: ${JSON.stringify(overflow)}`);
    await page.pdf({path: output, format: 'A4', printBackground: true,
      margin: {top:'15mm', bottom:'17mm', left:'15mm', right:'15mm'}, displayHeaderFooter: true,
      headerTemplate: '<span></span>',
      footerTemplate: '<div style="width:100%;text-align:center;font-size:8px;color:#64748b;font-family:Arial">QRing Android SDK &nbsp; <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
    console.log(JSON.stringify({output, bytes:fs.statSync(output).size, overflow:0, browser:executablePath}));
  } finally { await browser.close(); }
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch(error => {console.error(error.stack); process.exitCode = 1;});
}
