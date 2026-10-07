#!/usr/bin/env node
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  calleeName,
  createResolver,
  forEachDescendant,
  isTestFile,
  lineOf,
  loadConfig,
  loadTypeScript,
  normalize,
  parseArgs,
  parseSource,
  relativeTo,
  repoRoot,
  selectPackages,
  stateDir,
  walkFiles,
} from "./lib.mjs";

const WEIGHTS = {
  "no-assertion": 3,
  "self-compare": 3,
  "sut-computes-expected": 3,
  "render-smoke": 3,
  "static-copy": 3,
  "props-echo": 3,
  "style-assertion": 3,
  "props-capture": 2,
  snapshot: 2,
  "source-grep": 2,
  "duplicate-body": 2,
  skipped: 2,
  "call-echo": 2,
  "conditional-render": 1,
  "call-shape": 1,
  "mock-call-only": 1,
};

const PRESENCE_MATCHERS = new Set([
  "toBeInTheDocument", "toBeVisible", "toHaveTextContent", "toBeTruthy", "toBeDefined", "toBeNull",
  "toBeUndefined", "toHaveLength", "toContainElement", "toHaveAccessibleName", "toBeEmptyDOMElement",
  "toHaveValue", "toHaveDisplayValue", "toHaveAttribute", "toBeDisabled", "toBeEnabled", "toBeChecked",
]);
const MOCK_CALL_MATCHERS = new Set([
  "toHaveBeenCalled", "toHaveBeenCalledWith", "toHaveBeenCalledTimes", "toHaveBeenLastCalledWith",
  "toHaveBeenNthCalledWith", "toBeCalled", "toBeCalledWith", "toBeCalledTimes",
]);
const SNAPSHOT_MATCHERS = new Set(["toMatchSnapshot", "toMatchInlineSnapshot", "toMatchFileSnapshot"]);
const STYLE_ATTRIBUTES = /^(class|style|data-(variant|color|size|theme|active|position|orientation|state|disabled))$/;
const QUERY = /^(get|query|find)(All)?By(Text|Role|LabelText|PlaceholderText|DisplayValue|AltText|Title)$/;
const USER_ACTIONS = /^(click|dblClick|tripleClick|type|keyboard|hover|unhover|clear|selectOptions|deselectOptions|upload|tab|paste|pointer)$/;
const RENDER_CALLS = new Set(["render", "renderHook", "mount", "shallow"]);
const TEST_CALLEES = new Set(["it", "test"]);
const MOCK_CALLEES = new Set(["vi.mock", "vi.doMock", "jest.mock", "jest.doMock"]);
const ASSERTION_HELPER = /^(expect|assert|verify|check)[A-Z_]/;
const UI_MOCK_CATEGORIES = new Set(["component", "design-system", "ui-library"]);
const CONDITIONAL_PARENTS = ["ConditionalExpression", "IfStatement", "CaseClause", "ElementAccessExpression"];
const ABSENCE_MATCHERS = new Set(["toBeNull", "toBeUndefined", "toBeEmptyDOMElement"]);

const args = parseArgs(process.argv.slice(2));
const root = repoRoot();
const config = loadConfig(root);
const output = { generatedAt: new Date().toISOString(), root, packages: [] };

for (const pkg of selectPackages(config, args.package)) {
  const pkgRoot = path.join(root, pkg.root);
  const scanRoot = args.path ? path.resolve(process.cwd(), args.path) : pkgRoot;
  const ts = loadTypeScript(pkgRoot);
  const resolve = createResolver(ts, pkgRoot);
  const designSystemDirs = pkg.designSystem.map((dir) => path.join(root, dir) + path.sep);
  const files = walkFiles(scanRoot, (file) => isTestFile(file, pkg)).sort();
  const scanned = files.map((file) => scanFile(ts, file, { pkg, resolve, designSystemDirs }));
  markDuplicates(scanned);
  for (const file of scanned) {
    for (const test of file.tests) {
      test.score = test.flags.reduce((sum, flag) => sum + flag.weight, 0);
      delete test.bodyKey;
    }
  }
  output.packages.push({ name: pkg.name, root: pkg.root, files: scanned });
}

mkdirSync(stateDir(root), { recursive: true });
const outFile = path.join(stateDir(root), "candidates.json");
writeFileSync(outFile, `${JSON.stringify(output, null, 2)}\n`);
printSummary(output);
console.log(`\nwrote ${relativeTo(root, outFile)}`);

