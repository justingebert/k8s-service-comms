import http from "node:http";
import crypto from "node:crypto";

const PORT = process.env.PORT ? Number(process.env.PORT) : 8080;

const server = http.createServer(async (req, res) => {
    if (req.method === "POST" && req.url === "/upload") {
        // Read full body
        const chunks = [];
        for await (const chunk of req) chunks.push(chunk);
        const body = Buffer.concat(chunks);

        // Tiny work so it's not a no-op
        crypto.createHash("sha256").update(body).digest("hex");

        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ len: body.length }));
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(PORT, "0.0.0.0", () => {
    console.log(`net server on :${PORT}`);
});
