#!/usr/bin/env node

import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import path from "node:path";

const BASE_URL = "https://lanhuapp.com";
const SUCCESS_CODES = new Set([0, "0", "00000"]);

class AuthenticationError extends Error {}

function usage() {
  return `Usage: node lanhu_pull.mjs <lanhu-url> --output <review-dir> [options]

Options:
  --screens <names|ids|all>       Comma-separated exact names or IDs; defaults to URL image_id
  --assets-output <dir>           Existing Android drawable-xxhdpi target directory
  --design-scale <number>         Design pixels per logical unit when metadata is missing
  --profile-dir <dir>             Persistent Chrome profile outside the project
  --cache-dir <dir>               Versioned raw response cache outside the project
  --channel <chrome|msedge>       Installed browser channel (default: chrome)
  --concurrency <1..8>            Request/download concurrency (default: 4)
  --refresh                       Ignore version cache
  --overwrite                     Replace conflicting asset files
  --show-browser                  Keep the browser visible even when already authenticated
  --self-test                     Run deterministic parser/extractor checks`;
}

function parseArgs(argv) {
  const args = {
    url: "", output: "", screens: "", assetsOutput: "", designScale: 0,
    profileDir: path.join(homedir(), ".lanhu-android-fast-workflow", "chrome-profile"),
    cacheDir: path.join(homedir(), ".lanhu-android-fast-workflow", "cache"),
    channel: "chrome", concurrency: 4, refresh: false, overwrite: false,
    showBrowser: false, selfTest: false, help: false,
  };
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--output") args.output = argv[++index] || "";
    else if (value === "--screens") args.screens = argv[++index] || "";
    else if (value === "--assets-output") args.assetsOutput = argv[++index] || "";
    else if (value === "--design-scale") args.designScale = Number(argv[++index]);
    else if (value === "--profile-dir") args.profileDir = argv[++index] || "";
    else if (value === "--cache-dir") args.cacheDir = argv[++index] || "";
    else if (value === "--channel") args.channel = argv[++index] || "chrome";
    else if (value === "--concurrency") args.concurrency = Number(argv[++index]);
    else if (value === "--refresh") args.refresh = true;
    else if (value === "--overwrite") args.overwrite = true;
    else if (value === "--show-browser") args.showBrowser = true;
    else if (value === "--self-test") args.selfTest = true;
    else if (value === "-h" || value === "--help") args.help = true;
    else if (value.startsWith("--")) throw new Error(`Unknown option: ${value}`);
    else positional.push(value);
  }
  args.url = positional[0] || "";
  if (!Number.isInteger(args.concurrency) || args.concurrency < 1 || args.concurrency > 8) {
    throw new Error("--concurrency must be an integer between 1 and 8");
  }
  if (!Number.isFinite(args.designScale) || args.designScale < 0) {
    throw new Error("--design-scale must be a positive number");
  }
  return args;
}

export function parseLanhuUrl(value) {
  const url = new URL(value);
  if (!/(^|\.)lanhuapp\.com$/i.test(url.hostname)) throw new Error("Expected a lanhuapp.com URL");
  const query = url.hash.includes("?") ? url.hash.slice(url.hash.indexOf("?") + 1) : url.search.slice(1);
  const params = new URLSearchParams(query);
  const projectId = params.get("pid") || params.get("project_id");
  if (!projectId) throw new Error("Lanhu URL is missing pid/project_id");
  return {
    projectId,
    teamId: params.get("tid") || "",
    imageId: params.get("image_id") || "",
  };
}

function safeFileStem(value, fallback) {
  const result = String(value || "")
    .normalize("NFKD")
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^[._-]+|[._-]+$/g, "")
    .toLowerCase();
  return result || fallback;
}

