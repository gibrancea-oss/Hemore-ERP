import streamlit as st
import extra_streamlit_components as stx
import utils
import os 
import uuid
import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL & ESTILO "PREMIUM"
# ==========================================
st.set_page_config(page_title="Inicio | ERP Hemore", page_icon="💼", layout="wide")
utils.aplicar_estilo_movil()

# Inyección de Estilos CSS Ejecutivos (Look & Feel "Carro / High-End Corporate")
st.markdown("""
    <style>
        /* Fondo general y tipografía limpia */
        .stApp {
            background-color: #0f1117;
            color: #f8fafc;
        }
        
        /* Contenedores tipo tarjeta ejecutiva (Cards) */
        .executive-card {
            background: linear-gradient(135deg, #1e222b 0%, #161922 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        
        /* Tipografía de títulos corporativos */
        h1, h2, h3 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            letter-spacing: -0.5px;
        }
        
        /* Estilizar inputs de texto para que luzcan modernos */
        .stTextInput>div>div>input {
            background-color: #161922;
            color: #ffffff;
            border: 1px solid #2d3748;
            border-radius: 8px;
            padding: 10px 14px;
        }
        .stTextInput>div>div>input:focus {
            border-color: #0066cc;
            box-shadow: 0 0 0 1px #0066cc;
        }
        
        /* Botones ejecutivos primarios */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 0.3s ease;
        }
        
        /* Métricas y divisores sutiles */
        hr {
            border-color: rgba(255, 255, 255, 0.08);
        }
    </style>
""", unsafe_allow_html=True)

if "bypass_device" not in st.session_state:
    st.session_state["bypass_device"] = False

# ==========================================
# 🛡️ BARRERA 1: DISPOSITIVO DE CONFIANZA
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager_hemore")

device_token = cookie_manager.get(cookie="hemore_device_token")
dispositivo_valido = False

if device_token:
    try:
        res_device = utils.supabase.table("Dispositivos_Autorizados").select("*").eq("token", device_token).execute()
        if len(res_device.data) > 0:
            dispositivo_valido = True
    except Exception as e:
        pass 

if st.session_state["bypass_device"]:
    dispositivo_valido = True

