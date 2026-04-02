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

# ==========================================
# 🛡️ BARRERA 1: DISPOSITIVO DE CONFIANZA
# ==========================================
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()
time.sleep(0.1) # Pausa milimétrica para asegurar la lectura de la cookie

device_token = cookie_manager.get(cookie="hemore_device_token")
dispositivo_valido = False

# Verificamos si el equipo tiene la cookie y si existe en Supabase
if device_token:
    try:
        res_device = utils.supabase.table("Dispositivos_Autorizados").select("*").eq("token", device_token).execute()
        if len(res_device.data) > 0:
            dispositivo_valido = True
    except Exception as e:
        pass # Si hay error de red, se asume inválido por seguridad

# SI EL DISPOSITIVO NO ES RECONOCIDO, SE BLOQUEA LA PANTALLA AQUÍ
if not dispositivo_valido:
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.error("⛔ Acceso Denegado: Dispositivo No Autorizado")
        st.markdown("Este equipo no está vinculado a la red de la fábrica. Por seguridad, no puedes visualizar la pantalla de inicio de sesión.")
        
        # --- PUERTA TRASERA PARA VINCULAR EQUIPO ---
        with st.expander("⚙️ Vincular este equipo (Solo Administrador)"):
            admin_pass_link = st.text_input("Contraseña Maestra", type="password", key="auth_pass")
            nombre_equipo = st.text_input("Nombre de este equipo (Ej. Computadora Almacén)", key="auth_name")
            
            if st.button("Vincular Equipo Físico", type="primary", use_container_width=True):
                # Validamos contra la bóveda de secretos de Streamlit
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
                            
                            st.success("✅ Equipo vinculado exitosamente.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al conectar con la base de datos: {e}")
                    else:
                        st.warning("Escribe un nombre para identificar este equipo.")
                else:
                    st.error("Contraseña incorrecta. Contacta a gerencia.")
    
    # ESTO DETIENE EL CÓDIGO. NADIE PASA AL LOGIN SIN SER VINCULADO.
    st.stop() 

# ==========================================
# 🛡️ BARRERA 2: SISTEMA DE LOGIN Y SESIONES
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False
if "permisos" not in st.session_state:
    st.session_state["permisos"] = []

if not st.session_state["authenticated"]:
    st.write("<br><br>", unsafe_allow_html=True) 
    
    col_logo, col_login = st.columns([1, 1.5], gap="large")
    
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
            
    with col_login:
        st.title("🔐 Acceso al Sistema ERP")
        st.success("✅ Equipo Autorizado")
        st.markdown("Por favor ingresa tus credenciales operativas.")
        
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        st.write("<br>", unsafe_allow_html=True) 
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if not usuario_input or not password_input:
                st.warning("⚠️ Ingresa usuario y contraseña.")
            else:
                # 👑 1. VALIDACIÓN ADMIN MAESTRO (LEYENDO DESDE SECRETS)
                if usuario_input == st.secrets["admin_user"] and password_input == st.secrets["admin_password"]: 
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_actual"] = "Administrador Master"
                    st.session_state["es_admin"] = True
                    st.session_state["permisos"] = ["TODO"]
                    st.session_state["last_activity"] = time.time() 
                    
                    st.toast("✅ Acceso Concedido (Admin)")
                    time.sleep(1) 
                    st.rerun()
                
                # 👷‍♂️ 2. VALIDACIÓN OPERADORES
                else:
                    try:
                        res = utils.supabase.table("Personal").select("*").eq("usuario", usuario_input).eq("pin", password_input).eq("activo", True).execute()
                        datos_usuario = res.data
                        
                        if len(datos_usuario) > 0:
                            usuario_db = datos_usuario[0]
                            st.session_state["authenticated"] = True
                            st.session_state["last_activity"] = time.time() 
                            
                            st.session_state["usuario_actual"] = usuario_db["nombre"]
                            st.session_state["es_admin"] = False
                            
                            permisos_str = usuario_db.get("permisos", "")
                            if permisos_str:
                                st.session_state["permisos"] = [p.strip() for p in permisos_str.split(",")]
                            else:
                                st.session_state["permisos"] = []
                                
                            st.toast(f"✅ Bienvenido, {usuario_db['nombre']}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("⛔ Usuario o contraseña incorrectos (o usuario inactivo)")
                    except Exception as e:
                        st.error(f"Error de conexión con la base de datos: {e}")
    
    st.stop() 

# ==========================================
# 🏠 PANTALLA PRINCIPAL COMPACTA
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🏠 Bienvenido al Panel de Control")

with col_t2:
    st.write("") 
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        st.session_state.pop("last_activity", None)
        st.rerun()

if st.session_state["es_admin"]:
    st.success(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 👑 Acceso Total Habilitado")
else:
    st.info(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 🔒 Accesos Restringidos")

st.divider()

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("Selecciona una opción en el menú de la izquierda:")
    
    st.info("**📦 Almacén:** Control de inventarios, entradas, salidas, recibos y préstamos.")
    st.info("**⚙️ Configuración:** Alta de productos, clientes, proveedores, personal y catálogos QR.")

with col_info2:
    if st.session_state["es_admin"]:
         st.markdown("### 🛡️ Nivel de Acceso")
         st.success("Eres Administrador del Sistema. Tienes control total sobre los módulos de Almacén y Configuración.")
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            permisos_texto = " | ".join([f"✅ {p}" for p in st.session_state["permisos"]])
            st.success(permisos_texto)
        else:
            st.warning("No tienes permisos asignados actualmente.")
