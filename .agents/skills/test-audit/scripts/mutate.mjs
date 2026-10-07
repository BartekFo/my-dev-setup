#!/usr/bin/env node
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  fail,
  forEachDescendant,
  loadConfig,
  loadTypeScript,
  parseArgs,
  parseSource,
  relativeTo,
  repoRoot,
  selectPackages,
  stateDir,
} from "./lib.mjs";

const STYLE_ATTRIBUTES = new Set([
  "className", "style", "classNames", "styles", "color", "c", "bg", "variant", "size", "radius", "fw", "fz", "ta", "tt", "td",
  "gap", "p", "px", "py", "pt", "pb", "pl", "pr", "m", "mx", "my", "mt", "mb", "ml", "mr", "w", "h", "miw", "maw", "mih", "mah",
  "justify", "align", "direction", "wrap", "opacity", "shadow", "withBorder", "lh", "lts", "ff", "display", "pos", "inset",
]);
const COPY_ATTRIBUTE = /label|title|text|message|placeholder|description|tooltip|^alt$|caption|heading|subtitle|helper/i;
const OPERATOR_SWAPS = {
  EqualsEqualsEqualsToken: "!==", ExclamationEqualsEqualsToken: "===", EqualsEqualsToken: "!=", ExclamationEqualsToken: "==",
  LessThanToken: ">=", GreaterThanToken: "<=", LessThanEqualsToken: ">", GreaterThanEqualsToken: "<",
  AmpersandAmpersandToken: "||", BarBarToken: "&&", QuestionQuestionToken: "&&", PlusToken: "-", MinusToken: "+",
  AsteriskToken: "/", SlashToken: "*",
};

const args = parseArgs(process.argv.slice(2));
const root = repoRoot();
const config = loadConfig(root);
const [pkg] = selectPackages(config, args.package);
if (!args.package && config.packages.length > 1) fail("pass --package <name>");
if (!args.owner) fail("pass --owner <source file>");

const pkgRoot = path.join(root, pkg.root);
const owner = path.resolve(root, args.owner);
if (!existsSync(owner)) fail(`owner not found: ${owner}`);
const ownerRel = relativeTo(root, owner);
const outDir = path.join(stateDir(root), "mutations");
const slug = ownerRel.replace(/[^A-Za-z0-9]+/g, "_");
const resultFile = path.join(outDir, `${slug}.json`);

if (args.drop) {
  reportDrop(JSON.parse(readFileSync(resultFile, "utf8")), JSON.parse(readFileSync(path.resolve(String(args.drop)), "utf8")));
  process.exit(0);
}

const testFiles = resolveTestFiles();
if (testFiles.length === 0) fail(`no test files own ${ownerRel}. Pass --tests a.test.tsx,b.test.tsx`);

mkdirSync(outDir, { recursive: true });
const backup = path.join(outDir, `${slug}.backup`);
if (existsSync(backup)) {
  writeFileSync(owner, readFileSync(backup));
  rmSync(backup);
  console.warn(`restored ${ownerRel} from a backup left by an interrupted run`);
}
if (execFileSync("git", ["status", "--porcelain", "--", owner], { cwd: root, encoding: "utf8" }).trim()) {
  fail(`${ownerRel} has uncommitted changes. Mutate only a clean file.`);
}

const original = readFileSync(owner, "utf8");
const restore = () => {
  writeFileSync(owner, original);
  if (existsSync(backup)) rmSync(backup);
};
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => { restore(); process.exit(130); });

const ts = loadTypeScript(pkgRoot);
const mutants = sample(generateMutants(ts, parseSource(ts, owner)));
console.log(`owner ${ownerRel}\ntests ${testFiles.map((f) => relativeTo(root, f)).join(", ")}\nmutants logic ${count("logic")} · copy ${count("copy")} · style ${count("style")}`);

const baseline = runTests();
if (!baseline) fail("baseline run crashed. Fix the test command in config first.");
const failingAtBaseline = Object.entries(baseline).filter(([, status]) => status !== "passed" && status !== "skipped" && status !== "pending");
if (failingAtBaseline.length > 0) fail(`baseline is red:\n${failingAtBaseline.map(([k]) => `  ${k}`).join("\n")}`);
const testKeys = Object.keys(baseline).filter((key) => baseline[key] === "passed");

writeFileSync(backup, original);
const results = [];
try {
  for (const [index, mutant] of mutants.entries()) {
    writeFileSync(owner, original.slice(0, mutant.start) + mutant.replacement + original.slice(mutant.end));
    const run = runTests();
    const killedBy = run ? testKeys.filter((key) => run[key] !== "passed") : null;
    results.push({ ...mutant, killedBy, crashed: run === null });
    if ((index + 1) % 10 === 0) console.log(`${index + 1}/${mutants.length}`);
  }
} finally {
  restore();
}

const report = { owner: ownerRel, testFiles: testFiles.map((f) => relativeTo(root, f)), tests: testKeys, mutants: results };
writeFileSync(resultFile, `${JSON.stringify(report, null, 2)}\n`);
printReport(report);
console.log(`\nwrote ${relativeTo(root, resultFile)}`);

