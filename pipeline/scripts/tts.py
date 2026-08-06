import edge_tts
import asyncio

async def generate_audio(text, voice="es-ES-ElviraNeural", rate="+0%", output_path="output.mp3"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)
    return output_path

async def list_voices(language="es"):
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]

if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Hola, esto es una prueba de Correcaminos."
    asyncio.run(generate_audio(text, output_path="test_audio.mp3"))
    print("Audio generated: test_audio.mp3")
