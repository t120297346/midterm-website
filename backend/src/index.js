import express from "express";
import path, { dirname } from "path";
import { fileURLToPath } from "url";
import rootRouter from "./routes";
import { prisma } from "./adapters";

const _dirname = dirname(fileURLToPath(import.meta.url));
const frontendDir = path.join(_dirname, "../../frontend/dist");
const port = process.env.PORT || 8000;
const app = express();

app.use(express.static(frontendDir));
app.use(express.json());
app.use(rootRouter);
app.get('*', (req, res) => {
    if (!req.originalUrl.startsWith("/api")) {
        return res.sendFile(path.join(frontendDir, "index.html"));
    }
    return res.status(404).send();
});

app.post("/", function (req, res) {
    res.send("Got a POST request");
});

app.listen(port, () => {
console.log(`Example app listening at http://localhost:${port}`);
});

process.on("exit", async () => {
    await prisma.$disconnect();
})