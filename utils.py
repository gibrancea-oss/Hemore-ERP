import streamlit as st
from supabase import create_client, Client

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
# 3. OPTIMIZACIÓN VISUAL PARA CELULARES
# ==========================================
def aplicar_estilo_movil():
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            .block-container {
                padding-top: 2rem;
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
