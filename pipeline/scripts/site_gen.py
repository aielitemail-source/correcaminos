"""Generador de sitio estatico para Correcaminos (sin dependencias externas)."""
import json
import html
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
POSTS_FILE = ROOT / "web" / "src" / "data" / "posts.json"
SITE_DIR = ROOT / "site"

CSS = """
:root{--bg:#0a0a0a;--bg-card:#141414;--bg-hover:#1c1c1c;--text:#f5f5f5;
--text-muted:#8a8a8a;--accent:#ef4444;--border:#232323}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);
color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.container{max-width:1180px;margin:0 auto;padding:0 1.5rem}
header{border-bottom:1px solid var(--border);position:sticky;top:0;
background:rgba(10,10,10,.85);backdrop-filter:blur(12px);z-index:50}
.nav{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{font-family:'Playfair Display',serif;font-weight:800;font-size:1.35rem;
letter-spacing:-.02em}
.logo span{color:var(--accent)}
.nav-links{display:flex;gap:1.75rem;font-size:.9rem;color:var(--text-muted);font-weight:500}
.nav-links a:hover{color:var(--text)}
.hero{padding:5rem 0 3.5rem;text-align:center;border-bottom:1px solid var(--border)}
.hero h1{font-family:'Playfair Display',serif;font-size:clamp(2.5rem,7vw,4.5rem);
font-weight:800;letter-spacing:-.035em;line-height:1.05}
.hero p{color:var(--text-muted);font-size:1.05rem;margin-top:1.1rem;
max-width:560px;margin-inline:auto}
.badge{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.12em;
text-transform:uppercase;color:var(--accent);border:1px solid var(--accent);
border-radius:999px;padding:.3rem .85rem;margin-bottom:1.5rem}
.section-title{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;
margin:3.5rem 0 1.5rem;letter-spacing:-.02em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:14px;
overflow:hidden;transition:transform .2s,border-color .2s}
.card:hover{transform:translateY(-3px);border-color:#333}
.card-media{aspect-ratio:16/9;overflow:hidden;background:#000}
.card-media img,.card-media video{width:100%;height:100%;object-fit:cover;display:block}
.card-body{padding:1.15rem 1.25rem 1.35rem}
.card-date{font-size:.72rem;color:var(--accent);font-weight:700;
text-transform:uppercase;letter-spacing:.09em}
.card h3{margin:.45rem 0 .5rem;font-size:1.08rem;font-weight:600;line-height:1.35}
.card p{font-size:.88rem;color:var(--text-muted);line-height:1.55}
.feature{display:grid;grid-template-columns:minmax(0,340px) 1fr;gap:2.5rem;
align-items:center;background:var(--bg-card);border:1px solid var(--border);
border-radius:18px;padding:1.75rem;margin-top:2.5rem}
.feature video{width:100%;border-radius:12px;display:block;background:#000}
.feature h2{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:700;
letter-spacing:-.02em;margin-bottom:.75rem}
.feature p{color:var(--text-muted);font-size:.98rem}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem}
.gallery img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px;
border:1px solid var(--border)}
.empty{text-align:center;padding:5rem 0;color:var(--text-muted)}
footer{border-top:1px solid var(--border);margin-top:5rem;padding:2.5rem 0;
color:var(--text-muted);font-size:.85rem;text-align:center}
@media(max-width:760px){.feature{grid-template-columns:1fr;gap:1.5rem}}
"""

HEAD = """<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
<header><div class="container nav">
<a href="./" class="logo">Corre<span>caminos</span></a>
<nav class="nav-links"><a href="./">Inicio</a><a href="./archivo.html">Archivo</a><a href="./about.html">Sobre</a></nav>
</div></header>"""

FOOT = """<footer><div class="container">
<p>Correcaminos &middot; Contenido generado automaticamente &middot; {year}</p>
</div></footer></body></html>"""


def esc(s):
    return html.escape(str(s or ""))


def card(post):
    cover = post.get("cover") or (post.get("images") or [""])[0]
    excerpt = (post.get("script") or "")[:130]
    if len(post.get("script") or "") > 130:
        excerpt += "..."
    return f"""<a class="card" href="./post-{esc(post['date'])}.html">
<div class="card-media"><img src="{esc(cover)}" alt="{esc(post.get('title'))}" loading="lazy"></div>
<div class="card-body"><span class="card-date">{esc(post['date'])}</span>
<h3>{esc(post.get('title'))}</h3><p>{esc(excerpt)}</p></div></a>"""


