"""Ejecuta el ciclo diario completo: contenido -> sitio -> publicacion."""
import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def main():
    from pipeline import run_pipeline
    from site_gen import build_site
    from publish import publish

    print("=" * 60)
    print("CORRECAMINOS - Ciclo diario")
    print("=" * 60)

    try:
        meta = await run_pipeline()
    except Exception:
        print("[Daily] Fallo generando contenido:")
        traceback.print_exc()
        return 1

    try:
        build_site()
    except Exception:
        print("[Daily] Fallo generando el sitio:")
        traceback.print_exc()
        return 2

    try:
        ok = publish()
    except Exception:
        print("[Daily] Fallo publicando:")
        traceback.print_exc()
        return 3

    print("=" * 60)
    print(f"OK -> {meta['title']} ({meta['duration']}s)")
    print("https://aielitemail-source.github.io/correcaminos/")
    print("=" * 60)
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))