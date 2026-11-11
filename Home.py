import streamlit as st
import extra_streamlit_components as stx
import utils
import os 
import uuid
import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL & ESTILO "APPLE HIG" (HUMAN INTERFACE GUIDELINES)
# ==========================================
st.set_page_config(page_title="Inicio | ERP Hemore", page_icon="", layout="wide")
utils.aplicar_estilo_movil()

# Inyección de Estilos CSS Maestros (Estética Apple / Light Mode Minimalista de Élite)
st.markdown("""
    <style>
        /* Tipografía y fondo general estilo macOS/iOS Settings */
        .stApp {
            background-color: #F5F5F7;
            color: #1D1D1F;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }
        
        /* Ocultar elementos predeterminados de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Tarjetas estilo Apple Glass / Clean Box */
        .apple-card {
            background: #FFFFFF;
            border: 0.5px solid #D2D2D7;
            border-radius: 18px;
            padding: 32px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
            margin-bottom: 24px;
            transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
        }
        .apple-card:hover {
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
            border-color: #86868B;
        }
        
        /* Tipografía de títulos con tracking de Apple */
        h1, h2, h3 {
            font-family: inherit;
            font-weight: 600;
            letter-spacing: -0.022em;
            color: #1D1D1F;
        }
        
        /* Campos de Texto (Inputs) estilo iOS */
        .stTextInput>div>div>input {
            background-color: #FFFFFF;
            color: #1D1D1F;
            border: 1px solid #D2D2D7;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 15px;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        .stTextInput>div>div>input:focus {
            border-color: #0071E3;
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.15);
        }
        
        /* Botones Principales (Estilo botón azul de Apple / CTA de alto nivel) */
        .stButton>button {
            background-color: #0071E3;
            color: #FFFFFF;
            border: none;
            border-radius: 12px;
            font-weight: 500;
            padding: 12px 24px;
            font-size: 15px;
            letter-spacing: -0.016em;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.3);
            transition: all 0.2s cubic-bezier(0.25, 1, 0.5, 1);
        }
        .stButton>button:hover {
            background-color: #0077ED;
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.4);
            transform: translateY(-1px);
        }
        
        /* Divisores limpios */
        hr {
            border-color: #D2D2D7;
            margin: 32px 0;
        }
        
        /* Indicador de estado en vivo tipo Apple */
        .apple-dot {
            display: inline-block;
            width: 7px;
            height: 7px;
            background-color: #34C759;
            border-radius: 50%;
            margin-right: 6px;
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
            <div style="background: #FFFFFF; border: 0.5px solid #FF3B30; border-radius: 20px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.06);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 22px;">🔒</span>
                    <h3 style='color: #FF3B30; margin: 0; font-size: 20px; font-weight: 600;'>Terminal No Autorizada</h3>
                </div>
                <p style='color: #86868B; font-size: 14px; line-height: 1.5; margin-bottom: 0;'>Este equipo no está vinculado a la red central de la fábrica. Por protocolos de seguridad, el sistema permanece bloqueado para esta terminal.</p>
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
            st.markdown("<h1 style='color: #1D1D1F; font-size: 3.5rem; font-weight: 700; letter-spacing: -0.03em;'>HEMORE</h1><p style='color: #86868B; font-size: 16px; font-weight: 400;'>Enterprise Resource Planning</p>", unsafe_allow_html=True)
            
    with col_login:
        st.markdown("""
            <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; border-radius: 24px; padding: 44px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04);">
                <div style="margin-bottom: 24px;">
                    <span style="background: #F5F5F7; color: #1D1D1F; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Autenticación</span>
                    <h2 style='color: #1D1D1F; margin-top: 14px; margin-bottom: 6px; font-size: 24px;'>Iniciar Sesión</h2>
                    <p style='color: #86868B; font-size: 14px; margin: 0;'>Introduce tus credenciales operativas autorizadas.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Superposición limpia de inputs y botón manteniendo la lógica original
        with st.container():
            st.markdown("<div style='margin-top: -300px; padding: 24px;'>", unsafe_allow_html=True)
            usuario_input = st.text_input("Usuario", placeholder="ej. jPerez")
            password_input = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
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
# 🏠 PANTALLA PRINCIPAL ("APPLE EXECUTIVE DASHBOARD")
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("Panel de Control")
    st.markdown("<p style='color: #86868B; font-size: 15px; margin-top: -6px; font-weight: 400;'>Sistema Centralizado de Operaciones y Manufactura — Industrias Hemore</p>", unsafe_allow_html=True)

