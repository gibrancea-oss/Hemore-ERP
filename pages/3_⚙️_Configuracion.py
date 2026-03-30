import streamlit as st
import pandas as pd
import utils 
import time
import datetime
import io
import qrcode
import os
import base64
from fpdf import FPDF

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- 🔒 SEGURIDAD ACTIVADA ---
utils.validar_login()
# -----------------------------

supabase = utils.supabase

# ==========================================
# FUNCIÓN DE PERMISOS
# ==========================================
def tiene_permiso(permiso):
    if st.session_state.get("es_admin", False): return True
    return permiso in st.session_state.get("permisos", [])

# ==========================================
# MANUAL DE AYUDA NATIVO (CONFIGURACIÓN ⚡)
# ==========================================
def renderizar_manual_config(modulo):
    if modulo == "Personal" or modulo == "Todos":
        st.markdown("## 👥 Módulo: Personal y Accesos")
        st.markdown("Exclusivo para administradores. Aquí controlas quién entra al sistema y qué puede hacer.")
        st.markdown("""
        **➕ Alta Personal:**
        1. Llena los datos generales del empleado.
        2. Crea su **Usuario** y **Contraseña / PIN** (con estos datos iniciará sesión).
        3. En la lista desplegable de **Permisos**, selecciona exactamente qué botones y pantallas podrá usar en el Almacén o Finanzas. 
        4. Haz clic en Guardar.
        
        **📋 Kardex y Accesos:**
        Muestra a todo el personal. Dando clic en **Ver / Editar** puedes cambiar contraseñas, agregarle nuevos permisos, o dar de baja (eliminar) a un usuario que ya no labora en la empresa.
        """)
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Insumos" or modulo == "Todos":
        st.markdown("## 📦 Módulo: Catálogo de Insumos")
        st.markdown("Aquí se 'bautizan' los materiales nuevos. **Ojo:** Aquí no se mete stock, solo se crea el nombre oficial para que el almacén lo pueda usar.")
        st.markdown("""
        **➕ Alta Manual:**
        Escribe el Código/SKU, la descripción exacta, la unidad de medida (Pzas, Kg, Mts) y el stock mínimo ideal. Da clic en Guardar.
        
        **📋 Inventario Maestro:**
        Aquí puedes ver la lista completa. Si escribiste mal un nombre o quieres cambiar el stock mínimo, modifica la celda directamente y da clic en **Guardar Cambios**.
        """)
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Herramientas" or modulo == "Todos":
        st.markdown("## 🛠️ Módulo: Catálogo de Herramientas")
        st.markdown("Registro maestro de la maquinaria y equipo de la empresa.")
        st.markdown("""
        **➕ Alta de Herramienta:**
        Asigna un Código (ID), el nombre del equipo, su estado físico y quién la tiene inicialmente (usualmente BODEGA).
        
        **📋 Inventario de Activos:**
        Catálogo completo editable. Aquí puedes corregir nombres o estatus directamente en la tabla y dar clic en **Actualizar Catálogo**.
        """)
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Clientes" or modulo == "Todos":
        st.markdown("## 🏢 Módulo: Clientes")
        st.markdown("Directorio para las salidas de almacén.")
        st.markdown("""
        **➕ Alta Cliente:**
        Llena el Nombre de la empresa o persona, RFC y datos de contacto. El nombre es obligatorio porque es el que aparecerá en los Recibos de Entrega PDF.
        
        **📋 Lista de Clientes:**
        Edita la información de contacto o fiscal directamente en la tabla y guarda los cambios.
        """)
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()
    
    if modulo == "Proveedores" or modulo == "Todos":
        st.markdown("## 🚚 Módulo: Proveedores")
        st.markdown("Directorio para las entradas de almacén.")
        st.markdown("""
        **➕ Alta Proveedor:**
        Registra a las empresas que surten a HEMORE. Este nombre será el que el Almacén seleccione al registrar llegadas de material o compras.
        
        **📋 Lista de Proveedores:**
        Mantén el directorio actualizado modificando las celdas directamente.
        """)
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Etiquetas" or modulo == "Todos":
        st.markdown("## 📂 Módulo: Catálogos y Etiquetas QR")
        st.markdown("Generador automático de etiquetas para el inventario físico.")
        st.markdown("""
        1. Entra a la pestaña de Insumos o Herramientas.
        2. Verás tu catálogo completo y el código QR generado automáticamente por el sistema.
        3. En la columna de la izquierda, marca la casilla (**Seleccionar**) de todas las etiquetas que necesites imprimir.
        4. Haz clic en **Generar PDF**.
        5. Descarga el archivo. Está configurado con las medidas exactas (3.0 x 2.3 cm) para mandarse a una impresora de etiquetas térmicas.
        """)

@st.dialog("📖 Manual de Configuración", width="large")
def modal_manual_completo_config():
    renderizar_manual_config("Todos")

