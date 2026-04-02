import streamlit as st
from supabase import create_client, Client

# ==========================================
# 1. CONEXIÓN SEGURA A SUPABASE (Lee desde secrets)
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    # Lee los datos directamente de la bóveda de st.secrets
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializamos la variable que usarán los demás archivos (almacen.py, configuracion.py)
supabase = init_supabase()

# ==========================================
# 2. BARRERA DE SEGURIDAD PARA PÁGINAS INTERNAS
# ==========================================
def validar_login():
    """
    Esta función se llama al inicio de almacen.py y configuracion.py.
    Si alguien intenta entrar directo por URL sin pasar por home.py, lo bloquea.
    """
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.error("🔒 ACCESO DENEGADO")
        st.warning("Debes iniciar sesión desde la pantalla de Inicio para acceder a este módulo.")
        st.stop() # Detiene la ejecución del código por completo

# ==========================================
# 3. OPTIMIZACIÓN VISUAL PARA CELULARES
# ==========================================
def aplicar_estilo_movil():
    """
    Ajusta los márgenes para que los botones y tablas 
    se vean bien en las pantallas de las tablets y celulares de la fábrica.
    """
    st.markdown("""
        <style>
        /* Reducir márgenes en pantallas pequeñas */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            /* Hacer que los botones ocupen todo el ancho en móviles */
            .stButton>button {
                width: 100%;
            }
        }
        </style>
    """, unsafe_allow_html=True)
