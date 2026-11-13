// Static checks on the test code an agent wrote. Usage: node lint_tests.mjs <file>...
// Prints JSON: { findings: [{rule, file, line, text}], facts: {...} }.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const ts = createRequire("/app/package.json")("typescript");

const findings = [];
const facts = { mswImported: false, fakeTimersUsed: false, realTimersRestoredInAfterEach: false };

const GET_BY = /^(getBy|getAllBy)[A-Z]/;
const FIND_BY = /^(findBy|findAllBy)[A-Z]/;
const PRESENCE_MATCHERS = new Set(["toBeInTheDocument", "toBeTruthy", "toBeDefined", "toBeVisible"]);
const TRUTHY_MATCHERS = new Set(["toBeTruthy", "toBeDefined"]);
const GLOBAL_STUBS = new Set(["matchMedia", "ResizeObserver"]);

function calleeName(call) {
  const e = call.expression;
  if (ts.isIdentifier(e)) return e.text;
  if (ts.isPropertyAccessExpression(e)) return e.name.text;
  return "";
}
function calleeText(call, sf) {
  return call.expression.getText(sf).replace(/\s+/g, "");
}
// A replacement that still calls a saved/real fetch (e.g. resolving relative URLs, then delegating) keeps
// the network layer, and so MSW, in the loop; only a replacement that answers without fetching is a stub.
function delegatesToFetch(expr, sf) {
  return !!expr && /\b\w*[Ff]etch\w*\s*(\(|\.(call|apply)\b)/.test(expr.getText(sf));
}

function stringArg(call, i) {
  const a = call.arguments[i];
  return a && (ts.isStringLiteral(a) || ts.isNoSubstitutionTemplateLiteral(a)) ? a.text : undefined;
}
function unwrap(node) {
  while (node && (ts.isAwaitExpression(node) || ts.isParenthesizedExpression(node) || ts.isAsExpression(node) || ts.isNonNullExpression(node))) {
    node = node.expression;
  }
  return node;
}
function isQueryCall(node, pattern) {
  node = unwrap(node);
  return !!node && ts.isCallExpression(node) && pattern.test(calleeName(node));
}
function isAwaitedQuery(node, pattern) {
  while (node && (ts.isParenthesizedExpression(node) || ts.isAsExpression(node))) node = node.expression;
  return !!node && ts.isAwaitExpression(node) && isQueryCall(node.expression, pattern);
}
// expect(subject)[.not].matcher(...) -> {subject, negated, matcher}
function matcherChain(call) {
  if (!ts.isPropertyAccessExpression(call.expression)) return undefined;
  const matcher = call.expression.name.text;
  let target = call.expression.expression;
  let negated = false;
  if (ts.isPropertyAccessExpression(target) && target.name.text === "not") {
    negated = true;
    target = target.expression;
  }
  if (!ts.isCallExpression(target) || calleeName(target) !== "expect") return undefined;
  return { subject: target.arguments[0], negated, matcher };
}
function enclosingFunction(node) {
  for (let p = node.parent; p; p = p.parent) {
    if (ts.isFunctionLike(p)) return p;
  }
  return undefined;
}
function enclosingHook(node) {
  // name of the lifecycle hook (beforeEach, afterEach, ...) whose callback contains node, if any
  for (let p = node.parent; p; p = p.parent) {
    if (ts.isFunctionLike(p) && p.parent && ts.isCallExpression(p.parent)) {
      const name = calleeName(p.parent);
      if (/^(before|after)(Each|All)$/.test(name)) return name;
    }
  }
  return undefined;
}
function hasUndefinedValue(node) {
  if (!node) return false;
  if (ts.isObjectLiteralExpression(node)) {
    return node.properties.some((p) =>
      ts.isPropertyAssignment(p) && ((ts.isIdentifier(p.initializer) && p.initializer.text === "undefined") || hasUndefinedValue(p.initializer)),
    );
  }
  if (ts.isArrayLiteralExpression(node)) return node.elements.some(hasUndefinedValue);
  return false;
}

for (const file of process.argv.slice(2)) {
  const text = readFileSync(file, "utf8");
  const kind = /\.(tsx|jsx)$/.test(file) ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
  const isTestFile = /\.(test|spec)\.[cm]?[jt]sx?$/.test(file);
  const waitsAsync = /\b(waitFor|findBy|findAllBy)/.test(text);
  const report = (rule, node) =>
    findings.push({ rule, file, line: sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1, text: node.getText(sf).slice(0, 160) });

  const visit = (node) => {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier) && /^msw(\/|$)/.test(node.moduleSpecifier.text)) {
      facts.mswImported = true;
    }
    if (ts.isCallExpression(node) && /^(require|import)$/.test(node.expression.getText(sf)) && /^msw(\/|$)/.test(stringArg(node, 0) ?? "")) {
      facts.mswImported = true;
    }

    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.EqualsToken && ts.isPropertyAccessExpression(node.left)) {
      const prop = node.left.name.text;
      if (prop === "fetch" && !delegatesToFetch(node.right, sf)) report("fetch-mocked", node);
      if (GLOBAL_STUBS.has(prop) && isTestFile) report("global-stub-in-test-file", node);
    }

    if (ts.isCallExpression(node)) {
      const callee = calleeText(node, sf);
      const name = calleeName(node);
      const arg0 = stringArg(node, 0);
      const arg1 = stringArg(node, 1);

      if (/^(vi|jest)\.stubGlobal$/.test(callee)) {
        if (arg0 === "fetch" && !delegatesToFetch(node.arguments[1], sf)) report("fetch-mocked", node);
        if (GLOBAL_STUBS.has(arg0 ?? "") && isTestFile) report("global-stub-in-test-file", node);
      }
      if (/^(vi|jest)\.spyOn$/.test(callee)) {
        if (arg1 === "fetch") report("fetch-mocked", node);
        if (arg1 && /^use[A-Z]/.test(arg1)) report("data-module-mocked", node);
        if (GLOBAL_STUBS.has(arg1 ?? "") && isTestFile) report("global-stub-in-test-file", node);
      }
      if (callee === "Object.defineProperty") {
        if (arg1 === "fetch" && !delegatesToFetch(node.arguments[2], sf)) report("fetch-mocked", node);
        if (GLOBAL_STUBS.has(arg1 ?? "") && isTestFile) report("global-stub-in-test-file", node);
      }
      if (/^(vi|jest)\.(mock|doMock)$/.test(callee) && arg0 !== undefined) {
        if (/^(\.|@\/|~\/|src\/)/.test(arg0) || arg0 === "@tanstack/react-query") report("data-module-mocked", node);
      }

      if (callee === "vi.useFakeTimers" || callee === "jest.useFakeTimers") {
        facts.fakeTimersUsed = true;
        const hook = enclosingHook(node);
        if (waitsAsync && (hook === "beforeEach" || hook === "beforeAll" || !enclosingFunction(node))) report("fake-timers-before-async-queries", node);
      }
      if ((callee === "vi.useRealTimers" || callee === "jest.useRealTimers") && enclosingHook(node) === "afterEach") {
        facts.realTimersRestoredInAfterEach = true;
      }

      if (name === "waitFor" && node.arguments[0] && ts.isFunctionLike(node.arguments[0])) {
        const cb = node.arguments[0];
        if (cb.body && !ts.isBlock(cb.body) && isQueryCall(cb.body, GET_BY)) report("waitfor-getby", node);
        const inner = (n) => {
          if (ts.isExpressionStatement(n) && isQueryCall(n.expression, GET_BY)) report("waitfor-getby", node);
          if (ts.isReturnStatement(n) && n.expression && isQueryCall(n.expression, GET_BY)) report("waitfor-getby", node);
          if (ts.isCallExpression(n)) {
            const chain = matcherChain(n);
            if (chain && !chain.negated && PRESENCE_MATCHERS.has(chain.matcher) && isQueryCall(chain.subject, GET_BY)) report("waitfor-getby", node);
          }
          ts.forEachChild(n, inner);
        };
        ts.forEachChild(cb, inner);
      }

      const chain = matcherChain(node);
      if (chain) {
        const truthy = (!chain.negated && TRUTHY_MATCHERS.has(chain.matcher)) || (chain.negated && chain.matcher === "toBeNull");
        if (truthy && isAwaitedQuery(chain.subject, FIND_BY)) report("findby-wrapped-in-truthy", node);
        if (truthy && isQueryCall(chain.subject, GET_BY)) report("getby-truthy", node);
        if ((chain.matcher === "toEqual") && node.arguments.some(hasUndefinedValue)) report("undefined-in-toEqual", node);
      }
    }

    if (ts.isNewExpression(node) && node.expression.getText(sf) === "QueryClient") {
      if (!enclosingFunction(node)) report("query-client-module-scope", node);
      const argText = (node.arguments ?? []).map((a) => a.getText(sf)).join(" ");
      if (!/\bretry\s*:\s*(false|0)\b/.test(argText) && !/\bretry\s*:\s*(false|0)\b/.test(text)) report("query-client-retries", node);
    }

    ts.forEachChild(node, visit);
  };
  visit(sf);
}

console.log(JSON.stringify({ findings, facts }));
