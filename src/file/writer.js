import fsp from "node:fs/promises";
import fs from "node:fs";
import crypto from "node:crypto";
import path from "node:path";
import { CONFIG, getBenchmarkSizes } from "../common/config.js";
import { calculateThroughput, logResult } from "../common/utils.js";

const DATA_DIR = CONFIG.file.dataDir;
const READY_SIGNAL = path.join(DATA_DIR, ".reader-ready");

// Simple wait for reader to be ready (no logs to keep CSV clean)
while (true) {
    try {
        await fsp.access(READY_SIGNAL);
        break;
    } catch {
        await new Promise(r => setTimeout(r, 100));
    }
}

console.log("method,size_bytes,rep,elapsed_ms,throughput_mib_s");

for (const size of getBenchmarkSizes()) {
    const payload = crypto.randomBytes(size); // random data to avoid compression bias

    for (let r = 1; r <= CONFIG.benchmark.reps; r++) {
        const tmp = path.join(DATA_DIR, "payload.tmp");
        const ready = path.join(DATA_DIR, "payload.ready");
        const ack = path.join(DATA_DIR, "ack");

        // Clean up any leftover files
        for (const p of [tmp, ready, ack]) {
            try {
                await fsp.unlink(p);
            } catch {
            }
        }

        const t0 = process.hrtime.bigint();

        // Write payload to temp file
        const fd = await fsp.open(tmp, "w");
        try {
            await fd.write(payload, 0, payload.length, 0);
            if (CONFIG.file.durable) {
                await fd.sync();
            }
        } finally {
            await fd.close();
        }

        // Atomic rename → reader sees it
        await fsp.rename(tmp, ready);

        // Wait for ACK (no busy-wait)
        await new Promise((resolve, reject) => {
            let resolved = false;
            const watcher = fs.watch(DATA_DIR, (eventType, filename) => {
                if (resolved) return;
                if (filename === "ack" && (eventType === "rename" || eventType === "change")) {
                    fsp.access(ack).then(() => {
                        if (!resolved) {
                            resolved = true;
                            watcher.close();
                            resolve();
                        }
                    }).catch(() => { });
                }
            });
            watcher.on("error", (err) => {
                if (!resolved) {
                    resolved = true;
                    watcher.close();
                    reject(err);
                }
            });
            // Check after watcher is set up to catch files created before watching
            fsp.access(ack).then(() => {
                if (!resolved) {
                    resolved = true;
                    watcher.close();
                    resolve();
                }
            }).catch(() => { });
        });

        const dtMs = Number(process.hrtime.bigint() - t0) / 1e6;
        const thr = calculateThroughput(size, dtMs);
        logResult(`file-${CONFIG.file.storageMedium}`, size, r, dtMs, thr);

        // Clean up
        for (const p of [ready, ack]) {
            try {
                await fsp.unlink(p);
            } catch {
            }
        }
    }
}

