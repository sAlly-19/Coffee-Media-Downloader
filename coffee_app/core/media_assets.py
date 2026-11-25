"""Recursos visuais, SVGs, thumbnails e ícones Pillow do CoffeeMediaDownloader Pro."""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from coffee_app.core.storage import get_app_data_dir


def round_corners(img: Image.Image, radius: int = 10) -> Image.Image:
    """Aplica cantos arredondados com canal alfa em uma imagem Pillow."""
    rgba = img.convert("RGBA")
    mask = Image.new("L", rgba.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, rgba.width, rgba.height), radius=radius, fill=255)
    rgba.putalpha(mask)
    return rgba


COFFEE_CUP_BASE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="cupBody" x1="15%" y1="10%" x2="90%" y2="95%">
      <stop offset="0%" stop-color="#FFFBF7"/>
      <stop offset="55%" stop-color="#F2E2D4"/>
      <stop offset="100%" stop-color="#C89E7E"/>
    </linearGradient>
    <linearGradient id="handleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F4E5D7"/>
      <stop offset="100%" stop-color="#B98B6A"/>
    </linearGradient>
    <radialGradient id="coffeeTop" cx="45%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#8B451E"/>
      <stop offset="65%" stop-color="#4A220F"/>
      <stop offset="100%" stop-color="#2B1207"/>
    </radialGradient>
    <linearGradient id="saucerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#C49A7B"/>
      <stop offset="45%" stop-color="#F7EADF"/>
      <stop offset="100%" stop-color="#A87A59"/>
    </linearGradient>
    <linearGradient id="playGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4B2513"/>
      <stop offset="100%" stop-color="#261007"/>
    </linearGradient>
  </defs>

  <!-- Pires elegante -->
  <ellipse cx="62" cy="109" rx="34" ry="5.5" fill="#5A2F19" opacity="0.65"/>
  <ellipse cx="62" cy="105" rx="41" ry="7.5" fill="url(#saucerGrad)"/>
  <ellipse cx="62" cy="104" rx="28" ry="4" fill="#8C5939" opacity="0.35"/>

  <!-- Alca graciosa -->
  <path d="M93 58 C113 57, 114 86, 89 88" fill="none" stroke="url(#handleGrad)" stroke-width="7.5" stroke-linecap="round"/>
  <path d="M93 58 C111 58, 111 84, 89 86" fill="none" stroke="#FFFBF7" stroke-width="2" stroke-linecap="round" opacity="0.45"/>

  <!-- Corpo afunilado da xicara -->
  <path d="M27 51 C27 84, 38 104, 62 104 C86 104, 97 84, 97 51 Z" fill="url(#cupBody)"/>
  <!-- Brilho sutil lateral esquerdo -->
  <path d="M33 56 C33 78, 39 92, 47 97 C42 88, 39 74, 39 56 Z" fill="#FFFFFF" opacity="0.45"/>

  <!-- Borda e cafe expresso -->
  <ellipse cx="62" cy="51" rx="35" ry="9" fill="#F8ECE1"/>
  <ellipse cx="62" cy="51.5" rx="31" ry="6.5" fill="url(#coffeeTop)"/>
  <path d="M40 50.5 C46 47, 58 46.5, 68 47.5" fill="none" stroke="#C97A42" stroke-width="1.6" stroke-linecap="round" opacity="0.55"/>

  <!-- Emblema Play central -->
  <circle cx="62" cy="77" r="14.5" fill="url(#playGrad)" stroke="#D97736" stroke-width="1.8"/>
  <path d="M58 70.5 L70 77 L58 83.5 Z" fill="#FFF8F2" stroke="#FFF8F2" stroke-width="1.5" stroke-linejoin="round"/>