def build_index(posts):
    if not posts:
        body = '<div class="empty"><p>Proximamente contenido aqui.</p></div>'
    else:
        latest = posts[0]
        gallery = "".join(
            f'<img src="{esc(i)}" alt="escena" loading="lazy">'
            for i in latest.get("images", [])
        )
        rest = "".join(card(p) for p in posts[1:13])
        body = f"""<section class="container">
<div class="feature">
<video src="{esc(latest.get('video'))}" poster="{esc(latest.get('cover'))}" controls playsinline preload="metadata"></video>
<div><span class="card-date">{esc(latest['date'])}</span>
<h2>{esc(latest.get('title'))}</h2><p>{esc(latest.get('script'))}</p></div>
</div>
<h2 class="section-title">Imagenes del dia</h2>
<div class="gallery">{gallery}</div>
{'<h2 class="section-title">Anteriores</h2><div class="grid">' + rest + '</div>' if rest else ''}
</section>"""

    hero = """<section class="hero"><div class="container">
<span class="badge">Edicion diaria</span>
<h1>Correcaminos</h1>
<p>Corrupcion, transparencia y rendicion de cuentas. Un video y una serie de imagenes cada dia.</p>
</div></section>"""

    return (HEAD.format(title="Correcaminos - Corrupcion y transparencia",
                        desc="Contenido diario sobre corrupcion y transparencia",
                        css=CSS) + hero + body
            + FOOT.format(year=datetime.now().year))


def build_post(post):
    gallery = "".join(
        f'<img src="{esc(i)}" alt="escena" loading="lazy">'
        for i in post.get("images", [])
    )
    body = f"""<section class="container" style="padding:3.5rem 0">
<span class="card-date">{esc(post['date'])}</span>
<h1 style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:800;
letter-spacing:-.03em;margin:.5rem 0 1.75rem">{esc(post.get('title'))}</h1>
<video src="{esc(post.get('video'))}" poster="{esc(post.get('cover'))}" controls playsinline
style="width:100%;max-width:420px;border-radius:14px;display:block;background:#000"></video>
<p style="color:var(--text-muted);margin:1.75rem 0 2.5rem;max-width:700px;font-size:1.02rem">{esc(post.get('script'))}</p>
<h2 class="section-title" style="margin-top:0">Imagenes</h2>
<div class="gallery">{gallery}</div>
<p style="margin-top:3rem"><a href="./" style="color:var(--accent);font-weight:600">&larr; Volver</a></p>
</section>"""
    return (HEAD.format(title=f"{post.get('title')} - Correcaminos",
                        desc=(post.get("script") or "")[:150], css=CSS)
            + body + FOOT.format(year=datetime.now().year))


def build_archive(posts):
    grid = "".join(card(p) for p in posts) or '<div class="empty"><p>Sin entradas.</p></div>'
    body = f"""<section class="container" style="padding:3.5rem 0">
<h1 style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:800;
letter-spacing:-.03em;margin-bottom:2rem">Archivo</h1>
<div class="grid">{grid}</div></section>"""
    return (HEAD.format(title="Archivo - Correcaminos", desc="Todas las ediciones",
                        css=CSS) + body + FOOT.format(year=datetime.now().year))


def build_about():
    body = """<section class="container" style="padding:3.5rem 0;max-width:720px">
<h1 style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:800;
letter-spacing:-.03em;margin-bottom:1.5rem">Sobre Correcaminos</h1>
<p style="color:var(--text-muted);font-size:1.02rem;margin-bottom:1rem">
Correcaminos publica cada dia una pieza corta de video y una serie de imagenes
sobre corrupcion, transparencia y rendicion de cuentas.</p>
<p style="color:var(--text-muted);font-size:1.02rem">
Todo el contenido se genera y publica de forma automatica mediante un pipeline
local: sintesis de voz, generacion de imagenes y montaje de video.</p>
</section>"""
    return (HEAD.format(title="Sobre - Correcaminos", desc="Sobre el proyecto", css=CSS)
            + body + FOOT.format(year=datetime.now().year))


def load_posts():
    if not POSTS_FILE.exists():
        return []
    with open(POSTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_site():
    posts = load_posts()
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (SITE_DIR / "index.html").write_text(build_index(posts), encoding="utf-8")
    (SITE_DIR / "archivo.html").write_text(build_archive(posts), encoding="utf-8")
    (SITE_DIR / "about.html").write_text(build_about(), encoding="utf-8")
    for p in posts:
        (SITE_DIR / f"post-{p['date']}.html").write_text(build_post(p), encoding="utf-8")

    import shutil
    media_src = ROOT / "web" / "public" / "media"
    media_dst = SITE_DIR / "media"
    if media_src.exists():
        if media_dst.exists():
            shutil.rmtree(media_dst)
        shutil.copytree(media_src, media_dst)

    print(f"[Site] Built {len(posts)} posts -> {SITE_DIR}")
    return SITE_DIR


if __name__ == "__main__":
    build_site()