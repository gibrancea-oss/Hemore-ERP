import streamlit as st
import time

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