</svg>"""


COFFEE_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <radialGradient id="aura" cx="50%" cy="56%" r="46%">
      <stop offset="0%" stop-color="#E0823E" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#E0823E" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="cupBody" x1="15%" y1="10%" x2="90%" y2="95%">
      <stop offset="0%" stop-color="#FFFBF7"/>
      <stop offset="55%" stop-color="#F2E2D4"/>
      <stop offset="100%" stop-color="#C89E7E"/>
    </linearGradient>
    <linearGradient id="handleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F4E5D7"/>
      <stop offset="100%" stop-color="#B98B6A"/>
    </linearGradient>
    <radialGradient id="coffeeTop" cx="45%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#8B451E"/>
      <stop offset="65%" stop-color="#4A220F"/>
      <stop offset="100%" stop-color="#2B1207"/>
    </radialGradient>
    <linearGradient id="saucerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#C49A7B"/>
      <stop offset="45%" stop-color="#F7EADF"/>
      <stop offset="100%" stop-color="#A87A59"/>
    </linearGradient>
    <linearGradient id="steamGrad" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#E69352" stop-opacity="0.88"/>
      <stop offset="65%" stop-color="#F7CCA2" stop-opacity="0.65"/>
      <stop offset="100%" stop-color="#FFF3E6" stop-opacity="0.05"/>
    </linearGradient>
    <linearGradient id="playGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4B2513"/>
      <stop offset="100%" stop-color="#261007"/>
    </linearGradient>
  </defs>

  <circle cx="62" cy="70" r="56" fill="url(#aura)"/>

  <!-- Vapor fluido em fitas afiladas -->
  <path d="M46 42 C41 35, 48 28, 43 20 C49 26, 47 35, 48 42 Z" fill="url(#steamGrad)"/>
  <path d="M62 40 C55 30, 69 20, 61 9 C69 18, 61 30, 65 40 Z" fill="url(#steamGrad)"/>
  <path d="M78 42 C83 34, 76 27, 81 19 C75 26, 79 34, 76 42 Z" fill="url(#steamGrad)"/>

  <!-- Pires elegante -->
  <ellipse cx="62" cy="109" rx="34" ry="5.5" fill="#5A2F19" opacity="0.65"/>
  <ellipse cx="62" cy="105" rx="41" ry="7.5" fill="url(#saucerGrad)"/>
  <ellipse cx="62" cy="104" rx="28" ry="4" fill="#8C5939" opacity="0.35"/>

  <!-- Alca graciosa -->
  <path d="M93 58 C113 57, 114 86, 89 88" fill="none" stroke="url(#handleGrad)" stroke-width="7.5" stroke-linecap="round"/>
  <path d="M93 58 C111 58, 111 84, 89 86" fill="none" stroke="#FFFBF7" stroke-width="2" stroke-linecap="round" opacity="0.45"/>

  <!-- Corpo afunilado da xicara -->
  <path d="M27 51 C27 84, 38 104, 62 104 C86 104, 97 84, 97 51 Z" fill="url(#cupBody)"/>
  <!-- Brilho sutil lateral esquerdo -->
  <path d="M33 56 C33 78, 39 92, 47 97 C42 88, 39 74, 39 56 Z" fill="#FFFFFF" opacity="0.45"/>

  <!-- Borda e cafe expresso -->
  <ellipse cx="62" cy="51" rx="35" ry="9" fill="#F8ECE1"/>
  <ellipse cx="62" cy="51.5" rx="31" ry="6.5" fill="url(#coffeeTop)"/>
  <path d="M40 50.5 C46 47, 58 46.5, 68 47.5" fill="none" stroke="#C97A42" stroke-width="1.6" stroke-linecap="round" opacity="0.55"/>

  <!-- Emblema Play central -->
  <circle cx="62" cy="77" r="14.5" fill="url(#playGrad)" stroke="#D97736" stroke-width="1.8"/>
  <path d="M58 70.5 L70 77 L58 83.5 Z" fill="#FFF8F2" stroke="#FFF8F2" stroke-width="1.5" stroke-linejoin="round"/>
</svg>"""


