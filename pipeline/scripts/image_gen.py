import asyncio
from pathlib import Path
from diffusers import StableDiffusionXLPipeline
import torch

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        model_id = "stabilityai/stable-diffusion-xl-base-1.0"
        _pipeline = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True
        ).to("cuda")
    return _pipeline

async def generate_image(prompt, style="editorial illustration, dramatic lighting", 
                         output_path="output.png", width=1024, height=1024):
    pipe = get_pipeline()
    full_prompt = f"{prompt}, {style}, high quality, professional"
    negative_prompt = "blurry, low quality, distorted, watermark, text"
    
    image = asyncio.get_event_loop().run_in_executor(
        None,
        lambda: pipe(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=30,
            guidance_scale=7.5
        ).images[0]
    )
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path

if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A journalist investigating corruption"
    asyncio.run(generate_image(prompt, output_path="test_image.png"))
    print("Image generated: test_image.png")