function count(category) {
  return mutants.filter((m) => m.category === category).length;
}

function resolveTestFiles() {
  if (args.tests) return String(args.tests).split(",").map((f) => path.resolve(root, f.trim()));
  const candidates = path.join(stateDir(root), "candidates.json");
  if (!existsSync(candidates)) return [];
  const scan = JSON.parse(readFileSync(candidates, "utf8"));
  return scan.packages.flatMap((p) => p.files).filter((f) => f.owner === ownerRel || f.imports.some((imp) => imp.resolved === ownerRel)).map((f) => path.join(root, f.file));
}

function runTests() {
  const outFile = path.join(outDir, `${slug}.run.json`);
  rmSync(outFile, { force: true });
  const files = testFiles.map((f) => JSON.stringify(path.relative(pkgRoot, f))).join(" ");
  const reporter = pkg.runner === "jest" ? `--json --outputFile=${JSON.stringify(outFile)}` : `--reporter=json --outputFile=${JSON.stringify(outFile)}`;
  spawnSync(`${pkg.runTests} ${files} ${reporter}`, { cwd: pkgRoot, shell: true, stdio: "ignore", timeout: Number(args.timeout ?? 180) * 1000 });
  if (!existsSync(outFile)) return null;
  const json = JSON.parse(readFileSync(outFile, "utf8"));
  rmSync(outFile, { force: true });
  const statuses = {};
  for (const file of json.testResults ?? []) {
    const rel = relativeTo(root, path.resolve(pkgRoot, file.name));
    for (const assertion of file.assertionResults ?? []) statuses[`${rel} > ${assertion.fullName}`] = assertion.status;
  }
  return Object.keys(statuses).length > 0 ? statuses : null;
}

function generateMutants(ts, sf) {
  const out = [];
  const text = sf.getFullText();
  const add = (node, replacement, kind, start = node.getStart(sf), end = node.getEnd()) => {
    out.push({
      category: categoryOf(ts, node, kind),
      line: sf.getLineAndCharacterOfPosition(start).line + 1,
      original: text.slice(start, end).replace(/\s+/g, " ").slice(0, 80),
      replacement,
      start,
      end,
    });
  };
  forEachDescendant(ts, sf, (node) => {
    if (ts.isImportDeclaration(node) || ts.isTypeNode(node) || ts.isInterfaceDeclaration(node) || ts.isTypeAliasDeclaration(node)) return false;
    if (ts.isBinaryExpression(node)) {
      const operator = ts.SyntaxKind[node.operatorToken.kind];
      const swap = OPERATOR_SWAPS[operator];
      const concatenation = operator === "PlusToken" && [node.left, node.right].some((side) => ts.isStringLiteralLike(side) || ts.isTemplateExpression(side));
      if (swap && !concatenation) add(node.operatorToken, swap, "logic");
      for (const side of [node.left, node.right]) {
        if (ts.isStringLiteral(side) && /^(===|!==|==|!=)$/.test(node.operatorToken.getText(sf))) add(side, JSON.stringify("__mutant__"), "logic");
      }
    } else if (ts.isPrefixUnaryExpression(node) && node.operator === ts.SyntaxKind.ExclamationToken) {
      add(node, node.operand.getText(sf), "logic");
    } else if (node.kind === ts.SyntaxKind.TrueKeyword || node.kind === ts.SyntaxKind.FalseKeyword) {
      add(node, node.kind === ts.SyntaxKind.TrueKeyword ? "false" : "true", "logic");
    } else if (ts.isConditionalExpression(node)) {
      add(node, `(${node.condition.getText(sf)}) ? (${node.whenFalse.getText(sf)}) : (${node.whenTrue.getText(sf)})`, "logic");
    } else if (ts.isIfStatement(node)) {
      add(node.expression, `!(${node.expression.getText(sf)})`, "logic");
    } else if (ts.isCaseClause(node) && ts.isStringLiteral(node.expression)) {
      add(node.expression, JSON.stringify("__mutant__"), "logic");
    } else if (ts.isExpressionStatement(node) && ts.isCallExpression(node.expression) && !/^console\./.test(node.expression.expression.getText(sf))) {
      add(node, "void 0;", "logic");
    } else if (ts.isJsxText(node) && /[A-Za-z]{2}/.test(node.text)) {
      const lead = node.text.match(/^\s*/)[0].length;
      const trail = node.text.match(/\s*$/)[0].length;
      add(node, "MUTANT", "copy", node.getStart(sf) + lead, node.getEnd() - trail);
    } else if (ts.isJsxAttribute(node) && node.initializer) {
      const name = node.name.getText(sf);
      const value = node.initializer;
      if (STYLE_ATTRIBUTES.has(name)) add(value, ts.isStringLiteral(value) ? '"mutant"' : "{undefined}", "style");
      else if (COPY_ATTRIBUTE.test(name) && ts.isStringLiteral(value)) add(value, '"MUTANT"', "copy");
      if (STYLE_ATTRIBUTES.has(name)) return false;
    }
  });
  return out.filter((m, i) => out.findIndex((other) => other.start === m.start && other.end === m.end && other.replacement === m.replacement) === i);
}

