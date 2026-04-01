import streamlit as st
import time
from supabase import create_client, Client

# =========================================================
# CONEXIÓN A SUPABASE (ACTIVA)
# =========================================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# =========================================================
# FUNCIÓN DE VALIDACIÓN DE LOGIN E INACTIVIDAD
# =========================================================
def validar_login():
    # 1. Verificar si hay una sesión activa
    if not st.session_state.get("authenticated", False):
        st.warning("🔒 Por favor, inicia sesión para acceder a este módulo.")
        st.stop()
    
    # 2. Lógica de Inactividad (Solo para No Administradores)
    if not st.session_state.get("es_admin", False):
        # Si no existe el registro de tiempo, lo creamos
        if "last_activity" not in st.session_state:
            st.session_state["last_activity"] = time.time()
        
        # Calculamos cuánto tiempo ha pasado desde el último clic
        tiempo_inactivo = time.time() - st.session_state["last_activity"]
        
        if tiempo_inactivo > 60:  # 60 segundos = 1 minuto
            # Limpiamos las variables para forzar el cierre de sesión
            st.session_state["authenticated"] = False
            st.session_state["usuario_actual"] = ""
            st.session_state["es_admin"] = False
            st.session_state["permisos"] = []
            st.session_state.pop("last_activity", None)
            
            st.error("⏱️ Tu sesión ha expirado por inactividad (1 minuto). Volviendo al inicio...")
            time.sleep(2.5)
            st.rerun()
        else:
            # Si hizo clic antes del minuto, reiniciamos el reloj
            st.session_state["last_activity"] = time.time()

# =========================================================
# DISEÑO RESPONSIVO PARA CELULARES (MOBILE-FRIENDLY)
# =========================================================
def aplicar_estilo_movil():
    st.markdown("""
    <style>
    /* Ajustes específicos para pantallas de celular (menores a 768px) */
    @media (max-width: 768px) {
        /* 1. Reducir los márgenes laterales gigantes de Streamlit */
        .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* 2. Hacer los botones más altos y anchos para que sea fácil tocarlos con el dedo */
        div[data-testid="stButton"] > button {
            width: 100% !important;
            height: 3.5rem !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* 3. Ajustar tamaño de los títulos para que no se desborden ni ocupen media pantalla */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.2rem !important; }
        
        /* 4. Asegurar que los inputs de texto y selectores sean cómodos de tocar */
        div[data-testid="stTextInput"] input, 
        div[data-testid="stSelectbox"] div[role="combobox"],
        div[data-testid="stNumberInput"] input {
            height: 3rem !important;
            font-size: 1rem !important;
        }
        
        /* 5. Ajustar las pestañas (Tabs) para que se puedan deslizar horizontalmente si son muchas */
        div[data-testid="stTabs"] button {
            flex: 1;
            font-size: 0.9rem !important;
            padding: 0.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
