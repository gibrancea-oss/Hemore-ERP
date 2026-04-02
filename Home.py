import streamlit as st
import extra_streamlit_components as stx
import utils
import time 
import os 
import uuid
import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="Inicio", layout="wide")
utils.aplicar_estilo_movil()

# Creamos un contenedor vacío para evitar el parpadeo visual
placeholder = st.empty()

# ==========================================
# 🛡️ BARRERA 1: DISPOSITIVO DE CONFIANZA
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager_hemore")

# Damos un tiempo mínimo para que la cookie sea leída por el navegador
time.sleep(0.5) 

device_token = cookie_manager.get(cookie="hemore_device_token")
dispositivo_valido = False

# Verificamos si el equipo tiene la cookie y si existe en Supabase
if device_token:
    try:
        res_device = utils.supabase.table("Dispositivos_Autorizados").select("*").eq("token", device_token).execute()
        if len(res_device.data) > 0:
            dispositivo_valido = True
    except Exception:
        pass 

# SI EL DISPOSITIVO NO ES RECONOCIDO
if not dispositivo_valido:
    with placeholder.container():
        st.write("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.error("⛔ Acceso Denegado: Dispositivo No Autorizado")
            st.markdown("Este equipo no está vinculado a la red de la fábrica.")
            
            with st.expander("⚙️ Vincular este equipo (Solo Administrador)"):
                admin_pass_link = st.text_input("Contraseña Maestra", type="password", key="auth_pass")
                nombre_equipo = st.text_input("Nombre de este equipo", key="auth_name")
                
                if st.button("Vincular Equipo Físico", type="primary", use_container_width=True):
                    if admin_pass_link == st.secrets["admin_password"]:
                        if nombre_equipo:
                            nuevo_token = str(uuid.uuid4())
                            try:
                                # 1. Guardar en Supabase
                                utils.supabase.table("Dispositivos_Autorizados").insert({
                                    "token": nuevo_token,
                                    "descripcion": nombre_equipo
                                }).execute()
                                
                                # 2. Inyectar la Cookie (Vence en 5 años)
                                vencimiento = datetime.datetime.now() + datetime.timedelta(days=1825)
                                cookie_manager.set("hemore_device_token", nuevo_token, expires_at=vencimiento)
                                
                                st.success("✅ Equipo vinculado. Redirigiendo...")
                                time.sleep(1)
                                st.rerun() # Recarga automática para quitar los botones de vinculación
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")
                        else:
                            st.warning("Escribe un nombre para el equipo.")
                    else:
                        st.error("Contraseña incorrecta.")
        st.stop() 

# ==========================================
# 🛡️ BARRERA 2: SISTEMA DE LOGIN (EQUIPO AUTORIZADO)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with placeholder.container():
        st.write("<br><br>", unsafe_allow_html=True) 
        col_logo, col_login = st.columns([1, 1.5], gap="large")
        
        with col_logo:
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
                
        with col_login:
            st.title("🔐 Acceso al Sistema ERP")
            st.success("✅ Equipo Autorizado para uso de HEMORE")
            
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            
            if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
                if usuario_input == st.secrets["admin_user"] and password_input == st.secrets["admin_password"]: 
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_actual"] = "Administrador Master"
                    st.session_state["es_admin"] = True
                    st.session_state["permisos"] = ["TODO"]
                    st.rerun()
                else:
                    res = utils.supabase.table("Personal").select("*").eq("usuario", usuario_input).eq("pin", password_input).eq("activo", True).execute()
                    if len(res.data) > 0:
                        usuario_db = res.data[0]
                        st.session_state["authenticated"] = True
                        st.session_state["usuario_actual"] = usuario_db["nombre"]
                        st.session_state["es_admin"] = False
                        permisos_str = usuario_db.get("permisos", "")
                        st.session_state["permisos"] = [p.strip() for p in permisos_str.split(",")] if permisos_str else []
                        st.rerun()
                    else:
                        st.error("⛔ Credenciales incorrectas")
    st.stop()

# ==========================================
# 🏠 PANTALLA PRINCIPAL (YA LOGUEADO)
# ==========================================
with placeholder.container():
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)

    col_t1, col_t2 = st.columns([8, 2])
    with col_t1:
        st.title("🏠 Bienvenido al Panel de Control")

    with col_t2:
        st.write("") 
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    if st.session_state.get("es_admin", False):
        st.success(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 👑 Acceso Total")
    else:
        st.info(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 🔒 Accesos Restringidos")

    st.divider()

    col_info1, col_info2 = st.columns(2, gap="large")
    with col_info1:
        st.markdown("### 🚀 Accesos Directos")
        st.info("**📦 Almacén:** Gestión de inventarios y movimientos.")
        st.info("**⚙️ Configuración:** Catálogos y control de seguridad.")

    with col_info2:
        if st.session_state.get("es_admin", False):
             st.success("Tienes control total sobre los módulos del sistema.")
        else:
            st.markdown("### 🛡️ Tus permisos:")
            if st.session_state.get("permisos"):
                st.success(" | ".join([f"✅ {p}" for p in st.session_state["permisos"]]))
            else:
                st.warning("No tienes permisos asignados.")
