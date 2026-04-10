import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import io
import base64
import requests
import re
from groq import Groq

st.set_page_config(page_title="Fer's Visual Studio", page_icon="🌸", layout="wide", initial_sidebar_state="collapsed")

GROQ_API_KEY     = "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"
REMOVEBG_API_KEY = "5yDP28t5jHUvThb7WBhJPnx2m"

# ── TIPOGRAFÍAS POR TEMA ────────────────────────────────────────────────────
FONT_THEMES = {
    "gaming": {
        "keywords": ["game","gam","juego","arcade","level","skin","esport","lol","league","fps","rpg","xbox","playstation","nintendo","steam","valorant","fortnite","minecraft","pixel","retro","cyber","neon"],
        "fonts": [
            ("Rajdhani", "Futurista, geométrica, muy usada en HUDs de videojuegos"),
            ("Orbitron", "Sci-fi angular, perfecta para marcas gaming"),
            ("Bebas Neue", "Display bold, impacto máximo en títulos"),
            ("Press Start 2P", "Pixel art retro 8-bit, icónica en gaming indie"),
            ("Exo 2", "Tecnológica pero legible, buena para cuerpo de texto"),
        ]
    },
    "luxury": {
        "keywords": ["lujo","luxury","premium","elegante","exclusiv","high-end","sofisticad","refinad","couture","haute","vogue"],
        "fonts": [
            ("Cormorant Garamond", "Serif de lujo, elegancia editorial"),
            ("Playfair Display", "Clásica y sofisticada, ideal para moda"),
            ("Libre Baskerville", "Serif refinada para marcas premium"),
            ("Cinzel", "Romana majestuosa, autoridad y clase"),
            ("Bodoni Moda", "Alta moda, contraste dramático"),
        ]
    },
    "lifestyle": {
        "keywords": ["lifestyle","vida","wellness","salud","fitness","yoga","natural","organic","comida","food","travel","viaje","moda","fashion","beauty","belleza"],
        "fonts": [
            ("Nunito", "Amigable y moderna, muy versátil"),
            ("Lato", "Limpia humanista, calidez y profesionalismo"),
            ("Josefin Sans", "Geométrica elegante, muy usada en lifestyle"),
            ("Quicksand", "Suave y accesible, sensación de bienestar"),
            ("DM Sans", "Contemporánea, excelente legibilidad"),
        ]
    },
    "tech": {
        "keywords": ["tech","tecnolog","software","app","digital","startup","saas","ia","ai","data","code","dev","innovaci"],
        "fonts": [
            ("Space Grotesk", "Técnica pero con personalidad"),
            ("IBM Plex Sans", "Corporativa tecnológica, muy legible"),
            ("Syne", "Geométrica moderna, startups y tech"),
            ("Chakra Petch", "Futurista industrial, interfaces tech"),
            ("Share Tech Mono", "Monospace, evoca código y sistemas"),
        ]
    },
    "default": {
        "keywords": [],
        "fonts": [
            ("Outfit", "Geométrica moderna y versátil"),
            ("DM Sans", "Contemporánea, excelente legibilidad"),
            ("Fraunces", "Display serif expresiva y distintiva"),
            ("Syne", "Geométrica con personalidad fuerte"),
            ("Epilogue", "Variable moderna, muy adaptable"),
        ]
    }
}

def detect_font_theme(copy: str) -> str:
    text = copy.lower()
    for theme, data in FONT_THEMES.items():
        if theme == "default": continue
        if any(kw in text for kw in data["keywords"]):
            return theme
    return "default"

def get_font_context(copy: str) -> str:
    theme = detect_font_theme(copy)
    fonts = FONT_THEMES[theme]["fonts"]
    lines = [f"- {name}: {desc}" for name, desc in fonts]
    return f"Tema detectado: {theme}\nFuentes recomendadas para este tema (todas disponibles en Google Fonts):\n" + "\n".join(lines)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Outfit:wght@300;400;500&family=Rajdhani:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; color: #f0ece8; }