if not dispositivo_valido:
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1e222b 0%, #161922 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.4);">
                <h3 style='color: #ef4444; margin-top: 0;'>⛔ Acceso Denegado</h3>
                <p style='color: #94a3b8; font-size: 15px; line-height: 1.5;'>Este equipo no está vinculado a la red de la fábrica. Por seguridad, no puedes visualizar la pantalla de inicio de sesión.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        with st.expander("⚙️ Vincular este equipo (Solo Administrador)"):
            admin_pass_link = st.text_input("Contraseña Maestra", type="password", key="auth_pass")
            nombre_equipo = st.text_input("Nombre de este equipo (Ej. Computadora Almacén)", key="auth_name")
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Vincular Equipo Físico", type="primary", use_container_width=True):
                if admin_pass_link == st.secrets["admin_password"]:
                    if nombre_equipo:
                        nuevo_token = str(uuid.uuid4())
                        try:
                            utils.supabase.table("Dispositivos_Autorizados").insert({"token": nuevo_token, "descripcion": nombre_equipo}).execute()
                            vencimiento = datetime.datetime.now() + datetime.timedelta(days=1825)
                            cookie_manager.set("hemore_device_token", nuevo_token, expires_at=vencimiento)
                            st.session_state["bypass_device"] = True
                            st.toast("✅ Equipo vinculado exitosamente", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al conectar: {e}")
                    else:
                        st.warning("Escribe un nombre para identificar este equipo.")
                else:
                    st.error("Contraseña incorrecta.")
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
    
    col_logo, col_login = st.columns([1.2, 1.5], gap="large")
    
    with col_logo:
        st.write("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='color: #0066cc; font-size: 3rem;'>HEMORE</h1><p style='color: #64748b;'>Enterprise Resource Planning</p>", unsafe_allow_html=True)
            
    with col_login:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1e222b 0%, #161922 100%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 35px; box-shadow: 0 20px 40px rgba(0,0,0,0.4);">
                <h2 style='color: #f8fafc; margin-top: 0; margin-bottom: 5px; font-size: 24px;'>Acceso al Sistema</h2>
                <p style='color: #94a3b8; font-size: 14px; margin-bottom: 25px;'>Ingresa tus credenciales operativas autorizadas.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Superposición de los inputs y botones dentro del flujo visual limpio de Streamlit
        with st.container():
            st.markdown("<div style='margin-top: -330px; padding: 20px;'>", unsafe_allow_html=True)
            usuario_input = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password_input = st.text_input("Contraseña / PIN", type="password", placeholder="••••••••")
            
            st.write("<br>", unsafe_allow_html=True) 
            
            if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
                if not usuario_input or not password_input:
                    st.warning("⚠️ Ingresa usuario y contraseña.")
                else:
                    if usuario_input == st.secrets["admin_user"] and password_input == st.secrets["admin_password"]: 
                        st.session_state["authenticated"] = True
                        st.session_state["usuario_actual"] = "Administrador Master"
                        st.session_state["es_admin"] = True
                        st.session_state["permisos"] = ["TODO"]
                        st.toast("✅ Acceso Concedido", icon="🔓")
                        st.rerun()
                    else:
                        try:
                            res = utils.supabase.table("Personal").select("*").eq("usuario", usuario_input).eq("pin", password_input).eq("activo", True).execute()
                            if len(res.data) > 0:
                                usuario_db = res.data[0]
                                st.session_state["authenticated"] = True
                                st.session_state["usuario_actual"] = usuario_db["nombre"]
                                st.session_state["es_admin"] = False
                                permisos_str = usuario_db.get("permisos", "")
                                st.session_state["permisos"] = [p.strip() for p in permisos_str.split(",")] if permisos_str else []
                                st.toast(f"✅ Bienvenido {usuario_db['nombre']}", icon="🔓")
                                st.rerun()
                            else:
                                st.error("⛔ Usuario o contraseña incorrectos")
                        except Exception as e:
                            st.error(f"Error de conexión: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop() 

# ==========================================
# 🏠 PANTALLA PRINCIPAL COMPACTA & EJECUTIVA
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("Panel de Control")
    st.caption("Sistema Centralizado de Operaciones y Manufactura — Industrias Hemore")

with col_t2:
    st.write("") 
    
    def cerrar_sesion():
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        
    st.button("🚪 Cerrar Sesión", use_container_width=True, on_click=cerrar_sesion)

st.write("<br>", unsafe_allow_html=True)

# Tarjeta de Estado de Sesión Estilizada
if st.session_state["es_admin"]:
    st.markdown(f"""
        <div style="background: rgba(0, 102, 204, 0.1); border-left: 4px solid #0066cc; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 25px;">
            <span style='color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;'>Sesión Activa</span><br>
            <strong style='color: #f8fafc; font-size: 16px;'>{st.session_state['usuario_actual']}</strong> &nbsp;&nbsp;|&nbsp;&nbsp; <span style='color: #60a5fa;'>👑 Acceso Total Habilitado</span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 25px;">
            <span style='color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;'>Sesión Activa</span><br>
            <strong style='color: #f8fafc; font-size: 16px;'>{st.session_state['usuario_actual']}</strong> &nbsp;&nbsp;|&nbsp;&nbsp; <span style='color: #93c5fd;'>🔒 Accesos Restringidos</span>
        </div>
    """, unsafe_allow_html=True)

st.divider()

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Selecciona una opción en el menú de la izquierda para comenzar:</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: #161922; border: 1px solid rgba(255,255,255,0.06); padding: 16px; border-radius: 10px; margin-bottom: 12px;">
            <strong style='color: #f8fafc; font-size: 15px;'>📦 Almacén</strong>
            <p style='color: #94a3b8; font-size: 13px; margin: 4px 0 0 0;'>Control de inventarios, entradas, salidas, recibos y préstamos.</p>
        </div>
        <div style="background: #161922; border: 1px solid rgba(255,255,255,0.06); padding: 16px; border-radius: 10px;'>
            <strong style='color: #f8fafc; font-size: 15px;'>⚙️ Configuración</strong>
            <p style='color: #94a3b8; font-size: 13px; margin: 4px 0 0 0;'>Alta de productos, clientes, proveedores, personal y catálogos QR.</p>
        </div>
    """, unsafe_allow_html=True)

with col_info2:
    if st.session_state["es_admin"]:
        st.markdown("### 🛡️ Nivel de Acceso")
        st.markdown("""
            <div style="background: #161922; border: 1px solid rgba(16, 185, 129, 0.2); padding: 20px; border-radius: 10px;">
                <p style='color: #10b981; font-weight: 600; margin-bottom: 8px;'>Administrador del Sistema</p>
                <p style='color: #94a3b8; font-size: 13px; margin: 0;'>Tienes control absoluto y total sobre los módulos operativos de Almacén y Configuración de Industrias Hemore.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            permisos_html = "".join([f"<span style='background: rgba(59, 130, 246, 0.15); color: #93c5fd; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-block; margin: 3px;'>✅ {p}</span>" for p in st.session_state["permisos"]])
            st.markdown(f"""
                <div style="background: #161922; border: 1px solid rgba(255,255,255,0.06); padding: 20px; border-radius: 10px; line-height: 1.8;">
                    {permisos_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: #161922; border: 1px solid rgba(239, 68, 68, 0.2); padding: 20px; border-radius: 10px;">
                    <p style='color: #ef4444; font-weight: 600; margin-bottom: 4px;'>Sin privilegios activos</p>
                    <p style='color: #94a3b8; font-size: 13px; margin: 0;'>No tienes permisos asignados actualmente en el sistema.</p>
                </div>
            """, unsafe_allow_html=True)
