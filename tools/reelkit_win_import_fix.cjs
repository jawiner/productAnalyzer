// Works around a reelkit-cli bug on Windows (seen in 0.19.1): `reelkit preview` / `render` start
// their worker with `node --import C:\...\tsx\dist\loader.mjs ...`, and Node reads the drive
// letter "C:" as a URL scheme (ERR_UNSUPPORTED_ESM_URL_SCHEME), so nothing renders.
//
// This preload changes nothing on disk. It wraps child_process.execFile so that a Windows path
// given to --import becomes a file:// URL, then syncs the ESM view of the builtin so
// `import { execFile } from "node:child_process"` in reelkit sees the wrapper too.
//
// Use it for every reelkit command that renders (Git Bash):
//   NODE_OPTIONS="--require C:/Users/97254/wat-framework/tools/reelkit_win_import_fix.cjs" reelkit preview
// Drop it once reelkit passes a URL there itself.

const cp = require("node:child_process");
const { pathToFileURL } = require("node:url");
const { promisify } = require("node:util");
const { syncBuiltinESMExports } = require("node:module");

const original = cp.execFile;

function fixArgs(args) {
  if (!Array.isArray(args)) return args;
  const i = args.indexOf("--import");
  if (i < 0 || typeof args[i + 1] !== "string" || !/^[A-Za-z]:[\\/]/.test(args[i + 1])) return args;
  const out = args.slice();
  out[i + 1] = pathToFileURL(out[i + 1]).href;
  return out;
}

function execFile(file, args, ...rest) {
  return original.call(this, file, fixArgs(args), ...rest);
}

// What promisify(execFile) returns: a promise of { stdout, stderr }, rejecting with both attached.
execFile[promisify.custom] = (file, args, options) =>
  new Promise((resolve, reject) => {
    execFile(file, args, options, (err, stdout, stderr) => {
      if (err) {
        err.stdout = stdout;
        err.stderr = stderr;
        reject(err);
      } else resolve({ stdout, stderr });
    });
  });

cp.execFile = execFile;
syncBuiltinESMExports();