function scanFile(ts, file, { pkg, resolve, designSystemDirs }) {
  const sf = parseSource(ts, file);
  const text = sf.getFullText();
  const imports = collectImports(ts, sf, file, resolve);
  const mocks = collectMocks(ts, sf, file, { pkg, resolve, designSystemDirs });
  const owner = pickOwner(file, imports, mocks);
  const ownerLiterals = owner ? collectOwnerLiterals(ts, owner, resolve) : [];
  const sutNames = new Set(imports.filter((imp) => imp.resolved === owner).flatMap((imp) => imp.names));
  const helpers = collectHelpers(ts, sf);
  const captured = new Map(mocks.flatMap((mock) => mock.captured.map((id) => [id, mock.category])));
  const testNodes = collectTests(ts, sf);
  const outsideTests = stripRanges(text, testNodes.map((t) => t.body), 0);
  const tests = testNodes.map((node) =>
    analyzeTest(ts, sf, node, { outsideTests, ownerLiterals, sutNames, helpers, captured, imports }),
  );
  return {
    file: relativeTo(root, file),
    owner: owner ? relativeTo(root, owner) : null,
    mocks: mocks.map(({ specifier, category, captured: ids }) => ({ specifier, category, captured: ids })),
    imports: imports.filter((imp) => imp.resolved).map((imp) => ({ resolved: relativeTo(root, imp.resolved), names: imp.names })),
    tests,
  };
}

function collectImports(ts, sf, file, resolve) {
  const imports = [];
  for (const statement of sf.statements) {
    if (!ts.isImportDeclaration(statement) || !ts.isStringLiteral(statement.moduleSpecifier)) continue;
    const specifier = statement.moduleSpecifier.text;
    const names = [];
    const clause = statement.importClause;
    if (clause?.name) names.push("default");
    if (clause?.namedBindings && ts.isNamedImports(clause.namedBindings)) {
      for (const element of clause.namedBindings.elements) names.push(element.name.text);
    }
    if (clause?.namedBindings && ts.isNamespaceImport(clause.namedBindings)) names.push("*");
    imports.push({ specifier, resolved: resolve(specifier, file), names, raw: specifier.includes("?raw") });
  }
  return imports;
}

function collectMocks(ts, sf, file, { pkg, resolve, designSystemDirs }) {
  const mocks = [];
  forEachDescendant(ts, sf, (node) => {
    if (!ts.isCallExpression(node) || !MOCK_CALLEES.has(calleeName(ts, node))) return;
    const [target, factory] = node.arguments;
    if (!target || !ts.isStringLiteralLike(target)) return;
    const specifier = target.text;
    const resolved = resolve(specifier, file);
    const captured = [];
    if (factory) {
      forEachDescendant(ts, factory, (inner) => {
        if (ts.isCallExpression(inner) && ts.isIdentifier(inner.expression) && /^mock/i.test(inner.expression.text)) {
          captured.push(inner.expression.text);
        }
      });
    }
    mocks.push({ specifier, resolved, category: mockCategory(specifier, resolved, pkg, designSystemDirs), captured: [...new Set(captured)] });
  });
  return mocks;
}

function mockCategory(specifier, resolved, pkg, designSystemDirs) {
  if (pkg.uiLibraries.some((lib) => specifier === lib || specifier.startsWith(lib.endsWith("/") ? lib : `${lib}/`))) return "ui-library";
  if (!resolved) return "external";
  if (designSystemDirs.some((dir) => resolved.startsWith(dir))) return "design-system";
  if (/\.[jt]sx$/.test(resolved)) return "component";
  return "module";
}

function pickOwner(file, imports, mocks) {
  const mocked = new Set(mocks.map((mock) => mock.resolved).filter(Boolean));
  const local = imports.filter((imp) => imp.resolved && !mocked.has(imp.resolved) && !imp.resolved.includes(`${path.sep}node_modules${path.sep}`));
  const base = path.basename(file).replace(/\.(test|spec)\.[cm]?[jt]sx?$/, "");
  const stem = (p) => path.basename(p).replace(/\.[cm]?[jt]sx?$/, "");
  const testDir = path.dirname(file);
  const sameName = local.find((imp) => stem(imp.resolved) === base);
  if (sameName) return sameName.resolved;
  const indexBesides = local.find((imp) => stem(imp.resolved) === "index" && [testDir, path.dirname(testDir)].includes(path.dirname(imp.resolved)));
  if (indexBesides) return indexBesides.resolved;
  const relative = local.find((imp) => imp.specifier.startsWith("."));
  return relative?.resolved ?? null;
}