.stApp {
    background: #0c0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(180,100,255,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,120,180,0.10) 0%, transparent 60%);
}

.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-weight: 300;
    font-size: 3.2rem;
    line-height: 1;
    background: linear-gradient(135deg, #f5d0fe 0%, #fbcfe8 40%, #e0f2fe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero-sub {
    font-size: 0.8rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(240,236,232,0.35);
    margin-top: 0.3rem;
}
.section-label {
    font-size: 0.68rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(240,236,232,0.35);
    margin-bottom: 0.6rem;
    display: block;
}
.stButton > button {
    background: rgba(255,255,255,0.06) !important;
    color: #f0ece8 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: rgba(180,100,255,0.18) !important;
    border-color: rgba(180,100,255,0.4) !important;
    transform: translateY(-1px) !important;
}
.result-block {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
    position: relative;
    overflow: hidden;
}
.result-block::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #c084fc, #f472b6);
    border-radius: 3px 0 0 3px;
}
.result-block .rb-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c084fc;
    margin-bottom: 0.5rem;
    display: block;
}
.result-block .rb-content {
    font-size: 0.9rem;
    line-height: 1.7;
    color: rgba(240,236,232,0.82);
}
.font-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.5rem;
}
.font-card .fc-name {
    font-size: 1.1rem;
    font-weight: 500;
    color: #f5d0fe;
    margin-bottom: 0.15rem;
}
.font-card .fc-desc {
    font-size: 0.75rem;
    color: rgba(240,236,232,0.45);
}
.font-badge {
    display: inline-block;
    background: rgba(192,132,252,0.15);
    border: 1px solid rgba(192,132,252,0.3);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.65rem;
    color: #c084fc;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.prompt-box {
    background: rgba(192,132,252,0.08);
    border: 1px solid rgba(192,132,252,0.25);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 0.75rem;
    position: relative;
}
.prompt-box .pb-num {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 2rem;
    color: rgba(192,132,252,0.3);
    position: absolute;
    top: 0.8rem;
    right: 1.2rem;
    line-height: 1;
}
.prompt-box .pb-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(192,132,252,0.7);
    margin-bottom: 0.6rem;
    display: block;
}
.prompt-box .pb-text {
    font-size: 0.88rem;
    line-height: 1.65;
    color: rgba(240,236,232,0.85);
}
.metrics-row { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-top: 0.5rem; }
.metric-chip {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 0.4rem 0.9rem;
    font-size: 0.78rem;
    color: rgba(240,236,232,0.6);
}
.metric-chip span { color: #e0f2fe; font-weight: 500; margin-left: 0.3rem; }
.swatch-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
.swatch {
    width: 36px; height: 36px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.15);
    display: inline-block;
}
.stFileUploader > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px dashed rgba(192,132,252,0.3) !important;
    border-radius: 16px !important;
}
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #f0ece8 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border-color: rgba(192,132,252,0.4) !important;
    box-shadow: 0 0 0 3px rgba(192,132,252,0.08) !important;
}
.stDownloadButton > button {
    background: rgba(16,185,129,0.15) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    border-radius: 12px !important;
    color: #6ee7b7 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important;
    width: 100% !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(240,236,232,0.45) !important;
    border-radius: 9px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(192,132,252,0.2) !important;
    color: #f0ece8 !important;
}
div[data-testid="stImage"] img { border-radius: 14px !important; }
hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def img_to_b64(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()

def img_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def upscale_hd(img, scale=2):
    w, h = img.size
    big = img.resize((w * scale, h * scale), Image.LANCZOS)
    big = big.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
    big = ImageEnhance.Sharpness(big).enhance(1.4)
    big = ImageEnhance.Contrast(big).enhance(1.08)
    return big

def enhance_smart(img):
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    b, c = gray.mean(), gray.std()
    result = img
    if b < 100:   result = ImageEnhance.Brightness(result).enhance(1.3)
    elif b > 185: result = ImageEnhance.Brightness(result).enhance(0.85)
    if c < 45:    result = ImageEnhance.Contrast(result).enhance(1.5)
    elif c < 65:  result = ImageEnhance.Contrast(result).enhance(1.2)
    result = ImageEnhance.Color(result).enhance(1.15)
    result = ImageEnhance.Sharpness(result).enhance(1.3)
    return result

def remove_bg(img):
    try:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        buf.seek(0)
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": ("image.png", buf, "image/png")},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVEBG_API_KEY},
        )
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
        else:
            try:
                error_msg = response.json().get("errors", [{}])[0].get("title", "Error desconocido")
            except Exception:
                error_msg = f"HTTP {response.status_code}"
            st.error(f"remove.bg error: {error_msg}")
            return img
    except Exception as e:
        st.error(f"Error al quitar fondo: {e}")
        return img