function androidName(value, fallback) {
  let result = safeFileStem(value, fallback).replace(/[^a-z0-9_]+/g, "_");
  if (!/^[a-z]/.test(result)) result = `lh_${result}`;
  return result.slice(0, 80).replace(/_+$/g, "") || fallback;
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

async function exists(filePath) {
  try { await stat(filePath); return true; } catch { return false; }
}

function resolveUrl(value) {
  if (!value) return "";
  try { return new URL(value, BASE_URL).toString(); } catch { return ""; }
}

function assertAllowedRemote(value) {
  const url = new URL(resolveUrl(value));
  const host = url.hostname.toLowerCase();
  const allowed = ["lanhuapp.com", "lanhu.com", "aliyuncs.com"]
    .some((suffix) => host === suffix || host.endsWith(`.${suffix}`));
  if (url.protocol !== "https:" || !allowed) {
    throw new Error(`Refusing unexpected Lanhu resource host: ${host}`);
  }
  return url.toString();
}

async function responseBuffer(context, url) {
  const response = await context.request.get(assertAllowedRemote(url), {
    headers: { Referer: `${BASE_URL}/web/`, "request-from": "web" },
    timeout: 30_000,
  });
  if (response.status() === 401 || response.status() === 403) throw new AuthenticationError(`HTTP ${response.status()}`);
  if (!response.ok()) throw new Error(`HTTP ${response.status()} ${response.statusText()}`);
  return { buffer: await response.body(), contentType: response.headers()["content-type"] || "" };
}

async function responseJson(context, url) {
  const response = await responseBuffer(context, url);
  try { return JSON.parse(response.buffer.toString("utf8")); }
  catch { throw new Error("Lanhu endpoint returned non-JSON content"); }
}

function unwrap(payload, label) {
  if (payload && Object.hasOwn(payload, "code") && !SUCCESS_CODES.has(payload.code)) {
    const message = String(payload.msg || payload.message || `${label} failed`);
    if (/(登录|认证|cookie|login|auth|expired|过期)/i.test(message)) throw new AuthenticationError(message);
    throw new Error(`${label}: ${message}`);
  }
  return payload?.data ?? payload?.result ?? payload;
}

function projectEndpoint(params) {
  const query = new URLSearchParams({ project_id: params.projectId, dds_status: "1", position: "1", show_cb_src: "1" });
  if (params.teamId) query.set("team_id", params.teamId);
  return `${BASE_URL}/api/project/images?${query}`;
}

function detailEndpoint(params, imageId) {
  const query = new URLSearchParams({ project_id: params.projectId, image_id: imageId, dds_status: "1" });
  if (params.teamId) query.set("team_id", params.teamId);
  return `${BASE_URL}/api/project/image?${query}`;
}

async function fetchProject(context, params) {
  const payload = await responseJson(context, projectEndpoint(params));
  const project = unwrap(payload, "project list");
  const images = project?.images || project?.list || [];
  if (!Array.isArray(images)) throw new Error("Lanhu project response has no images array");
  return { project, images };
}

async function launchContext(chromium, args, headless) {
  await mkdir(args.profileDir, { recursive: true });
  return chromium.launchPersistentContext(args.profileDir, {
    channel: args.channel,
    headless,
    viewport: { width: 1440, height: 1000 },
    acceptDownloads: true,
  });
}

async function authenticate(chromium, args, params) {
  let context = await launchContext(chromium, args, !args.showBrowser);
  try {
    const project = await fetchProject(context, params);
    return { context, ...project };
  } catch (error) {
    const cookies = await context.cookies(BASE_URL);
    await context.close();
    if (!(error instanceof AuthenticationError) && cookies.length > 0) throw error;
  }

  context = await launchContext(chromium, args, false);
  const page = context.pages()[0] || await context.newPage();
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30_000 });
  process.stderr.write("Lanhu login is required. Complete login in the opened browser window; the script will continue automatically.\n");
  const deadline = Date.now() + 5 * 60_000;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const project = await fetchProject(context, params);
      return { context, ...project };
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, 2_000));
    }
  }
  await context.close();
  throw new AuthenticationError(`Login was not completed within five minutes: ${lastError?.message || "unknown"}`);
}

