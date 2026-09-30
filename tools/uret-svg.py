#!/usr/bin/env python3
"""Profil README'sindeki hareketli SVG'leri üretir.

Çıktılar (depo kökünde):
  assets/banner-dark.svg   assets/banner-light.svg
  assets/typing-dark.svg   assets/typing-light.svg

Kurallar:
  - Dış kaynak yok: font, görsel ya da servis çağrılmaz. Başlık yazıları
    Inter (SIL OFL 1.1) glif hatlarından path'e çevrilir; daktilo satırı
    sistemin eş aralıklı fontunu kullanır.
  - Hareket yalnız CSS @keyframes ile yapılır; prefers-reduced-motion: reduce
    olan tarayıcıda her şey durur ve okunur bir durağan kare kalır.

Kullanım:
  python3 tools/uret-svg.py [--font /yol/InterVariable.ttf]
Font verilmezse `fc-match "Inter Variable"` ile aranır. Gerekli paket: fontTools.
"""

import argparse
import html
import pathlib
import subprocess
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

KOK = pathlib.Path(__file__).resolve().parent.parent
ASSETS = KOK / "assets"

# Daktilo satırında sırayla yazılıp silinen cümleler.
SATIRLAR = [
    "Merhaba, ben Yunus.",
    "Otel operasyonunu AI ile yönetiyorum.",
    "Klinik asistanı dentai'yi geliştiriyorum.",
    "Çok ajanlı bir AI ofisi kuruyorum.",
]
# Hareket kapalıyken gösterilecek satır.
DURAGAN_SATIR = 1

TEMALAR = {
    "dark": {
        "bg0": "#06131a", "bg1": "#0b232b",
        "ink": "#e8fbf7", "ink2": "#9dbdb8",
        "acc": "#5eead4", "acc2": "#2dd4bf",
        "grid": "#5eead4",
        "plateTop0": "#5eead4", "plateTopOp0": 0.20, "plateTopOp1": 0.04,
        "sideL": "#0f3a3a", "sideR": "#0a2a2c", "plateStroke": "#5eead4",
        "sweep": "#ffffff", "sweepOp": 0.07,
        "chipFill": "#5eead4", "chipFillOp": 0.10, "chipStroke": "#5eead4",
        "card": "#0c1c22", "cardStroke": "#1d3a40", "typeInk": "#d8f6f0",
    },
    "light": {
        "bg0": "#f5fbfa", "bg1": "#e0f1ed",
        "ink": "#0c2b2a", "ink2": "#46625f",
        "acc": "#0f766e", "acc2": "#14b8a6",
        "grid": "#0f766e",
        "plateTop0": "#14b8a6", "plateTopOp0": 0.26, "plateTopOp1": 0.06,
        "sideL": "#a9ddd3", "sideR": "#92d0c5", "plateStroke": "#0f766e",
        "sweep": "#ffffff", "sweepOp": 0.55,
        "chipFill": "#0f766e", "chipFillOp": 0.08, "chipStroke": "#0f766e",
        "card": "#f3faf8", "cardStroke": "#cde5e0", "typeInk": "#12302e",
    },
}


def sayi(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# ---------------------------------------------------------------- font → path
class Yazici:
    """Değişken fonttan belirli ağırlıkta örnek alıp metni path'e çevirir."""

    def __init__(self, yol, wght, opsz):
        self.font = instantiateVariableFont(TTFont(yol), {"wght": wght, "opsz": opsz})
        self.cmap = self.font.getBestCmap()
        self.gs = self.font.getGlyphSet()
        self.upm = self.font["head"].unitsPerEm
        self.kern = self._kern_tablosu()

    def _kern_tablosu(self):
        gpos = self.font["GPOS"].table
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        alt = []
        for li in sorted(idx):
            lk = gpos.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "LookupType", 2) == 2 and hasattr(st, "Coverage"):
                    alt.append(st)
        return alt

    def _cift(self, sol, sag):
        for st in self.kern:
            if sol not in st.Coverage.glyphs:
                continue
            if st.Format == 1:
                ps = st.PairSet[st.Coverage.glyphs.index(sol)]
                for pvr in ps.PairValueRecord:
                    if pvr.SecondGlyph == sag:
                        return getattr(pvr.Value1, "XAdvance", 0) or 0
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs.get(sol, 0)
                c2 = st.ClassDef2.classDefs.get(sag, 0)
                v = st.Class1Record[c1].Class2Record[c2].Value1
                xa = getattr(v, "XAdvance", 0) or 0
                if xa:
                    return xa
        return 0

    def path(self, metin, boyut, x, y, iz=0.0):
        """(d, genişlik_px) döndürür. iz: harf arası, em cinsinden."""
        olcek = boyut / self.upm
        pen = SVGPathPen(self.gs, ntos=sayi)
        imlec = 0.0
        onceki = None
        for ch in metin:
            ad = self.cmap.get(ord(ch))
            if ad is None:
                raise SystemExit(f"fontta glif yok: {ch!r}")
            if onceki:
                imlec += self._cift(onceki, ad)
            tp = TransformPen(pen, (olcek, 0, 0, -olcek, x + imlec * olcek, y))
            self.gs[ad].draw(tp)
            imlec += self.font["hmtx"][ad][0] + iz * self.upm
            onceki = ad
        return pen.getCommands(), (imlec - iz * self.upm) * olcek


