// Parses every non-test .tsx/.ts file under /app/src with the TypeScript compiler API and
// reports Mantine styling-rule findings as JSON on stdout. Usage: node mantine_lint.cjs /app/src
const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");
const ts = createRequire("/app/package.json")("typescript");

const STYLE_PROPS = new Set(
  (
    "m mt mb ml mr ms me mx my mis mie p pt pb pl pr ps pe px py pis pie w miw maw h mih mah " +
    "bg c bd bdrs bgsz bgp bgr bga ff fz fw lts lh fs tt td ta pos top left bottom right inset display flex " +
    "gap rowGap columnGap spacing verticalSpacing horizontalSpacing radius size"
  ).split(" "),
);
const FRACTIONAL_STRING = /(^|[^\w.])\d*\.\d+(rem|em|px|vh|vw|%)?\b/;
const HARDCODED_COLOR = /#[0-9a-fA-F]{3,8}\b|\b(rgba?|hsla?)\(/;

function walkFiles(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "node_modules" && entry.name !== "__verifier__") walkFiles(full, out);
    } else if (/\.tsx?$/.test(entry.name) && !/\.(test|spec)\.tsx?$/.test(entry.name) && !entry.name.endsWith(".d.ts")) {
      if (!/setupTests\.ts$|test-utils\.tsx$/.test(entry.name)) out.push(full);
    }
  }
  return out;
}

function literalsIn(node, found = []) {
  if (ts.isNumericLiteral(node) || ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) found.push(node);
  ts.forEachChild(node, (child) => literalsIn(child, found));
  return found;
}

function lint(file) {
  const text = fs.readFileSync(file, "utf8");
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const rel = path.relative("/app", file);
  const findings = {
    inlineStyle: [],
    bracedStringLiteral: [],
    fractionalValue: [],
    hardcodedColor: [],
    createStyles: [],
    handRolledFlex: [],
    alertCall: [],
    stateBoundInput: [],
    mantineFormImport: false,
  };
  const at = (node) => `${rel}:${source.getLineAndCharacterOfPosition(node.getStart()).line + 1}`;
  const stateNames = new Set();

  function collectState(node) {
    if (
      ts.isVariableDeclaration(node) &&
      node.initializer &&
      ts.isCallExpression(node.initializer) &&
      /^(React\.)?useState$/.test(node.initializer.expression.getText()) &&
      ts.isArrayBindingPattern(node.name) &&
      node.name.elements[0] &&
      ts.isBindingElement(node.name.elements[0])
    ) {
      stateNames.add(node.name.elements[0].name.getText());
    }
    ts.forEachChild(node, collectState);
  }
  collectState(source);

  function visit(node) {
    if (ts.isImportDeclaration(node)) {
      const from = node.moduleSpecifier.text;
      if (from === "@mantine/form") findings.mantineFormImport = true;
      if (from === "@mantine/emotion") findings.createStyles.push(at(node));
    }
    if (ts.isIdentifier(node) && node.text === "createStyles") findings.createStyles.push(at(node));
    if (ts.isCallExpression(node)) {
      const callee = node.expression.getText();
      if (callee === "alert" || callee === "window.alert") findings.alertCall.push(at(node));
    }
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) || ts.isTemplateExpression(node)) {
      if (HARDCODED_COLOR.test(node.getText())) findings.hardcodedColor.push(at(node));
    }
    if (ts.isJsxAttribute(node)) {
      const name = node.name.getText();
      const init = node.initializer;
      if (name === "style") findings.inlineStyle.push(at(node));
      if (init && ts.isJsxExpression(init) && init.expression) {
        const expr = init.expression;
        if (ts.isStringLiteral(expr) || ts.isNoSubstitutionTemplateLiteral(expr)) findings.bracedStringLiteral.push(at(node));
        if ((name === "value" || name === "checked") && stateNames.has(expr.getText().split(".")[0]))
          findings.stateBoundInput.push(at(node));
      }
      if (STYLE_PROPS.has(name) && init) {
        for (const literal of literalsIn(init)) {
          const isFraction = ts.isNumericLiteral(literal) ? literal.getText().includes(".") : FRACTIONAL_STRING.test(literal.text);
          if (isFraction) findings.fractionalValue.push(`${at(node)} ${name}=${init.getText()}`);
        }
      }
      if (name === "display" && init) {
        if (/["'`](inline-)?flex["'`]/.test(init.getText())) findings.handRolledFlex.push(at(node));
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  return findings;
}

const root = process.argv[2] || "/app/src";
const report = {};
for (const file of walkFiles(root)) report[path.relative("/app", file)] = lint(file);
process.stdout.write(JSON.stringify(report, null, 2));
