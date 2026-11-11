import streamlit as st
from supabase import create_client, Client
import io
import base64
from PIL import Image, ImageOps

# ==========================================
# 1. CONEXIÓN SEGURA A SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# 2. BARRERA DE SEGURIDAD PARA PÁGINAS INTERNAS
# ==========================================
def validar_login():
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.error("🔒 ACCESO DENEGADO")
        st.warning("Debes iniciar sesión desde la pantalla de Inicio para acceder a este módulo.")
        st.stop()

# ==========================================
# 3. PROCESADOR DE FOTOS DE PERFIL (LIGERO Y RÁPIDO)
# ==========================================
def procesar_foto_perfil(archivo_subido) -> str:
    """Recorta la foto a cuadrado 240x240px y la convierte a Base64 ultraligero (~10KB)."""
    if not archivo_subido:
        return ""
    try:
        img = Image.open(archivo_subido).convert("RGB")
        img = ImageOps.fit(img, (240, 240), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=82, optimize=True)
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception:
        return ""

# ==========================================
# 4. SISTEMA VISUAL GLOBAL · HEMORE EXECUTIVE UI
# ==========================================
def aplicar_estilo_movil():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --hm-ink: #142038;
            --hm-navy: #0B1830;
            --hm-royal: #2D62D9;
            --hm-muted: #758198;
            --hm-line: #E4EAF2;
            --hm-surface: #FFFFFF;
            --hm-bg: #F4F7FB;
            --hm-success: #12A67B;
            --hm-danger: #CE4252;
            --hm-shadow: 0 25px 75px rgba(18, 36, 70, .08);
        }

        html, body, .stApp, [data-testid="stAppViewContainer"] {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--hm-ink);
            background: var(--hm-bg);
        }
        [data-testid="stAppViewContainer"] {
            background-image:
                radial-gradient(ellipse 48% 38% at 96% 4%, rgba(214,225,247,.43), transparent 76%),
                radial-gradient(ellipse 37% 37% at 0% 94%, rgba(229,236,248,.47), transparent 77%);
        }
        #MainMenu, footer, [data-testid="stToolbar"] {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent !important;}
        [data-testid="stDecoration"] {display: none;}
        [data-testid="stMainBlockContainer"], .block-container {
            max-width: 1310px;
            padding-top: 3.3rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3, h4, h5 {
            font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            letter-spacing: -.045em;
            color: var(--hm-ink);
        }
        h1 {font-weight: 800 !important;}
        h3 {font-weight: 750 !important;}
        p {line-height: 1.65;}
        hr {
            margin: 1.8rem 0 !important;
            border: none !important;
            border-top: 1px solid var(--hm-line) !important;
        }

        /* Controles globales de formularios, tablas y pestañas del ERP */
        [data-testid="stTextInput"] label p,
        [data-testid="stNumberInput"] label p,
        [data-testid="stSelectbox"] label p,
        [data-testid="stDateInput"] label p,
        [data-testid="stTextArea"] label p,
        [data-testid="stMultiSelect"] label p {
            color: #344258 !important;
            font-size: 12px !important;
            font-weight: 700 !important;
        }
        [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stNumberInput"] [data-baseweb="input"],
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
        [data-testid="stDateInput"] [data-baseweb="input"],
        [data-testid="stTextArea"] [data-baseweb="textarea"] {
            background: #FAFBFD !important;
            border: 1px solid #DCE4EE !important;
            border-radius: 11px !important;
            box-shadow: 0 1px 2px rgba(23,43,77,.02);
            transition: border-color .2s ease, background .2s ease, box-shadow .2s ease;
        }
        [data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
        [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
        [data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {
            border-color: #4174DF !important;
            background: #FFF !important;
            box-shadow: 0 0 0 4px rgba(65,116,223,.11) !important;
        }
        [data-testid="stButton"] > button,
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="stDownloadButton"] > button {
            min-height: 46px;
            background: #2D62D9;
            color: #FFFFFF;
            border: 1px solid #2D62D9;
            border-radius: 11px;
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: .008em;
            box-shadow: 0 6px 18px rgba(42,95,207,.16);
            transition: all .2s ease;
        }
        [data-testid="stButton"] > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover,
        [data-testid="stDownloadButton"] > button:hover {
            background: #2455C7;
            color: #FFFFFF;
            border-color: #2455C7;
            box-shadow: 0 10px 25px rgba(42,95,207,.23);
            transform: translateY(-1px);
        }
        [data-testid="stButton"] > button[kind="secondary"] {
            background: #FFFFFF !important;
            color: #34435B !important;
            border: 1px solid #DDE5F0 !important;
            box-shadow: 0 2px 9px rgba(26,44,74,.035) !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 8px;
            background: #EAF0F8;
            padding: 6px;
            border-radius: 13px;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            border-radius: 9px;
            padding: 8px 16px;
            font-weight: 700;
            font-size: 13px;
            color: #53647F;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            background: #FFFFFF !important;
            color: #142038 !important;
            box-shadow: 0 3px 10px rgba(18,36,70,.06);
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            background: #FFFFFF;
            border: 1px solid #E2E9F3;
            border-radius: 15px;
            padding: 6px;
            box-shadow: 0 6px 22px rgba(18,36,70,.03);
        }
        [data-testid="stSidebar"] {
            background: #101E36;
            border-right: 1px solid #1D2D4B;
        }
        [data-testid="stSidebar"] * {color: #D5E0F1;}

        @media (max-width: 768px) {
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .stButton>button {
                width: 100%;
            }
        }
    </style>
    """, unsafe_allow_html=True)
