<!-- mcp-name: io.github.vvvvking/novai-media-mcp -->

# novai-media-mcp

Generate **images and video** with Chinese models (Seedream, WAND Vega, Hunyuan, Hailuo, Kling, Seedance) directly from Claude Desktop, Cline, Cursor or any MCP client — through one OpenAI-compatible API.

## Why

Chinese image/video models are often 3-10x cheaper than their Western equivalents, but they are awkward to reach: Chinese-only consoles, phone-number verification, prepaid credit packs. This server exposes them as ordinary MCP tools.

## Tools

| Tool | What it does |
|---|---|
| `generate_image` | Text → image (default `seedream-5.0`), returns image URLs |
| `generate_video` | Text → video job (default `minimax-video-h3`), returns a job id |
| `get_video` | Poll a video job; returns `status` and `video_url` when done |
| `list_models` | Live model ids from `/v1/models`, optionally filtered |

## Setup

1. Create an API key at <https://aiapi-pro.com/register> ($2 credit, no card required).
2. Put it in your MCP client config:

```json
{
  "mcpServers": {
    "novai-media": {
      "command": "python3",
      "args": ["/absolute/path/to/server.py"],
      "env": { "NOVAI_API_KEY": "nvai-..." }
    }
  }
}
```

No dependencies beyond Python 3.9+.

## Example

```
→ generate_image {"prompt": "a paper boat in the rain, macro photography"}
← Generated 1 image(s) with seedream-5.0:
  https://.../image.png

→ generate_video {"prompt": "same boat drifting downstream, slow dolly", "duration": 5}
← Video job submitted with minimax-video-h3.
  id: task_abc123
  status: queued

→ get_video {"id": "task_abc123"}
← status: succeeded
  video_url: https://.../video.mp4
```

Video is asynchronous: submit, then poll. Failed jobs are refunded automatically.

## Models worth knowing

| Model | Modality | Rough price |
|---|---|---|
| `cogvideox-flash` | video | free (10 free-model calls/day) |
| `seedream-5.0` | image | $0.027 per image |
| `minimax-video-h3` | video | ~$0.077/s (~$0.385 per 5s clip) |
| `kling-video-v3` | video | ~$0.092/s (~$0.46 per 5s clip) |
| `doubao-seedance-2.5` | video | from $0.14/s (480p) |

Prices are provider list price with **0% platform markup**; live feed at <https://aiapi-pro.com/china-ai-leaderboard.json>.

## Notes

- Image and video models are billed per generation/per second, not per token.
- The free tier includes 5 calls/day for video via `cogvideox-flash`.
- Errors come back as OpenAI-style JSON; this server surfaces the message.

## License

MIT