function selectScreens(images, selection, imageId) {
  const requested = selection ? selection.split(",").map((item) => item.trim()).filter(Boolean) : (imageId ? [imageId] : []);
  if (requested.length === 0) throw new Error("Specify --screens or provide image_id in the Lanhu URL");
  if (requested.length === 1 && requested[0].toLowerCase() === "all") return images;
  const selected = [];
  for (const token of requested) {
    const byId = images.filter((item) => String(item.id) === token);
    const byName = images.filter((item) => String(item.name) === token);
    const index = Number(token);
    const matches = byId.length ? byId : byName.length ? byName : (Number.isInteger(index) && index >= 1 && index <= images.length ? [images[index - 1]] : []);
    if (matches.length !== 1) {
      const candidates = images.filter((item) => String(item.name || "").includes(token)).map((item) => item.name).slice(0, 8);
      throw new Error(matches.length > 1 ? `Ambiguous screen: ${token}` : `Screen not found: ${token}${candidates.length ? `; candidates=${candidates.join(",")}` : ""}`);
    }
    if (!selected.some((item) => String(item.id) === String(matches[0].id))) selected.push(matches[0]);
  }
  return selected;
}

function frameOf(node) {
  const frame = node?.frame || node?.bounds || {};
  return {
    x: Number(frame.x ?? frame.left ?? node?.left ?? 0),
    y: Number(frame.y ?? frame.top ?? node?.top ?? 0),
    width: Number(frame.width ?? node?.width ?? 0),
    height: Number(frame.height ?? node?.height ?? 0),
  };
}

function colorValue(value) {
  if (typeof value === "string") {
    const match = value.trim().match(/^#([0-9a-f]{3,8})$/i);
    if (match) return `#${match[1].toUpperCase()}`;
    const rgba = value.trim().match(/^rgba?\(([^)]+)\)$/i);
    if (rgba) return value.trim().replace(/\s+/g, "");
  }
  if (value && typeof value === "object" && [value.r, value.g, value.b].every(Number.isFinite)) {
    const scale = Math.max(value.r, value.g, value.b) <= 1 ? 255 : 1;
    const r = Math.round(value.r * scale);
    const g = Math.round(value.g * scale);
    const b = Math.round(value.b * scale);
    const a = Number.isFinite(value.a) ? value.a : Number.isFinite(value.alpha) ? value.alpha : 1;
    return `rgba(${r},${g},${b},${Number(a.toFixed(3))})`;
  }
  return "";
}

function addCount(map, key) {
  if (key) map.set(key, (map.get(key) || 0) + 1);
}

function parseSize(value) {
  if (value && typeof value === "object") return { width: Number(value.width || value.w || 0), height: Number(value.height || value.h || 0) };
  const match = String(value || "").match(/(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)/);
  return match ? { width: Number(match[1]), height: Number(match[2]) } : { width: 0, height: 0 };
}

function explicitScale(data, override) {
  if (override > 0) return { value: override, source: "argument" };
  const candidates = [data?.sliceScale, data?.exportScale, data?.meta?.sliceScale];
  for (const item of candidates) {
    const value = Number(item);
    if (Number.isFinite(value) && value > 0) return { value, source: "metadata" };
  }
  const origin = String(data?.artboard?.origin || data?.meta?.host?.name || "").toLowerCase();
  if (origin === "figma") return { value: 1, source: "figma-origin" };
  return { value: 0, source: "unresolved" };
}