def create_coffee_logo_image(size: tuple[int, int] = (72, 72)) -> Image.Image:
    """Desenha uma versao Pillow refinada da xicara afunilada com botao play."""
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Pires fino e elegante
    draw.ellipse((w * 0.16, h * 0.80, w * 0.80, h * 0.89), fill="#B88968")
    draw.ellipse((w * 0.18, h * 0.79, w * 0.78, h * 0.87), fill="#EADAD0")

    # Alca curva
    draw.arc(
        (w * 0.65, h * 0.44, w * 0.89, h * 0.71),
        start=270,
        end=90,
        fill="#E8D6C6",
        width=max(4, int(w * 0.052)),
    )

    # Corpo afunilado da xicara via poligono suavizado
    pts = []
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        x = w * (0.21 + 0.09 * (t ** 1.6))
        y = h * (0.40 + 0.43 * t)
        pts.append((x, y))
    for i in range(steps, -1, -1):
        t = i / steps
        x = w * (0.75 - 0.09 * (t ** 1.6))
        y = h * (0.40 + 0.43 * t)
        pts.append((x, y))
    draw.polygon(pts, fill="#F7ECE2")
    draw.ellipse((w * 0.30, h * 0.76, w * 0.66, h * 0.85), fill="#E9D6C6")

    # Borda e cafe escuro
    draw.ellipse((w * 0.21, h * 0.35, w * 0.75, h * 0.46), fill="#FFF9F3")
    draw.ellipse((w * 0.24, h * 0.365, w * 0.72, h * 0.445), fill="#4E2511")

    # Botao Play escuro com aro caramelo
    cx, cy = w * 0.48, h * 0.60
    r = w * 0.115
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#3B1A0C", outline="#D97736", width=max(2, int(w * 0.015)))
    tri = [
        (cx - r * 0.28, cy - r * 0.44),
        (cx - r * 0.28, cy + r * 0.44),
        (cx + r * 0.48, cy),
    ]
    draw.polygon(tri, fill="#FFF8F2")

    return canvas.resize(size, Image.Resampling.LANCZOS)


