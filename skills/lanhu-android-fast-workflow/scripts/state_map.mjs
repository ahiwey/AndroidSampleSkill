#!/usr/bin/env node

import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

function usage() {
  return "Usage: node state_map.mjs <manifest.json> [--hints hints.json] [--output state-map.json] [--threshold 0.65]";
}

function parseArgs(argv) {
  const args = { manifest: "", hints: "", output: "", threshold: 0.65, selfTest: false };
  const positional = [];
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === "--hints") args.hints = argv[++i] || "";
    else if (value === "--output") args.output = argv[++i] || "";
    else if (value === "--threshold") args.threshold = Number(argv[++i]);
    else if (value === "--self-test") args.selfTest = true;
    else if (value === "-h" || value === "--help") args.help = true;
    else if (value.startsWith("--")) throw new Error(`Unknown option: ${value}`);
    else positional.push(value);
  }
  args.manifest = positional[0] || "";
  if (!Number.isFinite(args.threshold) || args.threshold < 0 || args.threshold > 1) {
    throw new Error("--threshold must be between 0 and 1");
  }
  return args;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function flattenLayers(layers, target = []) {
  for (const layer of layers || []) {
    if (!layer || typeof layer !== "object") continue;
    target.push(layer);
    flattenLayers(layer.children || layer.layers, target);
  }
  return target;
}

function signature(layer) {
  const kind = normalize(layer.type || layer.kind || layer.node_type);
  const name = normalize(layer.name || layer.layer_path).replace(/(?:copy|拷贝)\s*\d*/g, "");
  const text = normalize(layer.text || layer.content || layer.value);
  const asset = normalize(layer.asset_id || layer.image_hash || layer.resource_name);
  return [kind, name, text, asset].join("|");
}

function signatures(screen) {
  return new Set(flattenLayers(screen.layers || []).map(signature).filter((item) => item !== "|||"));
}

function jaccard(left, right) {
  if (left.size === 0 && right.size === 0) return 1;
  let intersection = 0;
  for (const item of left) if (right.has(item)) intersection += 1;
  const union = left.size + right.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

function inferredState(name) {
  const value = String(name || "");
  const state = {};
  if (/(未连接|未绑定|disconnected|unbound)/i.test(value)) state.connection = "disconnected";
  else if (/(有数据|已连接|connected)/i.test(value)) state.connection = "connected";
  if (/(列表|list)/i.test(value)) state.layout = "list";
  else if (/(宫格|网格|grid)/i.test(value)) state.layout = "grid";
  if (/(折叠|收起|collapsed)/i.test(value)) state.appBar = "collapsed";
  if (/(展开|expanded)/i.test(value)) state.appBar = "expanded";
  if (/(空数据|empty)/i.test(value)) state.content = "empty";
  else if (/(加载|loading)/i.test(value)) state.content = "loading";
  else if (/(错误|error)/i.test(value)) state.content = "error";
  else if (/(有数据|data)/i.test(value)) state.content = "data";
  return state;
}

function buildStateMap(manifest, hints = {}, threshold = 0.65) {
  const screens = Array.isArray(manifest.screens) ? manifest.screens : [];
  const sets = screens.map(signatures);
  const pairs = [];
  const parent = screens.map((_, index) => index);
  const find = (x) => parent[x] === x ? x : (parent[x] = find(parent[x]));
  const join = (a, b) => { a = find(a); b = find(b); if (a !== b) parent[b] = a; };
  for (let i = 0; i < screens.length; i += 1) {
    for (let j = i + 1; j < screens.length; j += 1) {
      const similarity = jaccard(sets[i], sets[j]);
      pairs.push({ left: screens[i].name, right: screens[j].name, similarity: Number(similarity.toFixed(3)) });
      if (similarity >= threshold) join(i, j);
    }
  }
  const groups = new Map();
  screens.forEach((screen, index) => {
    const root = find(index);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(screen.name);
  });
  const mapped = screens.map((screen) => {
    const provided = hints[screen.id] || hints[screen.name] || {};
    return {
      id: screen.id,
      name: screen.name,
      state: { ...inferredState(screen.name), ...provided },
      evidence: Object.keys(provided).length > 0 ? "confirmed_hint+name" : "name_only_inference",
    };
  });
  return {
    schema_version: 1,
    threshold,
    screens: mapped,
    candidate_shared_groups: [...groups.values()].filter((group) => group.length > 1),
    pairwise_similarity: pairs.sort((a, b) => b.similarity - a.similarity),
    guidance: "Similarity generates shared-layout candidates only; confirm dimensions with prototype links, design images, and current behavior.",
  };
}

async function selfTest() {
  const manifest = {
    screens: [
      { id: "a", name: "首页-有数据", layers: [{ type: "text", name: "title", text: "健康" }, { type: "image", name: "steps" }] },
      { id: "b", name: "首页-有数据 列表", layers: [{ type: "text", name: "title", text: "健康" }, { type: "image", name: "steps" }] },
      { id: "c", name: "首页-未连接", layers: [{ type: "text", name: "title", text: "健康" }, { type: "button", name: "connect" }] },
    ],
  };
  const result = buildStateMap(manifest, { "首页-有数据": { appBar: "expanded" } }, 0.6);
  if (result.screens[0].state.connection !== "connected" || result.screens[1].state.layout !== "list") {
    throw new Error("state inference self-test failed");
  }
  if (result.candidate_shared_groups.length !== 1) throw new Error("similarity self-test failed");
  console.log(JSON.stringify({ status: "ok", test: "state_map" }));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return console.log(usage());
  if (args.selfTest) return selfTest();
  if (!args.manifest) throw new Error(usage());
  const manifest = JSON.parse(await readFile(args.manifest, "utf8"));
  const hints = args.hints ? JSON.parse(await readFile(args.hints, "utf8")) : {};
  const result = buildStateMap(manifest, hints, args.threshold);
  if (args.output) {
    await mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
    await writeFile(args.output, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }
  console.log(JSON.stringify({ status: "ok", screens: result.screens.length, shared_groups: result.candidate_shared_groups.length, output: args.output || null }));
}

main().catch((error) => {
  console.error(JSON.stringify({ status: "error", message: error.message }));
  process.exitCode = 1;
});