function rasterExtension(url) {
  const pathname = (() => { try { return new URL(url).pathname; } catch { return String(url).split(/[?#]/)[0]; } })();
  const extension = path.extname(pathname).toLowerCase();
  return [".png", ".jpg", ".jpeg", ".webp"].includes(extension) ? extension : ".png";
}

function resizeUrl(url, width, height) {
  const clean = String(url).replace(/([?&])x-oss-process=[^&]*/i, "$1").replace(/[?&]$/, "");
  const separator = clean.includes("?") ? "&" : "?";
  return `${clean}${separator}x-oss-process=image/resize,w_${Math.round(width)},h_${Math.round(height)}/format,png`;
}

function extractDesign(data, screen, designScaleOverride) {
  const colors = new Map();
  const typography = new Map();
  const layers = [];
  const assets = [];
  const seenObjects = new Set();
  const seenAssets = new Set();
  const scale = explicitScale(data, designScaleOverride);

  function visit(node, parentPath = "") {
    if (!node || typeof node !== "object" || seenObjects.has(node)) return;
    seenObjects.add(node);
    if (Array.isArray(node)) {
      for (const item of node) visit(item, parentPath);
      return;
    }
    const name = String(node.name || "");
    const layerPath = parentPath && name ? `${parentPath}/${name}` : name || parentPath;
    const frame = frameOf(node);
    const text = typeof node.text === "string" ? node.text : typeof node.content === "string" ? node.content : "";
    if (layers.length < 800 && (name || text) && (node.type || node.layerType || frame.width || frame.height)) {
      layers.push({
        type: node.type || node.layerType || node.ddsType || "layer",
        name,
        text: text.slice(0, 160),
        frame,
        layer_path: layerPath,
      });
    }

    for (const [key, value] of Object.entries(node)) {
      if (/(color|fill|stroke|background|shadow)/i.test(key)) {
        const direct = colorValue(value);
        if (direct) addCount(colors, direct);
        if (Array.isArray(value)) for (const item of value) addCount(colors, colorValue(item?.color ?? item));
      }
    }
    const style = node.textStyle || node.style?.text || {};
    const fontSize = Number(style.fontSize || node.fontSize || 0);
    if (fontSize > 0) {
      addCount(typography, [style.fontFamily || node.fontFamily || "default", style.fontWeight || node.fontWeight || "normal", fontSize, style.lineHeight || "auto"].join("|"));
    }

    const imageBag = node.images && typeof node.images === "object" ? node.images : {};
    const exactUrl = imageBag.android_xxhdpi || imageBag.png_xxhdpi || imageBag.png_xxhd || imageBag.png_3x || "";
    const image = node.image || node.ddsImage || {};
    const genericUrl = image.imageUrl || image.url || "";
    const exportMarked = Boolean(node.hasExportImage || node.isSlice || node.isAsset || Object.keys(imageBag).length > 0);
    let downloadUrl = resolveUrl(exactUrl);
    let expected = { width: 0, height: 0 };
    let densityEvidence = exactUrl ? "explicit-xxhdpi-field" : "";
    const parsed = parseSize(image.size);
    const rawWidth = parsed.width || frame.width;
    const rawHeight = parsed.height || frame.height;
    if (!downloadUrl && exportMarked && genericUrl && scale.value > 0 && rawWidth > 0 && rawHeight > 0) {
      const logicalWidth = rawWidth / scale.value;
      const logicalHeight = rawHeight / scale.value;
      expected = { width: Math.round(logicalWidth * 3), height: Math.round(logicalHeight * 3) };
      downloadUrl = resizeUrl(resolveUrl(genericUrl), expected.width, expected.height);
      densityEvidence = `logical-size+${scale.source}`;
    }
    if (downloadUrl || exportMarked) {
      const key = `${node.id || layerPath}|${downloadUrl}`;
      if (!seenAssets.has(key)) {
        seenAssets.add(key);
        assets.push({
          id: String(node.id || ""), name: name || "asset", layer_path: layerPath,
          url: downloadUrl, extension: rasterExtension(downloadUrl || genericUrl),
          expected_width: expected.width, expected_height: expected.height,
          density_evidence: densityEvidence || "unresolved",
          unresolved_reason: downloadUrl ? "" : "No explicit xxhdpi source or reliable logical-size scale",
        });
      }
    }

    for (const value of Object.values(node)) {
      if (value && typeof value === "object") visit(value, layerPath);
    }
  }

  visit(data);
  const sortCounts = (map, limit) => [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit).map(([value, count]) => ({ value, count }));
  return {
    scale,
    colors: sortCounts(colors, 50),
    typography: sortCounts(typography, 30),
    layers,
    assets,
    screen_size: { width: Number(screen.width || 0), height: Number(screen.height || 0) },
  };
}

function pngSize(buffer) {
  if (buffer.length >= 24 && buffer.subarray(1, 4).toString("ascii") === "PNG") {
    return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20), format: "png", alpha: [4, 6].includes(buffer[25]) };
  }
  return { width: 0, height: 0, format: "unknown", alpha: null };
}

async function mapLimit(items, limit, task) {
  const results = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const index = cursor++;
      results[index] = await task(items[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}

async function processScreen(context, args, params, screen, index) {
  const detailPayload = await responseJson(context, detailEndpoint(params, screen.id));
  const detail = unwrap(detailPayload, `screen ${screen.name}`);
  const versions = detail?.versions || [];
  const latest = versions[0];
  if (!latest?.json_url) throw new Error(`Screen has no design JSON: ${screen.name}`);
  const version = String(latest.id || latest.version_id || latest.update_time || screen.update_time || "latest");
  const cachePath = path.join(args.cacheDir, params.projectId, String(screen.id), `${safeFileStem(version, "latest")}.json`);
  let designData;
  let cache = "hit";
  if (!args.refresh && await exists(cachePath)) {
    designData = JSON.parse(await readFile(cachePath, "utf8"));
  } else {
    designData = await responseJson(context, latest.json_url);
    await mkdir(path.dirname(cachePath), { recursive: true });
    await writeFile(cachePath, `${JSON.stringify(designData)}\n`, "utf8");
    cache = "miss";
  }
  const extracted = extractDesign(designData, screen, args.designScale);
  const designDirectory = path.join(args.output, "designs");
  await mkdir(designDirectory, { recursive: true });
  let preview = "";
  const previewUrl = resolveUrl(screen.url || screen.image_url || latest.url || latest.image_url);
  if (previewUrl) {
    const extension = rasterExtension(previewUrl);
    preview = path.join(designDirectory, `${androidName(screen.name, `screen_${index + 1}`)}${extension}`);
    const payload = await responseBuffer(context, previewUrl);
    await writeFile(preview, payload.buffer);
  }
  return {
    id: String(screen.id), name: String(screen.name || `screen_${index + 1}`), version,
    width: Number(screen.width || 0), height: Number(screen.height || 0), preview,
    cache, scale: extracted.scale, colors: extracted.colors, typography: extracted.typography,
    layers: extracted.layers, assets: extracted.assets,
  };
}

async function downloadAssets(context, args, screens) {
  if (!args.assetsOutput) return [];
  await mkdir(args.assetsOutput, { recursive: true });
  const plans = [];
  const seenUrls = new Map();
  const usedNames = new Map();
  for (let screenIndex = 0; screenIndex < screens.length; screenIndex += 1) {
    const screen = screens[screenIndex];
    for (let assetIndex = 0; assetIndex < screen.assets.length; assetIndex += 1) {
      const asset = screen.assets[assetIndex];
      if (!asset.url) continue;
      if (seenUrls.has(asset.url)) {
        plans.push({ screen, asset, duplicateOf: seenUrls.get(asset.url) });
        continue;
      }
      let stem = androidName(asset.name, `lh_${screenIndex + 1}_${assetIndex + 1}`);
      const count = (usedNames.get(stem) || 0) + 1;
      usedNames.set(stem, count);
      if (count > 1) stem = `${stem}_${count}`;
      const outputPath = path.join(args.assetsOutput, `${stem}${asset.extension || ".png"}`);
      seenUrls.set(asset.url, outputPath);
      plans.push({ screen, asset, outputPath });
    }
  }

  return mapLimit(plans, args.concurrency, async (plan) => {
    if (plan.duplicateOf) return { screen_id: plan.screen.id, asset_id: plan.asset.id, status: "deduplicated", output: plan.duplicateOf };
    const payload = await responseBuffer(context, plan.asset.url);
    const hash = sha256(payload.buffer);
    const image = pngSize(payload.buffer);
    if (plan.asset.expected_width && image.width && (plan.asset.expected_width !== image.width || plan.asset.expected_height !== image.height)) {
      return { screen_id: plan.screen.id, asset_id: plan.asset.id, status: "dimension_mismatch", expected: [plan.asset.expected_width, plan.asset.expected_height], actual: [image.width, image.height], sha256: hash };
    }
    if (await exists(plan.outputPath)) {
      const existing = await readFile(plan.outputPath);
      if (sha256(existing) === hash) return { screen_id: plan.screen.id, asset_id: plan.asset.id, status: "reused", output: plan.outputPath, sha256: hash, ...image };
      if (!args.overwrite) return { screen_id: plan.screen.id, asset_id: plan.asset.id, status: "conflict", output: plan.outputPath, sha256: hash, ...image };
    }
    await writeFile(plan.outputPath, payload.buffer);
    return { screen_id: plan.screen.id, asset_id: plan.asset.id, status: "downloaded", output: plan.outputPath, sha256: hash, ...image };
  });
}

async function selfTest() {
  const parsed = parseLanhuUrl("https://lanhuapp.com/web/#/item/project/stage?pid=p1&image_id=i1&tid=t1");
  if (parsed.projectId !== "p1" || parsed.imageId !== "i1") throw new Error("URL parser self-test failed");
  if (androidName("Home Icon 24dp", "fallback") !== "home_icon_24dp") throw new Error("Android name self-test failed");
  let rejectedHost = false;
  try { assertAllowedRemote("https://example.com/private"); } catch { rejectedHost = true; }
  if (!rejectedHost) throw new Error("resource host allowlist self-test failed");
  const fixture = { sliceScale: 2, layers: [{ id: "a", name: "heart", isSlice: true, frame: { width: 48, height: 48 }, image: { imageUrl: "https://example.lanhuapp.com/a.png" }, fills: [{ color: "#ff0000" }] }] };
  const extracted = extractDesign(fixture, { width: 750, height: 1334 }, 0);
  if (extracted.assets[0].expected_width !== 72 || extracted.colors[0].value !== "#FF0000") throw new Error("design extraction self-test failed");
  console.log(JSON.stringify({ status: "ok", test: "lanhu_pull" }));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return console.log(usage());
  if (args.selfTest) return selfTest();
  if (!args.url || !args.output) throw new Error(usage());
  args.output = path.resolve(args.output);
  args.cacheDir = path.resolve(args.cacheDir);
  args.profileDir = path.resolve(args.profileDir);
  if (args.assetsOutput) args.assetsOutput = path.resolve(args.assetsOutput);
  await mkdir(args.output, { recursive: true });
  await mkdir(args.cacheDir, { recursive: true });
  const params = parseLanhuUrl(args.url);
  let chromium;
  try { ({ chromium } = await import("playwright-core")); }
  catch { throw new Error("playwright-core is missing; run npm install in the skill directory before using Lanhu extraction"); }

  const auth = await authenticate(chromium, args, params);
  const context = auth.context;
  try {
    const selected = selectScreens(auth.images, args.screens, params.imageId);
    const screens = await mapLimit(selected, args.concurrency, (screen, index) => processScreen(context, args, params, screen, index));
    const downloads = await downloadAssets(context, args, screens);
    const manifest = {
      schema_version: 1,
      source: "lanhu-web-adapter",
      project: { id: params.projectId, team_id: params.teamId, name: auth.project?.name || "" },
      density: "android_xxhdpi",
      screens: screens.map((screen) => ({
        ...screen,
        assets: screen.assets.map(({ url, ...asset }) => asset),
      })),
      downloads,
      unresolved_assets: screens.flatMap((screen) => screen.assets.filter((asset) => !asset.url).map(({ url, ...asset }) => ({ screen_id: screen.id, ...asset }))),
    };
    const manifestPath = path.join(args.output, "manifest.json");
    await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
    const counts = downloads.reduce((result, item) => ((result[item.status] = (result[item.status] || 0) + 1), result), {});
    console.log(JSON.stringify({ status: "ok", screens: screens.length, assets: screens.reduce((sum, screen) => sum + screen.assets.length, 0), unresolved: manifest.unresolved_assets.length, downloads: counts, manifest: manifestPath }));
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ status: "error", type: error.constructor.name, message: error.message }));
  process.exitCode = 1;
});
