import streamlit as st
import extra_streamlit_components as stx
import utils
import os 
import uuid
import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL & ESTILO "SILICON VALLEY LUXURY"
# ==========================================
st.set_page_config(page_title="Inicio | ERP Hemore", page_icon="💼", layout="wide")
utils.aplicar_estilo_movil()

# Inyección de Estilos CSS Maestros (Light Mode High-End Corporate)
st.markdown("""
    <style>
        /* Fondo general platino/perla ultra limpio */
        .stApp {
            background-color: #f8fafc;
            color: #0f172a;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Ocultar elementos predeterminados de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Tarjetas Ejecutivas Supremas con Borde de Luz Superior */
        .executive-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 3px solid #2563eb;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
            margin-bottom: 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .executive-card:hover {
            box-shadow: 0 20px 35px -10px rgba(37, 99, 235, 0.08);
            border-color: #cbd5e1;
            transform: translateY(-2px);
        }
        
        /* Tipografía corporativa con tracking optimizado */
        h1, h2, h3 {
            font-family: inherit;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #0f172a;
        }
        
        /* Campos de Texto (Inputs) de Lujo */
        .stTextInput>div>div>input {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        .stTextInput>div>div>input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        }
        
        /* Botones Principales con Gradiente Ejecutivo */
        .stButton>button {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 12px 24px;
            letter-spacing: 0.025em;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.22);
            transform: translateY(-1px);
        }
        
        /* Divisores elegantes */
        hr {
            border-color: #e2e8f0;
            margin: 28px 0;
        }
        
        /* Animación sutil de pulso para el indicador en vivo */
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }
        .live-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
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
            <div style="background: #ffffff; border: 1px solid #fecaca; border-top: 4px solid #dc2626; border-radius: 16px; padding: 36px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 24px;">🛡️</span>
                    <h3 style='color: #dc2626; margin: 0; font-size: 20px;'>Terminal No Autorizada</h3>
                </div>
                <p style='color: #64748b; font-size: 14px; line-height: 1.6; margin-bottom: 0;'>Este equipo no está vinculado a la red central de la fábrica. Por protocolos de seguridad, el sistema permanece bloqueado para este dispositivo.</p>
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
            st.markdown("<h1 style='color: #0f172a; font-size: 3.2rem; font-weight: 800; letter-spacing: -0.04em;'>HEMORE</h1><p style='color: #64748b; font-size: 15px; font-weight: 500;'>Enterprise Resource Planning System</p>", unsafe_allow_html=True)
            
    with col_login:
        st.markdown("""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #2563eb; border-radius: 20px; padding: 40px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.06);">
                <div style="margin-bottom: 24px;">
                    <span style="background: #eff6ff; color: #1d4ed8; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Autenticación Segura</span>
                    <h2 style='color: #0f172a; margin-top: 14px; margin-bottom: 6px; font-size: 26px;'>Iniciar Sesión</h2>
                    <p style='color: #64748b; font-size: 14px; margin: 0;'>Introduce tus credenciales operativas autorizadas.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Superposición limpia de inputs y botón
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
# 🏠 PANTALLA PRINCIPAL EJECUTIVA ("MILLION-DOLLAR DASHBOARD")
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("Panel de Control")
    st.markdown("<p style='color: #64748b; font-size: 15px; margin-top: -8px; font-weight: 400;'>Sistema Centralizado de Operaciones y Manufactura — Industrias Hemore</p>", unsafe_allow_html=True)

with col_t2:
    st.write("") 
    
    def cerrar_sesion():
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        
    st.button("🚪 Cerrar Sesión", use_container_width=True, on_click=cerrar_sesion)

st.write("<br>", unsafe_allow_html=True)

# Tarjeta de Estado de Sesión Estilizada (Estilo Perfil Corporativo Activo con Indicador Live)
if st.session_state["es_admin"]:
    st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #2563eb; padding: 22px 28px; border-radius: 0 16px 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px;">
            <div>
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span class="live-dot"></span>
                    <span style='color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;'>Sesión Activa Cloud</span>
                </div>
                <strong style='color: #0f172a; font-size: 19px; font-weight: 700;'>{st.session_state['usuario_actual']}</strong>
            </div>
            <div>
                <span style="background: #eff6ff; color: #1d4ed8; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">👑 Acceso Total Habilitado</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #0ea5e9; padding: 22px 28px; border-radius: 0 16px 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px;">
            <div>
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span class="live-dot"></span>
                    <span style='color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;'>Sesión Activa Cloud</span>
                </div>
                <strong style='color: #0f172a; font-size: 19px; font-weight: 700;'>{st.session_state['usuario_actual']}</strong>
            </div>
            <div>
                <span style="background: #f0f9ff; color: #0369a1; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">🔒 Accesos Restringidos</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 18px;'>Selecciona una opción en el menú lateral izquierdo para operar:</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 22px; border-radius: 16px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 20px;">📦</span>
                <strong style='color: #0f172a; font-size: 16px;'>Almacén Central</strong>
            </div>
            <p style='color: #64748b; font-size: 13px; margin: 0; line-height: 1.5;'>Control integral de inventarios, entradas, salidas, recibos oficiales y trazabilidad de préstamos.</p>
        </div>
        <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 22px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 20px;">⚙️</span>
                <strong style='color: #0f172a; font-size: 16px;'>Configuración Master</strong>
            </div>
            <p style='color: #64748b; font-size: 13px; margin: 0; line-height: 1.5;'>Alta y administración de productos, directorio de clientes, proveedores, personal y catálogos QR.</p>
        </div>
    """, unsafe_allow_html=True)

with col_info2:
    if st.session_state["es_admin"]:
        st.markdown("### 🛡️ Nivel de Acceso")
        st.markdown("""
            <div style="background: #ffffff; border: 1px solid #a7f3d0; border-top: 3px solid #059669; padding: 24px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style='color: #065f46; font-weight: 700; font-size: 15px;'>Administrador del Sistema</span>
                </div>
                <p style='color: #475569; font-size: 13px; margin: 0; line-height: 1.6;'>Posees privilegios absolutos para gestionar la infraestructura de datos, seguridad perimetral de equipos y control total sobre los submódulos de Almacén y Configuración de Industrias Hemore.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            permisos_html = "".join([f"<span style='background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; display: inline-block; margin: 4px;'>✅ {p}</span>" for p in st.session_state["permisos"]])
            st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 24px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01); line-height: 2;">
                    {permisos_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: #ffffff; border: 1px solid #fecaca; padding: 24px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01);">
                    <p style='color: #dc2626; font-weight: 700; font-size: 15px; margin-bottom: 4px;'>Sin privilegios activos</p>
                    <p style='color: #64748b; font-size: 13px; margin: 0;'>Tu cuenta no tiene permisos operativos asignados actualmente en el sistema.</p>
                </div>
            """, unsafe_allow_html=True)
