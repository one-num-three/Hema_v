#!/usr/bin/env python
"""Call Grsai image generation for PPT page visuals."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _request_json(method: str, url: str, *, api_key: str, payload: dict | None = None) -> dict:
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error: {exc}") from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Response was not JSON: {text[:1000]}") from exc


def _extract_task_id(data: dict) -> str | None:
    for key in ("id", "task_id", "taskId"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    nested = data.get("data")
    if isinstance(nested, dict):
        return _extract_task_id(nested)
    return None


def _extract_urls(data: object) -> list[str]:
    urls: list[str] = []
    if isinstance(data, dict):
        for key in ("url", "image_url", "imageUrl"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                urls.append(value)
        for key in ("results", "images", "data", "output"):
            value = data.get(key)
            urls.extend(_extract_urls(value))
    elif isinstance(data, list):
        for item in data:
            urls.extend(_extract_urls(item))
    return list(dict.fromkeys(urls))


def _download_first(urls: list[str], out_dir: Path, filename: str | None = None) -> str | None:
    if not urls:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    url = urls[0]
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix or ".png"
    if filename:
        out_name = Path(filename).name
        if not Path(out_name).suffix:
            out_name = f"{out_name}{suffix}"
    else:
        out_name = f"grsai_ppt_page_{int(time.time())}{suffix}"
    out_path = out_dir / out_name
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Grsai-PPT/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        out_path.write_bytes(resp.read())
    return str(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a PPT page image with Grsai.")
    parser.add_argument("--prompt", help="Prompt text. Prefer --prompt-file for long prompts.")
    parser.add_argument("--prompt-file", help="UTF-8 text file containing the prompt.")
    parser.add_argument("--model", required=True, choices=["gpt-image-2", "gpt-image-2-vip"])
    parser.add_argument("--aspect-ratio", required=True, help="Example: 2048x1152 or 3840x2160.")
    parser.add_argument("--reply-type", default="json", choices=["json", "async"])
    parser.add_argument("--base-url", default="https://grsai.dakka.com.cn")
    parser.add_argument("--api-key", default=os.getenv("GRSAI_API_KEY"))
    parser.add_argument("--out-dir", default="outputs/grsai-ppt-pages")
    parser.add_argument("--filename", help="Optional output filename, e.g. 001_cover.png.")
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    parser.add_argument("--max-polls", type=int, default=80)
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Set GRSAI_API_KEY or pass --api-key in a trusted local shell.")

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        prompt = args.prompt or ""
    prompt = prompt.strip()
    if not prompt:
        raise SystemExit("Prompt is required. Use --prompt or --prompt-file.")

    base_url = args.base_url.rstrip("/")
    payload = {
        "model": args.model,
        "prompt": prompt,
        "images": [],
        "aspectRatio": args.aspect_ratio,
        "replyType": args.reply_type,
    }

    result = _request_json("POST", f"{base_url}/v1/api/generate", api_key=args.api_key, payload=payload)

    if args.reply_type == "async":
        task_id = _extract_task_id(result)
        if not task_id:
            print(json.dumps({"initial_response": result, "error": "No task id found"}, ensure_ascii=False, indent=2))
            return 1
        for _ in range(args.max_polls):
            time.sleep(args.poll_seconds)
            result = _request_json("GET", f"{base_url}/v1/api/result?id={urllib.parse.quote(task_id)}", api_key=args.api_key)
            status = str(result.get("status") or (result.get("data") or {}).get("status") or "").lower()
            if status in {"succeeded", "failed", "violation"}:
                break

    urls = _extract_urls(result)
    downloaded = None
    try:
        downloaded = _download_first(urls, Path(args.out_dir), args.filename)
    except Exception as exc:  # keep API result even when CDN download fails
        downloaded = None
        result = {"api_result": result, "download_error": str(exc)}

    output = {
        "success": bool(urls),
        "model": args.model,
        "aspectRatio": args.aspect_ratio,
        "urls": urls,
        "downloaded": downloaded,
        "raw": result,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if urls else 1


if __name__ == "__main__":
    raise SystemExit(main())
