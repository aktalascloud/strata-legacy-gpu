// Exercise the actual language handler with a streaming target or editor attached; no browser/model/network.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname, 'app.js'), 'utf8');
const start = source.indexOf('function showLanguage() {');
const end = source.indexOf('\nconst headerLang', start);
assert(start >= 0 && end > start);
for (const [busy, panel] of [[null, null], [{}, null], [null, {}], [{}, {}]]) {
  let renders = 0;
  const node = {setAttribute() {}};
  const context = {busy, panel, $: () => node, StrataI18n: {lang: 'ru'}, headerLang: node,
    window: {}, tr: () => '', renderEmptyChat() {}, setSidebar() {}, sidebarOpen: false,
    outputs() {}, renderChat() { renders++; }, setBusy() {}, lastMetrics: null};
  vm.runInNewContext(source.slice(start, end) + '\nshowLanguage();', context);
  assert.equal(renders, !busy && !panel ? 1 : 0);
}
console.log('language state: 4 cases PASS');
