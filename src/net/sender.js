const HOST = process.env.HOST || "net-svc";
const PORT = Number(process.env.PORT || "8080");
const REPS = Number(process.env.REPS || "5");
const url = `http://${HOST}:${PORT}/upload`;

console.log("method,size_bytes,rep,elapsed_ms,throughput_mib_s");

for (const size of getSizesFromEnv()) {
    const payload = Buffer.alloc(size, 0x78); // repeated 'x'
    for (let r = 1; r <= REPS; r++) {
        const t0 = process.hrtime.bigint();
        const resp = await fetch(url, { method: "POST", body: payload });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        await resp.arrayBuffer(); // ensure full response
        const dtMs = Number(process.hrtime.bigint() - t0) / 1e6;
        const mib = size / (1024 * 1024);
        const thr = mib / (dtMs / 1000);
        console.log(`net,${size},${r},${dtMs.toFixed(3)},${thr.toFixed(3)}`);
        // console.log(`NET size=${size}B rep=${r}/${REPS} time=${dtMs.toFixed(3)}ms thr=${thr.toFixed(3)}MiB/s`);
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