def get_metrics(img):
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray.mean(), gray.std(), img.size[0], img.size[1]

def extract_colors(text):
    return re.findall(r'#[0-9A-Fa-f]{6}', text)

# ── GROQ ─────────────────────────────────────────────────────────────────────
def groq_analyze(img, copy=""):
    client = Groq(api_key=GROQ_API_KEY)
    copy_part = f"\nCopy del proyecto: {copy}" if copy.strip() else ""
    font_ctx = get_font_context(copy) if copy.strip() else ""
    font_instruction = f"\n\nContexto de tipografía:\n{font_ctx}\nElige 2 fuentes de la lista anterior que mejor apliquen para este proyecto específico y explica por qué." if font_ctx else "\nSugiere 2 fuentes de Google Fonts específicas y relevantes al estilo de la imagen."

    prompt = f"""Eres un director de arte senior. Analiza esta imagen con profundidad profesional.{copy_part}{font_instruction}

Responde en este formato exacto (sin asteriscos, sin markdown):

CONCEPTO: [Una frase que capture la dirección creativa ideal]

ESTILO: [Nombre del estilo visual]

ESCENA IDEAL: [2-3 oraciones describiendo la imagen final perfecta, muy específico]

IDEAS VISUALES:
- [idea concreta 1]
- [idea concreta 2]
- [idea concreta 3]
- [idea concreta 4]

COMPOSICIÓN:
- [consejo técnico 1]
- [consejo técnico 2]
- [consejo técnico 3]

PALETA DE COLOR: [exactamente 4 colores hex con nombre, ej: #1A1A2E azul noche, #E94560 rojo neón]

TIPOGRAFÍA: [las 2 fuentes elegidas con una oración explicando por qué cada una]

AJUSTES TÉCNICOS: [valores específicos de brillo, contraste, saturación recomendados]"""

    r = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_to_b64(img)}"}},
            {"type": "text", "text": prompt}
        ]}],
        max_tokens=1000, temperature=0.75
    )
    return r.choices[0].message.content

def groq_prompts(img, copy, analysis=""):
    client = Groq(api_key=GROQ_API_KEY)
    theme = detect_font_theme(copy)
    prompt = f"""Basándote en esta imagen, genera 4 prompts para Midjourney o Stable Diffusion.

Copy: {copy if copy.strip() else 'sin copy'}
Tema detectado: {theme}
Contexto: {analysis[:400] if analysis else 'analiza visualmente la imagen'}

Genera prompts en INGLÉS, detallados, 40-60 palabras cada uno. Cada uno con enfoque diferente.

Formato exacto:

PROMPT 1 — [nombre del enfoque]:
[prompt completo]

PROMPT 2 — [nombre del enfoque]:
[prompt completo]

PROMPT 3 — [nombre del enfoque]:
[prompt completo]

PROMPT 4 — [nombre del enfoque]:
[prompt completo]"""

    r = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_to_b64(img)}"}},
            {"type": "text", "text": prompt}
        ]}],
        max_tokens=900, temperature=0.85
    )
    return r.choices[0].message.content

