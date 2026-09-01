#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const DEFAULT_LOCALES = ['cn', 'cs', 'de', 'en', 'es', 'fr', 'hu', 'it', 'ja', 'pt', 'sk'];

function usage(exitCode = 0) {
  console.log(`Usage:
  node faq_sync.mjs audit --dir <faq-json-dir> [--base <english-source>] [--locales <csv>] [--json] [--max-errors <n>]
  node faq_sync.mjs inspect --dir <faq-json-dir> [--base <english-source>] [--faq <n> | --contains <text>] [--json]
  node faq_sync.mjs apply --dir <faq-json-dir> --spec <change-spec.json> [--base <english-source>] [--locales <csv>] [--write]

Defaults: ${DEFAULT_LOCALES.join(', ')}
--base accepts an English JSON file or a Vue/JS file containing items: [...].`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!command || command === '--help' || command === '-h') usage(0);
  const options = { command, write: false, json: false, locales: DEFAULT_LOCALES, maxErrors: 12 };
  for (let index = 0; index < rest.length; index += 1) {
    const arg = rest[index];
    if (arg === '--write') options.write = true;
    else if (arg === '--json') options.json = true;
    else if (['--dir', '--spec', '--base', '--locales', '--faq', '--contains', '--max-errors'].includes(arg)) {
      if (!rest[index + 1]) throw new Error(`${arg} requires a value`);
      const key = arg === '--max-errors' ? 'maxErrors' : arg.slice(2);
      options[key] = rest[++index];
    } else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!['audit', 'inspect', 'apply'].includes(command)) throw new Error(`Unknown command: ${command}`);
  if (!options.dir) throw new Error('--dir is required');
  if (command === 'apply' && !options.spec) throw new Error('--spec is required for apply');
  if (options.locales !== DEFAULT_LOCALES) {
    options.locales = [...new Set(String(options.locales).split(',').map(value => value.trim()).filter(Boolean))];
    if (!options.locales.includes('en')) throw new Error('--locales must include en as the structural baseline');
  }
  if (options.faq !== undefined) {
    options.faq = Number(options.faq);
    if (!Number.isInteger(options.faq) || options.faq < 1) throw new Error('--faq must be a positive integer');
  }
  options.maxErrors = Number(options.maxErrors);
  if (!Number.isInteger(options.maxErrors) || options.maxErrors < 0) throw new Error('--max-errors must be a non-negative integer');
  return options;
}

function extractEmbeddedArray(raw, filePath) {
  const marker = /\bitems\s*:\s*/g;
  let match;
  while ((match = marker.exec(raw)) !== null) {
    const start = raw.indexOf('[', match.index + match[0].length);
    if (start < 0) continue;
    let depth = 0;
    let inString = false;
    let escaped = false;
    for (let index = start; index < raw.length; index += 1) {
      const char = raw[index];
      if (inString) {
        if (escaped) escaped = false;
        else if (char === '\\') escaped = true;
        else if (char === '"') inString = false;
        continue;
      }
      if (char === '"') inString = true;
      else if (char === '[') depth += 1;
      else if (char === ']') {
        depth -= 1;
        if (depth === 0) {
          const json = raw.slice(start, index + 1);
          try {
            const data = JSON.parse(json);
            if (Array.isArray(data)) return { data, start, end: index + 1, json };
          } catch {
            break;
          }
        }
      }
    }
  }
  throw new Error(`${filePath}: cannot find a JSON array assigned to items`);
}

