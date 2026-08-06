import asyncio
import subprocess
import sys
from pathlib import Path

_liveportrait_path = None
_sadtalker_path = None

def get_liveportrait_path():
    global _liveportrait_path
    if _liveportrait_path is None:
        project_root = Path(__file__).parent.parent.parent
        _liveportrait_path = project_root / "liveportrait" / "repo"
    return _liveportrait_path

def get_sadtalker_path():
    global _sadtalker_path
    if _sadtalker_path is None:
        project_root = Path(__file__).parent.parent.parent
        _sadtalker_path = project_root / "sadtalker" / "repo"
    return _sadtalker_path

async def generate_video(source_image, audio_path, output_path="output.mp4"):
    # Try SadTalker first (audio-driven lip sync)
    sadtalker_path = get_sadtalker_path()
    if (sadtalker_path / "inference.py").exists():
        print("[VideoGen] Attempting SadTalker for lip sync...")
        try:
            await sadtalker_inference(source_image, audio_path, output_path, sadtalker_path)
            if Path(output_path).exists():
                return output_path
        except Exception as e:
            print(f"[VideoGen] SadTalker failed: {e}")
    
    # Try LivePortrait (video-driven, needs driving video)
    lp_path = get_liveportrait_path()
    if (lp_path / "inference.py").exists():
        print("[VideoGen] Attempting LivePortrait...")
        try:
            await liveportrait_inference(source_image, audio_path, output_path, lp_path)
            if Path(output_path).exists():
                return output_path
        except Exception as e:
            print(f"[VideoGen] LivePortrait failed: {e}")
    
    # Fallback to ffmpeg
    print("[VideoGen] Using ffmpeg fallback (static image + audio)")
    await ffmpeg_fallback(source_image, audio_path, output_path)
    return output_path

async def sadtalker_inference(source_image, audio_path, output_path, sadtalker_path):
    cmd = [
        sys.executable, str(sadtalker_path / "inference.py"),
        "--driven_audio", str(audio_path),
        "--source_image", str(source_image),
        "--result_dir", str(Path(output_path).parent),
        "--still", "--preprocess", "full",
        "--expression_scale", "1.0"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        cwd=str(sadtalker_path)
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stderr.decode()[:300])

async def liveportrait_inference(source_image, audio_path, output_path, lp_path):
    cmd = [
        sys.executable, str(lp_path / "inference.py"),
        "--source", str(source_image),
        "--driving", str(audio_path),
        "--output-dir", str(Path(output_path).parent),
        "--flag-use-half-precision", "--device-id", "0"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        cwd=str(lp_path)
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stderr.decode()[:300])

async def ffmpeg_fallback(source_image, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(source_image), "-i", str(audio_path),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", str(output_path)
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    if process.returncode == 0:
        print(f"[VideoGen] Video saved: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python video_gen.py <source_image> <audio_path> <output_path>")
        sys.exit(1)
    asyncio.run(generate_video(sys.argv[1], sys.argv[2], sys.argv[3]))