def parse_section(text, key):
    lines = text.split('\n')
    collecting = False
    result = []
    stops = ["CONCEPTO","ESTILO","ESCENA IDEAL","IDEAS VISUALES","COMPOSICIÓN","PALETA DE COLOR","TIPOGRAFÍA","AJUSTES TÉCNICOS","PROMPT"]
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(key + ":") or stripped.startswith(key + " —"):
            collecting = True
            after = stripped[len(key)+1:].strip().lstrip("—").strip()
            if after: result.append(after)
            continue
        if collecting:
            if any(stripped.startswith(s) for s in stops if s != key):
                break
            result.append(line)
    return '\n'.join(result).strip()

def parse_prompts(text):
    prompts = []
    blocks = re.split(r'PROMPT \d+\s*[—–-]\s*', text)
    for block in blocks[1:]:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        if lines:
            title = lines[0].rstrip(':') if lines[0].endswith(':') else lines[0]
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            if not content: content = title; title = "Variación"
            prompts.append({"title": title, "prompt": content})
    return prompts

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Visual Studio</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Mejora de imagen · Análisis creativo · Generador de prompts</p>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── INPUT ────────────────────────────────────────────────────────────────────
col_up, col_copy = st.columns([1, 1], gap="large")
with col_up:
    st.markdown('<span class="section-label">Imagen</span>', unsafe_allow_html=True)
    uploaded = st.file_uploader("img", type=["png","jpg","jpeg"], label_visibility="collapsed")
with col_copy:
    st.markdown('<span class="section-label">Contexto del proyecto (opcional)</span>', unsafe_allow_html=True)
    copy = st.text_area("copy", placeholder="Ej: Skin de League of Legends para promoción, estilo gaming vibrante...", height=120, label_visibility="collapsed")

