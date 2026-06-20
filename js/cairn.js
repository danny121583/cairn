#!/usr/bin/env node
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

const SCALAR_FIELDS = ["title", "description", "status", "timestamp", "type"];
const FORBIDDEN = new Set(["memory", "embeddings", "workflow", "permissions"]);

function normalizeText(text) {
  return String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function parseFrontmatter(text) {
  const normalized = normalizeText(text);
  if (!normalized.startsWith("---\n")) {
    return [{}, normalized];
  }
  const end = normalized.indexOf("\n---\n", 4);
  if (end === -1) {
    return [{}, normalized];
  }
  try {
    const meta = yaml.load(normalized.slice(4, end)) || {};
    return [meta, normalized.slice(end + 5)];
  } catch (e) {
    return [{}, normalized];
  }
}

function canonicalBody(text) {
  return parseFrontmatter(text)[1];
}

function bodyHash(body) {
  return crypto.createHash("sha256").update(normalizeText(body), "utf8").digest("hex");
}

function parseFile(filePath) {
  const [frontmatter, body] = parseFrontmatter(fs.readFileSync(filePath, "utf8"));
  return {
    path: filePath,
    type: frontmatter.type,
    title: frontmatter.title,
    aliases: frontmatter.aliases || [],
    relations: frontmatter.relations || [],
    frontmatter,
    body,
  };
}

// Deterministic Merging Section 8

function parseTimestamp(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  try {
    const raw = String(value);
    const d = new Date(raw.endsWith("Z") ? raw : raw.replace(/([+-]\d{2}):(\d{2})$/, "$1:$2"));
    return isNaN(d.getTime()) ? null : d;
  } catch (e) {
    return null;
  }
}

function laterSide(oursMeta, theirsMeta) {
  const oursTs = parseTimestamp(oursMeta.timestamp);
  const theirsTs = parseTimestamp(theirsMeta.timestamp);
  if (oursTs && theirsTs) {
    if (oursTs.getTime() > theirsTs.getTime()) return "ours";
    if (theirsTs.getTime() > oursTs.getTime()) return "theirs";
  }
  return null;
}

function mergeUniqueList(...lists) {
  const merged = new Set();
  for (const list of lists) {
    if (Array.isArray(list)) {
      for (const item of list) {
        if (item !== undefined && item !== null) {
          merged.add(String(item).normalize("NFC"));
        }
      }
    }
  }
  return Array.from(merged).sort();
}

function relationKey(rel) {
  if (!rel) return "";
  const type = String(rel.type || "").normalize("NFC");
  const target = String(rel.target || "").normalize("NFC");
  return JSON.stringify([type, target]);
}

function conflictValue(field, ours, theirs) {
  return `<<<<<<< ours ${field}\n${ours}\n=======\n${theirs}\n>>>>>>> theirs ${field}`;
}

function mergeScalar(field, base, ours, theirs, side, conflicts) {
  const baseVal = base[field];
  const oursVal = ours.hasOwnProperty(field) ? ours[field] : baseVal;
  const theirsVal = theirs.hasOwnProperty(field) ? theirs[field] : baseVal;
  if (oursVal === theirsVal) return oursVal;
  if (oursVal === baseVal) return theirsVal;
  if (theirsVal === baseVal) return oursVal;
  if (side === "ours") return oursVal;
  if (side === "theirs") return theirsVal;
  conflicts.push(`scalar conflict: ${field}`);
  return conflictValue(field, oursVal, theirsVal);
}

function mergeRelation(baseRel, oursRel, theirsRel, side, conflicts) {
  if (JSON.stringify(oursRel) === JSON.stringify(theirsRel)) return oursRel;
  if (JSON.stringify(oursRel) === JSON.stringify(baseRel)) return theirsRel;
  if (JSON.stringify(theirsRel) === JSON.stringify(baseRel)) return oursRel;
  if (side === "ours") return oursRel;
  if (side === "theirs") return theirsRel;

  const merged = Object.assign({}, baseRel || {});
  const allRels = [oursRel || {}, theirsRel || {}];
  const keys = new Set();
  for (const r of allRels) {
    for (const k of Object.keys(r)) keys.add(k);
  }

  for (const key of keys) {
    const baseVal = (baseRel || {})[key];
    const oursVal = (oursRel || {})[key];
    const theirsVal = (theirsRel || {})[key];
    if (oursVal === theirsVal) {
      merged[key] = oursVal;
    } else if (oursVal === baseVal) {
      merged[key] = theirsVal;
    } else if (theirsVal === baseVal) {
      merged[key] = oursVal;
    } else {
      const type = (oursRel || theirsRel || {}).type || "";
      const target = (oursRel || theirsRel || {}).target || "";
      conflicts.push(`relation conflict: ${type},${target}.${key}`);
      merged[key] = conflictValue(`relation.${key}`, oursVal || "", theirsVal || "");
    }
  }
  return merged;
}

function mergeRelations(base, ours, theirs, side, conflicts) {
  const baseMap = new Map();
  for (const r of base.relations || []) {
    const k = relationKey(r);
    if (k && k !== JSON.stringify(["", ""])) baseMap.set(k, r);
  }
  const oursMap = new Map();
  for (const r of ours.relations || []) {
    const k = relationKey(r);
    if (k && k !== JSON.stringify(["", ""])) oursMap.set(k, r);
  }
  const theirsMap = new Map();
  for (const r of theirs.relations || []) {
    const k = relationKey(r);
    if (k && k !== JSON.stringify(["", ""])) theirsMap.set(k, r);
  }

  const allKeys = Array.from(new Set([...baseMap.keys(), ...oursMap.keys(), ...theirsMap.keys()])).sort();
  const output = [];
  for (const key of allKeys) {
    const rel = mergeRelation(baseMap.get(key), oursMap.get(key), theirsMap.get(key), side, conflicts);
    if (rel) output.push(rel);
  }
  return output;
}

function mergeBody(baseBody, oursBody, theirsBody, conflicts) {
  const normBase = normalizeText(baseBody);
  const normOurs = normalizeText(oursBody);
  const normTheirs = normalizeText(theirsBody);
  if (normOurs === normTheirs) return oursBody;
  if (normOurs === normBase) return theirsBody;
  if (normTheirs === normBase) return oursBody;
  conflicts.push("body conflict");
  return `<<<<<<< ours\n${oursBody}\n=======\n${theirsBody}\n>>>>>>> theirs\n`;
}

function mergeDocs(baseText, oursText, theirsText) {
  const [baseMeta, baseBody] = parseFrontmatter(baseText);
  const [oursMeta, oursBody] = parseFrontmatter(oursText);
  const [theirsMeta, theirsBody] = parseFrontmatter(theirsText);
  const conflicts = [];
  const side = laterSide(oursMeta, theirsMeta);

  const merged = {};
  for (const field of SCALAR_FIELDS) {
    const val = mergeScalar(field, baseMeta, oursMeta, theirsMeta, side, conflicts);
    if (val !== undefined && val !== null) {
      merged[field] = val;
    }
  }

  const tags = mergeUniqueList(baseMeta.tags, oursMeta.tags, theirsMeta.tags);
  if (tags.length) merged.tags = tags;

  const aliases = mergeUniqueList(baseMeta.aliases, oursMeta.aliases, theirsMeta.aliases);
  if (aliases.length) merged.aliases = aliases;

  const relations = mergeRelations(baseMeta, oursMeta, theirsMeta, side, conflicts);
  if (relations.length) merged.relations = relations;

  const body = mergeBody(baseBody, oursBody, theirsBody, conflicts);
  if (conflicts.length === 0) {
    merged.hash = bodyHash(body);
  } else {
    delete merged.hash;
  }
  return [merged, body, conflicts];
}

function dumpDoc(meta, body) {
  const frontmatter = yaml.dump(meta, { sortKeys: false, lineWidth: -1 }).trim();
  return `---\n${frontmatter}\n---\n${body}`;
}

// Validation Section 9

function getFiles(dir, rootDir = dir) {
  const ignored = new Set(["node_modules", ".git", "cairn-runs", "corpus-runs", "fixtures", "build", "dist", ".venv", "venv"]);
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const filePath = path.join(dir, file);
    const relParts = path.relative(rootDir, filePath).split(path.sep);
    if (relParts.some(part => ignored.has(part))) {
      continue;
    }
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results.push(...getFiles(filePath, rootDir));
    } else if (filePath.endsWith(".md")) {
      results.push(filePath);
    }
  }
  return results;
}

