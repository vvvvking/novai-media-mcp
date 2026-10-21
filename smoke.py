"""Smoke test novai-media MCP: initialize, tools/list, list_models (no key needed), and the no-key error path."""
import json
import subprocess
import sys

SERVER = r'C:\Users\32065\Documents\deepseek-harness\default-workspace\novai-marketing\mcp-media\server.py'

reqs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_models", "arguments": {"category": "video"}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "generate_image", "arguments": {"prompt": "test"}}},
]

p = subprocess.run([sys.executable, SERVER], input=("\n".join(json.dumps(r) for r in reqs) + "\n").encode(),
                   capture_output=True, timeout=120)
print('returncode:', p.returncode)
if p.stderr:
    print('stderr:', p.stderr.decode()[:300])
for line in p.stdout.decode().splitlines():
    d = json.loads(line)
    if d.get('id') == 1:
        print('initialize ->', d['result']['serverInfo'])
    elif d.get('id') == 2:
        print('tools:', [t['name'] for t in d['result']['tools']])
    elif d.get('id') == 3:
        txt = d['result']['content'][0]['text']
        print('list_models ->', txt[:220])
    else:
        r = d.get('result', {})
        print('no-key path ->', r.get('isError'), r.get('content', [{}])[0].get('text', '')[:120])
