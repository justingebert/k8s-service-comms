import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";

const DATA_DIR = process.env.DATA_DIR || "/data";

//run forever to keep looking for files, should be improved
while (true) {
    const ready = path.join(DATA_DIR, "payload.ready");
    const ack = path.join(DATA_DIR, "ack");

    try {
        await fsp.access(ready, fs.constants.F_OK);
        // consume the entire file
        const fh = await fsp.open(ready, "r");
        try {
            const buf = Buffer.alloc(1024 * 1024);
            while (true) {
                const { bytesRead } = await fh.read(buf, 0, buf.length, null);
                if (bytesRead === 0) break;
            }
        } finally {
            await fh.close();
        }
        await fsp.writeFile(ack, "ok");
    } catch {
        await new Promise(res => setTimeout(res, 1));
    }
}
