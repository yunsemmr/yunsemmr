#!/usr/bin/env python3
"""Profil README'sindeki hareketli SVG'leri üretir (HeyAgent estetiği).

Çıktılar (depo kökünde):
  assets/banner-dark.svg   assets/banner-light.svg
  assets/typing-dark.svg   assets/typing-light.svg

Görünüm: HeyAgent paleti (zemin #090B0D, mint #79E7C5), üstte yaylı açılıp kapanan siyah
ada, sağda Astra kurallarıyla akan mini terminal (❯ kullanıcı şeridi, ● ajan, camgöbeği
araç, yeşil/kırmızı fark).

Maskot: adadaki yuvada şimdilik HeyAgent'ın terminal işareti `>_` var. Mochi (coucou)
yalnız iç kullanım izniyle kullanılıyor; kamuya açık profile ancak sahibinin YAYIN izni
yazılı gelince girer (kendi-ofis/docs/izinler/coucou-mochi.md).

Kurallar:
  - Dış kaynak yok: font, görsel ya da servis çağrılmaz. Başlık ve terminal yazıları
    Inter (SIL OFL 1.1) ve JetBrains Mono (SIL OFL 1.1) glif hatlarından path'e çevrilir;
    daktilo satırı sistemin eş aralıklı fontunu kullanır.
  - Hareket yalnız CSS @keyframes ile yapılır; prefers-reduced-motion: reduce olan
    tarayıcıda her şey durur ve okunur bir durağan kare kalır (ada açık, satırlar dolu).

Kullanım:
  python3 tools/uret-svg.py [--font /yol/InterVariable.ttf] [--mono /yol/Mono-Regular.ttf]
Font verilmezse fc-match ile aranır. Gerekli paket: fontTools.
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
    "heyagent: AI ajanlarımla bir ofis kuruyorum.",
    "heyhotelai: otel operasyonunu AI ile yönetiyorum.",
    "heydentai: klinikler için AI asistanı geliştiriyorum.",
]
# Hareket kapalıyken gösterilecek satır.
DURAGAN_SATIR = 1

URUNLER = ["heyagent", "heyhotelai", "heydentai"]

# Mini terminal: her satır (metin, renk anahtarı, kalın mı) parçalarından oluşur.
# "serit" satırı kullanıcı satırıdır (düz zemin şeridi + ❯).
TERMINAL = [
    ("serit", [("❯ ", "acc", True), ("profil README'sini yenile", "ink", False)]),
    ("", [("● ", "ink", False), ("Arda", "ink", True), ("  tasarımı çiziyor", "ink2", False)]),
    ("", [("  └ ", "ink2", False), ("Edit", "cyan", True), ("  assets/banner-dark.svg", "ink2", False)]),
    ("", [("      ", "ink2", False), ("+128", "yesil", True), ("  ", "ink2", False), ("−41", "kirmizi", True)]),
    ("", [("● ", "ink", False), ("Lina", "ink", True), ("  önizlemeyi doğruluyor", "ink2", False)]),
    ("", [("  └ ", "ink2", False), ("Bash", "cyan", True), ("  python3 tools/uret-svg.py", "ink2", False)]),
    ("son", [("● ", "acc", False), ("hazır", "acc", True), ("  2 dosya · kanıtlı", "ink2", False)]),
]

TEMALAR = {
    "dark": {
        "bg": "#090b0d", "glow": "#79e7c5", "glowOp": 0.13, "grid": "#79e7c5", "gridOp": 0.22,
        "ink": "#ededef", "ink2": "#8e959d",
        "acc": "#79e7c5", "cyan": "#67e8f9", "yesil": "#4ade80", "kirmizi": "#f87171",
        "card": "#111417", "cardStroke": "#22282e", "serit": "#191d21",
        "chip": "#111417", "chipStroke": "#262c33", "chipOn": "#79e7c5",
        "ada": "#000000", "adaRing": "#2a3037", "adaInk": "#ededef", "adaInk2": "#8e959d",
        "golge": 0.55, "typeInk": "#e6e8ea",
    },
    "light": {
        "bg": "#f6f7f8", "glow": "#79e7c5", "glowOp": 0.30, "grid": "#087d61", "gridOp": 0.16,
        "ink": "#0b0d0f", "ink2": "#5b6168",
        "acc": "#087d61", "cyan": "#0e7490", "yesil": "#15803d", "kirmizi": "#b91c1c",
        "card": "#ffffff", "cardStroke": "#e1e4e8", "serit": "#f0f2f4",
        "chip": "#ffffff", "chipStroke": "#dfe3e7", "chipOn": "#087d61",
        "ada": "#000000", "adaRing": "#000000", "adaInk": "#ededef", "adaInk2": "#9aa0a6",
        "golge": 0.14, "typeInk": "#15191d",
    },
}


def sayi(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# ---------------------------------------------------------------- font → path
class Yazici:
    """Fonttan (değişkense belirli ağırlıkta örnek alıp) metni path'e çevirir."""

    def __init__(self, yol, wght=None, opsz=None):
        font = TTFont(yol)
        if "fvar" in font:
            eksen = {"wght": wght}
            if opsz is not None:
                eksen["opsz"] = opsz
            font = instantiateVariableFont(font, eksen)
        self.font = font
        self.cmap = font.getBestCmap()
        self.gs = font.getGlyphSet()
        self.upm = font["head"].unitsPerEm
        self.kern = self._kern_tablosu()

    def _kern_tablosu(self):
        if "GPOS" not in self.font:
            return []
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

    def genislik(self, metin, boyut, iz=0.0):
        return self.path(metin, boyut, 0, 0, iz)[1]


