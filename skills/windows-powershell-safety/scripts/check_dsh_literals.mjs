import assert from "node:assert/strict";
import { Script } from "node:vm";

// Synthetic, local-only regression checks; never invokes tools, shell commands or network.
const slash = String.fromCharCode(92);
const call = "service_now_request(";
const rawSource = "return String.raw`service_now_request" + slash + "(`;";
const native = "C:" + slash + "example" + slash + "0548315" + slash + "app";
const cases = [
  ["backslash-free literal regex", () => {
    const regex = new RegExp("service_now_request[(]");
    assert.equal(regex.test(call), true);
    assert.equal(regex.test("service_now_requestx"), false);
  }],
  ["ordinary JS literal loses identity escape", () => {
    const broken = new Function("return 'service_now_request" + slash + "(';")();
    assert.equal(broken, call);
    assert.throws(() => new RegExp(broken), SyntaxError);
  }],
  ["String.raw preserves regex escape", () => {
    const regex = new RegExp(new Function(rawSource)());
    assert.equal(regex.test(call), true);
  }],
  ["transport JSON round trip", () => {
    const transported = JSON.parse(JSON.stringify({ code: rawSource }));
    assert.equal(transported.code, rawSource);
    assert.equal(new RegExp(new Function(transported.code)()).test(call), true);
  }],
  ["forward slash Windows path", () => {
    assert.equal(new Function("return 'C:/example/0548315/app';")(), "C:/example/0548315/app");
  }],
  ["raw Windows path", () => {
    assert.equal(new Function("return String.raw`" + native + "`;")(), native);
  }],
  ["strict unescaped numeric path rejected before execution", () => {
    const source = 'async function execute() { "use strict"; return "' + native + '"; }';
    assert.throws(() => new Script(source), SyntaxError);
  }],
  ["escaped ordinary path", () => {
    const encoded = native.replaceAll(slash, slash + slash);
    assert.equal(new Function('return "' + encoded + '";')(), native);
  }],
];
for (const [name, check] of cases) {
  check();
  console.log(`PASS ${name}`);
}
console.log(`PASS ${cases.length} synthetic literal regression cases`);
