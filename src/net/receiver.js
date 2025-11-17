import http from "node:http";
import crypto from "node:crypto";
import { CONFIG } from "../common/config.js";

const server = http.createServer(async (req, res) => {
    if (req.method === "POST" && req.url === "/upload") {
        try {
            // Read body
            const chunks = [];
            for await (const chunk of req) chunks.push(chunk);
            const body = Buffer.concat(chunks);

            // Compute hash for validation
            const hash = crypto.createHash("sha256").update(body).digest("hex");

            res.writeHead(200, {"content-type": "application/json"});
            res.end(JSON.stringify({
                len: body.length,
                hash: hash
            }));
        } catch (err) {
            console.error("Error processing upload:", err);
            res.writeHead(500, {"content-type": "application/json"});
            res.end(JSON.stringify({error: err.message}));
        }
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(CONFIG.net.port, "0.0.0.0", () => {
    console.log(`net-receiver listening on :${CONFIG.net.port}`);
});