# ---------------------------------------------------------------- başlık
BANNER_W, BANNER_H = 1200, 340
DONGU = 10  # saniye: ada ve terminal aynı döngüde
# Döngü "ada açık + terminal dolu" karesinden başlar; yoksa ziyaretçi ilk ~2,5 sn boş pencere görür.
BASLA = -6.2

# Ada: açıkken 440x40, kapalıyken 150x40; merkez x=600.
ADA_CX, ADA_Y, ADA_H, ADA_ACIK, ADA_KAPALI = 600, 20, 40, 440, 150


def banner(t, yz):
    s = []
    a = s.append

    a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
      'role="img" aria-labelledby="t d">' % (BANNER_W, BANNER_H, BANNER_W, BANNER_H))
    a('<title id="t">Yunus · heyone — heyagent · heyhotelai · heydentai</title>')
    a('<desc id="d">Üstte açılıp kapanan siyah ada, solda ad ve üç ürün, sağda AI ajanlarının '
      'satır satır çalıştığı bir terminal.</desc>')

    # ---- hareket
    r = ADA_H / 2
    kayma = (ADA_ACIK - ADA_KAPALI) / 2
    orta_olcek = (ADA_KAPALI - ADA_H) / (ADA_ACIK - ADA_H)
    yay = "cubic-bezier(.34,1.5,.64,1)"
    a("<style>")
    a(".am,.al,.ar{transform-box:fill-box;animation:%ds %s %ss infinite}" % (DONGU, yay, BASLA))
    a(".am{transform-origin:center;animation-name:am}.al{animation-name:al}.ar{animation-name:ar}")
    a("@keyframes am{0%%,10%%{transform:scaleX(%.4f)}22%%,72%%{transform:scaleX(1)}"
      "84%%,100%%{transform:scaleX(%.4f)}}" % (orta_olcek, orta_olcek))
    a("@keyframes al{0%%,10%%{transform:translateX(%spx)}22%%,72%%{transform:translateX(0)}"
      "84%%,100%%{transform:translateX(%spx)}}" % (sayi(kayma), sayi(kayma)))
    a("@keyframes ar{0%%,10%%{transform:translateX(-%spx)}22%%,72%%{transform:translateX(0)}"
      "84%%,100%%{transform:translateX(-%spx)}}" % (sayi(kayma), sayi(kayma)))
    a(".ai{animation:ai %ds ease-in-out %ss infinite}" % (DONGU, BASLA))
    a("@keyframes ai{0%,19%{opacity:0}27%,67%{opacity:1}73%,100%{opacity:0}}")
    a(".nb{animation:nb 1.6s ease-in-out infinite}@keyframes nb{50%{opacity:.3}}")
    a(".cp{animation:cp .9s cubic-bezier(.2,.7,.2,1) backwards}")
    a("@keyframes cp{from{opacity:0;transform:translateY(10px)}}")
    a(".c0{animation-delay:.4s}.c1{animation-delay:.8s}.c2{animation-delay:1.2s}")
    a(".im{animation:im 1s steps(1) infinite}@keyframes im{50%{opacity:0}}")
    satir_bas, satir_ara, sonus = 24, 6.2, 93
    for i in range(len(TERMINAL)):
        gor = satir_bas + i * satir_ara
        a(".s%d{animation:s%d %ds ease-out %ss infinite}" % (i, i, DONGU, BASLA))
        a("@keyframes s%d{0%%,%.1f%%{opacity:0;transform:translateY(4px)}%.1f%%,%d%%{opacity:1;"
          "transform:translateY(0)}%d%%,100%%{opacity:0}}" % (i, gor, gor + 2.5, sonus, sonus + 4))
    a("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    a("</style>")

    # ---- tanımlar
    a("<defs>")
    a('<clipPath id="k"><rect width="%d" height="%d" rx="20"/></clipPath>' % (BANNER_W, BANNER_H))
    a('<radialGradient id="pa" cx="960" cy="40" r="520" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="%s" stop-opacity="%s"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
      % (t["glow"], t["glowOp"], t["glow"]))
    a('<radialGradient id="mg" cx="900" cy="170" r="620" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>')
    a('<mask id="m"><rect width="%d" height="%d" fill="url(#mg)"/></mask>' % (BANNER_W, BANNER_H))
    a('<pattern id="p" width="24" height="24" patternUnits="userSpaceOnUse">'
      '<circle cx="12" cy="12" r="1" fill="%s" fill-opacity="%s"/></pattern>' % (t["grid"], t["gridOp"]))
    a('<filter id="g" x="-20%%" y="-20%%" width="140%%" height="150%%">'
      '<feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000" flood-opacity="%s"/></filter>'
      % t["golge"])
    a("</defs>")

    a('<g clip-path="url(#k)">')
    a('<rect width="%d" height="%d" fill="%s"/>' % (BANNER_W, BANNER_H, t["bg"]))
    a('<rect width="%d" height="%d" fill="url(#p)" mask="url(#m)"/>' % (BANNER_W, BANNER_H))
    a('<rect width="%d" height="%d" fill="url(#pa)"/>' % (BANNER_W, BANNER_H))

    # ---- ada
    sol_cx, sag_cx = ADA_CX - ADA_ACIK / 2 + r, ADA_CX + ADA_ACIK / 2 - r
    cy = ADA_Y + r
    for ek, renk in ((1.2, t["adaRing"]), (0, t["ada"])):
        a('<g fill="%s">' % renk)
        a('<rect class="am" x="%s" y="%s" width="%s" height="%s"/>' % (
            sayi(sol_cx), sayi(ADA_Y - ek), sayi(sag_cx - sol_cx), sayi(ADA_H + 2 * ek)))
        a('<circle class="al" cx="%s" cy="%s" r="%s"/>' % (sayi(sol_cx), sayi(cy), sayi(r + ek)))
        a('<circle class="ar" cx="%s" cy="%s" r="%s"/>' % (sayi(sag_cx), sayi(cy), sayi(r + ek)))
        a("</g>")
    # Ada içi: maskot yuvası (>_), ürün adı, çalışan ajan sayısı
    ix = sol_cx - 4
    a('<g class="ai">')
    a('<path d="M%s %s l7 6 -7 6" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round" '
      'stroke-linejoin="round"/>' % (sayi(ix), sayi(cy - 6), t["acc"]))
    a('<path d="M%s %s h9" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round"/>'
      % (sayi(ix + 11), sayi(cy + 6), t["acc"]))
    d, _ = yz["ada"].path("heyagent", 17, ix + 30, cy + 6)
    a('<path d="%s" fill="%s"/>' % (d, t["adaInk"]))
    etiket = "3 ajan çalışıyor"
    eg = yz["kucuk"].genislik(etiket, 14)
    d, _ = yz["kucuk"].path(etiket, 14, sag_cx + 4 - eg, cy + 5)
    a('<path d="%s" fill="%s"/>' % (d, t["adaInk2"]))
    a('<circle class="nb" cx="%s" cy="%s" r="4" fill="%s"/>' % (sayi(sag_cx - eg - 8), sayi(cy), "#4ade80"))
    a("</g>")

    # ---- sol blok
    x0 = 72
    d, _ = yz["etiket"].path("HEYONE", 15, x0 + 2, 114, iz=0.22)
    a('<path d="%s" fill="%s"/>' % (d, t["acc"]))
    d, _ = yz["baslik"].path("Yunus", 98, x0, 204, iz=-0.025)
    a('<path d="%s" fill="%s"/>' % (d, t["ink"]))
    d, _ = yz["alt"].path("AI ajanlarıyla ürün geliştiriyorum", 26, x0 + 2, 246)
    a('<path d="%s" fill="%s"/>' % (d, t["ink2"]))

    cx, cy0, ch = x0, 270, 44
    for i, ad in enumerate(URUNLER):
        gen = yz["cip"].genislik(ad, 19)
        w = 20 + 8 + 10 + gen + 20
        vurgu = i == 0
        a('<g class="cp c%d">' % i)
        a('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
            sayi(cx), cy0, sayi(w), ch, ch / 2, t["chip"], t["chipOn"] if vurgu else t["chipStroke"]))
        a('<circle cx="%s" cy="%s" r="4.5" fill="%s"/>' % (sayi(cx + 24), cy0 + ch / 2, t["acc"]))
        d, _ = yz["cip"].path(ad, 19, cx + 38, cy0 + ch / 2 + 6.5)
        a('<path d="%s" fill="%s"/>' % (d, t["ink"]))
        a("</g>")
        cx += w + 12

    # ---- terminal
    tx, ty, tw, th = 690, 92, 440, 226
    a('<g filter="url(#g)"><rect x="%d" y="%d" width="%d" height="%d" rx="14" fill="%s" stroke="%s" '
      'stroke-width="1.2"/></g>' % (tx, ty, tw, th, t["card"], t["cardStroke"]))
    for j, renk in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a('<circle cx="%d" cy="%d" r="5.5" fill="%s"/>' % (tx + 20 + j * 18, ty + 17, renk))
    baslik = "heyagent — ofis"
    bg = yz["kucuk"].genislik(baslik, 13)
    d, _ = yz["kucuk"].path(baslik, 13, tx + tw / 2 - bg / 2, ty + 21.5)
    a('<path d="%s" fill="%s"/>' % (d, t["ink2"]))
    a('<path d="M%d %d h%d" stroke="%s" stroke-width="1"/>' % (tx, ty + 34, tw, t["cardStroke"]))

    fs, adim = 15.5, 24
    sx, sy = tx + 18, ty + 62
    for i, (tur, parcalar) in enumerate(TERMINAL):
        y = sy + i * adim
        a('<g class="s%d">' % i)
        if tur == "serit":
            a('<rect x="%d" y="%s" width="%d" height="%d" fill="%s"/>' % (
                tx + 1, sayi(y - 17), tw - 2, 24, t["serit"]))
        x = sx
        for metin, renk, kalin in parcalar:
            yazici = yz["mono_kalin"] if kalin else yz["mono"]
            if metin == "❯ ":
                a('<path d="M%s %s l6 5.5 -6 5.5" fill="none" stroke="%s" stroke-width="2.4" '
                  'stroke-linecap="round" stroke-linejoin="round"/>' % (sayi(x + 1.5), sayi(y - 11), t[renk]))
                x += yazici.genislik(metin, fs)
                continue
            d, gen = yazici.path(metin, fs, x, y)
            if d:
                a('<path d="%s" fill="%s"/>' % (d, t[renk]))
            x += gen
        if tur == "son":
            a('<rect class="im" x="%s" y="%s" width="9" height="17" rx="1.5" fill="%s"/>' % (
                sayi(x + 6), sayi(y - 13.5), t["acc"]))
        a("</g>")

    a("</g>")
    a("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- daktilo
def typing(t):
    fs = 21
    cw = round(fs * 0.6, 2)  # eş aralıklı fontlarda harf genişliği ≈ 0.6 em
    x0 = 58
    uzun = max(len(sat) for sat in SATIRLAR)
    W = int(x0 + uzun * cw + 48)
    H = 60
    taban = H / 2 + fs * 0.35

    yaz_ms, sil_ms, bekle, ara, bas = 64, 26, 2100, 420, 300
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
    a("text{font:500 %dpx ui-monospace,SFMono-Regular,'SF Mono','JetBrains Mono',Menlo,Consolas,"
      "'Liberation Mono','DejaVu Sans Mono',monospace;fill:%s}" % (fs, t["typeInk"]))
    # .st durağan satırdır: CSS animasyonu işleyen tarayıcıda hep saydam kalır;
    # animasyon yoksa (reduced-motion ya da animasyonsuz görüntüleyici) görünür.
    a(".st{animation:gz 1s infinite}@keyframes gz{from,to{opacity:0}}")
    a(".ln{opacity:0;animation:%dms linear infinite}" % T)
    a(".mv{animation:%dms linear infinite}" % T)
    a(".cr{animation:cr 1s steps(1) infinite}")
    a("@keyframes cr{50%{opacity:0}}")
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
    a('<defs><clipPath id="k"><rect x="1" y="1" width="%d" height="%d" rx="14"/></clipPath></defs>'
      % (W - 2, H - 2))
    a('<rect x="1" y="1" width="%d" height="%d" rx="14" fill="%s"/>' % (W - 2, H - 2, t["card"]))
    a('<path d="M26 %s l8 6 -8 6" fill="none" stroke="%s" stroke-width="2.6" '
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
        a('<rect class="cr" x="%s" y="%s" width="10" height="%s" rx="1.5" fill="%s"/>' % (
            x0 + 1, sayi(taban - fs * 0.8), sayi(fs * 0.98), t["acc"]))
        a("</g></g>")
    a("</g>")
    a('<rect x="1" y="1" width="%d" height="%d" rx="14" fill="none" stroke="%s" stroke-width="1.2"/>'
      % (W - 2, H - 2, t["cardStroke"]))
    a("</svg>")
    return "\n".join(s) + "\n"


def font_bul(desen, ad_parcasi):
    try:
        yol = subprocess.run(["fc-match", "-f", "%{file}", desen],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        yol = ""
    if not yol or ad_parcasi not in pathlib.Path(yol).name:
        sys.exit(f"{desen} bulunamadı; yolu bayrakla ver.")
    return yol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", help="Inter Variable .ttf")
    ap.add_argument("--mono", help="JetBrains Mono Regular .ttf")
    ap.add_argument("--mono-kalin", help="JetBrains Mono Bold .ttf")
    arg = ap.parse_args()
    inter = arg.font or font_bul("Inter Variable", "Inter")
    mono = arg.mono or font_bul("JetBrainsMono Nerd Font:style=Regular", "JetBrains")
    mono_kalin = arg.mono_kalin or font_bul("JetBrainsMono Nerd Font:style=Bold", "JetBrains")
    yz = {
        "baslik": Yazici(inter, 780, 32),
        "alt": Yazici(inter, 450, 24),
        "etiket": Yazici(inter, 700, 14),
        "cip": Yazici(inter, 620, 20),
        "ada": Yazici(inter, 640, 18),
        "kucuk": Yazici(inter, 500, 14),
        "mono": Yazici(mono),
        "mono_kalin": Yazici(mono_kalin),
    }
    ASSETS.mkdir(exist_ok=True)
    for ad, tema in TEMALAR.items():
        (ASSETS / f"banner-{ad}.svg").write_text(banner(tema, yz), encoding="utf-8")
        (ASSETS / f"typing-{ad}.svg").write_text(typing(tema), encoding="utf-8")
        print(f"yazıldı: assets/banner-{ad}.svg, assets/typing-{ad}.svg")


if __name__ == "__main__":
    main()