def create_placeholder_thumbnail(
    size: tuple[int, int] = (128, 72),
    is_audio: bool = False,
) -> Image.Image:
    """Gera uma miniatura padrão elegante em tons de café enquanto carrega ou sem imagem."""
    img = Image.new("RGBA", size, "#2F1F17")
    draw = ImageDraw.Draw(img)
    w, h = size
    # Gradiente sutil simulado em faixas quentes
    draw.rectangle((0, 0, w, h // 2), fill="#38251B")
    cx, cy = w // 2, h // 2
    r = 16
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#D97736")
    if is_audio:
        # Ícone simples de nota musical / barras de áudio
        for idx, bar_h in enumerate((10, 16, 12)):
            bx = cx - 7 + idx * 6
            draw.rounded_rectangle(
                (bx, cy - bar_h // 2, bx + 3, cy + bar_h // 2),
                radius=1,
                fill="#FFF8F2",
            )
    else:
        draw.polygon(
            [(cx - 4, cy - 6), (cx - 4, cy + 6), (cx + 7, cy)],
            fill="#FFF8F2",
        )
    return round_corners(img, radius=8)


def _trim_letterbox_bars(img: Image.Image) -> Image.Image:
    """Remove faixas pretas horizontais ou verticais comuns em capas 4:3/1:1 do YouTube."""
    w, h = img.size
    if w < 32 or h < 32:
        return img
    gray = img.convert("L")
    px = gray.load()
    if px is None:
        return img

    def _row_is_dark(y: int) -> bool:
        step = max(1, w // 32)
        samples = [px[x, y] for x in range(0, w, step)]
        return max(samples) < 26

    def _col_is_dark(x: int) -> bool:
        step = max(1, h // 24)
        samples = [px[x, y] for y in range(0, h, step)]
        return max(samples) < 26

    max_y_trim = int(h * 0.25)
    top = 0
    while top < max_y_trim and _row_is_dark(top):
        top += 1
    bottom = h - 1
    while bottom > h - 1 - max_y_trim and _row_is_dark(bottom):
        bottom -= 1

    max_x_trim = int(w * 0.25)
    left = 0
    while left < max_x_trim and _col_is_dark(left):
        left += 1
    right = w - 1
    while right > w - 1 - max_x_trim and _col_is_dark(right):
        right -= 1

    if right - left >= w * 0.5 and bottom - top >= h * 0.5:
        return img.crop((left, top, right + 1, bottom + 1))
    return img


def fetch_rounded_thumbnail(
    url: str,
    size: tuple[int, int] = (132, 74),
    timeout: float = 6.0,
) -> Image.Image | None:
    """Baixa uma miniatura remota, remove letterbox e retorna imagem Pillow arredondada."""
    if not url:
        return None
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(5 * 1024 * 1024)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = _trim_letterbox_bars(img)
        fitted = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)
        return round_corners(fitted, radius=8)
    except Exception:
        return None


def compose_thumbnail_with_duration(
    base_img: Image.Image,
    duration_text: str = "",
) -> Image.Image:
    """Desenha o badge de duração diretamente no canto inferior direito da miniatura."""
    img = base_img.copy().convert("RGBA")
    if not duration_text:
        return img

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), duration_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x, pad_y = 6, 3
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    x2 = img.width - 5
    y2 = img.height - 5
    x1 = x2 - bw
    y1 = y2 - bh

    draw.rounded_rectangle((x1, y1, x2, y2), radius=4, fill=(14, 9, 6, 225))
    draw.text((x1 + pad_x, y1 + pad_y - 1), duration_text, font=font, fill="#FFF8F2")
    return round_corners(img, radius=8)


def get_or_create_app_icon_ico(data_dir: Path | None = None) -> str | None:
    """Gera o arquivo .ico do logotipo da xícara de café para a barra de título do Windows."""
    try:
        target = (data_dir or get_app_data_dir()) / "coffee_media_v2.ico"
        if not target.is_file():
            logo = create_coffee_logo_image((128, 128))
            logo.save(target, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        return str(target)
    except Exception:
        return None


def get_or_create_chevron_svg(data_dir: Path | None = None) -> str | None:
    """Gera o ícone SVG nítido de seta para baixo usado nos seletores QComboBox."""
    try:
        target = (data_dir or get_app_data_dir()) / "chevron_down.svg"
        if not target.is_file():
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
                'viewBox="0 0 24 24" fill="none" stroke="#EBB87A" stroke-width="2.5" '
                'stroke-linecap="round" stroke-linejoin="round">'
                '<polyline points="6 9 12 15 18 9"/></svg>'
            )
            target.write_text(svg, encoding="utf-8")
        return target.as_posix()
    except Exception:
        return None


def create_vector_icon(
    name: str,
    size: int = 18,
    color: str = "#F5EDE6",
) -> Image.Image:
    """Desenha ícones vetoriais nítidos (supersampled 4x) substituindo emojis do sistema."""
    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lw = max(3, int(s * 0.085))
    pad = int(s * 0.16)

    if name == "link":
        d.arc((pad, int(s * 0.32), int(s * 0.62), int(s * 0.78)), 120, 310, fill=color, width=lw)
        d.arc((int(s * 0.38), int(s * 0.22), s - pad, int(s * 0.68)), 300, 130, fill=color, width=lw)
        d.line((int(s * 0.36), int(s * 0.64), int(s * 0.64), int(s * 0.36)), fill=color, width=lw)
    elif name == "download":
        cx = s // 2
        d.line((cx, pad, cx, int(s * 0.66)), fill=color, width=lw)
        d.line((int(s * 0.28), int(s * 0.48), cx, int(s * 0.68), int(s * 0.72), int(s * 0.48)), fill=color, width=lw)
        d.line((pad, int(s * 0.80), s - pad, int(s * 0.80)), fill=color, width=lw)
    elif name == "history":
        d.arc((pad, pad, s - pad, s - pad), 40, 330, fill=color, width=lw)
        d.line((s // 2, int(s * 0.30), s // 2, s // 2, int(s * 0.66), int(s * 0.60)), fill=color, width=lw)
    elif name == "settings":
        cx, cy = s // 2, s // 2
        r_out = int(s * 0.33)
        r_in = int(s * 0.15)
        d.ellipse((cx - r_out, cy - r_out, cx + r_out, cy + r_out), outline=color, width=lw)
        d.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), outline=color, width=lw)
    elif name == "info":
        d.ellipse((pad, pad, s - pad, s - pad), outline=color, width=lw)
        cx = s // 2
        d.ellipse((cx - lw // 2, int(s * 0.30), cx + lw // 2, int(s * 0.30) + lw), fill=color)
        d.line((cx, int(s * 0.46), cx, int(s * 0.70)), fill=color, width=lw)
    elif name == "paste":
        d.rounded_rectangle((int(s * 0.24), int(s * 0.22), int(s * 0.76), s - pad), radius=int(s * 0.1), outline=color, width=lw)
        d.rounded_rectangle((int(s * 0.36), int(s * 0.13), int(s * 0.64), int(s * 0.28)), radius=int(s * 0.06), fill=color)
    elif name == "trash":
        d.line((pad, int(s * 0.26), s - pad, int(s * 0.26)), fill=color, width=lw)
        d.line((int(s * 0.38), int(s * 0.16), int(s * 0.62), int(s * 0.16)), fill=color, width=lw)
        d.rounded_rectangle((int(s * 0.26), int(s * 0.28), int(s * 0.74), s - pad), radius=int(s * 0.08), outline=color, width=lw)
    elif name == "folder":
        d.polygon(
            [
                (pad, int(s * 0.26)),
                (int(s * 0.44), int(s * 0.26)),
                (int(s * 0.52), int(s * 0.36)),
                (s - pad, int(s * 0.36)),
                (s - pad, int(s * 0.80)),
                (pad, int(s * 0.80)),
            ],
            outline=color,
            width=lw,
        )
    elif name == "stack":
        for y_off in (0.24, 0.48, 0.70):
            y = int(s * y_off)
            d.line((pad, y, s - pad, y), fill=color, width=lw)
    elif name == "speed":
        d.arc((pad, int(s * 0.24), s - pad, int(s * 0.94)), 180, 360, fill=color, width=lw)
        d.line((s // 2, int(s * 0.66), int(s * 0.70), int(s * 0.38)), fill=color, width=lw)
    elif name == "cancel":
        d.line((int(s * 0.26), int(s * 0.26), int(s * 0.74), int(s * 0.74)), fill=color, width=lw)
        d.line((int(s * 0.74), int(s * 0.26), int(s * 0.26), int(s * 0.74)), fill=color, width=lw)
    elif name == "check":
        d.line((int(s * 0.22), int(s * 0.52), int(s * 0.42), int(s * 0.72), int(s * 0.78), int(s * 0.30)), fill=color, width=lw)
    elif name == "video":
        d.rounded_rectangle((pad, int(s * 0.26), int(s * 0.72), int(s * 0.74)), radius=int(s * 0.08), outline=color, width=lw)
        d.polygon([(int(s * 0.72), int(s * 0.40)), (s - pad, int(s * 0.28)), (s - pad, int(s * 0.72)), (int(s * 0.72), int(s * 0.60))], outline=color, width=lw)
    elif name == "audio":
        d.ellipse((int(s * 0.20), int(s * 0.58), int(s * 0.44), int(s * 0.80)), outline=color, width=lw)
        d.ellipse((int(s * 0.58), int(s * 0.50), int(s * 0.82), int(s * 0.72)), outline=color, width=lw)
        d.line((int(s * 0.42), int(s * 0.68), int(s * 0.42), int(s * 0.24), int(s * 0.80), int(s * 0.18), int(s * 0.80), int(s * 0.60)), fill=color, width=lw)

    return img.resize((size, size), Image.Resampling.LANCZOS)