function rel(root, filePath) {
  return path.relative(path.resolve(root), path.resolve(filePath)).split(path.sep).join("/");
}

function localTarget(root, current, target, aliases) {
  if (!target || String(target).startsWith("cairn://")) {
    return true;
  }
  const rootResolved = path.resolve(root);
  const currentDir = path.dirname(path.resolve(current));
  const candidates = [
    path.resolve(currentDir, target),
    path.resolve(rootResolved, target)
  ];
  for (const candidate of candidates) {
    const relToRoot = path.relative(rootResolved, candidate);
    const isInside = !relToRoot.startsWith("..") && !path.isAbsolute(relToRoot);
    if (isInside || candidate === rootResolved) {
      if (fs.existsSync(candidate) || aliases.has(rel(root, candidate))) {
        return true;
      }
    }
  }
  return aliases.has(String(target));
}

function validate(root) {
  const docs = new Map();
  const aliases = new Map();
  const filePaths = getFiles(root);

  for (const filePath of filePaths) {
    const text = fs.readFileSync(filePath, "utf8");
    const [meta, body] = parseFrontmatter(text);
    const isConcept = text.replace(/\r\n/g, "\n").startsWith("---\n") && (meta.type || meta.title);
    if (!isConcept) continue;

    const key = rel(root, filePath);
    docs.set(key, { path: filePath, meta, body });
    for (const alias of meta.aliases || []) {
      if (!aliases.has(alias)) {
        aliases.set(alias, []);
      }
      aliases.get(alias).push(key);
    }
  }

  const results = [];
  const sortedKeys = Array.from(docs.keys()).sort();
  for (const key of sortedKeys) {
    const { path: filePath, meta, body } = docs.get(key);
    const errors = [];
    const warnings = [];

    if (!meta.type) errors.push("missing type");
    if (!meta.title) errors.push("missing title");

    for (const field of Object.keys(meta)) {
      if (FORBIDDEN.has(field)) {
        errors.push("contains forbidden core fields");
      }
    }

    const schema = meta.type;
    if (schema && !String(schema).startsWith("cairn://") && !docs.has(schema)) {
      errors.push(`type does not resolve: ${schema}`);
    }

    for (const [alias, owners] of aliases.entries()) {
      if (owners.length > 1 && owners.includes(key)) {
        errors.push(`ambiguous alias: ${alias}`);
      }
    }

    for (const relation of meta.relations || []) {
      if (!relation.type || !relation.target) {
        errors.push("relation missing type or target");
      }
      if (relation.confidence !== "declared" && relation.confidence !== "inferred") {
        errors.push(`relation missing valid confidence: ${relation.target}`);
      }
      if (!localTarget(root, filePath, relation.target, aliases)) {
        errors.push(`broken relation target: ${relation.target}`);
      }
    }

    if (meta.hash) {
      const digest = bodyHash(body);
      if (digest !== meta.hash) {
        errors.push("hash mismatch");
      }
    }

    results.push({
      path: key,
      valid: errors.length === 0,
      errors,
      warnings
    });
  }
  return results;
}

