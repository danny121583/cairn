const fs = require("fs");
const path = require("path");
const { canonicalBody, bodyHash, mergeDocs, validate, audit } = require("./cairn");

const rootDir = path.join(__dirname, "..");
const vectorsDir = path.join(rootDir, "test-vectors");

// 1. Hash Vectors
const hashVectors = JSON.parse(fs.readFileSync(path.join(vectorsDir, "hash-vectors.json"), "utf8"));
for (const vector of hashVectors) {
  const body = canonicalBody(vector.document);
  if (body !== vector.canonical_body) {
    throw new Error(`${vector.name}: canonical body mismatch`);
  }
  const digest = bodyHash(body);
  if (digest !== vector.sha256) {
    throw new Error(`${vector.name}: hash mismatch ${digest} !== ${vector.sha256}`);
  }
}
console.log(`ok ${hashVectors.length} hash vectors`);

// 2. Merge Vectors
const mergeVectors = JSON.parse(fs.readFileSync(path.join(vectorsDir, "merge-vectors.json"), "utf8"));
for (const vector of mergeVectors) {
  const [meta, body, conflicts] = mergeDocs(vector.base, vector.ours, vector.theirs);
  if (meta.description !== vector.expected_description) {
    throw new Error(`${vector.name}: expected description "${vector.expected_description}", got "${meta.description}"`);
  }
  if (JSON.stringify(meta.tags) !== JSON.stringify(vector.expected_tags)) {
    throw new Error(`${vector.name}: tags mismatch`);
  }
  if (JSON.stringify(conflicts) !== JSON.stringify(vector.expected_conflicts)) {
    throw new Error(`${vector.name}: conflicts mismatch`);
  }
  if (conflicts.length === 0 && meta.hash !== bodyHash(body)) {
    throw new Error(`${vector.name}: hash mismatch for merged doc`);
  }
}
console.log(`ok ${mergeVectors.length} merge vectors`);

// 3. Compliance Vectors
const complianceVectors = JSON.parse(fs.readFileSync(path.join(vectorsDir, "compliance-vectors.json"), "utf8"));
for (const vector of complianceVectors) {
  const bundlePath = path.join(rootDir, vector.bundle);
  const results = validate(bundlePath);
  const result = results.find(item => item.path === vector.path);
  if (!result) {
    throw new Error(`${vector.name}: result for path ${vector.path} not found`);
  }
  if (result.valid !== vector.valid) {
    throw new Error(`${vector.name}: expected valid=${vector.valid}, got ${result.valid}. Errors: ${result.errors.join(", ")}`);
  }
  if (vector.expected_error) {
    const hasError = result.errors.some(err => err.includes(vector.expected_error));
    if (!hasError) {
      throw new Error(`${vector.name}: expected error to contain "${vector.expected_error}", got "${result.errors.join(", ")}"`);
    }
  }
  if (vector.valid) {
    const auditResults = audit(bundlePath);
    const auditResult = auditResults.find(item => item.path === vector.path);
    if (!auditResult) {
      throw new Error(`${vector.name}: audit result for path ${vector.path} not found`);
    }
    if (auditResult.level < vector.minimum_level) {
      throw new Error(`${vector.name}: expected level >= ${vector.minimum_level}, got ${auditResult.level}`);
    }
  }
}
console.log(`ok ${complianceVectors.length} compliance vectors`);
