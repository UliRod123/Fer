import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import io
import base64
import os
from groq import Groq

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(
    page_title="Visual Assistant ✨",
    page_icon="✨",
    layout="wide"
)

GROQ_API_KEY = "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"

# -------------------------
# CSS PERSONALIZADO
# -------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=Playfair+Display:ital,wght@0,400;1,400&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1025 50%, #0f1a1a 100%);
    }

    h1 {
        font-family: 'Playfair Display', serif !important;
        font-style: italic !important;
        background: linear-gradient(135deg, #e0c4ff, #c4f0ff, #ffc4e8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #9061f9, #6366f1);
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
    }

    .result-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }

    .result-card h3 {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        color: #c4f0ff;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
    }

    .result-card p {
        color: rgba(255,255,255,0.75);
        line-height: 1.7;
        font-size: 0.95rem;
    }

    .stTextArea textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stFileUploader {
        border: 2px dashed rgba(124, 58, 237, 0.4) !important;
        border-radius: 16px !important;
        background: rgba(124, 58, 237, 0.05) !important;
    }

    .metric-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }

    .metric-box .value {
        font-size: 1.8rem;
        font-weight: 300;
        color: #c4f0ff;
    }

    .metric-box .label {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.2rem;
    }

    div[data-testid="stImage"] img {
        border-radius: 16px !important;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0d9488, #0891b2) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("# ✨ Visual Assistant")
st.markdown("<p style='color: rgba(255,255,255,0.45); font-size: 0.9rem; margin-top: -0.8rem;'>Análisis creativo con inteligencia artificial</p>", unsafe_allow_html=True)

st.divider()

# -------------------------
# FUNCIONES DE IMAGEN
# -------------------------

def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img_rgb = img.convert("RGB")
    img_rgb.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def upscale_hd(img: Image.Image, scale: int = 2) -> Image.Image:
    """Upscaling de calidad con Lanczos + sharpening"""
    w, h = img.size
    new_w, new_h = w * scale, h * scale
    upscaled = img.resize((new_w, new_h), Image.LANCZOS)
    upscaled = upscaled.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
    upscaled = ImageEnhance.Sharpness(upscaled).enhance(1.3)
    return upscaled

def enhance_smart(img: Image.Image) -> Image.Image:
    """Mejora automática inteligente basada en análisis de la imagen"""
    img_np = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    brightness = gray.mean()
    contrast = gray.std()

    result = img

    if brightness < 100:
        result = ImageEnhance.Brightness(result).enhance(1.25)
    elif brightness > 180:
        result = ImageEnhance.Brightness(result).enhance(0.88)

    if contrast < 40:
        result = ImageEnhance.Contrast(result).enhance(1.4)
    elif contrast < 60:
        result = ImageEnhance.Contrast(result).enhance(1.15)

    result = ImageEnhance.Color(result).enhance(1.1)
    result = ImageEnhance.Sharpness(result).enhance(1.2)

    return result

def remove_bg(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
        return Image.fromarray(remove(np.array(img)))
    except ImportError:
        st.warning("rembg no está instalado. Instalando... intenta de nuevo en un momento.")
        return img

def analyze_image_metrics(img: Image.Image):
    img_np = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    brightness = gray.mean()
    contrast = gray.std()
    w, h = img.size

    tips = []
    if brightness < 90:
        tips.append("🔅 Imagen oscura — recomendable subir brillo")
    elif brightness > 200:
        tips.append("🌞 Sobreexpuesta — bajar exposición")
    else:
        tips.append("✅ Brillo balanceado")

    if contrast < 40:
        tips.append("⚖️ Bajo contraste — aplicar mejora")
    else:
        tips.append("✅ Contraste adecuado")

    if w < 800 or h < 800:
        tips.append(f"📐 Resolución baja ({w}×{h}px) — usar HD para mejorar")
    else:
        tips.append(f"✅ Buena resolución ({w}×{h}px)")

    return brightness, contrast, w, h, tips

# -------------------------
# GROQ AI
# -------------------------

def analyze_with_groq(img: Image.Image, copy_text: str = "") -> dict:
    """Analiza imagen con Groq LLaMA Vision y devuelve dirección creativa real"""
    client = Groq(api_key=GROQ_API_KEY)
    img_b64 = image_to_base64(img)

    copy_section = f"\nCopy del proyecto: {copy_text}" if copy_text.strip() else ""

    prompt = f"""Eres un director de arte y diseñador creativo senior. Analiza esta imagen profesionalmente.{copy_section}

Responde EXACTAMENTE en este formato (sin asteriscos, sin markdown, solo el texto):

CONCEPTO: [Una frase que capture la esencia creativa ideal para esta imagen]

ESTILO: [Nombre del estilo visual recomendado, ej: editorial minimalista, lifestyle vibrante, etc.]

ESCENA IDEAL: [Describe en 2-3 oraciones cómo debería verse la imagen final perfecta]

IDEAS VISUALES:
- [idea 1]
- [idea 2]
- [idea 3]
- [idea 4]

COMPOSICIÓN:
- [consejo 1]
- [consejo 2]
- [consejo 3]

PALETA DE COLOR: [3-4 colores hex sugeridos con su nombre, ej: #F5E6D3 crema cálido]

TIPOGRAFÍA SUGERIDA: [2 fuentes que combinen con el estilo visual]

AJUSTES TÉCNICOS: [Recomendaciones específicas de brillo, contraste, saturación para esta imagen]"""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        max_tokens=1000,
        temperature=0.7
    )

    raw = response.choices[0].message.content

    # Parsear la respuesta
    result = {}
    sections = {
        "CONCEPTO": "concepto",
        "ESTILO": "estilo",
        "ESCENA IDEAL": "escena",
        "IDEAS VISUALES": "ideas",
        "COMPOSICIÓN": "composicion",
        "PALETA DE COLOR": "paleta",
        "TIPOGRAFÍA SUGERIDA": "tipografia",
        "AJUSTES TÉCNICOS": "ajustes"
    }

    lines = raw.split('\n')
    current_key = None
    current_content = []

    for line in lines:
        line = line.strip()
        matched = False
        for section, key in sections.items():
            if line.startswith(section + ":"):
                if current_key:
                    result[current_key] = '\n'.join(current_content).strip()
                current_key = key
                content = line[len(section)+1:].strip()
                current_content = [content] if content else []
                matched = True
                break
        if not matched and current_key:
            current_content.append(line)

    if current_key:
        result[current_key] = '\n'.join(current_content).strip()

    if not result:
        result["concepto"] = raw

    return result


# -------------------------
# LAYOUT PRINCIPAL
# -------------------------

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("#### 📸 Imagen")
    uploaded_file = st.file_uploader("Sube tu imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

    st.markdown("#### ✍️ Copy (opcional)")
    copy = st.text_area(
        "Copy",
        placeholder="Ej: Producto premium para mujeres modernas que buscan elegancia...",
        height=100,
        label_visibility="collapsed"
    )

with col_right:
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Original", use_container_width=True)

# -------------------------
# ACCIONES
# -------------------------

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")

    st.divider()
    st.markdown("#### 🛠 Herramientas")

    c1, c2, c3, c4 = st.columns(4)

    result_image = None
    action_label = ""

    with c1:
        if st.button("🔆 Mejorar imagen"):
            with st.spinner("Mejorando..."):
                result_image = enhance_smart(image)
                action_label = "Imagen mejorada"

    with c2:
        if st.button("🔍 HD ×2"):
            with st.spinner("Escalando a HD..."):
                result_image = upscale_hd(image, scale=2)
                action_label = f"HD ×2 · {result_image.size[0]}×{result_image.size[1]}px"

    with c3:
        if st.button("🧼 Quitar fondo"):
            with st.spinner("Removiendo fondo..."):
                result_image = remove_bg(image)
                action_label = "Fondo removido"

    with c4:
        if st.button("📊 Analizar"):
            b, c_val, w, h, tips = analyze_image_metrics(image)

            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""<div class="metric-box"><div class="value">{b:.0f}</div><div class="label">Brillo</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-box"><div class="value">{c_val:.0f}</div><div class="label">Contraste</div></div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="metric-box"><div class="value">{w}×{h}</div><div class="label">Resolución</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            for tip in tips:
                st.markdown(f"<p style='color:rgba(255,255,255,0.7);margin:0.3rem 0'>{tip}</p>", unsafe_allow_html=True)

    # Mostrar resultado de herramienta
    if result_image:
        st.markdown("---")
        col_res1, col_res2 = st.columns([1, 1])
        with col_res1:
            st.markdown(f"<p style='color:rgba(255,255,255,0.5);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em'>{action_label}</p>", unsafe_allow_html=True)
            st.image(result_image, use_container_width=True)

        with col_res2:
            buf = io.BytesIO()
            save_img = result_image.convert("RGB") if result_image.mode == "RGBA" else result_image
            save_img.save(buf, format="PNG")
            st.download_button(
                "⬇️ Descargar resultado",
                data=buf.getvalue(),
                file_name="visual_assistant_resultado.png",
                mime="image/png"
            )

    # -------------------------
    # DIRECCIÓN CREATIVA IA
    # -------------------------
    st.divider()
    st.markdown("#### 🧠 Dirección creativa con IA")

    if st.button("✨ Generar análisis creativo con IA"):
        with st.spinner("Analizando imagen con inteligencia artificial..."):
            try:
                result = analyze_with_groq(image, copy)

                if "concepto" in result:
                    st.markdown(f"""<div class="result-card"><h3>💡 Concepto</h3><p>{result.get('concepto','')}</p></div>""", unsafe_allow_html=True)

                col_a, col_b = st.columns(2)

                with col_a:
                    if "escena" in result:
                        st.markdown(f"""<div class="result-card"><h3>🎬 Escena ideal</h3><p>{result.get('escena','')}</p></div>""", unsafe_allow_html=True)
                    if "ideas" in result:
                        st.markdown(f"""<div class="result-card"><h3>✨ Ideas visuales</h3><p>{result.get('ideas','')}</p></div>""", unsafe_allow_html=True)
                    if "paleta" in result:
                        st.markdown(f"""<div class="result-card"><h3>🎨 Paleta de color</h3><p>{result.get('paleta','')}</p></div>""", unsafe_allow_html=True)

                with col_b:
                    if "composicion" in result:
                        st.markdown(f"""<div class="result-card"><h3>📐 Composición</h3><p>{result.get('composicion','')}</p></div>""", unsafe_allow_html=True)
                    if "tipografia" in result:
                        st.markdown(f"""<div class="result-card"><h3>🔤 Tipografía</h3><p>{result.get('tipografia','')}</p></div>""", unsafe_allow_html=True)
                    if "ajustes" in result:
                        st.markdown(f"""<div class="result-card"><h3>⚙️ Ajustes técnicos</h3><p>{result.get('ajustes','')}</p></div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error al conectar con la IA: {str(e)}")

else:
    st.markdown("""
    <div style='text-align:center; padding: 4rem 2rem; color: rgba(255,255,255,0.25);'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>✨</div>
        <p style='font-size: 1rem;'>Sube una imagen para comenzar</p>
    </div>
    """, unsafe_allow_html=True)
