import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const skillRoot = path.resolve(import.meta.dirname, '..');
const script = path.join(skillRoot, 'scripts', 'faq_sync.mjs');
const locales = ['cn', 'cs', 'de', 'en', 'es', 'fr', 'hu', 'it', 'ja', 'pt', 'sk'];

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'faq-sync-'));
  const data = [
    { title: '1. Connect?', itemTexts: [{ q: '(1) Old requirement' }, { q: '(2) Enable Bluetooth' }, { q: '(3) Bind in app' }] },
    { title: '2. Charge?', itemTexts: [{ q: '(1) Insert USB' }, { q: '(2) Wait' }] },
    { title: '3. Weather?', itemTexts: [{ q: 'Allow location' }] },
  ];
  for (const locale of locales) fs.writeFileSync(path.join(root, `${locale}.json`), `${JSON.stringify(data, null, 2)}\n`);
  return root;
}

function run(args, options = {}) {
  return spawnSync(process.execPath, [script, ...args], { encoding: 'utf8', ...options });
}

function embeddedFixture({ keepEnglishJson = false } = {}) {
  const root = fixture();
  const english = fs.readFileSync(path.join(root, 'en.json'), 'utf8').trim();
  if (!keepEnglishJson) fs.unlinkSync(path.join(root, 'en.json'));
  const base = path.join(root, 'question_list.vue');
  fs.writeFileSync(base, `<script>\nexport default { data() { return { items: ${english}, active: 1 }; } };\n</script>\n`);
  return { root, base };
}

test('audit accepts aligned 11-locale data', () => {
  const root = fixture();
  const result = run(['audit', '--dir', root]);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /11 variants aligned/);
});

test('branch-only locale is discovered, inspected, and updated automatically', () => {
  const root = fixture();
  const trPath = path.join(root, 'tr.json');
  const tr = JSON.parse(fs.readFileSync(path.join(root, 'en.json')));
  tr[0].title = '1. Nasıl bağlanır?';
  tr[0].itemTexts[1].q = '(2) Bluetooth açın';
  fs.writeFileSync(trPath, `${JSON.stringify(tr, null, 2)}\n`);

  const audit = run(['audit', '--dir', root, '--json']);
  assert.equal(audit.status, 0, audit.stderr);
  const auditReport = JSON.parse(audit.stdout);
  assert.deepEqual(auditReport.extraLocales, ['tr']);
  assert.equal(auditReport.locales.includes('tr'), true);

  const inspect = run(['inspect', '--dir', root, '--locale', 'tr', '--contains', 'Bluetooth açın']);
  assert.equal(inspect.status, 0, inspect.stderr);
  assert.equal(JSON.parse(inspect.stdout)[0].matches[0].englishQ, '(2) Enable Bluetooth');

  const input = JSON.stringify({ operations: [{ type: 'delete_item', faq: 1, item: 1, expect_en_contains: 'Old requirement' }] });
  const write = run(['apply', '--dir', root, '--spec', '-', '--write', '--json'], { input });
  assert.equal(write.status, 0, write.stderr);
  const writeReport = JSON.parse(write.stdout);
  assert.deepEqual(writeReport.extraLocales, ['tr']);
  assert.equal(writeReport.writtenFiles.includes(trPath), true);
  assert.deepEqual(JSON.parse(fs.readFileSync(trPath))[0].itemTexts.map(item => item.q), ['(1) Bluetooth açın', '(2) Bind in app']);
});

test('add or update requires translations for branch-only locales', () => {
  const root = fixture();
  const trPath = path.join(root, 'tr.json');
  fs.copyFileSync(path.join(root, 'en.json'), trPath);
  const translations = Object.fromEntries(locales.map(locale => [locale, '(3) New instruction']));
  const input = JSON.stringify({ operations: [{ type: 'add_item', faq: 2, position: 3, translations }] });

  const result = run(['apply', '--dir', root, '--spec', '-', '--write'], { input });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /missing tr translation/);
  assert.equal(JSON.parse(fs.readFileSync(trPath))[1].itemTexts.length, 2);
});

