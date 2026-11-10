#!/usr/bin/env node
// Reads a project's intake-spec.json (written by hand, or by Claude while building the site) and
// pushes it to Intake Studio's /api/skill-sync — no scanning, no Anthropic API call. Intended for
// projects where the developer already knows what's placeholder because they built it that way.
//
// Usage:
//   node tools/sync_intake_spec.js <project-dir> [--base-url http://localhost:8080] [--project-id <uuid>]
//
// <project-dir>/intake-spec.json shape:
// {
//   "name": "Studio North",
//   "client_name": "Inbar Kandel",
//   "subject_type": "interior_design",
//   "brand_accent_color": "#93A883",
//   "brand_font": "Cormorant Garamond",
//   "brand_direction": "rtl",
//   "items": [
//     { "category": "Contact info", "title": "...", "detail": "...",
//       "current_placeholder": "...", "severity": "launch_blocking", "page_path": "index.html" }
//   ]
// }

import fs from "node:fs";
import path from "node:path";

function readEnvVar(envPath, key) {
  if (!fs.existsSync(envPath)) return null;
  const text = fs.readFileSync(envPath, "utf8");
  const m = text.match(new RegExp(`^${key}=(.*)$`, "m"));
  return m ? m[1].trim() : null;
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--base-url") args.baseUrl = argv[++i];
    else if (argv[i] === "--project-id") args.projectId = argv[++i];
    else args._.push(argv[i]);
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectDir = args._[0];
  if (!projectDir) {
    console.error("Usage: node tools/sync_intake_spec.js <project-dir> [--base-url URL] [--project-id UUID]");
    process.exit(1);
  }

  const specPath = path.join(projectDir, "intake-spec.json");
  if (!fs.existsSync(specPath)) {
    console.error(`No intake-spec.json found at ${specPath}`);
    process.exit(1);
  }
  const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  if (!Array.isArray(spec.items) || spec.items.length === 0) {
    console.error("intake-spec.json must have a non-empty items[] array");
    process.exit(1);
  }

  const baseUrl = args.baseUrl || "http://localhost:8080";
  const intakeStudioEnv = path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]):/, "$1:")), "..", "internal", "intake-studio", ".env");
  const token = process.env.INTAKE_API_TOKEN || readEnvVar(intakeStudioEnv, "INTAKE_API_TOKEN");
  if (!token) {
    console.error("INTAKE_API_TOKEN not found (set it in the environment or in intake-studio/.env)");
    process.exit(1);
  }

  const body = {
    ...(args.projectId ? { project_id: args.projectId } : { name: spec.name }),
    client_name: spec.client_name,
    brand_accent_color: spec.brand_accent_color,
    brand_font: spec.brand_font,
    brand_direction: spec.brand_direction,
    subject_type: spec.subject_type,
    notify_email: spec.notify_email,
    items: spec.items,
  };

  const res = await fetch(`${baseUrl}/api/skill-sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    console.error("Sync failed:", res.status, data.error || data);
    process.exit(1);
  }

  console.log(`Synced ${spec.items.length} items (added ${data.added}, updated ${data.updated}, removed ${data.removed}).`);
  console.log(`Client link:  ${data.share_url}`);
  console.log(`Editor link:  ${data.editor_url}`);
}

main();