@st.dialog("❓ Ayuda del Módulo", width="large")
def modal_ayuda_modulo_config(modulo):
    renderizar_manual_config(modulo)


# ==========================================
# FUNCIONES AUXILIARES (QR y PDF)
# ==========================================
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

class PDFEtiquetas(FPDF):
    def footer(self):
        self.set_y(-10)
        self.set_font('Arial', 'I', 6)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_etiquetas_qr(df_items, tipo="Insumos"):
    pdf = PDFEtiquetas()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_etiqueta = 30.0  # 3 cm de ancho
    alto_etiqueta = 23.0   # 2.3 cm de alto
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
# MENÚ LATERAL (DINÁMICO POR PERMISOS)
# ==========================================
st.sidebar.title("🔧 Configuración")

opciones_config = []
if tiene_permiso("Configuración: Personal"): opciones_config.append("Personal")
if tiene_permiso("Configuración: Insumos"): opciones_config.append("Insumos")
if tiene_permiso("Configuración: Herramientas"): opciones_config.append("Herramientas")
if tiene_permiso("Configuración: Clientes"): opciones_config.append("Clientes")
if tiene_permiso("Configuración: Proveedores"): opciones_config.append("Proveedores")
if tiene_permiso("Configuración: Generar QR"): opciones_config.append("📂 Catálogos & Etiquetas QR")

if not opciones_config:
    st.warning("🔒 No tienes permisos para acceder a ningún módulo de Configuración.")
    st.stop()

opcion = st.sidebar.radio("Selecciona Módulo:", opciones_config)

# --- BOTÓN DE MANUAL COMPLETO ---
st.sidebar.divider()
if st.sidebar.button("📖 Leer Manual de Configuración", use_container_width=True):
    modal_manual_completo_config()
# --------------------------------

# --- TÍTULOS DINÁMICOS CON BOTÓN DE AYUDA ---
c_tit, c_ayu = st.columns([9, 1])
with c_tit:
    if opcion == "Personal": st.title("👥 GESTIÓN DE PERSONAL")
    elif opcion == "Insumos": st.title("📦 CATÁLOGO DE INSUMOS")
    elif opcion == "Herramientas": st.title("🛠️ CATÁLOGO DE HERRAMIENTAS")
    elif opcion == "Clientes": st.title("🏢 DIRECTORIO DE CLIENTES")
    elif opcion == "Proveedores": st.title("🚚 DIRECTORIO DE PROVEEDORES")
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
    else:
        if st.button("❓ Ayuda", key="ayu_etiq"): modal_ayuda_modulo_config("Etiquetas")
# --------------------------------------------