function readDataSource(filePath) {
  const buffer = fs.readFileSync(filePath);
  const hasBom = buffer.length >= 3 && buffer[0] === 0xef && buffer[1] === 0xbb && buffer[2] === 0xbf;
  const raw = buffer.toString('utf8', hasBom ? 3 : 0);
  const common = { hasBom, newline: raw.includes('\r\n') ? '\r\n' : '\n', finalNewline: raw.endsWith('\n') };
  try {
    const data = JSON.parse(raw);
    return { data, format: { ...common, kind: 'json', pretty: /\[\s*\r?\n/.test(raw) } };
  } catch {
    const embedded = extractEmbeddedArray(raw, filePath);
    return {
      data: embedded.data,
      format: {
        ...common,
        kind: 'embedded',
        pretty: /\[\s*\r?\n/.test(embedded.json),
        prefix: raw.slice(0, embedded.start),
        suffix: raw.slice(embedded.end),
      },
    };
  }
}

function stringifyData(data, format) {
  let output = JSON.stringify(data, null, format.pretty ? 2 : 0);
  if (format.newline === '\r\n') output = output.replace(/\n/g, '\r\n');
  return output;
}

function serialize(record) {
  const { data, format } = record;
  let output;
  if (format.kind === 'embedded') output = `${format.prefix}${stringifyData(data, format)}${format.suffix}`;
  else {
    output = stringifyData(data, format);
    if (format.finalNewline) output += format.newline;
  }
  return format.hasBom ? `\uFEFF${output}` : output;
}

function makeRecord(filePath, locale = null) {
  return { locale, filePath, ...readDataSource(filePath) };
}

function loadWorkspace(directory, locales, baseOption) {
  const records = new Map();
  const errors = [];
  const missingLocales = [];
  const resolvedDirectory = path.resolve(directory);
  const basePath = baseOption ? path.resolve(baseOption) : path.join(resolvedDirectory, 'en.json');
  let baseRecord = null;

  if (!fs.existsSync(basePath)) errors.push(`Missing English baseline: ${basePath}`);
  else {
    try {
      baseRecord = makeRecord(basePath, 'en');
    } catch (error) {
      errors.push(error.message);
    }
  }

  for (const locale of locales) {
    const filePath = path.join(resolvedDirectory, `${locale}.json`);
    if (!fs.existsSync(filePath)) {
      if (!(locale === 'en' && baseOption)) {
        missingLocales.push(locale);
        errors.push(`Missing locale file: ${filePath}`);
      }
      continue;
    }
    try {
      records.set(locale, makeRecord(filePath, locale));
    } catch (error) {
      errors.push(error.message);
    }
  }

  if (!baseOption && records.has('en')) baseRecord = records.get('en');
  return { records, baseRecord, errors, missingLocales, locales };
}

function leadingNumber(text) {
  const match = String(text).match(/^\s*(?:[（(])?(\d+)(?=\s*(?:[-.)）]))/u);
  return match ? Number(match[1]) : null;
}

function placeholderTokens(text) {
  return (String(text).match(/%\d*\$?[A-Za-z]|\{\{[^{}]+\}\}|\{[A-Za-z_][^{}]*\}|https?:\/\/\S+/g) || []).sort();
}

function validateBaseline(baseline) {
  const errors = [];
  if (!Array.isArray(baseline)) return ['English baseline root must be an array'];
  baseline.forEach((faq, faqIndex) => {
    if (!faq || typeof faq.title !== 'string' || !Array.isArray(faq.itemTexts)) {
      errors.push(`English baseline FAQ ${faqIndex + 1} has invalid shape`);
      return;
    }
    faq.itemTexts.forEach((item, itemIndex) => {
      if (!item || typeof item.q !== 'string' || !item.q.trim()) errors.push(`English baseline FAQ ${faqIndex + 1} item ${itemIndex + 1} is empty or invalid`);
    });
  });
  return errors;
}

function auditWorkspace(workspace) {
  const errors = [...workspace.errors];
  if (!workspace.baseRecord) return errors;
  const baseline = workspace.baseRecord.data;
  const baselineErrors = validateBaseline(baseline);
  errors.push(...baselineErrors);
  if (baselineErrors.length) return errors;

  for (const [locale, record] of workspace.records) {
    const data = record.data;
    if (!Array.isArray(data)) {
      errors.push(`${locale}.json root must be an array`);
      continue;
    }
    if (data.length !== baseline.length) errors.push(`${locale}.json FAQ count ${data.length} != English baseline ${baseline.length}`);
    const faqCount = Math.min(data.length, baseline.length);
    for (let faqIndex = 0; faqIndex < faqCount; faqIndex += 1) {
      const faq = data[faqIndex];
      const baseFaq = baseline[faqIndex];
      if (!faq || typeof faq.title !== 'string' || !Array.isArray(faq.itemTexts)) {
        errors.push(`${locale}.json FAQ ${faqIndex + 1} has invalid shape`);
        continue;
      }
      const titleNumber = Number((faq.title.match(/^\s*(\d+)\./) || [])[1]);
      if (titleNumber !== faqIndex + 1) errors.push(`${locale}.json FAQ ${faqIndex + 1} title number is ${Number.isNaN(titleNumber) ? 'missing' : titleNumber}`);
      if (faq.itemTexts.length !== baseFaq.itemTexts.length) errors.push(`${locale}.json FAQ ${faqIndex + 1} item count ${faq.itemTexts.length} != English baseline ${baseFaq.itemTexts.length}`);
      const itemCount = Math.min(faq.itemTexts.length, baseFaq.itemTexts.length);
      for (let itemIndex = 0; itemIndex < itemCount; itemIndex += 1) {
        const value = faq.itemTexts[itemIndex]?.q;
        const baseValue = baseFaq.itemTexts[itemIndex]?.q;
        if (typeof value !== 'string' || !value.trim()) {
          errors.push(`${locale}.json FAQ ${faqIndex + 1} item ${itemIndex + 1} is empty or invalid`);
          continue;
        }
        const baseNumber = leadingNumber(baseValue);
        if (baseNumber !== null && leadingNumber(value) !== baseNumber) errors.push(`${locale}.json FAQ ${faqIndex + 1} item ${itemIndex + 1} leading number differs from English baseline`);
        if (JSON.stringify(placeholderTokens(value)) !== JSON.stringify(placeholderTokens(baseValue))) errors.push(`${locale}.json FAQ ${faqIndex + 1} item ${itemIndex + 1} placeholders differ from English baseline`);
      }
    }
  }
  return errors;
}

function normalizeTitle(title, number) {
  const value = String(title).trimStart();
  return /^\d+\./.test(value) ? value.replace(/^\d+\./, `${number}.`) : `${number}. ${value}`;
}

function renumberItems(items, mode, originalItems) {
  if (mode === 'none') return;
  const originalFullyNumbered = originalItems.length > 0 && originalItems.every(item => leadingNumber(item.q) !== null);
  if (mode === 'auto' && !originalFullyNumbered) return;
  for (let index = 0; index < items.length; index += 1) {
    const text = String(items[index].q);
    if (leadingNumber(text) === null) {
      if (mode === 'all') items[index].q = `(${index + 1}) ${text}`;
      continue;
    }
    items[index].q = text.replace(/^(\s*(?:[（(])?)\d+(?=\s*(?:[-.)）]))/u, `$1${index + 1}`);
  }
}

function requireIndex(value, length, label, allowEnd = false) {
  if (!Number.isInteger(value)) throw new Error(`${label} must be an integer`);
  const max = allowEnd ? length + 1 : length;
  if (value < 1 || value > max) throw new Error(`${label} ${value} is outside 1..${max}`);
  return value - 1;
}

function requireTranslations(operation, locales, validator) {
  if (!operation.translations || typeof operation.translations !== 'object') throw new Error(`${operation.type} requires translations`);
  for (const locale of locales) {
    if (!(locale in operation.translations)) throw new Error(`${operation.type} is missing ${locale} translation`);
    validator(operation.translations[locale], locale);
  }
}

function targetEnglishText(baseline, operation) {
  const faq = baseline[requireIndex(operation.faq, baseline.length, 'faq')];
  if (operation.type === 'delete_item' || operation.type === 'update_item') return faq.itemTexts[requireIndex(operation.item, faq.itemTexts.length, 'item')].q;
  return [faq.title, ...faq.itemTexts.map(item => item.q)].join('\n');
}

function checkPrecondition(baseline, operation) {
  if (!['delete_faq', 'delete_item', 'update_faq', 'update_item', 'update_title'].includes(operation.type)) return;
  if (typeof operation.expect_en_contains !== 'string' || !operation.expect_en_contains.trim()) throw new Error(`${operation.type} requires expect_en_contains`);
  const english = targetEnglishText(baseline, operation);
  if (!english.toLocaleLowerCase().includes(operation.expect_en_contains.toLocaleLowerCase())) throw new Error(`${operation.type} precondition failed: English target does not contain ${JSON.stringify(operation.expect_en_contains)}`);
}

function applyToData(data, operation, translationLocale) {
  const mode = operation.renumber_items || 'auto';
  if (operation.type === 'delete_faq') data.splice(requireIndex(operation.faq, data.length, 'faq'), 1);
  else if (operation.type === 'delete_item') {
    const faq = data[requireIndex(operation.faq, data.length, 'faq')];
    const original = structuredClone(faq.itemTexts);
    faq.itemTexts.splice(requireIndex(operation.item, faq.itemTexts.length, 'item'), 1);
    renumberItems(faq.itemTexts, mode, original);
  } else if (operation.type === 'add_faq') {
    const value = operation.translations[translationLocale];
    const faq = { title: value.title, itemTexts: value.itemTexts.map(q => ({ q })) };
    renumberItems(faq.itemTexts, mode === 'auto' ? 'none' : mode, []);
    data.splice(requireIndex(operation.position, data.length, 'position', true), 0, faq);
  } else if (operation.type === 'update_faq') {
    const index = requireIndex(operation.faq, data.length, 'faq');
    const original = data[index].itemTexts;
    const value = operation.translations[translationLocale];
    const faq = { title: value.title, itemTexts: value.itemTexts.map(q => ({ q })) };
    renumberItems(faq.itemTexts, mode, original);
    data[index] = faq;
  } else if (operation.type === 'add_item') {
    const faq = data[requireIndex(operation.faq, data.length, 'faq')];
    const original = structuredClone(faq.itemTexts);
    faq.itemTexts.splice(requireIndex(operation.position, faq.itemTexts.length, 'position', true), 0, { q: operation.translations[translationLocale] });
    renumberItems(faq.itemTexts, mode, original);
  } else if (operation.type === 'update_item') {
    const faq = data[requireIndex(operation.faq, data.length, 'faq')];
    const original = structuredClone(faq.itemTexts);
    faq.itemTexts[requireIndex(operation.item, faq.itemTexts.length, 'item')].q = operation.translations[translationLocale];
    renumberItems(faq.itemTexts, mode, original);
  } else if (operation.type === 'update_title') data[requireIndex(operation.faq, data.length, 'faq')].title = operation.translations[translationLocale];
  else throw new Error(`Unsupported operation type: ${operation.type}`);
  data.forEach((faq, index) => { faq.title = normalizeTitle(faq.title, index + 1); });
}

function applyOperation(workspace, operation) {
  checkPrecondition(workspace.baseRecord.data, operation);
  const mode = operation.renumber_items || 'auto';
  if (!['auto', 'all', 'none'].includes(mode)) throw new Error(`Invalid renumber_items: ${mode}`);
  const requiredLocales = [...new Set([...workspace.locales, 'en'])];
  if (operation.type === 'add_faq' || operation.type === 'update_faq') {
    requireTranslations(operation, requiredLocales, (value, locale) => {
      if (!value || typeof value.title !== 'string' || !Array.isArray(value.itemTexts) || value.itemTexts.some(item => typeof item !== 'string')) throw new Error(`${operation.type} ${locale} translation must contain title and itemTexts[]`);
    });
  } else if (['add_item', 'update_item', 'update_title'].includes(operation.type)) {
    requireTranslations(operation, requiredLocales, (value, locale) => {
      if (typeof value !== 'string' || !value.trim()) throw new Error(`${operation.type} ${locale} translation must be a non-empty string`);
    });
  }

  const targets = [];
  for (const [locale, record] of workspace.records) targets.push({ locale, record });
  if (![...workspace.records.values()].some(record => record.filePath === workspace.baseRecord.filePath)) targets.push({ locale: 'en', record: workspace.baseRecord });
  for (const target of targets) applyToData(target.record.data, operation, target.locale);
}

function resultSummary(workspace, errors, maxErrors) {
  const issuesByLocale = {};
  for (const locale of workspace.locales) issuesByLocale[locale] = errors.filter(error => error.startsWith(`${locale}.json`)).length;
  const displayedErrors = maxErrors === 0 ? [] : errors.slice(0, maxErrors);
  return {
    ok: errors.length === 0,
    locales: workspace.locales,
    presentLocales: [...workspace.records.keys()],
    missingLocales: workspace.missingLocales,
    baseline: workspace.baseRecord?.filePath ?? null,
    faqCount: workspace.baseRecord?.data?.length ?? null,
    faqCounts: Object.fromEntries([...workspace.records].map(([locale, record]) => [locale, Array.isArray(record.data) ? record.data.length : null])),
    errorCount: errors.length,
    issuesByLocale,
    errors: displayedErrors,
    omittedErrorCount: errors.length - displayedErrors.length,
  };
}

function printAudit(workspace, errors, asJson, maxErrors) {
  const result = resultSummary(workspace, errors, maxErrors);
  if (asJson) console.log(JSON.stringify(result, null, 2));
  else if (result.ok) console.log(`OK: ${result.locales.length} variants aligned, ${result.faqCount} FAQs each; baseline=${result.baseline}`);
  else {
    console.error(`FAIL: ${errors.length} issue(s); missing=${result.missingLocales.join(',') || 'none'}`);
    for (const error of result.errors) console.error(`- ${error}`);
    if (result.omittedErrorCount) console.error(`- ... ${result.omittedErrorCount} more issue(s) omitted; use --max-errors to adjust`);
  }
}

function inspectBaseline(workspace, options) {
  if (!workspace.baseRecord) throw new Error(workspace.errors.join('; ') || 'English baseline is unavailable');
  const data = workspace.baseRecord.data;
  const baselineErrors = validateBaseline(data);
  if (baselineErrors.length) throw new Error(baselineErrors.join('; '));
  let output;
  if (options.faq !== undefined) {
    const index = requireIndex(options.faq, data.length, 'faq');
    output = { faq: index + 1, ...data[index] };
  } else if (options.contains !== undefined) {
    const needle = String(options.contains).toLocaleLowerCase();
    output = data.flatMap((faq, faqIndex) => {
      const titleMatch = faq.title.toLocaleLowerCase().includes(needle);
      const matches = faq.itemTexts.flatMap((item, itemIndex) => item.q.toLocaleLowerCase().includes(needle) ? [{ item: itemIndex + 1, q: item.q }] : []);
      return titleMatch || matches.length ? [{ faq: faqIndex + 1, title: faq.title, matches }] : [];
    });
  } else output = data.map((faq, index) => ({ faq: index + 1, title: faq.title }));
  if (options.json || options.faq !== undefined || options.contains !== undefined) console.log(JSON.stringify(output, null, 2));
  else output.forEach(item => console.log(`${item.faq}\t${item.title}`));
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const workspace = loadWorkspace(options.dir, options.locales, options.base);
  if (options.command === 'inspect') {
    inspectBaseline(workspace, options);
    return;
  }

  const preAuditErrors = auditWorkspace(workspace);
  if (options.command === 'audit') {
    printAudit(workspace, preAuditErrors, options.json, options.maxErrors);
    process.exit(preAuditErrors.length ? 1 : 0);
  }
  if (preAuditErrors.length) {
    printAudit(workspace, preAuditErrors, false, options.maxErrors);
    throw new Error('Refusing to apply changes until the selected locale baseline audit passes');
  }

  const spec = JSON.parse(fs.readFileSync(path.resolve(options.spec), 'utf8'));
  if (!Array.isArray(spec.operations) || !spec.operations.length) throw new Error('Spec requires a non-empty operations array');
  spec.operations.forEach(operation => applyOperation(workspace, operation));
  const postAuditErrors = auditWorkspace(workspace);
  if (postAuditErrors.length) {
    printAudit(workspace, postAuditErrors, false, options.maxErrors);
    throw new Error('Generated FAQ data failed validation');
  }

  const writeTargets = new Map([...workspace.records.values()].map(record => [record.filePath, record]));
  writeTargets.set(workspace.baseRecord.filePath, workspace.baseRecord);
  if (options.write) {
    for (const record of writeTargets.values()) fs.writeFileSync(record.filePath, serialize(record), 'utf8');
    console.log(`WROTE: ${spec.operations.length} operation(s), ${writeTargets.size} source file(s), ${workspace.locales.length} variant(s).`);
  } else console.log(`DRY RUN OK: ${spec.operations.length} operation(s), ${writeTargets.size} source file(s), ${workspace.locales.length} variant(s). Add --write to save.`);
}

try {
  main();
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