test('delete_item dry-run does not write and write renumbers all locales', () => {
  const root = fixture();
  const spec = path.join(root, 'spec.json');
  fs.writeFileSync(spec, JSON.stringify({ operations: [{ type: 'delete_item', faq: 1, item: 1, expect_en_contains: 'Old requirement' }] }));
  const dryRun = run(['apply', '--dir', root, '--spec', spec]);
  assert.equal(dryRun.status, 0, dryRun.stderr);
  assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'en.json')))[0].itemTexts.length, 3);
  const write = run(['apply', '--dir', root, '--spec', spec, '--write']);
  assert.equal(write.status, 0, write.stderr);
  for (const locale of locales) {
    const data = JSON.parse(fs.readFileSync(path.join(root, `${locale}.json`)));
    assert.deepEqual(data[0].itemTexts.map(item => item.q), ['(1) Enable Bluetooth', '(2) Bind in app']);
  }
});

test('delete_faq renumbers titles and missing translations fail without writes', () => {
  const root = fixture();
  const deleteSpec = path.join(root, 'delete.json');
  fs.writeFileSync(deleteSpec, JSON.stringify({ operations: [{ type: 'delete_faq', faq: 2, expect_en_contains: 'Charge' }] }));
  assert.equal(run(['apply', '--dir', root, '--spec', deleteSpec, '--write']).status, 0);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root, 'en.json'))).map(faq => faq.title), ['1. Connect?', '2. Weather?']);
  const before = fs.readFileSync(path.join(root, 'en.json'), 'utf8');
  const updateSpec = path.join(root, 'update.json');
  fs.writeFileSync(updateSpec, JSON.stringify({ operations: [{ type: 'update_item', faq: 1, item: 1, expect_en_contains: 'Old requirement', translations: { en: '(1) New' } }] }));
  const result = run(['apply', '--dir', root, '--spec', updateSpec, '--write']);
  assert.notEqual(result.status, 0);
  assert.equal(fs.readFileSync(path.join(root, 'en.json'), 'utf8'), before);
});

test('audit detects locale drift', () => {
  const root = fixture();
  const cs = JSON.parse(fs.readFileSync(path.join(root, 'cs.json')));
  cs[0].itemTexts.pop();
  fs.writeFileSync(path.join(root, 'cs.json'), JSON.stringify(cs));
  const result = run(['audit', '--dir', root]);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /item count/);
});

test('JSON audit caps repeated errors and keeps summary counts', () => {
  const root = fixture();
  for (const locale of ['cs', 'de']) {
    const data = JSON.parse(fs.readFileSync(path.join(root, `${locale}.json`)));
    data[0].itemTexts.pop();
    fs.writeFileSync(path.join(root, `${locale}.json`), JSON.stringify(data));
  }
  const result = run(['audit', '--dir', root, '--json', '--max-errors', '1']);
  assert.notEqual(result.status, 0);
  const report = JSON.parse(result.stdout);
  assert.equal(report.errors.length, 1);
  assert.equal(report.errorCount, 2);
  assert.equal(report.omittedErrorCount, 1);
  assert.equal(report.issuesByLocale.cs, 1);
  assert.equal(report.issuesByLocale.de, 1);
});

test('external embedded English baseline replaces a missing en.json', () => {
  const { root, base } = embeddedFixture();
  const audit = run(['audit', '--dir', root, '--base', base]);
  assert.equal(audit.status, 0, audit.stderr);
  const inspect = run(['inspect', '--dir', root, '--base', base, '--contains', 'Old requirement']);
  assert.equal(inspect.status, 0, inspect.stderr);
  assert.deepEqual(JSON.parse(inspect.stdout)[0].matches.map(match => match.item), [1]);

  const spec = path.join(root, 'delete-embedded.json');
  fs.writeFileSync(spec, JSON.stringify({ operations: [{ type: 'delete_item', faq: 1, item: 1, expect_en_contains: 'Old requirement' }] }));
  const write = run(['apply', '--dir', root, '--base', base, '--spec', spec, '--write']);
  assert.equal(write.status, 0, write.stderr);
  assert.doesNotMatch(fs.readFileSync(base, 'utf8'), /Old requirement/);
  assert.match(fs.readFileSync(base, 'utf8'), /items: \[/);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root, 'cn.json')))[0].itemTexts.map(item => item.q), ['(1) Enable Bluetooth', '(2) Bind in app']);
});

