import streamlit as st
from supabase import create_client, Client
import extra_streamlit_components as stx
import time

# ==========================================
# 1. CONEXIÓN SEGURA A SUPABASE (Lee desde secrets)
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    # Lee los datos directamente de la bóveda de st.secrets
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializamos la variable que usarán los demás archivos
supabase = init_supabase()

# ==========================================
# 2. BARRERA DE SEGURIDAD PARA PÁGINAS INTERNAS
# ==========================================
def validar_login():
    """
    Bloqueo total: Verifica autenticación de usuario Y validez del dispositivo
    en cada clic de cualquier módulo.
    """
    # 1. Verificar si el usuario está logueado en la sesión
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.error("🔒 ACCESO DENEGADO")
        st.warning("Debes iniciar sesión desde la pantalla de Inicio para acceder a este módulo.")
        st.stop() # Detiene la ejecución del código por completo

    # 2. Verificar si el dispositivo físico sigue autorizado en Supabase
    cookie_manager = stx.CookieManager(key="cookie_check_global")
    # Pausa mínima para permitir que el navegador entregue la cookie
    time.sleep(0.3) 
    token = cookie_manager.get(cookie="hemore_device_token")
    
    if not token:
        st.session_state.clear()
        st.error("🚫 Dispositivo no identificado o cookie eliminada.")
        st.stop()
    
    # Consulta a la base de datos para ver si el token sigue siendo válido
    try:
        res = supabase.table("Dispositivos_Autorizados").select("id").eq("token", token).execute()
        if not res.data:
            st.session_state.clear() # Expulsa al usuario de la sesión actual
            st.error("🚨 ACCESO REVOCADO")
            st.info("Este equipo ha sido bloqueado por el Administrador. El acceso a todos los módulos ha sido cancelado.")
            st.stop()
    except:
        pass

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
