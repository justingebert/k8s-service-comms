import fsp from "node:fs/promises";
import path from "node:path";
import { CONFIG } from "../common/config.js";
import { exists } from "../common/utils.js";

const DATA_DIR = CONFIG.file.dataDir;
const READY_FILE = path.join(DATA_DIR, "payload.ready");
const ACK_FILE = path.join(DATA_DIR, "ack");
const READY_SIGNAL = path.join(DATA_DIR, ".reader-ready");

async function consumeReadyAndAck() {
    try {
        const fh = await fsp.open(READY_FILE, "r");
        try {
            const buf = Buffer.alloc(CONFIG.file.chunkSize);
            while (true) {
                const {bytesRead} = await fh.read(buf, 0, buf.length, null);
                if (bytesRead === 0) break;
            }
        } finally {
            await fh.close();
        }

        const ackTmp = `${ACK_FILE}.tmp`;
        await fsp.writeFile(ackTmp, "ok");
        await fsp.rename(ackTmp, ACK_FILE);
    } catch (err) {
        console.error("Error processing file:", err);
        throw err;
    }
}

console.error("Reader starting up...");

try {
    await fsp.mkdir(DATA_DIR, {recursive: true});
} catch {
}

await fsp.writeFile(READY_SIGNAL, "ready");
console.error("Reader ready, watching for files");

if (await exists(READY_FILE)) {
    try {
        await consumeReadyAndAck();
    } catch (e) {
        console.error("Reader error (startup):", e);
    }
}

while (true) {
    try {
        for await (const evt of fsp.watch(DATA_DIR)) {
            const {eventType, filename} = evt;
            if (!filename) continue;

            if (filename === path.basename(READY_FILE) &&
                (eventType === "rename" || eventType === "change")) {
                if (await exists(READY_FILE)) {
                    try {
                        await consumeReadyAndAck();
                    } catch (e) {
                        console.error("Reader error:", e);
                    }
                }
            }
        }
    } catch (e) {
        console.error("Reader watcher error, restarting watcher:", e);
        await new Promise(r => setTimeout(r, 50));
    }
}

