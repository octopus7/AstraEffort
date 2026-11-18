"use strict";

// Optional local preview. The HTML and assets also open directly from disk.
const { createServer } = require("node:http");
const { readFile } = require("node:fs/promises");
const path = require("node:path");

const route = "/Astra62/pixel-art-test/";
const previousRoute = "/pixel-art-test/";
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".gif": "image/gif"
};

const server = createServer(async (request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD" }).end();
    return;
  }
  const { pathname, search } = new URL(request.url, "http://localhost");
  const previousPath = pathname === previousRoute.slice(0, -1) || pathname.startsWith(previousRoute);
  if (pathname === "/" || pathname === route.slice(0, -1) || previousPath) {
    const suffix = previousPath ? pathname.slice(previousRoute.length) : "";
    response.writeHead(302, { Location: route + suffix + search }).end();
    return;
  }
  const asset = pathname.startsWith(route) ? pathname.slice(route.length) || "index.html" : "";
  const pageOrAsset = /^(index\.html|scene\.html|style\.css|lab\.js|assets\/[\w-]+\.(png|gif))$/.test(asset);
  const layer = /^art\/anime\/layers\/(body|far-arm-bow|near-arm|cape-back|cape-front)\.png$/.test(asset);
  if (!pageOrAsset && !layer) {
    response.writeHead(404).end();
    return;
  }
  try {
    const data = await readFile(path.join(__dirname, asset));
    response.writeHead(200, { "Content-Type": types[path.extname(asset)], "Content-Length": data.length });
    response.end(request.method === "HEAD" ? undefined : data);
  } catch (error) {
    response.writeHead(error.code === "ENOENT" ? 404 : 500).end();
  }
});

const port = Number(process.argv[2] ?? 8784);
server.listen(port, "127.0.0.1", () => {
  console.log("http://127.0.0.1:" + server.address().port + route);
});
