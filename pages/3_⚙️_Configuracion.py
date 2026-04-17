import streamlit as st
import pandas as pd
import utils 
import time
import datetime
import io
import qrcode
import os
import base64
import json
import urllib.request
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

utils.aplicar_estilo_movil()
utils.validar_login()

supabase = utils.supabase

def tiene_permiso(permiso):
    if st.session_state.get("es_admin", False): return True
    return permiso in st.session_state.get("permisos", [])

def renderizar_manual_config(modulo):
    if modulo == "Personal" or modulo == "Todos":
        st.markdown("## 👥 Módulo: Personal y Accesos")
        st.markdown("Este es el panel de control de Recursos Humanos y Seguridad.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Insumos" or modulo == "Todos":
        st.markdown("## 📦 Módulo: Catálogo de Insumos")
        st.markdown("Este es el 'Diccionario' de tu almacén.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Herramientas" or modulo == "Todos":
        st.markdown("## 🛠️ Módulo: Catálogo de Herramientas")
        st.markdown("El registro oficial de los activos fijos de la empresa.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Clientes" or modulo == "Todos":
        st.markdown("## 🏢 Módulo: Directorio de Clientes")
        st.markdown("El listado de las empresas a las que HEMORE les entrega mobiliario.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()
    
    if modulo == "Proveedores" or modulo == "Todos":
        st.markdown("## 🚚 Módulo: Directorio de Proveedores")
        st.markdown("El padrón de todas las empresas que surten materia prima a la fábrica.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Etiquetas" or modulo == "Todos":
        st.markdown("## 📂 Módulo: Catálogos y Etiquetas QR")
        st.markdown("Esta es tu herramienta de automatización para inventarios físicos.")

@st.dialog("📖 Manual de Configuración", width="large")
def modal_manual_completo_config():
    renderizar_manual_config("Todos")

@st.dialog("❓ Ayuda del Módulo", width="large")
def modal_ayuda_modulo_config(modulo):
    renderizar_manual_config(modulo)

def get_qr_data_url(text):
    if not text: return None
    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(str(text))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
    except: return None

# --- FUNCIONES PARA COLORES PERSONALIZADOS ---
CONFIG_FILE = "config_credencial.json"

def cargar_colores():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"color_1": "#1E2328", "color_2": "#0066CC"}

def guardar_colores(c1, c2):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"color_1": c1, "color_2": c2}, f)

def hex_a_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- SOLUCIÓN DEFINITIVA PARA FUENTES GIGANTES ---
def obtener_fuente_segura(size, bold=False):
    # Descarga fuentes Roboto oficiales de Google para asegurar que sí escale el tamaño
    font_name = "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"
    font_url = f"https://github.com/googlefonts/roboto/raw/main/src/hinted/{font_name}"
    
    if not os.path.exists(font_name):
        try:
            urllib.request.urlretrieve(font_url, font_name)
        except:
            pass # Falla silenciosa si no hay internet
            
    try:
        return ImageFont.truetype(font_name, size)
    except:
        return ImageFont.load_default()

# --- FUNCIÓN: GENERADOR DE TARJETAS TAMAÑO INE MEJORADO ---
def generar_credencial_pro(nombre, puesto, usuario, pin, c1_hex, c2_hex):
    width, height = 1012, 638 
    img = Image.new('RGB', (width, height), color=(245, 245, 250))
    canvas = ImageDraw.Draw(img)

    color_1 = hex_a_rgb(c1_hex)
    color_2 = hex_a_rgb(c2_hex)

    # Ahora sí usará fuentes escalables descargadas
    f_bold_xl = obtener_fuente_segura(85, bold=True)     # Título Principal
    f_italic_md = obtener_fuente_segura(35, bold=False)  # Subtítulo G Solutions
    f_bold_lg = obtener_fuente_segura(55, bold=True)     # Etiquetas (Nombre:, Puesto:)
    f_reg_lg = obtener_fuente_segura(55, bold=False)     # Valores (Gibran, etc)
    f_bold_sm = obtener_fuente_segura(24, bold=True)     # Etiquetas Empresa
    f_reg_sm = obtener_fuente_segura(24, bold=False)     # Valores Empresa
    f_footer = obtener_fuente_segura(18, bold=False)     # Pie de página miniatura

    # 1. Cabecera y Franja
    canvas.rectangle([0, 0, width, 170], fill=color_1)
    canvas.rectangle([0, 170, width, 185], fill=color_2)

    # 2. Logo de HEMORE (Más grande: 150x150)
    text_x_offset = 50
    if os.path.exists("logo.png"):
        try:
            logo = Image.open("logo.png").convert("RGBA")
            logo.thumbnail((150, 150))
            img.paste(logo, (40, 10), logo)
            text_x_offset = 220 
        except: pass

    # 3. Títulos de Cabecera
    canvas.text((text_x_offset, 25), "ERP HEMORE", font=f_bold_xl, fill=(255, 255, 255))
    canvas.text((text_x_offset + 5, 115), "Powered by G Solutions", font=f_italic_md, fill=(200, 220, 255))

    # 4. Cuadro contenedor
    try: canvas.rounded_rectangle([25, 205, 987, 615], radius=15, fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    except: canvas.rectangle([25, 205, 987, 615], fill=(255, 255, 255), outline=(200, 200, 200), width=2)

    # 5. Datos GIGANTES
    col1_x = 60
    col2_x = 360
    
    canvas.text((col1_x, 225), "Nombre:", font=f_bold_lg, fill=(80, 80, 80))
    canvas.text((col2_x, 225), f"{nombre}", font=f_reg_lg, fill=(0, 0, 0))
    
    canvas.text((col1_x, 295), "Puesto:", font=f_bold_lg, fill=(80, 80, 80))
    canvas.text((col2_x, 295), f"{puesto}", font=f_reg_lg, fill=(60, 60, 60))
    
    canvas.line((col1_x, 365, 952, 365), fill=(230, 230, 230), width=3)
    
    canvas.text((col1_x, 385), "Usuario:", font=f_bold_lg, fill=color_2)
    canvas.text((col2_x, 385), f"{usuario}", font=f_reg_lg, fill=(0, 0, 0))
    
    canvas.text((col1_x, 460), "Contraseña:", font=f_bold_lg, fill=(200, 0, 0))
    canvas.text((col2_x, 460), f"{pin}", font=f_reg_lg, fill=(200, 0, 0))

    canvas.line((col1_x, 530, 952, 530), fill=(230, 230, 230), width=2)

    # 6. Información de la Empresa (HEMORE)
    canvas.text((col1_x, 540), "Dirección:", font=f_bold_sm, fill=(100, 100, 100))
    canvas.text((col1_x + 130, 540), "De Las Americas 3621, América Sur, 72340 Heroica Puebla de Zaragoza, Pue", font=f_reg_sm, fill=(100, 100, 100))
    
    canvas.text((col1_x, 570), "Tel:", font=f_bold_sm, fill=(100, 100, 100))
    canvas.text((col1_x + 50, 570), "2228889858", font=f_reg_sm, fill=(100, 100, 100))
    
    canvas.text((col1_x + 280, 570), "Link:", font=f_bold_sm, fill=(100, 100, 100))
    canvas.text((col1_x + 350, 570), "https://industriashemore.com/", font=f_reg_sm, fill=color_2)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
# ------------------------------------------------

class PDFEtiquetas(FPDF):
    def footer(self):
        self.set_y(-10)
        self.set_font('Arial', 'I', 6)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_etiquetas_qr(df_items, tipo="Insumos"):
    pdf = PDFEtiquetas()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_etiqueta = 30.0  
    alto_etiqueta = 23.0   
    margen_izq = 10
    margen_sup = 15
    separacion = 2 
    cols_por_fila = 6  
    
    x = margen_izq
    y = margen_sup
    col_count = 0
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f"Catálogo {tipo} (3.0x2.3cm)", 0, 1, 'C')
    pdf.ln(2)
    y = pdf.get_y()
    
    for index, row in df_items.iterrows():
        sku = str(row['codigo'])
        desc = str(row['descripcion'])[:35] 
        
        pdf.set_draw_color(180, 180, 180)
        pdf.rect(x, y, ancho_etiqueta, alto_etiqueta)
        
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        temp_qr_path = f"temp_qr_{index}.png"
        img_qr.save(temp_qr_path)
        
        qr_size = 13  
        pos_qr_x = x + (ancho_etiqueta - qr_size) / 2
        pos_qr_y = y + 1.5
        pdf.image(temp_qr_path, x=pos_qr_x, y=pos_qr_y, w=qr_size, h=qr_size)
        
        pdf.set_xy(x, pos_qr_y + qr_size + 0.5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 7) 
        pdf.cell(ancho_etiqueta, 3, sku, 0, 1, 'C')
        
        pdf.set_xy(x + 1, pos_qr_y + qr_size + 3.5)
        pdf.set_font('Arial', '', 5) 
        pdf.multi_cell(ancho_etiqueta - 2, 2.5, desc, align='C')
        
        if os.path.exists(temp_qr_path): os.remove(temp_qr_path)
            
        col_count += 1
        if col_count < cols_por_fila:
            x += ancho_etiqueta + separacion
        else:
            col_count = 0
            x = margen_izq
            y += alto_etiqueta + separacion
            if y + alto_etiqueta > 285:
                pdf.add_page()
                y = margen_sup

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# MENÚ LATERAL 
# ==========================================
st.sidebar.title("🔧 Configuración")

opciones_config = []
if tiene_permiso("Configuración: Personal"): opciones_config.append("Personal")
if tiene_permiso("Configuración: Insumos"): opciones_config.append("Insumos")
if tiene_permiso("Configuración: Herramientas"): opciones_config.append("Herramientas")
if tiene_permiso("Configuración: Clientes"): opciones_config.append("Clientes")
if tiene_permiso("Configuración: Proveedores"): opciones_config.append("Proveedores")
if tiene_permiso("Configuración: Generar QR"): opciones_config.append("📂 Catálogos & Etiquetas QR")

if st.session_state.get("es_admin", False): opciones_config.append("💻 Equipos Autorizados")

if not opciones_config:
    st.warning("🔒 No tienes permisos para acceder a ningún módulo de Configuración.")
    st.stop()

opcion = st.sidebar.radio("Selecciona Módulo:", opciones_config)

st.sidebar.divider()
if st.sidebar.button("📖 Leer Manual de Configuración", use_container_width=True):
    modal_manual_completo_config()

c_tit, c_ayu = st.columns([9, 1])
with c_tit:
    if opcion == "Personal": st.title("👥 GESTIÓN DE PERSONAL")
    elif opcion == "Insumos": st.title("📦 CATÁLOGO DE INSUMOS")
    elif opcion == "Herramientas": st.title("🛠️ CATÁLOGO DE HERRAMIENTAS")
    elif opcion == "Clientes": st.title("🏢 DIRECTORIO DE CLIENTES")
    elif opcion == "Proveedores": st.title("🚚 DIRECTORIO DE PROVEEDORES")
    elif opcion == "💻 Equipos Autorizados": st.title("💻 CONTROL DE EQUIPOS AUTORIZADOS")
    else: st.title("📂 CATÁLOGOS Y ETIQUETAS QR")

with c_ayu:
    if opcion == "Personal":
        if st.button("❓ Ayuda", key="ayu_pers"): modal_ayuda_modulo_config("Personal")
    elif opcion == "Insumos":
        if st.button("❓ Ayuda", key="ayu_cat_ins"): modal_ayuda_modulo_config("Insumos")
    elif opcion == "Herramientas":
        if st.button("❓ Ayuda", key="ayu_cat_herr"): modal_ayuda_modulo_config("Herramientas")
    elif opcion == "Clientes":
        if st.button("❓ Ayuda", key="ayu_cli"): modal_ayuda_modulo_config("Clientes")
    elif opcion == "Proveedores":
        if st.button("❓ Ayuda", key="ayu_prov"): modal_ayuda_modulo_config("Proveedores")
    elif opcion == "💻 Equipos Autorizados":
        pass 
    else:
        if st.button("❓ Ayuda", key="ayu_etiq"): modal_ayuda_modulo_config("Etiquetas")

# ==========================================
# 1. PERSONAL 
# ==========================================
if opcion == "Personal":
    lista_permisos = [
        "Configuración: Personal", "Configuración: Insumos", "Configuración: Herramientas", 
        "Configuración: Clientes", "Configuración: Proveedores", "Configuración: Generar QR",
        "Almacén: Movimientos Insumos", "Almacén: Ver Existencias Insumos", "Almacén: Eliminar Historial Insumos",
        "Almacén: Prestar/Devolver Herramientas", "Almacén: Eliminar Historial Herramientas",
        "Almacén: Generar Recibos OC", "Almacén: Editar/Eliminar Recibos OC",
        "Almacén: Registrar Entrada Material", "Almacén: Editar/Eliminar Entrada Material",
        "Almacén: Solicitar Material", "Almacén: Despachar Pedidos",
        "Finanzas: Registrar Movimientos Dinero", "Finanzas: Editar/Eliminar Movimientos Dinero"
    ]

    try:
        response = utils.supabase.table("Personal").select("*").order("id").execute()
        df_personal = pd.DataFrame(response.data)
        if not df_personal.empty and "fecha_ingreso" in df_personal.columns:
            df_personal["fecha_ingreso"] = pd.to_datetime(df_personal["fecha_ingreso"], errors='coerce').dt.date
    except: df_personal = pd.DataFrame()
    
    if df_personal.empty: 
        df_personal = pd.DataFrame(columns=["id", "nombre", "puesto", "activo", "usuario", "pin", "permisos"])

    t1, t2, t3 = st.tabs(["➕ Alta Personal", "📋 Kardex y Accesos", "🪪 Generar Credenciales"])
    
    with t1:
        if "alta_pers_exito" not in st.session_state:
            st.session_state["alta_pers_exito"] = False

        if not st.session_state["alta_pers_exito"]:
            with st.form("alta_personal", clear_on_submit=True):
                st.subheader("1. Datos Generales")
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre Completo")
                puesto = c2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
                
                c3, c4 = st.columns(2)
                nacimiento = c3.text_input("Año Nacimiento")
                domicilio = c4.text_input("Domicilio")
                
                c5, c6 = st.columns(2)
                curp = c5.text_input("CURP")
                rfc = c6.text_input("RFC")
                fecha_ingreso = st.date_input("Fecha de Ingreso", value=datetime.date.today())
                
                st.divider()
                st.subheader("2. Credenciales y Permisos")
                c7, c8 = st.columns(2)
                usuario_login = c7.text_input("Usuario (Para iniciar sesión)")
                pin_login = c8.text_input("Contraseña / PIN", type="password")
                
                permisos_seleccionados = st.multiselect(
                    "Selecciona las operaciones a las que tendrá acceso:",
                    options=lista_permisos,
                    placeholder="Elige los permisos..."
                )

                if st.form_submit_button("Guardar Empleado y Accesos", type="primary"):
                    if nombre and usuario_login and pin_login:
                        permisos_str = ", ".join(permisos_seleccionados)
                        
                        datos = {
                            "nombre": nombre, "puesto": puesto, "anio_nacimiento": nacimiento, 
                            "domicilio": domicilio, "curp": curp, "rfc": rfc, 
                            "fecha_ingreso": fecha_ingreso.isoformat(), "activo": True,
                            "usuario": usuario_login, "pin": pin_login, 
                            "permisos": permisos_str
                        }
                        utils.supabase.table("Personal").insert(datos).execute()
                        st.session_state["alta_pers_exito"] = True
                        st.rerun()
                    else:
                        st.error("⚠️ El Nombre, Usuario y Contraseña son obligatorios.")
        else:
            st.success("✅ Empleado registrado correctamente con sus permisos asignados.")
            if st.button("➕ Agregar otro Empleado", type="primary"):
                st.session_state["alta_pers_exito"] = False
                st.rerun()

    with t2:
        @st.dialog("Edición de Personal y Accesos", width="large")
        def editar_empleado(emp_id, df_source):
            emp_data = df_source[df_source['id'] == emp_id].iloc[0]
            
            st.markdown(f"### ✏️ Editando a: {emp_data.get('nombre', '')}")
            
            permisos_actuales_str = emp_data.get('permisos', '')
            permisos_actuales_lista = [p.strip() for p in permisos_actuales_str.split(",")] if pd.notna(permisos_actuales_str) and permisos_actuales_str else []
            permisos_validos = [p for p in permisos_actuales_lista if p in lista_permisos]

            try: fecha_dt = pd.to_datetime(emp_data['fecha_ingreso']).date()
            except: fecha_dt = datetime.date.today()

            st.write("**Datos Generales**")
            col_e1, col_e2 = st.columns(2)
            n_nombre = col_e1.text_input("Nombre", value=emp_data.get('nombre', ''), key=f"nom_{emp_id}")
            
            lista_puestos = ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"]
            puesto_actual = emp_data.get('puesto', 'Operador')
            idx_puesto = lista_puestos.index(puesto_actual) if puesto_actual in lista_puestos else 0
            n_puesto = col_e2.selectbox("Puesto", lista_puestos, index=idx_puesto, key=f"pue_{emp_id}")
            
            col_e3, col_e4 = st.columns(2)
            n_nacimiento = col_e3.text_input("Año Nacimiento", value=emp_data.get('anio_nacimiento', ''), key=f"nac_{emp_id}")
            n_domicilio = col_e4.text_input("Domicilio", value=emp_data.get('domicilio', ''), key=f"dom_{emp_id}")
            
            n_fecha = st.date_input("Fecha Ingreso", value=fecha_dt, key=f"fec_{emp_id}")
            
            st.divider()
            st.write("**Control de Accesos**")
            col_e5, col_e6 = st.columns(2)
            n_user = col_e5.text_input("Usuario", value=emp_data.get('usuario', ''), key=f"usr_{emp_id}")
            n_pin = col_e6.text_input("Contraseña", value=emp_data.get('pin', ''), key=f"pin_{emp_id}")
            
            n_permisos = st.multiselect(
                "Operaciones permitidas:",
                options=lista_permisos,
                default=permisos_validos,
                key=f"perm_{emp_id}"
            )
            
            n_activo = st.checkbox("Empleado Activo (Puede iniciar sesión)", value=bool(emp_data.get('activo', True)), key=f"act_{emp_id}")
            
            st.divider()
            col_g, col_b = st.columns(2)
            
            if col_g.button("💾 Guardar Cambios", type="primary", use_container_width=True, key=f"btn_g_{emp_id}"):
                if n_nombre and n_user and n_pin:
                    permisos_str_update = ", ".join(n_permisos)
                    datos_update = {
                        "nombre": n_nombre, "puesto": n_puesto, "anio_nacimiento": n_nacimiento,
                        "domicilio": n_domicilio, "fecha_ingreso": n_fecha.isoformat(),
                        "usuario": n_user, "pin": n_pin, "permisos": permisos_str_update,
                        "activo": n_activo
                    }
                    utils.supabase.table("Personal").update(datos_update).eq("id", emp_id).execute()
                    st.success("✅ Información actualizada correctamente.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Nombre, Usuario y Contraseña no pueden estar vacíos.")
            
            if col_b.button("🗑️ ELIMINAR DEL SISTEMA", type="secondary", use_container_width=True, key=f"btn_d_{emp_id}"):
                utils.supabase.table("Personal").delete().eq("id", emp_id).execute()
                st.warning("⚠️ Empleado eliminado de la base de datos.")
                time.sleep(1)
                st.rerun()

        if not df_personal.empty:
            c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([1, 3, 2, 2, 2])
            c_h1.markdown("**ID**")
            c_h2.markdown("**Nombre**")
            c_h3.markdown("**Puesto**")
            c_h4.markdown("**Usuario Login**")
            c_h5.markdown("**Acciones**")
            
            for idx, row in df_personal.iterrows():
                estado_texto = "🔴" if not row.get('activo', True) else "🟢"
                c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
                c1.write(str(row.get('id', '')))
                c2.write(f"{estado_texto} {row.get('nombre', '')}")
                c3.write(row.get('puesto', ''))
                c4.write(row.get('usuario', 'S/N'))
                
                if c5.button("Ver / Editar", key=f"btn_pers_{row['id']}"):
                    editar_empleado(row['id'], df_personal)
        else:
            st.info("No hay personal registrado en el sistema aún.")

    with t3:
        st.subheader("Impresión de Credenciales de Acceso")
        st.info("Genera tarjetas en tamaño INE con los datos de acceso para tu equipo.")
        
        # --- ZONA DE DISEÑO DE COLORES CON DEMO ---
        colores_activos = cargar_colores()
        with st.expander("🎨 Personalizar Colores de la Credencial", expanded=True):
            st.write("Selecciona los colores institucionales. Modifica y mira el resultado en tiempo real.")
            
            col_c1, col_c2 = st.columns(2)
            nuevo_c1 = col_c1.color_picker("Color Principal (Fondo de Cabecera)", colores_activos["color_1"])
            nuevo_c2 = col_c2.color_picker("Color Secundario (Líneas y Textos)", colores_activos["color_2"])
            
            st.markdown("### 👀 Vista Previa (Demo):")
            demo_img = generar_credencial_pro(
                "JUAN PÉREZ GARCÍA", "SUPERVISOR", "jperez", "12345", nuevo_c1, nuevo_c2
            )
            st.image(demo_img, use_container_width=True)
            
            if st.button("💾 Guardar Diseño para Todos", type="primary", use_container_width=True):
                guardar_colores(nuevo_c1, nuevo_c2)
                st.success("¡Diseño guardado exitosamente!")
                time.sleep(1)
                st.rerun()
        
        st.divider()

        if not df_personal.empty:
            activos = df_personal[df_personal['activo'] == True]
            if not activos.empty:
                for idx, row in activos.iterrows():
                    with st.expander(f"🪪 {row.get('nombre', 'Sin nombre')} - {row.get('puesto', '')}"):
                        c_img, c_btn = st.columns([2, 1])
                        img_bytes = generar_credencial_pro(
                            row.get('nombre', ''),
                            row.get('puesto', ''),
                            row.get('usuario', ''),
                            row.get('pin', ''),
                            colores_activos["color_1"],
                            colores_activos["color_2"]
                        )
                        c_img.image(img_bytes, use_container_width=True)
                        c_btn.download_button(
                            label="📥 Descargar PNG (Tamaño INE)",
                            data=img_bytes,
                            file_name=f"Credencial_{row.get('usuario', 'user')}.png",
                            mime="image/png",
                            use_container_width=True
                        )
            else:
                st.warning("No hay usuarios activos para generar credenciales en este momento.")
        else:
            st.info("No hay personal registrado en el sistema aún.")

# ==========================================
# 2. INSUMOS (TABLA EXACTA Y LIMPIA)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: 
        df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Manual", "📋 Inventario Maestro"])
    
    with t1:
        if "alta_insumo_exito" not in st.session_state:
            st.session_state["alta_insumo_exito"] = False

        if not st.session_state["alta_insumo_exito"]:
            with st.form("alta_insumo", clear_on_submit=True):
                c1, c2 = st.columns([1, 3])
                cod = c1.text_input("Código / SKU")
                nom = c2.text_input("Descripción")
                
                c3, c4, c5 = st.columns(3)
                uni = c3.selectbox("Unidad", lista_unidades)
                cant = c4.number_input("Cantidad Inicial (Opcional)", min_value=0.0)
                mini = c5.number_input("Stock Min", value=5.0)
                
                ubi = st.text_input("Ubicación")
                
                if st.form_submit_button("Guardar Insumo", type="primary"):
                    if cod and nom:
                        datos = {
                            "codigo": str(cod), 
                            "descripcion": str(nom), 
                            "insumo": str(nom), 
                            "unidad": str(uni), 
                            "cantidad": float(cant), 
                            "stock_minimo": float(mini),
                            "ubicacion": str(ubi)
                        }
                        try:
                            utils.supabase.table("Insumos").insert(datos).execute()
                            st.session_state["alta_insumo_exito"] = True
                            st.rerun()
                        except Exception as e: st.error(f"Error al guardar: {e}")
                    else: st.warning("Código y Descripción obligatorios.")
        else:
            st.success("✅ Insumo guardado correctamente en la base de datos.")
            if st.button("➕ Agregar otro Insumo", type="primary"):
                st.session_state["alta_insumo_exito"] = False
                st.rerun()

    with t2:
        cols_bd = ["id", "codigo", "descripcion", "unidad", "cantidad", "stock_minimo", "ubicacion"]
        
        if df.empty:
            df_view = pd.DataFrame(columns=cols_bd)
        else:
            for col in cols_bd:
                if col not in df.columns:
                    df[col] = 0.0 if col in ["cantidad", "stock_minimo"] else ""
            df_view = df[cols_bd].copy()
            
        df_view["🗑️ Eliminar"] = False  
        
        edited = st.data_editor(
            df_view, 
            num_rows="dynamic", 
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None, 
                "codigo": "Código",
                "descripcion": "Descripción",
                "unidad": "Unidad",
                "cantidad": "Cantidad",
                "stock_minimo": "Stock Mínimo",
                "ubicacion": "Ubicación",
                "🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)
            }
        )
        
        if st.button("💾 Guardar Cambios", type="primary"):
            try:
                to_upsert = []
                to_delete = []
                
                for i, r in edited.iterrows():
                    if r.get("🗑️ Eliminar", False):
                        if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                            to_delete.append(int(r["id"]))
                    else:
                        d = {
                            "codigo": str(r.get("codigo", "")),
                            "descripcion": str(r.get("descripcion", "")),
                            "insumo": str(r.get("descripcion", "")),
                            "cantidad": float(r.get("cantidad", 0) if pd.notna(r.get("cantidad")) else 0),
                            "unidad": str(r.get("unidad", "")),
                            "stock_minimo": float(r.get("stock_minimo", 0) if pd.notna(r.get("stock_minimo")) else 0),
                            "ubicacion": str(r.get("ubicacion", ""))
                        }
                        
                        if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                            d["id"] = int(r["id"])
                        elif d["codigo"].strip() == "" or d["descripcion"].strip() == "":
                            continue  
                            
                        to_upsert.append(d)
                
                if to_delete:
                    utils.supabase.table("Insumos").delete().in_("id", to_delete).execute()
                if to_upsert:
                    utils.supabase.table("Insumos").upsert(to_upsert).execute()
                    
                st.toast("✅ Inventario actualizado al momento", icon="✅")
                time.sleep(0.5) 
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar los cambios: {e}")

# ==========================================
# 3. HERRAMIENTAS 
# ==========================================
elif opcion == "Herramientas":
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        
        res_pers = utils.supabase.table("Personal").select("nombre").eq("activo", True).execute()
        lista_personal = ["Bodega"] + [p["nombre"] for p in res_pers.data] if res_pers.data else ["Bodega"]
    except: 
        df = pd.DataFrame()
        lista_personal = ["Bodega"]
    
    t1, t2 = st.tabs(["➕ Alta de Herramienta", "📋 Inventario de Activos"])
    
    with t1:
        if "alta_herr_exito" not in st.session_state:
            st.session_state["alta_herr_exito"] = False

        if not st.session_state["alta_herr_exito"]:
            with st.form("alta_herramienta_form", clear_on_submit=True):
                st.write("**Datos de Identificación**")
                c1, c2 = st.columns(2)
                sku_id_h = c1.text_input("Código SKU / ID de la Herramienta")
                nombre_h = c2.text_input("Nombre Herramienta")
                
                st.write("**Estado y Localización**")
                c4, c5, c6 = st.columns(3)
                estado_h = c4.selectbox("Estado", ["NUEVO", "BUEN ESTADO", "REGULAR", "BAJA"])
                responsable_h = c5.selectbox("Responsable Inicial", lista_personal, index=0)
                ubicacion_h = c6.text_input("Ubicación (Ej. Estante A1)")
                
                if st.form_submit_button("Guardar Herramienta", type="primary"):
                    if sku_id_h and nombre_h:
                        datos_herramienta = {
                            "codigo": str(sku_id_h), 
                            "ID_Herramienta": str(sku_id_h),
                            "Herramienta": str(nombre_h), 
                            "Estado": str(estado_h), 
                            "Responsable": str(responsable_h),
                            "ubicacion": str(ubicacion_h)
                        }
                        utils.supabase.table("Herramientas").insert(datos_herramienta).execute()
                        st.session_state["alta_herr_exito"] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ El Código/ID y Nombre son obligatorios.")
        else:
            st.success("✅ Herramienta registrada con éxito en el catálogo.")
            if st.button("➕ Agregar otra Herramienta", type="primary"):
                st.session_state["alta_herr_exito"] = False
                st.rerun()

    with t2:
        if not df.empty:
            cols_base = ["id", "codigo", "Herramienta", "Estado", "Responsable", "ubicacion"]
            for col in cols_base:
                if col not in df.columns: df[col] = ""
            
            df_view = df[cols_base].copy()
            df_view.rename(columns={"codigo": "Código / ID", "ubicacion": "Ubicación"}, inplace=True)
            df_view["🗑️ Eliminar"] = False 
            
            edited_h = st.data_editor(
                df_view, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)
                }
            )
            
            if st.button("💾 Actualizar Catálogo", type="primary"):
                try:
                    to_upsert = []
                    to_delete = []
                    
                    for i, r in edited_h.iterrows():
                        if r.get("🗑️ Eliminar", False):
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                to_delete.append(int(r["id"]))
                        else:
                            d = {
                                "codigo": str(r.get("Código / ID", "")),
                                "ID_Herramienta": str(r.get("Código / ID", "")), 
                                "Herramienta": str(r.get("Herramienta", "")),
                                "Estado": str(r.get("Estado", "")),
                                "Responsable": str(r.get("Responsable", "")),
                                "ubicacion": str(r.get("Ubicación", ""))
                            }
                            
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                d["id"] = int(r["id"])
                            elif d["codigo"].strip() == "" or d["Herramienta"].strip() == "":
                                continue

                            to_upsert.append(d)
                    
                    if to_delete:
                        utils.supabase.table("Herramientas").delete().in_("id", to_delete).execute()
                    if to_upsert:
                        utils.supabase.table("Herramientas").upsert(to_upsert).execute()
                        
                    st.toast("✅ Catálogo sincronizado al momento.", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al actualizar: {e}")

# ==========================================
# 4. CLIENTES
# ==========================================
elif opcion == "Clientes":
    try: 
        df = pd.DataFrame(utils.supabase.table("Clientes").select("*").order("id").execute().data)
    except: 
        df = pd.DataFrame()

    t1, t2 = st.tabs(["➕ Alta Cliente", "📋 Lista de Clientes"])
    with t1:
        if "alta_cli_exito" not in st.session_state:
            st.session_state["alta_cli_exito"] = False

        if not st.session_state["alta_cli_exito"]:
            with st.form("alta_cliente_new", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre_cli = c1.text_input("Nombre / Empresa")
                rfc_cli = c2.text_input("RFC")
                
                c3, c4 = st.columns(2)
                telefono_cli = c3.text_input("Teléfono")
                email_cli = c4.text_input("E-mail")
                
                direccion_cli = st.text_input("Dirección (Calle y Número)")
                
                c5, c6, c7 = st.columns(3)
                colonia_cli = c5.text_input("Colonia")
                cp_cli = c6.text_input("Código Postal")
                estado_cli = c7.text_input("Estado (Provincia)")
                
                if st.form_submit_button("Guardar Cliente", type="primary"):
                    if nombre_cli:
                        datos_cli = {
                            "nombre": str(nombre_cli), "rfc": str(rfc_cli), "telefono": str(telefono_cli), "email": str(email_cli),
                            "direccion": str(direccion_cli), "colonia": str(colonia_cli), "codigo_postal": str(cp_cli), "estado": str(estado_cli)
                        }
                        utils.supabase.table("Clientes").insert(datos_cli).execute()
                        st.session_state["alta_cli_exito"] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ El nombre del cliente es obligatorio.")
        else:
            st.success("✅ Cliente registrado correctamente en el directorio.")
            if st.button("➕ Agregar otro Cliente", type="primary"):
                st.session_state["alta_cli_exito"] = False
                st.rerun()

    with t2:
        df_cli_view = df.copy()
        if not df_cli_view.empty:
            df_cli_view["🗑️ Eliminar"] = False
            
            edited_c = st.data_editor(
                df_cli_view, 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)
                }
            )
            
            if st.button("💾 Actualizar Clientes", type="primary"):
                try:
                    to_upsert = []
                    to_delete = []
                    
                    for i, r in edited_c.iterrows():
                        if r.get("🗑️ Eliminar", False):
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                to_delete.append(int(r["id"]))
                        else:
                            d = {k: str(v) for k, v in r.items() if k not in ['id', '🗑️ Eliminar', 'created_at'] and pd.notna(v)}
                            
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                d["id"] = int(r["id"])
                            elif d.get("nombre", "").strip() == "":
                                continue
                                
                            to_upsert.append(d)
                    
                    if to_delete:
                        utils.supabase.table("Clientes").delete().in_("id", to_delete).execute()
                    if to_upsert:
                        utils.supabase.table("Clientes").upsert(to_upsert).execute()
                        
                    st.toast("✅ Clientes actualizados al momento.", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")

# ==========================================
# 5. PROVEEDORES
# ==========================================
elif opcion == "Proveedores":
    try: 
        df = pd.DataFrame(utils.supabase.table("Proveedores").select("*").order("id").execute().data)
    except: 
        df = pd.DataFrame()

    t1, t2 = st.tabs(["➕ Alta Proveedor", "📋 Lista de Proveedores"])
    with t1:
        if "alta_prov_exito" not in st.session_state:
            st.session_state["alta_prov_exito"] = False

        if not st.session_state["alta_prov_exito"]:
            with st.form("alta_prov_new", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre_prov = c1.text_input("Nombre / Empresa")
                rfc_prov = c2.text_input("RFC")
                
                c3, c4 = st.columns(2)
                contacto_prov = c3.text_input("Persona de Contacto")
                telefono_prov = c4.text_input("Teléfono")
                
                domicilio_prov = st.text_input("Calle y Número")
                
                c5, c6 = st.columns(2)
                colonia_prov = c5.text_input("Colonia")
                cp_prov = c6.text_input("Código Postal")
                
                if st.form_submit_button("Guardar Proveedor", type="primary"):
                    if nombre_prov:
                        datos_prov = {
                            "nombre": str(nombre_prov), "empresa": str(nombre_prov), "rfc": str(rfc_prov), "contacto": str(contacto_prov),
                            "telefono": str(telefono_prov), "domicilio": str(domicilio_prov), "colonia": str(colonia_prov), "codigo_postal": str(cp_prov)
                        }
                        utils.supabase.table("Proveedores").insert(datos_prov).execute()
                        st.session_state["alta_prov_exito"] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ El nombre de la empresa es obligatorio.")
        else:
            st.success("✅ Proveedor registrado correctamente en el directorio.")
            if st.button("➕ Agregar otro Proveedor", type="primary"):
                st.session_state["alta_prov_exito"] = False
                st.rerun()

    with t2:
        df_prov_view = df.copy()
        if not df_prov_view.empty:
            df_prov_view["🗑️ Eliminar"] = False
            
            edited_p = st.data_editor(
                df_prov_view, 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)
                }
            )
            
            if st.button("💾 Actualizar Proveedores", type="primary"):
                try:
                    to_upsert = []
                    to_delete = []
                    
                    for i, r in edited_p.iterrows():
                        if r.get("🗑️ Eliminar", False):
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                to_delete.append(int(r["id"]))
                        else:
                            d = {k: str(v) for k, v in r.items() if k not in ['id', '🗑️ Eliminar', 'created_at'] and pd.notna(v)}
                            d["empresa"] = d.get("nombre", "")
                            
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                d["id"] = int(r["id"])
                            elif d.get("nombre", "").strip() == "":
                                continue
                                
                            to_upsert.append(d)
                            
                    if to_delete:
                        utils.supabase.table("Proveedores").delete().in_("id", to_delete).execute()
                    if to_upsert:
                        utils.supabase.table("Proveedores").upsert(to_upsert).execute()
                        
                    st.toast("✅ Proveedores actualizados al momento.", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR
# ==========================================
elif opcion == "📂 Catálogos & Etiquetas QR":
    tab_ins, tab_her = st.tabs(["📦 Etiquetas Insumos", "🛠️ Etiquetas Herramientas"])
    
    with tab_ins:
        try:
            res = utils.supabase.table("Insumos").select("*").order("id").execute()
            df_ins = pd.DataFrame(res.data)
            if not df_ins.empty:
                df_ins.columns = df_ins.columns.str.lower()
                df_ins["QR_Img"] = df_ins["codigo"].apply(get_qr_data_url)
                df_ins["Seleccionar"] = False
                edited_ins = st.data_editor(df_ins[["Seleccionar", "QR_Img", "codigo", "descripcion"]], column_config={"QR_Img": st.column_config.ImageColumn("QR")}, use_container_width=True, hide_index=True)
                if st.button("🖨️ Generar PDF Insumos"):
                    sel = edited_ins[edited_ins["Seleccionar"] == True]
                    if not sel.empty: 
                        pdf = generar_pdf_etiquetas_qr(sel, "Insumos")
                        st.download_button("📥 Descargar PDF", pdf, "Etiquetas_Insumos.pdf")
        except: st.error("Error cargando datos")
    
    with tab_her:
        try:
            res = utils.supabase.table("Herramientas").select("*").order("id").execute()
            df_her = pd.DataFrame(res.data)
            if not df_her.empty:
                df_her_clean = df_her[["codigo", "Herramienta"]].copy()
                df_her_clean["QR_Img"] = df_her_clean["codigo"].apply(get_qr_data_url)
                df_her_clean["Seleccionar"] = False
                df_her_tag = df_her_clean.rename(columns={"Herramienta": "descripcion"})
                
                edited_her = st.data_editor(
                    df_her_tag[["Seleccionar", "QR_Img", "codigo", "descripcion"]], 
                    column_config={
                        "QR_Img": st.column_config.ImageColumn("QR"),
                        "codigo": "Código / ID",
                        "descripcion": "Descripción (Herramienta)"
                    }, 
                    use_container_width=True, 
                    hide_index=True,
                    key="editor_herramientas_qr"
                )
                
                if st.button("🖨️ Generar PDF Herramientas"):
                    sel = edited_her[edited_her["Seleccionar"] == True]
                    if not sel.empty: 
                        pdf = generar_pdf_etiquetas_qr(sel, "Herramientas")
                        st.download_button("📥 Descargar PDF", pdf, "Etiquetas_Herramientas.pdf")
        except Exception as e: 
            st.error(f"Error cargando datos: {e}")

# ==========================================
# 7. EQUIPOS AUTORIZADOS
# ==========================================
elif opcion == "💻 Equipos Autorizados":
    st.markdown("Gestión de seguridad: Aquí puedes ver qué dispositivos físicos tienen acceso al ERP. Si un equipo se daña o se extravía, revoca su acceso inmediatamente.")
    
    try:
        res_dev = utils.supabase.table("Dispositivos_Autorizados").select("*").order("id", desc=True).execute()
        df_dev = pd.DataFrame(res_dev.data)
    except Exception as e:
        df_dev = pd.DataFrame()
        st.error(f"Error cargando base de datos: {e}")
        
    if not df_dev.empty:
        if 'created_at' in df_dev.columns:
            df_dev['Fecha de Vinculación'] = pd.to_datetime(df_dev['created_at']).dt.strftime('%d/%m/%Y %H:%M')
        
        df_view = df_dev[["id", "descripcion", "Fecha de Vinculación"]].copy()
        df_view.rename(columns={"descripcion": "Nombre del Equipo / Ubicación"}, inplace=True)
        
        df_view["🚫 Revocar Acceso"] = False
        
        st.warning("⚠️ Al marcar 'Revocar Acceso' y guardar, el equipo será expulsado del sistema al instante. Tendrá que ser vinculado físicamente de nuevo con la Contraseña Maestra.")
        
        edited_dev = st.data_editor(
            df_view,
            hide_index=True,
            use_container_width=True,
            disabled=["id", "Fecha de Vinculación"],
            column_config={
                "🚫 Revocar Acceso": st.column_config.CheckboxColumn("🚫 Revocar Acceso", default=False)
            }
        )
        
        if st.button("💾 Guardar Cambios de Seguridad", type="primary"):
            try:
                to_delete = []
                for i, r in edited_dev.iterrows():
                    if r.get("🚫 Revocar Acceso", False):
                        to_delete.append(int(r["id"]))
                    else:
                        utils.supabase.table("Dispositivos_Autorizados").update({
                            "descripcion": str(r["Nombre del Equipo / Ubicación"])
                        }).eq("id", int(r["id"])).execute()
                        
                if to_delete:
                    utils.supabase.table("Dispositivos_Autorizados").delete().in_("id", to_delete).execute()
                    st.toast("🚨 Accesos revocados con éxito. Los equipos han sido bloqueados.", icon="🚨")
                else:
                    st.toast("✅ Nombres de los equipos actualizados.", icon="✅")
                    
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar la seguridad: {e}")
    else:
        st.info("No hay ningún equipo vinculado al sistema en este momento.")
