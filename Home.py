import streamlit as st
import utils
import time 
import os 

# Configuración inicial en modo "wide" para aprovechar todo el ancho
st.set_page_config(page_title="Inicio", layout="wide")

# --- SISTEMA DE LOGIN Y SESIONES ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False
if "permisos" not in st.session_state:
    st.session_state["permisos"] = []

if not st.session_state["authenticated"]:
    # ==========================================
    # PANTALLA DE LOGIN COMPACTA (SIN SCROLL)
    # ==========================================
    st.write("<br><br>", unsafe_allow_html=True) # Espacio ligero superior
    
    col_logo, col_login = st.columns([1, 1.5], gap="large")
    
    with col_logo:
        # Mostramos el logo centrado en la columna izquierda
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
            
    with col_login:
        st.title("🔐 Acceso al Sistema ERP")
        st.markdown("El sistema está protegido. Por favor ingresa tus credenciales.")
        
        # Formulario compacto
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        st.write("<br>", unsafe_allow_html=True) # Espacio antes del botón
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if not usuario_input or not password_input:
                st.warning("⚠️ Ingresa usuario y contraseña.")
            else:
                # 👑 1. VALIDACIÓN ADMIN MAESTRO
                if usuario_input == "admin" and password_input == "123": 
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_actual"] = "Administrador"
                    st.session_state["es_admin"] = True
                    st.session_state["permisos"] = ["TODO"]
                    
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
# PANTALLA PRINCIPAL COMPACTA (SIN SCROLL)
# ==========================================

# Logo en el menú lateral
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

# Cabecera
col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🏠 Bienvenido al Panel de Control")

with col_t2:
    st.write("") # Alineación vertical
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        st.rerun()

# Barra de estado
if st.session_state["es_admin"]:
    st.success(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 👑 Acceso Total Habilitado")
else:
    st.info(f"👤 Sesión Activa: **{st.session_state['usuario_actual']}** | 🔒 Accesos Restringidos")

st.divider()

# División en dos columnas para evitar el scroll vertical
col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("Selecciona una opción en el menú de la izquierda:")
    
    # Usamos contenedores o alertas para que se vea como botones o tarjetas
    st.info("**📦 Almacén:** Control de inventarios, entradas, salidas, recibos y préstamos.")
    st.info("**⚙️ Configuración:** Alta de productos, clientes, proveedores, personal y catálogos QR.")

with col_info2:
    if st.session_state["es_admin"]:
         st.markdown("### 🛡️ Nivel de Acceso")
         st.success("Eres Administrador del Sistema. Tienes control total sobre los módulos de Almacén y Configuración, así como la gestión de finanzas e historiales.")
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            # Unimos los permisos horizontalmente separados por un " | " para no hacer lista vertical
            permisos_texto = " | ".join([f"✅ {p}" for p in st.session_state["permisos"]])
            st.success(permisos_texto)
        else:
            st.warning("No tienes permisos asignados actualmente. Contacta al administrador para que te habilite módulos.")
