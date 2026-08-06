import asyncio
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tts import generate_audio
from image_gen import generate_image, generate_image_set
from video_gen import generate_video

ROOT = Path(__file__).parent.parent.parent

SHOT_TYPES = [
    "wide establishing shot",
    "medium shot, shallow depth of field",
    "close-up detail, dramatic rim light",
    "low angle shot, cinematic composition",
    "over-the-shoulder shot, documentary style",
]


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def build_image_prompts(theme, script_text, count=4):
    shots = random.sample(SHOT_TYPES, min(count, len(SHOT_TYPES)))
    base = f"{theme}, spanish investigative journalism, newsroom atmosphere"
    return [f"{base}, {shot}" for shot in shots]


def generate_default_script(config, theme=None):
    if theme is None:
        theme = random.choice(config["content"]["themes"])
    return (
        f"Hoy en Correcaminos hablamos de {theme}. "
        f"Analizamos los hechos, los documentos y las cifras que casi nadie mira. "
        f"Porque la transparencia no es un favor, es una obligacion."
    ), theme


async def run_pipeline(script_text=None, theme=None, image_count=4):
    config = load_config()
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = ROOT / config["pipeline"]["output_dir"] / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Pipeline] Starting for {date_str}")

    if script_text is None:
        script_text, theme = generate_default_script(config, theme)
    elif theme is None:
        theme = random.choice(config["content"]["themes"])

    # 1) Audio
    audio_path = output_dir / "narration.mp3"
    await generate_audio(
        text=script_text,
        voice=config["pipeline"]["voice"],
        rate=config["pipeline"]["voice_rate"],
        output_path=str(audio_path),
    )
    print(f"[Pipeline] Audio: {audio_path}")

    # 2) Images
    style = config["content"]["image_style"]
    seed = int(datetime.now().strftime("%Y%m%d"))

    cover_path = output_dir / "cover.png"
    generate_image(
        prompt=f"{theme}, editorial cover image, spanish politics investigation",
        output_path=str(cover_path),
        style=style,
        width=1280,
        height=720,
        seed=seed,
    )

    prompts = build_image_prompts(theme, script_text, image_count)
    scenes = generate_image_set(
        prompts,
        output_dir=str(output_dir),
        style=style,
        width=1080,
        height=1080,
        prefix="scene",
        base_seed=seed,
    )
    print(f"[Pipeline] Images: {len(scenes)} scenes + cover")

    # 3) Video
    character_image = ROOT / config.get(
        "character_image", "pipeline/assets/characters/host.png"
    )
    video_path = output_dir / "final_video.mp4"
    await generate_video(
        source_image=str(character_image),
        audio_path=str(audio_path),
        output_path=str(video_path),
        broll_images=scenes,
    )
    print(f"[Pipeline] Video: {video_path}")

    # 4) Metadata
    metadata = {
        "date": date_str,
        "title": f"Correcaminos - {theme.capitalize()}",
        "theme": theme,
        "script": script_text,
        "video": f"media/{date_str}/final_video.mp4",
        "cover": f"media/{date_str}/cover.png",
        "images": [f"media/{date_str}/{Path(p).name}" for p in scenes],
        "duration": get_audio_duration(str(audio_path)),
    }
    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    sync_to_web(output_dir, date_str)
    update_posts_index(metadata)

    print(f"[Pipeline] Complete -> {output_dir}")
    return metadata


def get_audio_duration(audio_path):
    try:
        from mutagen.mp3 import MP3

        return round(MP3(audio_path).info.length, 1)
    except Exception:
        return 30.0


def sync_to_web(output_dir, date_str):
    import shutil

    dest = ROOT / "web" / "public" / "media" / date_str
    dest.mkdir(parents=True, exist_ok=True)
    for f in Path(output_dir).glob("*"):
        if f.suffix.lower() in (".mp4", ".png", ".jpg", ".jpeg", ".mp3"):
            shutil.copy2(f, dest / f.name)
    print(f"[Pipeline] Synced to web: {dest}")


def update_posts_index(metadata):
    posts_file = ROOT / "web" / "src" / "data" / "posts.json"
    posts_file.parent.mkdir(parents=True, exist_ok=True)
    posts = []
    if posts_file.exists():
        try:
            with open(posts_file, encoding="utf-8") as f:
                posts = json.load(f)
        except Exception:
            posts = []
    posts = [p for p in posts if p.get("date") != metadata["date"]]
    posts.insert(0, metadata)
    with open(posts_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"[Pipeline] Posts index updated ({len(posts)} entries)")


if __name__ == "__main__":
    asyncio.run(run_pipeline())