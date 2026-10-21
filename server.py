#!/usr/bin/env python3
"""NovAI media MCP server (stdio, zero dependencies).

Generate images and video through NovAI's OpenAI-compatible API from any MCP client
(Claude Desktop, Cline, Cursor, Continue...).

Env:
  NOVAI_API_KEY   required for generate_* tools  (get one at https://aiapi-pro.com/register)

Tools:
  - generate_image(prompt, model?, size?)   -> image URL(s)
  - generate_video(prompt, model?, duration?, resolution?) -> job id
  - get_video(id)                           -> status + video_url
  - list_models(category?)                  -> live model ids from /v1/models
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("NOVAI_BASE", "https://aiapi-pro.com/v1")
KEY = os.environ.get("NOVAI_API_KEY", "").strip()


def call(method, path, payload=None, timeout=120):
    if not KEY:
        raise RuntimeError("NOVAI_API_KEY is not set. Create one at https://aiapi-pro.com/register")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"HTTP {e.code}: {body}")


def tool_image(args):
    payload = {"model": args.get("model") or "seedream-5.0", "prompt": args["prompt"]}
    if args.get("size"):
        payload["size"] = args["size"]
    out = call("POST", "/images/generations", payload)
    items = out.get("data") or []
    urls = [i.get("url") or i.get("b64_json", "")[:80] for i in items]
    return f"Generated {len(urls)} image(s) with {payload['model']}:\n" + "\n".join(urls)


def tool_video(args):
    payload = {"model": args.get("model") or "minimax-video-h3", "prompt": args["prompt"]}
    for k in ("duration", "resolution"):
        if args.get(k):
            payload[k] = args[k]
    out = call("POST", "/video/generations", payload)
    return (f"Video job submitted with {payload['model']}.\nid: {out.get('id')}\n"
            f"status: {out.get('status')}\nPoll with get_video(id).")


def tool_video_status(args):
    out = call("GET", f"/video/generations/{args['id']}")
    lines = [f"status: {out.get('status')}"]
    if out.get("video_url"):
        lines.append(f"video_url: {out['video_url']}")
    if out.get("error"):
        lines.append(f"error: {out['error']}")
    return "\n".join(lines)


def tool_models(args):
    req = urllib.request.Request(BASE + "/models", headers={"User-Agent": "novai-media-mcp/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r).get("data", [])
    cat = (args.get("category") or "").lower()
    ids = [m["id"] for m in data if not cat or cat in m["id"].lower()]
    return f"{len(ids)} models" + (f" matching '{cat}'" if cat else "") + ":\n" + ", ".join(ids[:60])


TOOLS = [
    {"name": "generate_image",
     "description": "Generate an image with a Chinese image model (Seedream, WAND Vega, Hunyuan Image, CogView). Returns image URLs.",
     "inputSchema": {"type": "object", "properties": {
         "prompt": {"type": "string"},
         "model": {"type": "string", "description": "default seedream-5.0"},
         "size": {"type": "string", "description": "e.g. 1024x1024"}}, "required": ["prompt"]}},
    {"name": "generate_video",
     "description": "Submit a text-to-video job (MiniMax Hailuo, Tencent Hunyuan, Kling, Seedance). Async: returns a job id.",
     "inputSchema": {"type": "object", "properties": {
         "prompt": {"type": "string"},
         "model": {"type": "string", "description": "default minimax-video-h3"},
         "duration": {"type": "integer"},
         "resolution": {"type": "string"}}, "required": ["prompt"]}},
    {"name": "get_video",
     "description": "Poll a video job by id; returns status and video_url when finished.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "list_models",
     "description": "List live model ids from NovAI (optionally filtered by substring such as 'video', 'image', 'seedream').",
     "inputSchema": {"type": "object", "properties": {"category": {"type": "string"}}}},
]

HANDLERS = {"generate_image": tool_image, "generate_video": tool_video,
            "get_video": tool_video_status, "list_models": tool_models}


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    msg["error" if error is not None else "result"] = error if error is not None else result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        mid, method = req.get("id"), req.get("method")
        params = req.get("params") or {}
        if method == "initialize":
            reply(mid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                        "serverInfo": {"name": "novai-media", "version": "0.1.0"}})
        elif method == "tools/list":
            reply(mid, {"tools": TOOLS})
        elif method == "tools/call":
            h = HANDLERS.get(params.get("name"))
            if not h:
                reply(mid, error={"code": -32601, "message": "unknown tool"})
                continue
            try:
                reply(mid, {"content": [{"type": "text", "text": h(params.get("arguments") or {})}], "isError": False})
            except Exception as e:
                reply(mid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif method.startswith("notifications/"):
            continue
        else:
            reply(mid, error={"code": -32601, "message": f"unsupported method: {method}"})


if __name__ == "__main__":
    main()
