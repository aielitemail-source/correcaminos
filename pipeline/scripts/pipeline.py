import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tts import generate_audio
from image_gen import generate_image
from video_gen import generate_video

def load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        return json.load(f)

async def run_pipeline(script_text=None, theme=None):
    config = load_config()
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(config["pipeline"]["output_dir"]) / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[Pipeline] Starting for {date_str}")
    
    # Step 1: Generate audio from script
    if script_text is None:
        script_text = generate_default_script(config, theme)
    
    audio_path = output_dir / "narration.mp3"
    await generate_audio(
        text=script_text,
        voice=config["pipeline"]["voice"],
        rate=config["pipeline"]["voice_rate"],
        output_path=str(audio_path)
    )
    print(f"[Pipeline] Audio generated: {audio_path}")
    
    # Step 2: Generate image
    image_path = output_dir / "scene.png"
    await generate_image(
        prompt=script_text[:500],
        style=config["content"]["image_style"],
        output_path=str(image_path)
    )
    print(f"[Pipeline] Image generated: {image_path}")
    
    # Step 3: Generate video with lip sync
    character_image = config.get("character_image", "pipeline/assets/characters/host.png")
    video_path = output_dir / "final_video.mp4"
    await generate_video(
        source_image=character_image,
        audio_path=str(audio_path),
        output_path=str(video_path)
    )
    print(f"[Pipeline] Video generated: {video_path}")
    
    # Step 4: Create metadata for web
    metadata = {
        "date": date_str,
        "title": f"Correcaminos - {date_str}",
        "script": script_text,
        "video": f"media/videos/{date_str}/final_video.mp4",
        "image": f"media/images/{date_str}/scene.png",
        "duration": get_audio_duration(str(audio_path))
    }
    meta_path = output_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Step 5: Sync to web
    sync_to_web(output_dir, date_str, config)
    
    print(f"[Pipeline] Complete! Output: {output_dir}")
    return metadata

def generate_default_script(config, theme=None):
    if theme is None:
        import random
        theme = random.choice(config["content"]["themes"])
    return f"Hoy en Correcaminos hablamos de {theme}. Este es un tema importante que afecta a nuestra sociedad."

def get_audio_duration(audio_path):
    try:
        from mutagen.mp3 import MP3
        return MP3(audio_path).info.length
    except:
        return 30.0

def sync_to_web(output_dir, date_str, config):
    web_media = Path(config["web"]["base_url"] if config["web"]["base_url"] else "web/public/media")
    videos_dir = web_media / "videos" / date_str
    images_dir = web_media / "images" / date_str
    videos_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    import shutil
    for f in output_dir.glob("*"):
        if f.suffix == ".mp4":
            shutil.copy2(f, videos_dir / f.name)
        elif f.suffix in (".png", ".jpg", ".jpeg"):
            shutil.copy2(f, images_dir / f.name)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
