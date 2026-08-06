import asyncio
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def get_sadtalker_path():
    return ROOT / "sadtalker" / "repo"


def get_liveportrait_path():
    return ROOT / "liveportrait" / "repo"


def probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=30
        )
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return 30.0


async def generate_video(source_image, audio_path, output_path="output.mp4",
                         broll_images=None):
    sadtalker = get_sadtalker_path()
    if (sadtalker / "inference.py").exists():
        print("[VideoGen] Attempting SadTalker...")
        try:
            await sadtalker_inference(source_image, audio_path, output_path, sadtalker)
            if Path(output_path).exists():
                return output_path
        except Exception as e:
            print(f"[VideoGen] SadTalker failed: {str(e)[:200]}")

    if broll_images:
        print(f"[VideoGen] Building multi-shot video ({len(broll_images)+1} shots)")
        try:
            await multishot_video(source_image, broll_images, audio_path, output_path)
            if Path(output_path).exists():
                return output_path
        except Exception as e:
            print(f"[VideoGen] Multishot failed: {str(e)[:300]}")

    print("[VideoGen] ffmpeg fallback (static image + audio)")
    await ffmpeg_fallback(source_image, audio_path, output_path)
    return output_path


async def multishot_video(host_image, broll_images, audio_path, output_path):
    """Ken Burns slideshow: host shot first, then b-roll, synced to audio."""
    shots = [host_image] + list(broll_images)
    duration = probe_duration(audio_path)
    per_shot = max(2.5, duration / len(shots))
    fps = 25
    frames = int(per_shot * fps)
    w, h = 1080, 1920

    cmd = ["ffmpeg", "-y"]
    for img in shots:
        cmd += ["-loop", "1", "-t", f"{per_shot:.2f}", "-i", str(img)]
    cmd += ["-i", str(audio_path)]

    filters = []
    for i in range(len(shots)):
        zoom_in = i % 2 == 0
        z = ("min(zoom+0.0012,1.25)" if zoom_in
             else "if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0012))")
        filters.append(
            f"[{i}:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
            f"crop={w*2}:{h*2},"
            f"zoompan=z='{z}':d={frames}:s={w}x{h}:fps={fps},"
            f"setsar=1[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(shots)))
    filters.append(f"{concat_inputs}concat=n={len(shots)}:v=1:a=0[vout]")
    filter_complex = ";".join(filters)

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", f"{len(shots)}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest",
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore")[-500:])
    print(f"[VideoGen] Multi-shot video saved: {output_path}")


async def sadtalker_inference(source_image, audio_path, output_path, sadtalker_path):
    cmd = [
        sys.executable, str(sadtalker_path / "inference.py"),
        "--driven_audio", str(audio_path),
        "--source_image", str(source_image),
        "--result_dir", str(Path(output_path).parent),
        "--still", "--preprocess", "full",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        cwd=str(sadtalker_path)
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore")[:300])


async def ffmpeg_fallback(source_image, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(source_image), "-i", str(audio_path),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
        "-pix_fmt", "yuv420p", "-shortest", str(output_path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        print(f"[VideoGen] ffmpeg error: {stderr.decode(errors='ignore')[-300:]}")
    else:
        print(f"[VideoGen] Video saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python video_gen.py <source_image> <audio> <output>")
        sys.exit(1)
    asyncio.run(generate_video(sys.argv[1], sys.argv[2], sys.argv[3]))