with col_t2:
    st.write("") 
    
    def cerrar_sesion():
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        
    st.button("🚪 Cerrar Sesión", use_container_width=True, on_click=cerrar_sesion)

st.write("<br>", unsafe_allow_html=True)

# Tarjeta de Estado de Sesión Estilizada (Estilo Perfil Corporativo Activo)
if st.session_state["es_admin"]:
    st.markdown(f"""
        <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; border-left: 4px solid #0071E3; padding: 20px 24px; border-radius: 0 14px 14px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <div>
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span class="apple-dot"></span>
                    <span style='color: #86868B; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Sesión Activa</span>
                </div>
                <strong style='color: #1D1D1F; font-size: 18px; font-weight: 600;'>{st.session_state['usuario_actual']}</strong>
            </div>
            <div>
                <span style="background: #F0F8FF; color: #0071E3; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;">👑 Acceso Total Habilitado</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; border-left: 4px solid #34C759; padding: 20px 24px; border-radius: 0 14px 14px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <div>
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span class="apple-dot"></span>
                    <span style='color: #86868B; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Sesión Activa</span>
                </div>
                <strong style='color: #1D1D1F; font-size: 18px; font-weight: 600;'>{st.session_state['usuario_actual']}</strong>
            </div>
            <div>
                <span style="background: #F2F4F7; color: #1D1D1F; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;">🔒 Accesos Restringidos</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("<p style='color: #86868B; font-size: 14px; margin-bottom: 16px;'>Selecciona una opción en el menú lateral izquierdo:</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; padding: 20px; border-radius: 14px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="font-size: 18px;">📦</span>
                <strong style='color: #1D1D1F; font-size: 15px;'>Almacén Central</strong>
            </div>
            <p style='color: #86868B; font-size: 13px; margin: 0; line-height: 1.4;'>Control de inventarios, entradas, salidas, recibos y préstamos.</p>
        </div>
        <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; padding: 20px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="font-size: 18px;">⚙️</span>
                <strong style='color: #1D1D1F; font-size: 15px;'>Configuración Master</strong>
            </div>
            <p style='color: #86868B; font-size: 13px; margin: 0; line-height: 1.4;'>Alta de productos, clientes, proveedores, personal y catálogos QR.</p>
        </div>
    """, unsafe_allow_html=True)

with col_info2:
    if st.session_state["es_admin"]:
        st.markdown("### 🛡️ Nivel de Acceso")
        st.markdown("""
            <div style="background: #FFFFFF; border: 0.5px solid #34C759; padding: 24px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                <p style='color: #248A3D; font-weight: 600; font-size: 15px; margin-bottom: 6px;'>Administrador del Sistema</p>
                <p style='color: #86868B; font-size: 13px; margin: 0; line-height: 1.5;'>Tienes control total y absoluto sobre los submódulos de Almacén y Configuración de Industrias Hemore.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            permisos_html = "".join([f"<span style='background: #F5F5F7; color: #1D1D1F; border: 0.5px solid #D2D2D7; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; display: inline-block; margin: 3px;'>✅ {p}</span>" for p in st.session_state["permisos"]])
            st.markdown(f"""
                <div style="background: #FFFFFF; border: 0.5px solid #D2D2D7; padding: 24px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); line-height: 2;">
                    {permisos_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: #FFFFFF; border: 0.5px solid #FF3B30; padding: 24px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                    <p style='color: #FF3B30; font-weight: 600; font-size: 15px; margin-bottom: 4px;'>Sin privilegios activos</p>
                    <p style='color: #86868B; font-size: 13px; margin: 0;'>No tienes permisos asignados actualmente en el sistema.</p>
                </div>
            """, unsafe_allow_html=True)