# ==========================================
# 1. PERSONAL (CON CONTROL DE ACCESOS Y DIALOG)
# ==========================================
if opcion == "Personal":
    lista_permisos = [
        "Configuración: Personal", "Configuración: Insumos", "Configuración: Herramientas", 
        "Configuración: Clientes", "Configuración: Proveedores", "Configuración: Generar QR",
        "Almacén: Movimientos Insumos", "Almacén: Ver Existencias Insumos", "Almacén: Eliminar Historial Insumos",
        "Almacén: Prestar/Devolver Herramientas", "Almacén: Eliminar Historial Herramientas",
        "Almacén: Generar Recibos OC", "Almacén: Editar/Eliminar Recibos OC",
        "Almacén: Registrar Entrada Material", "Almacén: Editar/Eliminar Entrada Material",
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

    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex y Accesos"])
    
    with t1:
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
                    st.success(f"✅ Registrado con permisos asignados.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ El Nombre, Usuario y Contraseña son obligatorios.")

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

# ==========================================
# 2. INSUMOS 
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Manual", "📋 Inventario Maestro"])
    
    with t1:
        with st.form("alta_insumo"):
            c1, c2 = st.columns([1, 3]); cod = c1.text_input("Código / SKU"); nom = c2.text_input("Descripción")
            c3, c4, c5 = st.columns(3); uni = c3.selectbox("Unidad", lista_unidades); cant = c4.number_input("Cantidad Inicial (Opcional)", min_value=0.0); mini = c5.number_input("Stock Min", value=5.0)
            ubi = st.text_input("Ubicación")
            
            if st.form_submit_button("Guardar Insumo"):
                if cod and nom:
                    datos = {"codigo": cod, "Descripcion": nom, "Insumo": nom, "Unidad": uni, "Cantidad": cant, "stock_minimo": mini}
                    if "ubicacion" in df.columns or df.empty: datos["ubicacion"] = ubi
                    try:
                        utils.supabase.table("Insumos").insert(datos).execute()
                        st.success("✅ Guardado correctamente"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Error: {e}.")
                else: st.warning("Código y Descripción obligatorios.")
    with t2:
        if not df.empty:
            cols_base = ["id", "codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo"]
            if "ubicacion" in df.columns: cols_base.append("ubicacion")
            edited = st.data_editor(df[cols_base], num_rows="dynamic", use_container_width=True)
            if st.button("💾 Guardar Cambios"):
                for i, r in edited.iterrows():
                    d = {"codigo": r["codigo"], "Descripcion": r["Descripcion"], "Insumo": r["Descripcion"], "Cantidad": r["Cantidad"], "Unidad": r["Unidad"], "stock_minimo": r["stock_minimo"]}
                    if "ubicacion" in r: d["ubicacion"] = r["ubicacion"]
                    if pd.notna(r["id"]): utils.supabase.table("Insumos").update(d).eq("id", r["id"]).execute()
                    else: utils.supabase.table("Insumos").insert(d).execute()
                st.success("✅ Actualizado"); time.sleep(1); st.rerun()

# ==========================================
# 3. HERRAMIENTAS (Módulo Configuración)
# ==========================================
elif opcion == "Herramientas":
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        
        res_pers = utils.supabase.table("Personal").select("nombre").eq("activo", True).execute()
        lista_personal = ["BODEGA"] + [p["nombre"] for p in res_pers.data] if res_pers.data else ["BODEGA"]
    except: 
        df = pd.DataFrame()
        lista_personal = ["BODEGA"]
    
    t1, t2 = st.tabs(["➕ Alta de Herramienta", "📋 Inventario de Activos"])
    
    with t1:
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
                        "codigo": sku_id_h, 
                        "ID_Herramienta": sku_id_h,
                        "Herramienta": nombre_h, 
                        "Estado": estado_h, 
                        "Responsable": responsable_h,
                        "ubicacion": ubicacion_h
                    }
                    utils.supabase.table("Herramientas").insert(datos_herramienta).execute()
                    st.success("✅ Herramienta registrada con éxito.")
                    time.sleep(1); st.rerun()
                else:
                    st.warning("⚠️ El Código/ID y Nombre son obligatorios.")

    with t2:
        if not df.empty:
            cols_base = ["id", "codigo", "Herramienta", "Estado", "Responsable", "ubicacion"]
            for col in cols_base:
                if col not in df.columns: df[col] = ""
            
            df_view = df[cols_base].copy()
            df_view.rename(columns={"codigo": "Código / ID", "ubicacion": "Ubicación"}, inplace=True)
            
            edited_h = st.data_editor(df_view, num_rows="dynamic", use_container_width=True, hide_index=True)
            
            if st.button("💾 Actualizar Catálogo", type="primary"):
                try:
                    for i, r in edited_h.iterrows():
                        d = {
                            "codigo": r.get("Código / ID"),
                            "ID_Herramienta": r.get("Código / ID"), 
                            "Herramienta": r.get("Herramienta"),
                            "Estado": r.get("Estado"),
                            "Responsable": r.get("Responsable"),
                            "ubicacion": r.get("Ubicación")
                        }
                        d = {k: v for k, v in d.items() if pd.notna(v)}
                        id_row = r.get("id")
                        if pd.notna(id_row) and str(id_row).strip() != "": 
                            utils.supabase.table("Herramientas").update(d).eq("id", id_row).execute()
                        else: 
                            utils.supabase.table("Herramientas").insert(d).execute()
                            
                    st.success("✅ Catálogo sincronizado.")
                    time.sleep(1); st.rerun()
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
                        "nombre": nombre_cli, "rfc": rfc_cli, "telefono": telefono_cli, "email": email_cli,
                        "direccion": direccion_cli, "colonia": colonia_cli, "codigo_postal": cp_cli, "estado": estado_cli
                    }
                    utils.supabase.table("Clientes").insert(datos_cli).execute()
                    st.success("✅ Cliente registrado correctamente.")
                    time.sleep(1); st.rerun()
                else:
                    st.warning("⚠️ El nombre del cliente es obligatorio.")
    with t2:
        edited_c = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Clientes"):
            for i, r in edited_c.iterrows():
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): utils.supabase.table("Clientes").update(d).eq("id", r['id']).execute()
                else: utils.supabase.table("Clientes").insert(d).execute()
            st.rerun()

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
                        "nombre": nombre_prov, "empresa": nombre_prov, "rfc": rfc_prov, "contacto": contacto_prov,
                        "telefono": telefono_prov, "domicilio": domicilio_prov, "colonia": colonia_prov, "codigo_postal": cp_prov
                    }
                    utils.supabase.table("Proveedores").insert(datos_prov).execute()
                    st.success("✅ Proveedor registrado correctamente.")
                    time.sleep(1); st.rerun()
                else:
                    st.warning("⚠️ El nombre de la empresa es obligatorio.")
    with t2:
        edited_p = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Proveedores"):
            for i, r in edited_p.iterrows():
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                d["empresa"] = d.get("nombre", "")
                if pd.notna(r['id']): utils.supabase.table("Proveedores").update(d).eq("id", r['id']).execute()
                else: utils.supabase.table("Proveedores").insert(d).execute()
            st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR
# ==========================================
elif "Etiquetas" in opcion:
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