function collectOwnerLiterals(ts, owner, resolve) {
  const ownerSf = parseSource(ts, owner);
  const ownerTables = lookupTables(ts, ownerSf);
  const conditionalTags = new Set();
  forEachDescendant(ts, ownerSf, (node) => {
    if ((ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) && isConditional(ts, node, ownerTables)) conditionalTags.add(node.tagName.getText(ownerSf));
  });
  const children = collectImports(ts, ownerSf, owner, resolve)
    .filter((imp) => imp.specifier.startsWith(".") && imp.resolved && !/\.(test|spec)\./.test(imp.resolved))
    .map((imp) => ({ sf: parseSource(ts, imp.resolved), conditional: imp.names.some((name) => conditionalTags.has(name)) }))
    .map((child) => ({ ...child, tables: lookupTables(ts, child.sf) }));
  const literals = [];
  for (const source of [{ sf: ownerSf, conditional: false, tables: ownerTables }, ...children]) {
    forEachDescendant(ts, source.sf, (node) => {
      let text = null;
      if (ts.isJsxText(node)) text = normalize(node.text);
      else if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) text = node.text;
      else if (ts.isTemplateHead(node) || ts.isTemplateMiddle(node) || ts.isTemplateTail(node)) text = node.text;
      if (!text || !/[A-Za-z]{2}/.test(text) || ts.isImportDeclaration(node.parent)) return;
      literals.push({ text, conditional: source.conditional || isConditional(ts, node, source.tables) });
    });
  }
  return literals;
}

function lookupTables(ts, sf) {
  const names = new Set();
  forEachDescendant(ts, sf, (node) => {
    if (ts.isElementAccessExpression(node) && ts.isIdentifier(node.expression)) names.add(node.expression.text);
  });
  return names;
}

function isConditional(ts, node, tables) {
  for (let parent = node.parent; parent && !ts.isSourceFile(parent); parent = parent.parent) {
    if (CONDITIONAL_PARENTS.some((kind) => parent.kind === ts.SyntaxKind[kind])) return true;
    if (ts.isObjectLiteralExpression(parent) && ts.isVariableDeclaration(parent.parent) && ts.isIdentifier(parent.parent.name) && tables.has(parent.parent.name.text)) return true;
    if (ts.isBinaryExpression(parent) && [ts.SyntaxKind.AmpersandAmpersandToken, ts.SyntaxKind.BarBarToken, ts.SyntaxKind.QuestionQuestionToken].includes(parent.operatorToken.kind)) return true;
  }
  return false;
}

function literalSource(query, literals) {
  const hits = literals.filter((literal) => {
    if (query.text !== null) {
      const q = normalize(query.text);
      return q.length > 0 && (literal.text.includes(q) || (literal.text.length >= 4 && q.includes(literal.text)));
    }
    return matches(query, literal.text);
  });
  if (hits.length === 0) return null;
  return hits.every((hit) => !hit.conditional) ? "static" : "conditional";
}

function collectHelpers(ts, sf) {
  const helpers = new Map();
  forEachDescendant(ts, sf, (node) => {
    let name = null;
    let body = null;
    if (ts.isFunctionDeclaration(node) && node.name) {
      name = node.name.text;
      body = node.body;
    } else if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer && (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer))) {
      name = node.name.text;
      body = node.initializer.body;
    }
    if (name && body) helpers.set(name, { body, calls: callNames(ts, body) });
  });
  const flags = new Map([...helpers.keys()].map((name) => [name, { expect: false, render: false, interaction: false }]));
  for (let pass = 0; pass < 3; pass++) {
    for (const [name, { calls }] of helpers) {
      const flag = flags.get(name);
      for (const call of calls) {
        flag.expect ||= call === "expect" || call.startsWith("expect.") || call.startsWith("assert") || flags.get(call)?.expect === true;
        flag.render ||= RENDER_CALLS.has(call) || flags.get(call)?.render === true;
        flag.interaction ||= isInteraction(call) || flags.get(call)?.interaction === true;
      }
    }
  }
  return flags;
}

function callNames(ts, node) {
  const names = [];
  forEachDescendant(ts, node, (child) => {
    if (ts.isCallExpression(child)) names.push(calleeName(ts, child));
  });
  return names;
}

