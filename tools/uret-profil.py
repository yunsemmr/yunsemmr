"""GitHub profil afişi (koyu/açık) + maskot dosyaları. Kaynak: hello-siteler/marka-kiti + 00-TESLIM/instagram-profil-10ekim."""
import re
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KIT = Path.home() / "01-Gelistirme/hello-siteler/marka-kiti"
IG = Path.home() / "Masaüstü/00-TESLIM/instagram-profil-10ekim"
MASKOT = KOK / "assets/maskot"
MASKOT.mkdir(parents=True, exist_ok=True)

GOZ = ('<circle cx="46.7" cy="66.3" r="1.9" fill="#ffffff"/>'
       '<circle cx="85.2" cy="66.3" r="1.9" fill="#ffffff"/></svg>')


def parilti(svg: str) -> str:
    """Gözlere beyaz parıltı noktası (AgentAI/SocialAI ile aynı); zaten varsa dokunma."""
    return svg if 'cx="46.7"' in svg else svg.replace("</svg>", GOZ)


kaynak = {
    "hotelai": parilti((KIT / "isaret-hotelai.svg").read_text()),
    "dentai": parilti((KIT / "isaret-dentai.svg").read_text()),
    "agentai": (IG / "isaret-agentai.svg").read_text(),
    "socialai": (IG / "isaret-socialai.svg").read_text(),
}
for ad, svg in kaynak.items():
    (MASKOT / f"{ad}.svg").write_text(svg)
opone_logo = (KIT / "isaret.svg").read_text()


def ic(svg: str, onek: str) -> str:
    """Maskotu afişe gömmek için: kimlikleri öneklendir, dış svg etiketini at."""
    govde = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    govde = re.sub(r"<title>.*?</title>", "", govde)
    kimlikler = set(re.findall(r'id="([^"]+)"', govde))
    for k in sorted(kimlikler, key=len, reverse=True):
        govde = govde.replace(f'id="{k}"', f'id="{onek}{k}"').replace(f"url(#{k})", f"url(#{onek}{k})")
    return govde


TEMA = {
    "dark": dict(z1="#151a24", z2="#0b0c0f", yazi="#EDEDEF", ikinci="#9aa1ad", halka="#ffffff", halka_op="0.05",
                 logo="#EDEDEF", nokta="#ffb64d", etiket="#c5cad3"),
    "light": dict(z1="#ffffff", z2="#eef1f5", yazi="#14171c", ikinci="#5b6372", halka="#14171c", halka_op="0.06",
                  logo="#14171c", nokta="#f29a1f", etiket="#3a414d"),
}
SIRA = [("hotelai", "HotelAI", "konaklama"), ("dentai", "DentAI", "diş kliniği"),
        ("agentai", "AgentAI", "dijital ekip"), ("socialai", "SocialAI", "reklam ve içerik")]

for tema, r in TEMA.items():
    maskotlar = []
    for i, (ad, isim, alt) in enumerate(SIRA):
        x = 640 + i * 150
        maskotlar.append(
            f'<g class="m m{i}"><svg x="{x}" y="96" width="132" height="132" viewBox="0 0 128 128">'
            f'{ic(kaynak[ad], f"{ad}-")}</svg></g>'
            f'<text x="{x + 66}" y="262" text-anchor="middle" class="ad">{isim}</text>'
            f'<text x="{x + 66}" y="284" text-anchor="middle" class="alt">{alt}</text>')
    logo = ic(opone_logo, "op-").replace('stroke="currentColor"', f'stroke="{r["logo"]}"').replace(
        'fill="currentColor"', f'fill="{r["nokta"]}"')
    afis = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 360" width="1280" height="360" role="img" aria-label="OpOne — Operasyonun tamamı, tek bir ekranda">
<defs><linearGradient id="zemin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{r["z1"]}"/><stop offset="1" stop-color="{r["z2"]}"/></linearGradient></defs>
<style>
.baslik{{font:700 64px "Inter","Segoe UI",Helvetica,Arial,sans-serif;fill:{r["yazi"]};letter-spacing:-1.5px}}
.cumle{{font:500 22px "Inter","Segoe UI",Helvetica,Arial,sans-serif;fill:{r["yazi"]}}}
.ince{{font:400 16px "Inter","Segoe UI",Helvetica,Arial,sans-serif;fill:{r["ikinci"]}}}
.ad{{font:600 17px "Inter","Segoe UI",Helvetica,Arial,sans-serif;fill:{r["etiket"]}}}
.alt{{font:400 13px "Inter","Segoe UI",Helvetica,Arial,sans-serif;fill:{r["ikinci"]}}}
.m{{animation:salin 5.6s ease-in-out infinite}}
.m1{{animation-delay:-1.4s}} .m2{{animation-delay:-2.8s}} .m3{{animation-delay:-4.2s}}
@keyframes salin{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
@media (prefers-reduced-motion:reduce){{.m{{animation:none}}}}
</style>
<rect width="1280" height="360" rx="24" fill="url(#zemin)"/>
<circle cx="1180" cy="40" r="260" fill="none" stroke="{r["halka"]}" stroke-opacity="{r["halka_op"]}" stroke-width="2"/>
<circle cx="1180" cy="40" r="180" fill="none" stroke="{r["halka"]}" stroke-opacity="{r["halka_op"]}" stroke-width="2"/>
<svg x="64" y="78" width="72" height="72" viewBox="0 0 48 48">{logo}</svg>
<text x="152" y="138" class="baslik">OpOne</text>
<text x="66" y="196" class="cumle">Operasyonun tamamı, tek bir ekranda.</text>
<text x="66" y="228" class="ince">Otellere, kliniklere ve ekiplere yapay zekâ ile düzen.</text>
<text x="66" y="284" class="ince">hellopone.com</text>
{''.join(maskotlar)}
</svg>
'''
    (KOK / f"assets/afis-{tema}.svg").write_text(afis)
print("tamam:", sorted(p.name for p in (KOK / "assets").rglob("*.svg")))
