import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";

const DATA_DIR = process.env.DATA_DIR || "/data";
const READY_FILE = path.join(DATA_DIR, "payload.ready");
const ACK_FILE = path.join(DATA_DIR, "ack");

async function exists(p) {
  try { await fsp.access(p, fs.constants.F_OK); return true; } catch { return false; }
}

async function consumeReadyAndAck() {
  // consume the entire file in 1 MiB chunks
  const fh = await fsp.open(READY_FILE, "r");
  try {
    const buf = Buffer.alloc(1024 * 1024);
    while (true) {
      const { bytesRead } = await fh.read(buf, 0, buf.length, null);
      if (bytesRead === 0) break;
    }
  } finally {
    await fh.close();
  }

  // write ACK via atomic rename to reliably trigger a rename event
  const ackTmp = `${ACK_FILE}.tmp`;
  await fsp.writeFile(ackTmp, "ok");
  await fsp.rename(ackTmp, ACK_FILE);
}

// Event-driven loop: react to READY_FILE appearance
(async () => {
  // If a file is already present at startup, handle it immediately.
  if (await exists(READY_FILE)) {
    try { await consumeReadyAndAck(); } catch (e) { console.error("reader error (startup):", e); }
  }

  // Watch the directory for new ready files
  while (true) {
    try {
      for await (const evt of fsp.watch(DATA_DIR)) {
        const { eventType, filename } = evt;
        if (!filename) continue;
        if (filename === path.basename(READY_FILE) && (eventType === "rename" || eventType === "change")) {
          if (await exists(READY_FILE)) {
            try { await consumeReadyAndAck(); } catch (e) { console.error("reader error:", e); }
          }
        }
      }
    } catch (e) {
      console.error("reader watcher error, restarting watcher:", e);
      // small delay before re-establishing the watcher
      await new Promise(r => setTimeout(r, 50));
    }
  }
})();
