import fsp from "node:fs/promises";
import fs from "node:fs";
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
                const { bytesRead } = await fh.read(buf, 0, buf.length, null);
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
    await fsp.mkdir(DATA_DIR, { recursive: true });
} catch {
}

await fsp.writeFile(READY_SIGNAL, "ready");
console.error("Reader ready, watching for files");

// Process any file that exists at startup
if (await exists(READY_FILE)) {
    try {
        await consumeReadyAndAck();
    } catch (e) {
        console.error("Reader error (startup):", e);
    }
}

// Flag to signal when we should check for files
let shouldCheck = false;
let processing = false;

// Process files in a loop, checking after each processing completes
async function processLoop() {
    while (true) {
        // Wait for signal if no pending check
        if (!shouldCheck) {
            await new Promise(r => setTimeout(r, 5));
            continue;
        }

        shouldCheck = false;

        if (await exists(READY_FILE)) {
            processing = true;
            try {
                await consumeReadyAndAck();
            } catch (e) {
                console.error("Reader error:", e);
            }
            processing = false;
            // Re-check after processing in case we missed an event
            shouldCheck = true;
        }
    }
}

// Start the processing loop
processLoop();

fs.watch(DATA_DIR, (eventType, filename) => {
    if (!filename) return;
    if (filename === path.basename(READY_FILE) &&
        (eventType === "rename" || eventType === "change")) {
        shouldCheck = true;
    }
});

// Keep the process alive
setInterval(() => { }, 60000);