// Auditing Section 9

function resolves(root, current, target, docs, aliases) {
  if (!target || String(target).startsWith("cairn://")) {
    return true;
  }
  const rootResolved = path.resolve(root);
  const currentDir = path.dirname(path.resolve(current));
  const candidates = [
    path.resolve(currentDir, target),
    path.resolve(rootResolved, target)
  ];
  for (const candidate of candidates) {
    const relToRoot = path.relative(rootResolved, candidate);
    const isInside = !relToRoot.startsWith("..") && !path.isAbsolute(relToRoot);
    if (isInside || candidate === rootResolved) {
      const key = rel(root, candidate);
      if (docs.has(key) || aliases.has(key)) {
        return true;
      }
    }
  }
  return docs.has(String(target)) || aliases.has(String(target));
}

function hasRelations(meta) {
  return (meta.relations || []).some(r => r.type && r.target);
}

function score(root, key, docs, aliases) {
  const { path: filePath, meta, body } = docs.get(key);
  let level = 0;
  const notes = [];

  if (meta.type && meta.title) {
    level = 1;
  } else {
    return [0, ["missing type or title"]];
  }

  if (meta.description && meta.status && meta.tags) {
    level = 2;
  } else {
    notes.push("Level 2 requires description, status, and tags");
  }

  if (level === 2 && hasRelations(meta)) {
    level = 3;
  } else if (level >= 2) {
    notes.push("Level 3 requires typed relations where relevant");
  }

  if (level === 3 && docs.has(meta.type)) {
    level = 4;
  } else if (level >= 3) {
    notes.push("Level 4 requires type to resolve to a schema concept");
  }

  const relationErrors = [];
  for (const rel of meta.relations || []) {
    const target = rel.target;
    if (rel.confidence !== "declared" && rel.confidence !== "inferred") {
      relationErrors.push(`missing confidence: ${target}`);
    }
    if (target && !resolves(root, filePath, target, docs, aliases)) {
      relationErrors.push(`broken relation: ${target}`);
    }
  }

  const aliasErrors = [];
  for (const [alias, owners] of aliases.entries()) {
    if (owners.includes(key) && owners.length > 1) {
      aliasErrors.push(alias);
    }
  }

  if (level === 4 && relationErrors.length === 0 && aliasErrors.length === 0) {
    level = 5;
  } else if (level >= 4) {
    notes.push(...relationErrors);
    notes.push(...aliasErrors.map(a => `ambiguous alias: ${a}`));
  }

  if (level === 5 && meta.hash) {
    const digest = bodyHash(body);
    if (digest === meta.hash) {
      level = 6;
    } else {
      notes.push("hash mismatch");
    }
  } else if (level >= 5) {
    notes.push("Level 6 requires verified hash");
  }

  return [level, notes];
}