test('external upstream English and en.json are both updated when both exist', () => {
  const { root, base } = embeddedFixture({ keepEnglishJson: true });
  const spec = path.join(root, 'delete-both-english-sources.json');
  fs.writeFileSync(spec, JSON.stringify({ operations: [{ type: 'delete_item', faq: 1, item: 1, expect_en_contains: 'Old requirement' }] }));

  const write = run(['apply', '--dir', root, '--base', base, '--spec', spec, '--write']);
  assert.equal(write.status, 0, write.stderr);
  assert.doesNotMatch(fs.readFileSync(base, 'utf8'), /Old requirement/);
  assert.doesNotMatch(fs.readFileSync(path.join(root, 'en.json'), 'utf8'), /Old requirement/);
});

test('inspect can locate localized text and returns the English coordinate', () => {
  const root = fixture();
  const cnPath = path.join(root, 'cn.json');
  const cn = JSON.parse(fs.readFileSync(cnPath));
  cn[0].title = '1. 如何连接？';
  cn[0].itemTexts[1].q = '(2) 打开蓝牙';
  fs.writeFileSync(cnPath, JSON.stringify(cn, null, 2));

  const result = run(['inspect', '--dir', root, '--locale', 'cn', '--contains', '蓝牙']);
  assert.equal(result.status, 0, result.stderr);
  const [match] = JSON.parse(result.stdout);
  assert.equal(match.locale, 'cn');
  assert.equal(match.faq, 1);
  assert.equal(match.englishTitle, '1. Connect?');
  assert.deepEqual(match.matches, [{ item: 2, q: '(2) 打开蓝牙', englishQ: '(2) Enable Bluetooth' }]);
});

test('apply accepts a spec on stdin and emits a structured write report', () => {
  const root = fixture();
  const input = JSON.stringify({ operations: [{ type: 'delete_item', faq: 1, item: 1, expect_en_contains: 'Old requirement' }] });
  const result = run(['apply', '--dir', root, '--spec', '-', '--write', '--json'], { input });
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.ok, true);
  assert.equal(report.mode, 'write');
  assert.equal(report.operationCount, 1);
  assert.deepEqual(report.operations, [{ type: 'delete_item', faq: 1, item: 1 }]);
  assert.equal(report.sourceFileCount, 11);
  assert.equal(report.writtenFiles.length, 11);
  assert.equal(report.faqCountBefore, 3);
  assert.equal(report.faqCountAfter, 3);
  assert.equal(report.validation.ok, true);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root, 'en.json')))[0].itemTexts.map(item => item.q), ['(1) Enable Bluetooth', '(2) Bind in app']);
});

test('missing required locale data is compact and an explicit required subset can continue', () => {
  const { root, base } = embeddedFixture();
  fs.unlinkSync(path.join(root, 'cs.json'));
  fs.unlinkSync(path.join(root, 'hu.json'));
  fs.unlinkSync(path.join(root, 'sk.json'));
  const audit = run(['audit', '--dir', root, '--base', base, '--json']);
  assert.notEqual(audit.status, 0);
  assert.deepEqual(JSON.parse(audit.stdout).missingLocales, ['cs', 'hu', 'sk']);
  const selected = run(['audit', '--dir', root, '--base', base, '--locales', 'cn,de,en,es,fr,it,ja,pt']);
  assert.equal(selected.status, 0, selected.stderr);
});

test('add_faq auto preserves unnumbered item text', () => {
  const root = fixture();
  const translations = Object.fromEntries(locales.map(locale => [locale, { title: 'New FAQ', itemTexts: ['Plain answer'] }]));
  const spec = path.join(root, 'add.json');
  fs.writeFileSync(spec, JSON.stringify({ operations: [{ type: 'add_faq', position: 4, translations }] }));
  const write = run(['apply', '--dir', root, '--spec', spec, '--write']);
  assert.equal(write.status, 0, write.stderr);
  assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'en.json')))[3].itemTexts[0].q, 'Plain answer');
});
