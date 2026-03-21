import streamlit as st
import utils
import time 
import os # Añadido para poder leer el logo

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
    # MODO BLOQUEADO
    # --- MOSTRAR LOGO EN LA PANTALLA DE ACCESO ---
    if os.path.exists("logo.png"):
        st.image("logo.png", width=300)
        
    st.title("🔐 Acceso al Sistema ERP")
    st.markdown("El sistema está protegido. Por favor ingresa tus credenciales.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # Ahora pedimos Usuario y Contraseña
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al Sistema", type="primary"):
            if not usuario_input or not password_input:
                st.warning("⚠️ Ingresa usuario y contraseña.")
            else:
                # 👑 1. VALIDACIÓN ADMIN MAESTRO
                if usuario_input == "admin" and password_input == "123": 
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_actual"] = "Administrador"
                    st.session_state["es_admin"] = True
                    st.session_state["permisos"] = ["TODO"] # El admin tiene llave maestra
                    
                    st.toast("✅ Acceso Concedido (Admin)")
                    time.sleep(1) 
                    st.rerun()
                
                # 👷‍♂️ 2. VALIDACIÓN OPERADORES EN SUPABASE
                else:
                    try:
                        # Buscamos en la tabla Personal si coincide el usuario, el PIN y si está activo
                        res = utils.supabase.table("Personal").select("*").eq("usuario", usuario_input).eq("pin", password_input).eq("activo", True).execute()
                        datos_usuario = res.data
                        
                        if len(datos_usuario) > 0:
                            usuario_db = datos_usuario[0]
                            st.session_state["authenticated"] = True
                            st.session_state["usuario_actual"] = usuario_db["nombre"]
                            st.session_state["es_admin"] = False
                            
                            # Recuperamos los permisos y los convertimos en una lista
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

# --- CONTENIDO DEL SISTEMA (CUANDO YA ENTRASTE) ---

# --- MOSTRAR LOGO EN EL MENÚ LATERAL ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🏠 Bienvenido al Panel de Control")

with col_t2:
    # --- BOTÓN PARA CERRAR SESIÓN ---
    st.write("") # Espaciador ligero
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []
        st.rerun()

# Mostramos un mensaje diferente si es admin o si es operador
if st.session_state["es_admin"]:
    st.success(f"👤 Sesión Activa: {st.session_state['usuario_actual']} | 👑 Acceso Total Habilitado")
else:
    st.info(f"👤 Sesión Activa: {st.session_state['usuario_actual']} | 🔒 Accesos Restringidos")

st.markdown("""
### 🚀 Accesos Directos
Selecciona una opción en el menú de la izquierda:
- **📦 Almacén:** Control de inventarios, entradas, salidas y préstamos.
- **⚙️ Configuración:** Alta de productos, clientes, personal y catálogos maestros.
""")

# Le mostramos al operador a qué cosas tiene acceso para que no haya dudas
if not st.session_state["es_admin"]:
    st.markdown("#### Tus permisos habilitados:")
    if st.session_state["permisos"]:
        for p in st.session_state["permisos"]:
            st.write(f"- ✅ {p}")
    else:
        st.warning("No tienes permisos asignados actualmente. Contacta al administrador para que te habilite módulos.")