# ---------------------------------------------------------------- başlık
BANNER_W, BANNER_H = 1200, 320


def banner(t, yz):
    baslik, _ = yz["baslik"].path("Yunus", 104, 72, 132, iz=-0.02)
    alt, _ = yz["alt"].path("otel ve klinik için AI ürünleri", 36, 74, 188)

    # Ürün çipleri
    cipler = []
    cx = 72
    for i, ad in enumerate(["hotelai", "dentai"]):
        d, gen = yz["cip"].path(ad, 28, 0, 0)
        w = 24 + 10 + 12 + gen + 26
        cipler.append((cx, w, d, i))
        cx += w + 14

    # Katman yığını (izometrik plakalar)
    kx, kw, kh, kal = 940, 136, 68, 12
    plakalar = []
    for i in range(4):  # 0 = en üst
        cy = 98 + i * 40
        plakalar.append((i, cy))

    s = []
    a = s.append
    a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
      'role="img" aria-labelledby="t d">' % (BANNER_W, BANNER_H, BANNER_W, BANNER_H))
    a('<title id="t">Yunus — otel ve klinik için AI ürünleri: hotelai · dentai</title>')
    a('<desc id="d">Süzülen katmanlar ve sırayla beliren iki ürün adı: hotelai ve dentai.</desc>')
    a("<style>")
    a(".fl{animation:fl 7.2s ease-in-out infinite}")
    a("@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}")
    a(".f1{animation-delay:-.9s}.f2{animation-delay:-1.8s}.f3{animation-delay:-2.7s}")
    a(".dt{opacity:.3;animation:dt 6.4s ease-in-out infinite}")
    a("@keyframes dt{0%,100%{opacity:.3}14%{opacity:1}32%{opacity:.3}}")
    a(".sw{transform:translateX(-560px);animation:sw 12s cubic-bezier(.45,0,.3,1) infinite}")
    a("@keyframes sw{0%{transform:translateX(-560px)}42%,100%{transform:translateX(1480px)}}")
    a(".cp{animation:cp 1s cubic-bezier(.2,.7,.2,1) backwards}")
    a("@keyframes cp{from{opacity:0;transform:translateY(12px)}}")
    a(".c0{animation-delay:.5s}.c1{animation-delay:1.1s}")
    a(".gl{opacity:0;animation:gl 9s ease-in-out infinite}")
    a("@keyframes gl{0%,100%{opacity:0}22%{opacity:.95}48%{opacity:0}}")
    a(".g0{animation-delay:1.6s}.g1{animation-delay:6.1s}")
    a("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    a("</style>")

    a("<defs>")
    a('<clipPath id="k"><rect width="%d" height="%d" rx="18"/></clipPath>' % (BANNER_W, BANNER_H))
    a('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
      % (t["bg0"], t["bg1"]))
    a('<linearGradient id="pt" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0" stop-color="%s" stop-opacity="%s"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="%s"/></linearGradient>'
      % (t["plateTop0"], t["plateTopOp0"], t["plateTop0"], t["plateTopOp1"]))
    a('<linearGradient id="sg" x1="0" y1="0" x2="1" y2="0">'
      '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
      '<stop offset=".5" stop-color="%s" stop-opacity="%s"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
      % (t["sweep"], t["sweep"], t["sweepOp"], t["sweep"]))
    a('<radialGradient id="mg" cx="%s" cy="%s" r="560" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
      % (kx, 170))
    a('<mask id="m"><rect width="%d" height="%d" fill="url(#mg)"/></mask>' % (BANNER_W, BANNER_H))
    a('<pattern id="p" width="24" height="24" patternUnits="userSpaceOnUse">'
      '<circle cx="12" cy="12" r="1.1" fill="%s" fill-opacity=".28"/></pattern>' % t["grid"])
    a("</defs>")

    a('<g clip-path="url(#k)">')
    a('<rect width="%d" height="%d" fill="url(#bg)"/>' % (BANNER_W, BANNER_H))
    a('<rect width="%d" height="%d" fill="url(#p)" mask="url(#m)"/>' % (BANNER_W, BANNER_H))

    # Plakalar: alttan üste çizilir, üstteki alttakini örter.
    for i, cy in reversed(plakalar):
        L = (kx - kw, cy)
        T = (kx, cy - kh)
        R = (kx + kw, cy)
        B = (kx, cy + kh)
        f = lambda p: "%s,%s" % (sayi(p[0]), sayi(p[1]))
        a('<g class="fl f%d">' % i)
        a('<path d="M%s L%s L%s L%s Z" fill="%s"/>' % (
            f(L), f(B), f((B[0], B[1] + kal)), f((L[0], L[1] + kal)), t["sideL"]))
        a('<path d="M%s L%s L%s L%s Z" fill="%s"/>' % (
            f(B), f(R), f((R[0], R[1] + kal)), f((B[0], B[1] + kal)), t["sideR"]))
        a('<path d="M%s L%s L%s L%s Z" fill="url(#pt)" stroke="%s" stroke-opacity=".55" '
          'stroke-width="1.3" stroke-linejoin="round"/>' % (f(L), f(T), f(R), f(B), t["plateStroke"]))
        # Üst yüzdeki ışıklar: 3x3 ızgara, katmanlar boyunca yavaş bir dalga.
        for si, sv in enumerate((0.25, 0.5, 0.75)):
            for ti, tv in enumerate((0.25, 0.5, 0.75)):
                px = L[0] + sv * (T[0] - L[0]) + tv * (B[0] - L[0])
                py = L[1] + sv * (T[1] - L[1]) + tv * (B[1] - L[1])
                gecikme = (3 - i) * 0.55 + (si + ti) * 0.42
                a('<circle class="dt" style="animation-delay:%ss" cx="%s" cy="%s" r="2.7" fill="%s"/>'
                  % ("%.2f" % gecikme, sayi(px), sayi(py), t["acc"]))
        a("</g>")

    # Işık süzülmesi
    a('<g transform="skewX(-20)"><rect class="sw" x="0" y="-40" width="300" height="%d" fill="url(#sg)"/></g>'
      % (BANNER_H + 80))

    # Yazılar
    a('<path d="%s" fill="%s"/>' % (baslik, t["ink"]))
    a('<path d="%s" fill="%s"/>' % (alt, t["ink2"]))
    for x, w, d, i in cipler:
        y, h = 220, 54
        a('<g class="cp c%d">' % i)
        a('<rect class="gl g%d" x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="%s" '
          'stroke-opacity=".45" stroke-width="6"/>' % (i, sayi(x - 3), y - 3, sayi(w + 6), h + 6, (h + 6) / 2, t["acc2"]))
        a('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" fill-opacity="%s" stroke="%s" '
          'stroke-opacity=".5" stroke-width="1.4"/>' % (sayi(x), y, sayi(w), h, h / 2, t["chipFill"],
                                                         t["chipFillOp"], t["chipStroke"]))
        a('<circle cx="%s" cy="%s" r="5.5" fill="%s"/>' % (sayi(x + 29), y + h / 2, t["acc"]))
        a('<g transform="translate(%s %s)"><path d="%s" fill="%s"/></g>' % (
            sayi(x + 46), sayi(y + h / 2 + 10), d, t["ink"]))
        a("</g>")
    a("</g>")
    a("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- daktilo
def typing(t):
    fs = 22
    cw = round(fs * 0.6, 2)  # eş aralıklı fontlarda harf genişliği ≈ 0.6 em
    x0 = 60
    uzun = max(len(sat) for sat in SATIRLAR)
    W = int(x0 + uzun * cw + 48)
    H = 64
    taban = H / 2 + fs * 0.35

    yaz_ms, sil_ms, bekle, ara, bas = 72, 32, 1900, 420, 300
    dilimler = []
    zaman = bas
    for sat in SATIRLAR:
        n = len(sat)
        s0 = zaman
        s1 = s0 + n * yaz_ms
        s2 = s1 + bekle
        s3 = s2 + n * sil_ms
        dilimler.append((s0, s1, s2, s3))
        zaman = s3 + ara
    T = zaman

    def yuzde(ms):
        return "%.3f%%" % (ms / T * 100)

    eps = T * 0.0001
    s = []
    a = s.append
    a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
      'role="img" aria-labelledby="t">' % (W, H, W, H))
    a('<title id="t">%s</title>' % html.escape(" / ".join(SATIRLAR)))
    a("<style>")
    a("text{font:500 %dpx ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
      "'Liberation Mono','DejaVu Sans Mono',monospace;fill:%s}" % (fs, t["typeInk"]))
    # .st durağan satırdır: CSS animasyonu işleyen tarayıcıda hep saydam kalır;
    # animasyon yoksa (reduced-motion ya da animasyonsuz görüntüleyici) görünür.
    a(".st{animation:gz 1s infinite}@keyframes gz{from,to{opacity:0}}")
    a(".ln{opacity:0;animation:%dms linear infinite}" % T)
    a(".mv{animation:%dms linear infinite}" % T)
    a(".cr{animation:cr .9s ease-in-out infinite alternate}")
    a("@keyframes cr{from{opacity:1}to{opacity:.25}}")
    for i, (s0, s1, s2, s3) in enumerate(dilimler):
        n = len(SATIRLAR[i])
        L = n * cw
        a("@keyframes v%d{0%%,%s{opacity:0}%s,%s{opacity:1}%s,100%%{opacity:0}}" % (
            i, yuzde(max(s0 - eps, 0)), yuzde(s0), yuzde(s3), yuzde(s3 + eps)))
        a("@keyframes m%d{0%%,%s{transform:translateX(0);animation-timing-function:steps(%d,end)}"
          "%s,%s{transform:translateX(%spx);animation-timing-function:steps(%d,end)}"
          "%s,100%%{transform:translateX(0)}}" % (
              i, yuzde(s0), n, yuzde(s1), yuzde(s2), sayi(L), n, yuzde(s3)))
    a("@media (prefers-reduced-motion:reduce){.st,.ln,.mv,.cr{animation:none!important}}")
    a("</style>")
    a('<defs><clipPath id="k"><rect x="1" y="1" width="%d" height="%d" rx="13"/></clipPath></defs>'
      % (W - 2, H - 2))
    a('<rect x="1" y="1" width="%d" height="%d" rx="13" fill="%s"/>' % (W - 2, H - 2, t["card"]))
    a('<path d="M30 %s l8 6 -8 6" fill="none" stroke="%s" stroke-width="2.6" '
      'stroke-linecap="round" stroke-linejoin="round"/>' % (sayi(H / 2 - 6), t["acc"]))
    a('<text class="st" x="%s" y="%s" textLength="%s" lengthAdjust="spacing" xml:space="preserve">%s</text>'
      % (x0, sayi(taban), sayi(len(SATIRLAR[DURAGAN_SATIR]) * cw), html.escape(SATIRLAR[DURAGAN_SATIR])))
    a('<g clip-path="url(#k)">')
    for i, sat in enumerate(SATIRLAR):
        n = len(sat)
        L = n * cw
        a('<g class="ln ln%d" style="animation-name:v%d">' % (i, i))
        a('<text x="%s" y="%s" textLength="%s" lengthAdjust="spacing" xml:space="preserve">%s</text>'
          % (x0, sayi(taban), sayi(L), html.escape(sat)))
        a('<g class="mv" style="animation-name:m%d">' % i)
        a('<rect x="%s" y="4" width="%s" height="%d" fill="%s"/>' % (x0 - 1, sayi(L + 40), H - 8, t["card"]))
        a('<rect class="cr" x="%s" y="%s" width="2.6" height="%s" rx="1.3" fill="%s"/>' % (
            x0 + 1, sayi(taban - fs * 0.82), sayi(fs * 1.02), t["acc"]))
        a("</g></g>")
    a("</g>")
    a('<rect x="1" y="1" width="%d" height="%d" rx="13" fill="none" stroke="%s" stroke-width="1.2"/>'
      % (W - 2, H - 2, t["cardStroke"]))
    a("</svg>")
    return "\n".join(s) + "\n"


def font_bul():
    try:
        yol = subprocess.run(["fc-match", "-f", "%{file}", "Inter Variable"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        yol = ""
    if not yol or "Inter" not in pathlib.Path(yol).name:
        sys.exit("Inter Variable bulunamadı; --font ile yol ver.")
    return yol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font")
    arg = ap.parse_args()
    yol = arg.font or font_bul()
    yz = {
        "baslik": Yazici(yol, 760, 32),
        "alt": Yazici(yol, 450, 24),
        "cip": Yazici(yol, 620, 22),
    }
    ASSETS.mkdir(exist_ok=True)
    for ad, tema in TEMALAR.items():
        (ASSETS / f"banner-{ad}.svg").write_text(banner(tema, yz), encoding="utf-8")
        (ASSETS / f"typing-{ad}.svg").write_text(typing(tema), encoding="utf-8")
        print(f"yazıldı: assets/banner-{ad}.svg, assets/typing-{ad}.svg")


if __name__ == "__main__":
    main()