function audit(root) {
  const rubricPath = path.join(root, "schemas", "audit-rubric.md");
  if (!fs.existsSync(rubricPath)) {
    throw new Error("missing published rubric: schemas/audit-rubric.md");
  }

  const docs = new Map();
  const aliases = new Map();
  const filePaths = getFiles(root);

  for (const filePath of filePaths) {
    const text = fs.readFileSync(filePath, "utf8");
    const [meta, body] = parseFrontmatter(text);
    const isConcept = text.replace(/\r\n/g, "\n").startsWith("---\n") && (meta.type || meta.title);
    if (!isConcept) continue;

    const key = rel(root, filePath);
    docs.set(key, { path: filePath, meta, body });
    for (const alias of meta.aliases || []) {
      if (!aliases.has(alias)) {
        aliases.set(alias, []);
      }
      aliases.get(alias).push(key);
    }
  }

  const results = [];
  const sortedKeys = Array.from(docs.keys()).sort();
  for (const key of sortedKeys) {
    const [level, notes] = score(root, key, docs, aliases);
    results.push({
      path: key,
      level,
      notes
    });
  }
  return results;
}

function main(argv) {
  const [command, ...args] = argv;
  if (command === "parse") {
    for (const file of args) {
      console.log(JSON.stringify(parseFile(file), null, 2));
    }
    return 0;
  }
  if (command === "hash") {
    for (const file of args) {
      console.log(bodyHash(canonicalBody(fs.readFileSync(file, "utf8"))));
    }
    return 0;
  }
  console.error("usage: cairn-js <parse|hash> <file...>");
  return 2;
}

if (require.main === module) {
  process.exitCode = main(process.argv.slice(2));
}

module.exports = {
  parseFrontmatter,
  canonicalBody,
  bodyHash,
  parseFile,
  mergeDocs,
  validate,
  score,
  audit,
  dumpDoc,
  main
};
