import assert from 'node:assert/strict';
import { test } from 'node:test';
import { protectTableCodePipes } from './render_pdf.mjs';

test('protects logical and bitwise operators inside table code spans', () => {
  const input = '| Method | Condition | Behavior |\n| --- | --- | --- |\n| `call()` | `enabled || supported` and `a | b` | 完整说明 |';
  const output = protectTableCodePipes(input);
  assert.ok(output.includes('`enabled \\|\\| supported`'));
  assert.ok(output.includes('`a \\| b`'));
  assert.ok(output.endsWith('| 完整说明 |'));
  assert.equal(protectTableCodePipes(output), output);
});

test('does not rewrite fenced source code or ordinary paragraphs', () => {
  const input = 'Expression `a || b`.\n```kotlin\n| `a || b` |\n```\n~~~\n| `c | d` |\n~~~';
  assert.equal(protectTableCodePipes(input), input);
});
