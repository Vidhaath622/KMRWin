import { AuditReceipt } from "./types";

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.trim();
  const out = new Uint8Array(clean.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

function base64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) {
    out[i] = bin.charCodeAt(i);
  }
  return out;
}

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await window.crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") {
    return false;
  }
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((item, i) => deepEqual(item, b[i]));
  }
  const objA = a as Record<string, unknown>;
  const objB = b as Record<string, unknown>;
  const keysA = Object.keys(objA);
  const keysB = Object.keys(objB);
  if (keysA.length !== keysB.length) return false;
  return keysA.every((k) => Object.prototype.hasOwnProperty.call(objB, k) && deepEqual(objA[k], objB[k]));
}

export interface BrowserVerificationResult {
  valid: boolean;
  engine: "WebCrypto-Ed25519";
  checks: {
    payloadMatchesCanonicalJson: boolean;
    sha256DigestMatches: boolean;
    ed25519SignatureValid: boolean;
    correctionChainLinksIntact: boolean;
  };
  computedSha256: string;
  failures: string[];
}

export async function verifyReceiptInBrowser(
  receipt: AuditReceipt
): Promise<BrowserVerificationResult> {
  const failures: string[] = [];
  const checks = {
    payloadMatchesCanonicalJson: false,
    sha256DigestMatches: false,
    ed25519SignatureValid: false,
    correctionChainLinksIntact: false,
  };

  // 1. Verify structured payload equals canonical signed JSON
  try {
    const parsed = JSON.parse(receipt.canonical_payload);
    if (deepEqual(parsed, receipt.payload)) {
      checks.payloadMatchesCanonicalJson = true;
    } else {
      failures.push("Displayed payload object diverges from signed canonical JSON string.");
    }
  } catch {
    failures.push("canonical_payload is not valid JSON.");
  }

  // 2. Verify SHA-256 digest in WebCrypto
  const computedSha256 = await sha256Hex(receipt.canonical_payload);
  if (computedSha256 === receipt.payload_sha256) {
    checks.sha256DigestMatches = true;
  } else {
    failures.push(
      `SHA-256 mismatch: receipt claims ${receipt.payload_sha256.slice(0, 14)}..., browser computed ${computedSha256.slice(0, 14)}...`
    );
  }

  // 3. Verify Ed25519 digital signature natively in browser via SubtleCrypto
  try {
    const spkiBytes = base64ToBytes(receipt.public_key_spki_b64);
    const sigBytes = hexToBytes(receipt.signature_hex);
    const msgBytes = new TextEncoder().encode(receipt.canonical_payload);

    const pubKey = await window.crypto.subtle.importKey(
      "spki",
      spkiBytes.buffer as ArrayBuffer,
      { name: "Ed25519" },
      false,
      ["verify"]
    );
    const sigOk = await window.crypto.subtle.verify(
      { name: "Ed25519" },
      pubKey,
      sigBytes.buffer as ArrayBuffer,
      msgBytes.buffer as ArrayBuffer
    );
    if (sigOk) {
      checks.ed25519SignatureValid = true;
    } else {
      failures.push("WebCrypto Ed25519 signature verification rejected payload bytes.");
    }
  } catch (err) {
    failures.push(`WebCrypto Ed25519 check error: ${String(err)}`);
  }

  // 4. Verify append-only correction log prev_hash linkage & head hash binding
  let prev = "0".repeat(64);
  let linksOk = true;
  for (let i = 0; i < receipt.correction_history.length; i++) {
    const ev = receipt.correction_history[i];
    if (ev.seq !== i + 1 || ev.prev_hash !== prev) {
      linksOk = false;
      failures.push(`Broken hash chain link at correction event ${ev.event_id}.`);
      break;
    }
    prev = ev.event_hash;
  }
  const signedHead = (receipt.payload as Record<string, unknown>)["correction_log_head_hash"];
  if (linksOk && (receipt.correction_history.length === 0 || signedHead === prev)) {
    checks.correctionChainLinksIntact = true;
  } else if (linksOk) {
    failures.push("Correction log head hash does not match signed receipt head hash.");
  }

  return {
    valid: Object.values(checks).every(Boolean),
    engine: "WebCrypto-Ed25519",
    checks,
    computedSha256,
    failures,
  };
}