function categoryOf(ts, node, kind) {
  if (kind !== "logic") return kind;
  for (let parent = node.parent; parent && !ts.isSourceFile(parent); parent = parent.parent) {
    if (ts.isJsxAttribute(parent)) {
      const name = parent.name.getText();
      if (STYLE_ATTRIBUTES.has(name)) return "style";
      if (COPY_ATTRIBUTE.test(name)) return "copy";
    }
  }
  return "logic";
}

function sample(all) {
  const limits = { logic: Number(args["max-logic"] ?? 40), copy: Number(args["max-copy"] ?? 6), style: Number(args["max-style"] ?? 6) };
  const picked = [];
  for (const category of Object.keys(limits)) {
    const pool = all.filter((m) => m.category === category);
    const step = Math.max(1, pool.length / limits[category]);
    for (let i = 0; i < pool.length && picked.filter((m) => m.category === category).length < limits[category]; i += step) picked.push(pool[Math.floor(i)]);
  }
  return picked.map((m, id) => ({ id: `${m.category}-${id}`, ...m }));
}

function summarize(report, dropped = new Set()) {
  const live = report.mutants.filter((m) => !m.crashed);
  const remaining = report.tests.filter((t) => !dropped.has(t));
  const rows = remaining.map((test) => {
    const kills = live.filter((m) => m.killedBy.includes(test));
    const logic = kills.filter((m) => m.category === "logic");
    const unique = logic.filter((m) => m.killedBy.filter((t) => remaining.includes(t)).length === 1);
    const verdict = logic.length === 0 ? (kills.length > 0 ? "change-detector" : "no-kill") : unique.length === 0 ? "redundant" : "unique";
    return { test, logic: logic.length, unique: unique.length, copy: kills.filter((m) => m.category === "copy").length, style: kills.filter((m) => m.category === "style").length, verdict };
  });
  const survivors = live.filter((m) => m.category === "logic" && !m.killedBy.some((t) => remaining.includes(t)));
  return { rows, survivors, live };
}

function printReport(report) {
  const { rows, survivors, live } = summarize(report);
  const crashed = report.mutants.filter((m) => m.crashed).length;
  const logicTotal = live.filter((m) => m.category === "logic").length;
  console.log(`\nlogic mutants killed ${logicTotal - survivors.length}/${logicTotal} · crashed (ignored) ${crashed}`);
  const cover = minimalCover(report.tests, live.filter((m) => m.category === "logic"));
  console.log(`minimal cover: ${cover.size}/${report.tests.length} tests kill every killed logic mutant`);
  console.log("\nverdict          logic unique copy style cover  test");
  for (const r of rows.sort((a, b) => a.logic - b.logic)) {
    console.log(`${r.verdict.padEnd(16)} ${String(r.logic).padStart(5)} ${String(r.unique).padStart(6)} ${String(r.copy).padStart(4)} ${String(r.style).padStart(5)} ${(cover.has(r.test) ? "yes" : "-").padStart(5)}  ${r.test}`);
  }
  if (survivors.length > 0) {
    console.log("\nsurviving logic mutants (no test notices them)");
    for (const m of survivors) console.log(`  L${m.line} ${m.original} → ${m.replacement}`);
  }
}

function minimalCover(tests, logicMutants) {
  const uncovered = new Set(logicMutants.filter((m) => m.killedBy.length > 0).map((m) => m.id));
  const cover = new Set();
  while (uncovered.size > 0) {
    const [best] = tests
      .filter((t) => !cover.has(t))
      .map((t) => [t, logicMutants.filter((m) => uncovered.has(m.id) && m.killedBy.includes(t)).length])
      .sort((a, b) => b[1] - a[1]);
    if (!best || best[1] === 0) break;
    cover.add(best[0]);
    for (const m of logicMutants) if (m.killedBy.includes(best[0])) uncovered.delete(m.id);
  }
  return cover;
}

function reportDrop(report, keys) {
  const unknown = keys.filter((k) => !report.tests.includes(k));
  if (unknown.length > 0) fail(`unknown test keys:\n${unknown.join("\n")}`);
  const before = summarize(report).survivors.map((m) => m.id);
  const after = summarize(report, new Set(keys)).survivors;
  const lost = after.filter((m) => !before.includes(m.id));
  console.log(`dropping ${keys.length} tests`);
  if (lost.length === 0) {
    console.log("safe: remaining tests still kill every logic mutant the full suite killed");
    return;
  }
  console.log(`UNSAFE: ${lost.length} logic mutants would survive`);
  for (const m of lost) console.log(`  L${m.line} ${m.original} → ${m.replacement}  (killed only by ${m.killedBy.filter((t) => keys.includes(t)).join(" | ")})`);
  process.exitCode = 2;
}