function isInteraction(call) {
  const parts = call.split(".");
  const last = parts[parts.length - 1];
  if (parts[0] === "userEvent" || parts[0] === "fireEvent") return true;
  if (parts.length === 2 && USER_ACTIONS.test(last)) return true;
  if (call === "act" || last === "rerender" || call.startsWith("result.current.")) return true;
  return /^vi\.(advanceTimers|runAllTimers|runOnlyPendingTimers)/.test(call) || /^jest\.(advanceTimers|runAllTimers)/.test(call);
}

function collectTests(ts, sf) {
  const tests = [];
  forEachDescendant(ts, sf, (node) => {
    if (!ts.isCallExpression(node)) return;
    const name = calleeName(ts, node);
    const [rootName, ...modifiers] = name.split(".");
    if (!TEST_CALLEES.has(rootName) || modifiers.includes("each") && !ts.isCallExpression(node.expression)) return;
    const body = [...node.arguments].reverse().find((arg) => ts.isArrowFunction(arg) || ts.isFunctionExpression(arg));
    const title = node.arguments[0];
    if (!body && !modifiers.includes("todo")) return;
    tests.push({
      node,
      body: body ?? node,
      title: title && ts.isStringLiteralLike(title) ? title.text : title ? title.getText(sf) : "<anonymous>",
      skipped: modifiers.some((m) => m === "skip" || m === "todo"),
      ancestors: describeAncestors(ts, sf, node),
    });
    return false;
  });
  return tests;
}

function describeAncestors(ts, sf, node) {
  const titles = [];
  for (let parent = node.parent; parent; parent = parent.parent) {
    if (ts.isCallExpression(parent) && calleeName(ts, parent).split(".")[0] === "describe") {
      const title = parent.arguments[0];
      titles.unshift(title && ts.isStringLiteralLike(title) ? title.text : (title?.getText(sf) ?? ""));
    }
  }
  return titles;
}

function stripRanges(text, nodes, base) {
  const ranges = nodes.map((n) => [n.getStart() - base, n.getEnd() - base]).sort((a, b) => a[0] - b[0]);
  let out = "";
  let cursor = 0;
  for (const [start, end] of ranges) {
    if (start < cursor) continue;
    out += text.slice(cursor, start);
    cursor = end;
  }
  return out + text.slice(cursor);
}

