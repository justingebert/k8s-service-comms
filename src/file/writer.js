import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";

const DATA_DIR = process.env.DATA_DIR || "/data";
const REPS = Number(process.env.REPS || "5");

console.log("method,size_bytes,rep,elapsed_ms,throughput_mib_s");

for (const size of getSizesFromEnv()) {
    const payload = Buffer.alloc(size, 0x78); // repeated 'x'
    for (let r = 1; r <= REPS; r++) {
        const tmp = path.join(DATA_DIR, "payload.tmp");
        const ready = path.join(DATA_DIR, "payload.ready");
        const ack = path.join(DATA_DIR, "ack");

        // clean up
        for (const p of [tmp, ready, ack]) { try { await fsp.unlink(p); } catch {} }

        const t0 = process.hrtime.bigint();

        // write & fsync
        const fd = await fsp.open(tmp, "w");
        try {
            await fd.write(payload, 0, payload.length, 0);
            await fd.sync();
        } finally {
            await fd.close();
        }

        // atomic rename → reader sees it
        await fsp.rename(tmp, ready);

        // wait for ACK
        while (true) {
            try { await fsp.access(ack, fs.constants.F_OK); break; }
            catch { await new Promise(res => setTimeout(res, 1)); }
        }

        const dtMs = Number(process.hrtime.bigint() - t0) / 1e6;
        const mib = size / (1024 * 1024);
        const thr = mib / (dtMs / 1000);
        console.log(`file,${size},${r},${dtMs.toFixed(3)},${thr.toFixed(3)}`);
        console.log(`FILE size=${size}B rep=${r}/${REPS} time=${dtMs.toFixed(3)}ms thr=${thr.toFixed(3)}MiB/s`);

        for (const p of [ready, ack]) { try { await fsp.unlink(p); } catch {} }
    }
}

function getSizesFromEnv() {
    const sizesEnv = process.env.SIZES?.trim();
    if (!sizesEnv) throw new Error("SIZES env var must be set (comma-separated numbers)");
    return sizesEnv
        .split(",")
        .map(s => Number(s.trim()))
        .filter(n => !Number.isNaN(n) && n > 0);
}