# ── MAIN ─────────────────────────────────────────────────────────────────────
if uploaded:
    original = Image.open(uploaded).convert("RGB")
    b_orig, c_orig, w_orig, h_orig = get_metrics(original)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🖼  Mejorar imagen", "🧠  Análisis creativo con IA", "✨  Generador de prompts"])

    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        action = None
        with c1:
            if st.button("🔆  Mejorar automático"): action = "enhance"
        with c2:
            if st.button("🔍  HD ×2"): action = "hd2"
        with c3:
            if st.button("🔍  HD ×4"): action = "hd4"
        with c4:
            if st.button("🧼  Quitar fondo"): action = "rembg"

        if action:
            st.session_state["action"] = action
            st.session_state["result_img"] = None

        if "action" in st.session_state and st.session_state.get("result_img") is None:
            act = st.session_state["action"]
            with st.spinner("Procesando..."):
                if act == "enhance":
                    res = enhance_smart(original); lbl = "Mejorada automáticamente"
                elif act == "hd2":
                    res = upscale_hd(original, 2); lbl = f"HD ×2 — {res.size[0]}×{res.size[1]}px"
                elif act == "hd4":
                    res = upscale_hd(original, 4); lbl = f"HD ×4 — {res.size[0]}×{res.size[1]}px"
                elif act == "rembg":
                    res = remove_bg(original); lbl = "Fondo removido"
                st.session_state["result_img"] = res
                st.session_state["result_label"] = lbl

        if st.session_state.get("result_img"):
            res = st.session_state["result_img"]
            lbl = st.session_state.get("result_label", "Resultado")
            b_r, c_r, w_r, h_r = get_metrics(res)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<span class="section-label">Antes / Después</span>', unsafe_allow_html=True)
            col_b, col_a = st.columns(2, gap="medium")
            with col_b:
                st.markdown('<span class="section-label">Original</span>', unsafe_allow_html=True)
                st.image(original, use_container_width=True)
                st.markdown(f'<div class="metrics-row"><div class="metric-chip">Brillo <span>{b_orig:.0f}</span></div><div class="metric-chip">Contraste <span>{c_orig:.0f}</span></div><div class="metric-chip"><span>{w_orig}×{h_orig}px</span></div></div>', unsafe_allow_html=True)
            with col_a:
                st.markdown(f'<span class="section-label">{lbl}</span>', unsafe_allow_html=True)
                st.image(res, use_container_width=True)
                st.markdown(f'<div class="metrics-row"><div class="metric-chip">Brillo <span>{b_r:.0f}</span></div><div class="metric-chip">Contraste <span>{c_r:.0f}</span></div><div class="metric-chip"><span>{w_r}×{h_r}px</span></div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button("⬇️  Descargar resultado", data=img_to_bytes(res), file_name="visual_studio_resultado.png", mime="image/png")
        else:
            col_p, col_i = st.columns([2,1], gap="large")
            with col_p:
                st.image(original, use_container_width=True)
            with col_i:
                tips = []
                if b_orig < 90: tips.append("🔅 Imagen oscura")
                elif b_orig > 190: tips.append("🌞 Sobreexpuesta")
                else: tips.append("✅ Brillo OK")
                if c_orig < 45: tips.append("⚖️ Bajo contraste")
                else: tips.append("✅ Contraste OK")
                tips.append(f"📐 {'Baja resolución — prueba HD' if w_orig < 1000 else 'Buena resolución'}")
                tips_html = ''.join([f'<p style="font-size:0.82rem;color:rgba(240,236,232,0.65);margin:0.25rem 0">{t}</p>' for t in tips])
                st.markdown(f'<div class="result-block"><span class="rb-label">Diagnóstico</span><div class="metrics-row"><div class="metric-chip">Brillo <span>{b_orig:.0f}</span></div><div class="metric-chip">Contraste <span>{c_orig:.0f}</span></div><div class="metric-chip"><span>{w_orig}×{h_orig}px</span></div></div><br>{tips_html}</div>', unsafe_allow_html=True)

    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        col_i2, col_b2 = st.columns([2,1], gap="large")
        with col_i2:
            st.image(original, use_container_width=True)
        with col_b2:
            # Mostrar tema detectado si hay copy
            if copy.strip():
                theme = detect_font_theme(copy)
                theme_labels = {"gaming":"🎮 Gaming","luxury":"💎 Lujo","lifestyle":"🌿 Lifestyle","tech":"💻 Tech","default":"✦ General"}
                st.markdown(f'<span class="font-badge">Tema detectado: {theme_labels.get(theme, theme)}</span>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.82rem;color:rgba(240,236,232,0.45);line-height:1.6">La IA analiza tu imagen en contexto y genera dirección creativa con tipografías específicas para tu tema.</p>', unsafe_allow_html=True)
            run_analysis = st.button("🧠  Analizar con IA")

        if run_analysis or "ai_analysis" in st.session_state:
            if run_analysis:
                with st.spinner("Analizando..."):
                    result = groq_analyze(original, copy)
                    st.session_state["ai_analysis"] = result

            raw = st.session_state.get("ai_analysis", "")
            if raw:
                st.markdown("<br>", unsafe_allow_html=True)
                concepto = parse_section(raw, "CONCEPTO")
                estilo   = parse_section(raw, "ESTILO")
                if concepto:
                    st.markdown(f"""<div style="background:linear-gradient(135deg,rgba(192,132,252,0.12),rgba(244,114,182,0.08));border:1px solid rgba(192,132,252,0.2);border-radius:16px;padding:1.5rem 1.8rem;margin-bottom:1rem">
                        <span style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:#c084fc">Concepto creativo</span>
                        <p style="font-family:'Cormorant Garamond',serif;font-style:italic;font-size:1.4rem;color:#f5d0fe;margin:0.4rem 0 0;line-height:1.4">{concepto}</p>
                        {f'<p style="font-size:0.78rem;color:rgba(240,236,232,0.4);margin:0.5rem 0 0;letter-spacing:0.1em;text-transform:uppercase">{estilo}</p>' if estilo else ''}
                    </div>""", unsafe_allow_html=True)

                col_a, col_b = st.columns(2, gap="medium")
                with col_a:
                    for sec, lbl in [("ESCENA IDEAL","Escena ideal"),("IDEAS VISUALES","Ideas visuales"),("PALETA DE COLOR","Paleta de color")]:
                        val = parse_section(raw, sec)
                        if val:
                            extra = ""
                            if sec == "PALETA DE COLOR":
                                colors = extract_colors(val)
                                extra = '<div class="swatch-row">' + ''.join([f'<div class="swatch" style="background:{c}" title="{c}"></div>' for c in colors]) + '</div>'
                            content = val.replace('\n- ', '<br>• ').replace('- ','• ',1)
                            st.markdown(f'<div class="result-block"><span class="rb-label">{lbl}</span><div class="rb-content">{content}</div>{extra}</div>', unsafe_allow_html=True)

                with col_b:
                    for sec, lbl in [("COMPOSICIÓN","Composición"),("AJUSTES TÉCNICOS","Ajustes técnicos")]:
                        val = parse_section(raw, sec)
                        if val:
                            content = val.replace('\n- ', '<br>• ').replace('- ','• ',1)
                            st.markdown(f'<div class="result-block"><span class="rb-label">{lbl}</span><div class="rb-content">{content}</div></div>', unsafe_allow_html=True)

                    # Tipografías con cards visuales
                    typo = parse_section(raw, "TIPOGRAFÍA")
                    if typo:
                        st.markdown(f'<div class="result-block"><span class="rb-label">Tipografía sugerida para tu tema</span><div class="rb-content">{typo}</div></div>', unsafe_allow_html=True)

    # ── TAB 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        col_i3, col_b3 = st.columns([2,1], gap="large")
        with col_i3:
            st.image(original, use_container_width=True)
        with col_b3:
            st.markdown('<p style="font-size:0.82rem;color:rgba(240,236,232,0.45);line-height:1.6">Genera 4 prompts listos para <b style="color:rgba(240,236,232,0.7)">Midjourney</b>, Stable Diffusion o DALL-E.</p>', unsafe_allow_html=True)
            run_prompts = st.button("✨  Generar prompts")

        if run_prompts or "ai_prompts" in st.session_state:
            if run_prompts:
                with st.spinner("Generando prompts..."):
                    prompts_raw = groq_prompts(original, copy, st.session_state.get("ai_analysis",""))
                    st.session_state["ai_prompts"] = prompts_raw

            raw_p = st.session_state.get("ai_prompts","")
            if raw_p:
                st.markdown("<br>", unsafe_allow_html=True)
                prompts = parse_prompts(raw_p)
                if prompts:
                    for i, p in enumerate(prompts, 1):
                        st.markdown(f"""<div class="prompt-box">
                            <span class="pb-num">{i:02d}</span>
                            <span class="pb-label">{p['title']}</span>
                            <div class="pb-text">{p['prompt']}</div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="prompt-box"><div class="pb-text">{raw_p}</div></div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button("⬇️  Descargar prompts .txt", data=raw_p, file_name="prompts_visual_studio.txt", mime="text/plain")

else:
    st.markdown("""<div style="text-align:center;padding:5rem 2rem;">
        <p style="font-family:'Cormorant Garamond',serif;font-style:italic;font-size:2.5rem;color:rgba(240,236,232,0.12);margin:0">Sube una imagen para comenzar</p>
        <p style="font-size:0.8rem;letter-spacing:0.15em;text-transform:uppercase;color:rgba(240,236,232,0.15);margin-top:0.8rem">PNG · JPG · JPEG</p>
    </div>""", unsafe_allow_html=True)