function analyzeTest(ts, sf, testNode, ctx) {
  const { body } = testNode;
  const calls = callNames(ts, body);
  const helperFlags = calls.map((call) => ctx.helpers.get(call)).filter(Boolean);
  const expectations = collectExpectations(ts, sf, body);
  const queries = collectQueries(ts, sf, body);
  const render = calls.some((c) => RENDER_CALLS.has(c)) || helperFlags.some((h) => h.render);
  const interaction = calls.some(isInteraction) || helperFlags.some((h) => h.interaction);
  const helperAssertion = helperFlags.some((h) => h.expect) || calls.some((c) => ASSERTION_HELPER.test(c.split(".").pop()) || c.startsWith("assert"));
  const flags = [];
  const flag = (id, evidence) => flags.push({ id, weight: WEIGHTS[id], evidence });

  if (testNode.skipped) flag("skipped", "test is skipped or todo");
  if (!testNode.skipped && expectations.length === 0 && !helperAssertion) flag("no-assertion", "no expect/assert in body or called helpers");

  for (const e of expectations) {
    if (["toBe", "toEqual", "toStrictEqual"].includes(e.matcher) && e.args.length === 1 && normalize(e.args[0]) === normalize(e.actual)) {
      flag("self-compare", e.text);
    }
    const sutCall = e.argNodes.flatMap((arg) => callsTo(ts, arg, ctx.sutNames));
    const relational = e.actualNode && callsTo(ts, e.actualNode, new Set(sutCall)).length > 0;
    if (sutCall.length > 0 && !relational && !SNAPSHOT_MATCHERS.has(e.matcher)) flag("sut-computes-expected", `${e.text}  ← expected built with ${[...new Set(sutCall)].join(", ")}`);
    if (SNAPSHOT_MATCHERS.has(e.matcher)) flag("snapshot", e.text);
    if (render && isStyleAssertion(e)) flag("style-assertion", e.text);
    if (MOCK_CALL_MATCHERS.has(e.matcher) || /\.mock\.(calls|results)/.test(e.actual)) {
      const rootId = e.actual.split(/[.[(]/)[0];
      const category = ctx.captured.get(rootId);
      if (category && UI_MOCK_CATEGORIES.has(category)) flag("props-capture", `${e.text}  ← ${rootId} records props of a mocked ${category}`);
      else if (category) flag("call-shape", `${e.text}  ← ${rootId} records args of a mocked module`);
    }
  }

  const bodyText = body.getText(sf);
  if (/\breadFile(Sync)?\(/.test(bodyText) || ctx.imports.some((imp) => imp.raw)) flag("source-grep", "reads source text");

  if (render && !interaction && expectations.length > 0) {
    const matchers = expectations.map((e) => e.matcher);
    const only = expectations[0];
    const smoke = expectations.length === 1
      && /^(container|baseElement|asFragment\(\)|view)(\.firstChild)?$/.test(only.actual)
      && ((["toBeTruthy", "toBeDefined", "toBeInTheDocument"].includes(only.matcher) && !only.not) || (only.matcher === "toBeNull" && only.not) || (only.matcher === "toThrow" && only.not));
    if (smoke) {
      flag("render-smoke", only.text);
    } else if (matchers.every((m) => PRESENCE_MATCHERS.has(m))) {
      const searchable = stripRanges(bodyText, queries.map((q) => q.node), body.getStart(sf)) + ctx.outsideTests;
      const sources = queries.map((q) => ({ q, owner: literalSource(q, ctx.ownerLiterals), inTest: matches(q, searchable) }));
      const staticCopy = sources.filter((s) => s.owner === "static").map((s) => s.q.label);
      const echoed = sources.filter((s) => s.owner === null && s.inTest).map((s) => s.q.label);
      const absence = expectations.some((e) => e.not || ABSENCE_MATCHERS.has(e.matcher));
      const branchy = absence || sources.length === 0 || sources.some((s) => s.owner === "conditional" || (s.owner === null && !s.inTest));
      if (!branchy && staticCopy.length > 0) flag("static-copy", `queries unconditional JSX copy: ${staticCopy.join(", ")}`);
      if (!branchy && echoed.length > 0) flag("props-echo", `asserts values the test file itself supplies: ${echoed.join(", ")}`);
      if (branchy) flag("conditional-render", `no interaction; presence checks on a rendered branch: ${matchers.join(", ")}`);
    } else if (matchers.every((m) => MOCK_CALL_MATCHERS.has(m)) && !flags.some((f) => f.id === "props-capture")) {
      const echoedArgs = expectations.flatMap((e) => e.args).flatMap((arg) => [...arg.matchAll(/["'`]([^"'`]{3,})["'`]/g)].map((m) => m[1]))
        .filter((literal) => literalSource({ text: literal, regex: null }, ctx.ownerLiterals) === "static");
      if (echoedArgs.length > 0) flag("call-echo", `asserts a mock was called with literals copied from source: ${[...new Set(echoedArgs)].join(", ")}`);
      else flag("mock-call-only", "render triggers only mock-call assertions");
    }
  }

  return {
    name: testNode.title,
    fullName: [...testNode.ancestors, testNode.title].join(" "),
    line: lineOf(sf, testNode.node),
    endLine: sf.getLineAndCharacterOfPosition(testNode.node.getEnd()).line + 1,
    render,
    interaction,
    matchers: expectations.map((e) => (e.not ? `not.${e.matcher}` : e.matcher)),
    flags: dedupeFlags(flags),
    bodyKey: normalize(bodyText.replace(/^[^{]*{/, "")),
  };
}

function dedupeFlags(flags) {
  const seen = new Map();
  for (const f of flags) {
    if (!seen.has(f.id)) seen.set(f.id, { ...f, evidence: [f.evidence] });
    else if (seen.get(f.id).evidence.length < 3) seen.get(f.id).evidence.push(f.evidence);
  }
  return [...seen.values()];
}

function collectExpectations(ts, sf, body) {
  const out = [];
  forEachDescendant(ts, body, (node) => {
    if (!ts.isCallExpression(node) || !ts.isPropertyAccessExpression(node.expression)) return;
    let expr = node.expression;
    const chain = [];
    while (ts.isPropertyAccessExpression(expr)) {
      chain.unshift(expr.name.text);
      expr = expr.expression;
    }
    if (!ts.isCallExpression(expr)) return;
    const root = calleeName(ts, expr);
    if (root !== "expect" && root !== "expect.soft") return;
    const matcher = chain[chain.length - 1];
    out.push({
      matcher,
      not: chain.includes("not"),
      actual: expr.arguments[0]?.getText(sf) ?? "",
      actualNode: expr.arguments[0],
      args: node.arguments.map((a) => a.getText(sf)),
      argNodes: [...node.arguments],
      text: normalize(node.getText(sf)).slice(0, 160),
    });
  });
  return out;
}

function callsTo(ts, node, names) {
  const hits = [];
  const visit = (child) => {
    if (ts.isCallExpression(child) && ts.isIdentifier(child.expression) && names.has(child.expression.text)) hits.push(child.expression.text);
  };
  visit(node);
  forEachDescendant(ts, node, visit);
  return hits;
}

function isStyleAssertion(e) {
  if (e.matcher === "toHaveStyle" || e.matcher === "toHaveClass") return true;
  if (e.matcher === "toHaveAttribute" && STYLE_ATTRIBUTES.test(e.args[0]?.replace(/^["'`]|["'`]$/g, "") ?? "")) return true;
  return /\.(className|classList|style)\b|getComputedStyle/.test(e.actual);
}

function collectQueries(ts, sf, body) {
  const out = [];
  forEachDescendant(ts, body, (node) => {
    if (!ts.isCallExpression(node)) return;
    const name = calleeName(ts, node).split(".").pop();
    const match = QUERY.exec(name);
    if (!match) return;
    let literal = match[3] === "Role" ? roleName(ts, node.arguments[1]) : node.arguments[0];
    if (!literal) return;
    if (ts.isStringLiteralLike(literal)) out.push({ node, label: JSON.stringify(literal.text), text: literal.text, regex: null });
    else if (ts.isRegularExpressionLiteral(literal)) {
      const [, source, flagsText] = /^\/(.*)\/([a-z]*)$/s.exec(literal.text) ?? [];
      if (source !== undefined) out.push({ node, label: literal.text, text: null, regex: { source, flags: flagsText } });
    }
  });
  return out;
}

function roleName(ts, options) {
  if (!options || !ts.isObjectLiteralExpression(options)) return null;
  const prop = options.properties.find((p) => ts.isPropertyAssignment(p) && p.name.getText() === "name");
  return prop?.initializer ?? null;
}

function matches(query, haystack) {
  if (!haystack) return false;
  if (query.text !== null) return query.text.length > 0 && haystack.includes(query.text);
  try {
    const source = query.regex.source.replace(/^\^|\$$/g, "");
    return new RegExp(source, query.regex.flags.replace("g", "")).test(haystack);
  } catch {
    return false;
  }
}

function markDuplicates(files) {
  const byKey = new Map();
  for (const file of files) {
    for (const test of file.tests) {
      if (test.bodyKey.length < 40) continue;
      const list = byKey.get(test.bodyKey) ?? [];
      list.push({ file: file.file, test });
      byKey.set(test.bodyKey, list);
    }
  }
  for (const list of byKey.values()) {
    if (list.length < 2) continue;
    const [first, ...rest] = list;
    for (const dup of rest) {
      dup.test.flags.push({ id: "duplicate-body", weight: WEIGHTS["duplicate-body"], evidence: [`same body as ${first.file}:${first.test.line} "${first.test.name}"`] });
    }
  }
}

function printSummary(result) {
  for (const pkg of result.packages) {
    const tests = pkg.files.flatMap((f) => f.tests);
    const flagged = tests.filter((t) => t.score >= config.minScore);
    const byDetector = new Map();
    for (const t of tests) for (const f of t.flags) byDetector.set(f.id, (byDetector.get(f.id) ?? 0) + 1);
    const byMock = new Map();
    for (const f of pkg.files) for (const m of f.mocks) byMock.set(m.category, (byMock.get(m.category) ?? 0) + 1);
    const renderTests = tests.filter((t) => t.render);
    console.log(`\n## ${pkg.name} (${pkg.root})`);
    console.log(`files ${pkg.files.length} · tests ${tests.length} · render tests ${renderTests.length} · flagged (score>=${config.minScore}) ${flagged.length}`);
    console.log("\ndetector              tests");
    for (const [id, count] of [...byDetector].sort((a, b) => b[1] - a[1])) console.log(`${id.padEnd(22)}${count}`);
    console.log("\nvi.mock category      mocks");
    for (const [category, count] of [...byMock].sort((a, b) => b[1] - a[1])) console.log(`${category.padEnd(22)}${count}`);
    const topFiles = pkg.files
      .map((f) => ({ file: f.file, flagged: f.tests.filter((t) => t.score >= config.minScore).length, total: f.tests.length }))
      .filter((f) => f.flagged > 0)
      .sort((a, b) => b.flagged - a.flagged)
      .slice(0, 15);
    console.log("\ntop files (flagged/total)");
    for (const f of topFiles) console.log(`${String(f.flagged).padStart(3)}/${String(f.total).padEnd(4)} ${f.file}`);
  }
}
