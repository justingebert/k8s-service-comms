import crypto from "node:crypto";
import { CONFIG, getBenchmarkSizes } from "../common/config.js";
import { calculateThroughput, logResult } from "../common/utils.js";

const url = `http://${CONFIG.net.host}:${CONFIG.net.port}/upload`;

console.log("method,size_bytes,rep,elapsed_ms,throughput_mib_s");

for (const size of getBenchmarkSizes()) {
    const payload = crypto.randomBytes(size);
    const expectedHash = crypto.createHash("sha256").update(payload).digest("hex");

    for (let r = 1; r <= CONFIG.benchmark.reps; r++) {
        const t0 = process.hrtime.bigint();

        const resp = await fetch(url, {
            method: "POST",
            body: payload,
            signal: AbortSignal.timeout(CONFIG.net.timeout),
        });

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }

        const result = await resp.json();

        // Validate response
        if (result.len !== payload.length) {
            throw new Error(`Size mismatch: sent ${payload.length}, received ${result.len}`);
        }

        if (result.hash !== expectedHash) {
            throw new Error("Checksum mismatch");
        }

        const dtMs = Number(process.hrtime.bigint() - t0) / 1e6;
        const thr = calculateThroughput(size, dtMs);
        logResult("net", size, r, dtMs, thr);
    }
}

