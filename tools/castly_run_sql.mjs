#!/usr/bin/env node
// Run a SQL file on the live Castly (talentflow) database, project guuzgwrdpkoqjmlfiypi.
//
//   node tools/castly_run_sql.mjs <file.sql>               apply it
//   node tools/castly_run_sql.mjs <file.sql> --read-only   check only (the session refuses writes)
//
// Connection: the session pooler and DB password that the nightly backup already uses, read from
// %LOCALAPPDATA%\CastlyBackup\settings.env (override with CASTLY_BACKUP_SETTINGS). The password only
// travels in PGPASSWORD to psql; every line printed here is scrubbed of it. Uses the psql that
// ships with the backup (CastlyBackup\pgsql\bin), stops at the first error (ON_ERROR_STOP).
// Wrap changes in begin; ... commit; so a failure changes nothing, and end with a check SELECT.

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const readOnly = args.includes('--read-only');
const file = args.find((a) => !a.startsWith('--'));
if (!file || !fs.existsSync(file)) {
  console.error('usage: node tools/castly_run_sql.mjs <file.sql> [--read-only]');
  process.exit(2);
}

const HOME = path.join(process.env.LOCALAPPDATA || '', 'CastlyBackup');
const SETTINGS_FILE = process.env.CASTLY_BACKUP_SETTINGS || path.join(HOME, 'settings.env');
const S = {
  CASTLY_DB_HOST: 'aws-0-ap-northeast-1.pooler.supabase.com',
  CASTLY_DB_PORT: '5432',
  CASTLY_DB_USER: 'postgres.guuzgwrdpkoqjmlfiypi',
  CASTLY_DB_NAME: 'postgres',
  CASTLY_PG_BIN: path.join(HOME, 'pgsql', 'bin'),
};
if (!fs.existsSync(SETTINGS_FILE)) {
  console.error(`No settings file at ${SETTINGS_FILE}`);
  process.exit(2);
}
for (const line of fs.readFileSync(SETTINGS_FILE, 'utf8').split(/\r?\n/)) {
  const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
  if (!m) continue;
  let v = m[2];
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
  if (v !== '') S[m[1]] = v;
}
if (!S.CASTLY_DB_PASSWORD) {
  console.error(`CASTLY_DB_PASSWORD is empty in ${SETTINGS_FILE}`);
  process.exit(2);
}

const SECRETS = [S.CASTLY_DB_PASSWORD, S.CASTLY_SECRET_KEY].filter((s) => s && s.length >= 6);
const scrub = (s) => SECRETS.reduce((acc, sec) => acc.split(sec).join('[secret]'), String(s));

const psql = path.join(S.CASTLY_PG_BIN, process.platform === 'win32' ? 'psql.exe' : 'psql');
const psqlArgs = ['-X', '-v', 'ON_ERROR_STOP=1', '-P', 'pager=off'];
if (readOnly) psqlArgs.push('-c', 'set default_transaction_read_only = on');
psqlArgs.push('-f', path.resolve(file));

console.log(`Target: Castly (guuzgwrdpkoqjmlfiypi) · ${readOnly ? 'read-only' : 'APPLY'} · ${path.basename(file)}`);

const child = spawn(psql, psqlArgs, {
  windowsHide: true,
  env: {
    ...process.env,
    PGHOST: S.CASTLY_DB_HOST,
    PGPORT: S.CASTLY_DB_PORT,
    PGUSER: S.CASTLY_DB_USER,
    PGPASSWORD: S.CASTLY_DB_PASSWORD,
    PGDATABASE: S.CASTLY_DB_NAME,
    PGSSLMODE: 'require',
    PGAPPNAME: 'castly-run-sql',
    PGCONNECT_TIMEOUT: '30',
    PGCLIENTENCODING: 'UTF8',
  },
});
child.stdout.on('data', (d) => process.stdout.write(scrub(d)));
child.stderr.on('data', (d) => process.stderr.write(scrub(d)));
const timer = setTimeout(() => { console.error('Stopped after 10 minutes.'); child.kill(); }, 10 * 60 * 1000);
child.on('error', (e) => { clearTimeout(timer); console.error(scrub(e.message)); process.exit(1); });
child.on('close', (code) => { clearTimeout(timer); process.exit(code ?? 1); });
