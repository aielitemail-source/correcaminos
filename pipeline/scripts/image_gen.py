import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://image.pollinations.ai/prompt/"
UA = {"User-Agent": "Mozilla/5.0"}


def _build_url(prompt, width, height, seed, model="flux"):
    encoded = urllib.parse.quote(prompt[:200])
    url = f"{BASE}{encoded}?width={width}&height={height}&model={model}&nologo=true"
    if seed is not None:
        url += f"&seed={seed}"
    return url


def generate_image(prompt, output_path="output.png", style=None, width=1024,
                   height=1024, seed=None, retries=3):
    full_prompt = f"{prompt}, {style}" if style else prompt
    full_prompt = full_prompt[:200]
    url = _build_url(full_prompt, width, height, seed)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"[ImageGen] Prompt: {full_prompt[:90]}...")
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as response:
                data = response.read()
            if len(data) < 2000:
                raise ValueError(f"response too small ({len(data)} bytes)")
            with open(output_path, "wb") as f:
                f.write(data)
            print(f"[ImageGen] Saved: {output_path} ({len(data)/1024:.1f} KB)")
            return output_path
        except Exception as e:
            print(f"[ImageGen] Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(4 * attempt)
    print("[ImageGen] Giving up.")
    return None


def generate_image_set(prompts, output_dir, style=None, width=1024, height=1024,
                       prefix="scene", base_seed=None):
    results = []
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, prompt in enumerate(prompts, start=1):
        seed = None if base_seed is None else base_seed + i
        path = out / f"{prefix}_{i:02d}.png"
        got = generate_image(prompt, str(path), style=style, width=width,
                             height=height, seed=seed)
        if got:
            results.append(got)
        time.sleep(2)
    print(f"[ImageGen] Generated {len(results)}/{len(prompts)} images")
    return results


if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "journalist corruption investigation"
    generate_image(prompt, output_path="test_pollinations.png")