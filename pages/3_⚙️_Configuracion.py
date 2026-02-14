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
    
    ancho_etiqueta = 25.0  # mm
    alto_etiqueta = 35.0   # mm
    margen_izq = 10
    margen_sup = 15
    separacion = 2 
    cols_por_fila = 7 
    
    x = margen_izq
    y = margen_sup
    col_count = 0
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f"Catálogo {tipo} (2.5x3.5cm)", 0, 1, 'C')
    pdf.ln(2)
    y = pdf.get_y()
    
    for index, row in df_items.iterrows():
        sku = str(row['codigo'])
        desc = str(row['descripcion'])[:40] 
        
        pdf.set_draw_color(180, 180, 180)
        pdf.rect(x, y, ancho_etiqueta, alto_etiqueta)
        
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        temp_qr_path = f"temp_qr_{index}.png"
        img_qr.save(temp_qr_path)
        
        qr_size = 16 
        pos_qr_x = x + (ancho_etiqueta - qr_size) / 2
        pos_qr_y = y + 2
        pdf.image(temp_qr_path, x=pos_qr_x, y=pos_qr_y, w=qr_size, h=qr_size)
        
        pdf.set_xy(x, pos_qr_y + qr_size + 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 7) 
        pdf.cell(ancho_etiqueta, 3, sku, 0, 1, 'C')
        
        pdf.set_xy(x + 1, pos_qr_y + qr_size + 4)
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
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores", "📂 Catálogos & Etiquetas QR"]
)

# ==========================================
# 1. PERSONAL (MANTENIDO)
# ==========================================
if opcion == "Personal":
    st.markdown("### 👥 Gestión de Recursos Humanos")
    try:
        response = utils.supabase.table("Personal").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty and "fecha_ingreso" in df.columns:
            df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors='coerce').dt.date
    except: df = pd.DataFrame()
    if df.empty: df = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])
    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex"])
    with t1:
        with st.form("alta_personal", clear_on_submit=True):
            c1, c2 = st.columns(2); nombre = c1.text_input("Nombre Completo"); puesto = c2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            c3, c4 = st.columns(2); nacimiento = c3.text_input("Año Nacimiento"); domicilio = c4.text_input("Domicilio")
            c5, c6 = st.columns(2); curp = c5.text_input("CURP"); rfc = c6.text_input("RFC")
            fecha_ingreso = st.date_input("Fecha de Ingreso", value=datetime.date.today())
            if st.form_submit_button("Guardar Empleado"):
                if nombre:
                    datos = {"nombre": nombre, "puesto": puesto, "anio_nacimiento": nacimiento, "domicilio": domicilio, "curp": curp, "rfc": rfc, "fecha_ingreso": fecha_ingreso.isoformat(), "activo": True}
                    utils.supabase.table("Personal").insert(datos).execute()
                    st.success(f"✅ Registrado."); time.sleep(1); st.rerun()
                else: st.warning("Nombre obligatorio")
    with t2:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Personal"):
            for i, r in edited_df.iterrows():
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): utils.supabase.table("Personal").update(d).eq("id", r['id']).execute()
                else: utils.supabase.table("Personal").insert(d).execute()
            st.success("✅ Actualizado"); time.sleep(1); st.rerun()

# ==========================================
# 2. INSUMOS (MANTENIDO)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty and "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
    except: df = pd.DataFrame()
    t1, t2, t3 = st.tabs(["➕ Alta Manual", "📋 PEGAR DESDE EXCEL", "📋 Inventario Maestro"])
    with t1:
        with st.form("alta_insumo"):
            c1, c2 = st.columns([1, 3]); cod = c1.text_input("Código / SKU"); nom = c2.text_input("Descripción")
            c3, c4, c5 = st.columns(3); uni = c3.selectbox("Unidad", lista_unidades); cant = c4.number_input("Cantidad", min_value=0.0); mini = c5.number_input("Min", value=5.0)
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Insumos").insert({"codigo": cod, "Descripcion": nom, "Unidad": uni, "Cantidad": cant, "stock_minimo": mini}).execute()
                st.success("Ok"); time.sleep(1); st.rerun()
    with t2:
        df_template = pd.DataFrame(columns=["codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo"])
        grid = st.data_editor(df_template, num_rows="dynamic", use_container_width=True)
        if st.button("🚀 Guardar Pegado"):
            for i, r in grid.iterrows():
                if r['codigo']: utils.supabase.table("Insumos").insert({"codigo": r['codigo'], "Descripcion": r['Descripcion'], "Unidad": r['Unidad'], "Cantidad": r['Cantidad'], "stock_minimo": r['stock_minimo']}).execute()
            st.success("Ok"); time.sleep(1); st.rerun()
    with t3:
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Guardar"):
            for i, r in edited.iterrows():
                d = {"codigo": r["codigo"], "Descripcion": r["Descripcion"], "Cantidad": r["Cantidad"], "Unidad": r["Unidad"], "stock_minimo": r["stock_minimo"]}
                if pd.notna(r["id"]): utils.supabase.table("Insumos").update(d).eq("id", r["id"]).execute()
                else: utils.supabase.table("Insumos").insert(d).execute()
            st.success("Ok"); time.sleep(1); st.rerun()

# ==========================================
# 3. HERRAMIENTAS (MANTENIDO)
# ==========================================
elif opcion == "Herramientas":
    try: res = utils.supabase.table("Herramientas").select("*").order("id").execute(); df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()
    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("a_h"):
            c1, c2 = st.columns([1, 3]); sku = c1.text_input("SKU"); nom = c2.text_input("Nombre")
            est = st.selectbox("Estado", ["BUEN ESTADO", "MAL ESTADO", "BAJA"])
            if st.form_submit_button("Ok"):
                utils.supabase.table("Herramientas").insert({"codigo": sku, "Herramienta": nom, "Estado": est}).execute(); st.rerun()
    with t2:
        ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Guardar"):
            for i, r in ed.iterrows():
                d = {"codigo": r["codigo"], "Herramienta": r["Herramienta"], "Estado": r["Estado"]}
                if pd.notna(r["id"]): utils.supabase.table("Herramientas").update(d).eq("id", r["id"]).execute()
                else: utils.supabase.table("Herramientas").insert(d).execute()
            st.rerun()

# ==========================================
# 4. CLIENTES (ACTUALIZADO: nombre, rfc, dirección, colonia, codigo postal)
# ==========================================
elif opcion == "Clientes":
    st.markdown("### 🏢 Gestión de Clientes")
    try: df = pd.DataFrame(utils.supabase.table("Clientes").select("*").order("id").execute().data)
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Cliente", "📋 Lista de Clientes"])
    with t1:
        with st.form("alta_cliente_new", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre_cli = c1.text_input("Nombre / Empresa")
            rfc_cli = c2.text_input("RFC")
            direccion_cli = st.text_input("Dirección (Calle y Número)")
            c3, c4 = st.columns(2)
            colonia_cli = c3.text_input("Colonia")
            cp_cli = c4.text_input("Código Postal")
            
            if st.form_submit_button("Guardar Cliente"):
                if nombre_cli:
                    datos = {"nombre": nombre_cli, "rfc": rfc_cli, "direccion": direccion_cli, "colonia": colonia_cli, "codigo_postal": cp_cli}
                    utils.supabase.table("Clientes").insert(datos).execute()
                    st.success(f"✅ {nombre_cli} registrado."); time.sleep(1); st.rerun()
                else: st.warning("El nombre es obligatorio.")
    with t2:
        columnas = ["id", "nombre", "rfc", "direccion", "colonia", "codigo_postal"]
        for c in columnas:
            if c not in df.columns: df[c] = None
        edited_df = st.data_editor(df[columnas], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Clientes"):
            for i, r in edited_df.iterrows():
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): utils.supabase.table("Clientes").update(d).eq("id", r['id']).execute()
                else: utils.supabase.table("Clientes").insert(d).execute()
            st.success("Ok"); time.sleep(1); st.rerun()

# ==========================================
# 5. PROVEEDORES (ACTUALIZADO: nombre, rfc y domicilio)
# ==========================================
elif opcion == "Proveedores":
    st.markdown("### 🚚 Gestión de Proveedores")
    try: 
        df = pd.DataFrame(utils.supabase.table("Proveedores").select("*").order("id").execute().data)
        if "empresa" in df.columns and "nombre" not in df.columns: df["nombre"] = df["empresa"]
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Proveedor", "📋 Lista de Proveedores"])
    with t1:
        with st.form("alta_prov_new", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre_prov = c1.text_input("Nombre / Empresa")
            rfc_prov = c2.text_input("RFC")
            domicilio_prov = st.text_input("Domicilio Completo")
            
            if st.form_submit_button("Guardar Proveedor"):
                if nombre_prov:
                    datos = {"nombre": nombre_prov, "empresa": nombre_prov, "rfc": rfc_prov, "domicilio": domicilio_prov}
                    utils.supabase.table("Proveedores").insert(datos).execute()
                    st.success(f"✅ {nombre_prov} registrado."); time.sleep(1); st.rerun()
                else: st.warning("El nombre es obligatorio.")
    with t2:
        columnas = ["id", "nombre", "rfc", "domicilio"]
        for c in columnas:
            if c not in df.columns: df[c] = None
        edited_df = st.data_editor(df[columnas], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Proveedores"):
            for i, row in edited_df.iterrows():
                d = {k: v for k, v in row.items() if k != 'id' and pd.notna(v)}
                d["empresa"] = d.get("nombre", "")
                if pd.notna(row['id']): utils.supabase.table("Proveedores").update(d).eq("id", row['id']).execute()
                else: utils.supabase.table("Proveedores").insert(d).execute()
            st.success("Ok"); time.sleep(1); st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR (MANTENIDO)
# ==========================================
elif "Etiquetas" in opcion:
    st.markdown("### 📂 Catálogos y Etiquetas QR")
    tab_ins, tab_her = st.tabs(["📦 Etiquetas Insumos", "🛠️ Etiquetas Herramientas"])
    with tab_ins:
        try:
            res = utils.supabase.table("Insumos").select("*").order("id").execute(); df_ins = pd.DataFrame(res.data)
            if not df_ins.empty:
                df_ins.columns = df_ins.columns.str.lower()
                df_ins["QR_Img"] = df_ins["codigo"].apply(get_qr_data_url); df_ins["Seleccionar"] = False
                edited_ins = st.data_editor(df_ins[["Seleccionar", "QR_Img", "codigo", "descripcion"]], column_config={"QR_Img": st.column_config.ImageColumn("QR")}, use_container_width=True, hide_index=True)
                if st.button("🖨️ Generar PDF Insumos"):
                    sel = edited_ins[edited_ins["Seleccionar"] == True]
                    if not sel.empty: pdf = generar_pdf_etiquetas_qr(sel, "Insumos"); st.download_button("📥 PDF", pdf, "Etiquetas.pdf")
        except: st.error("Error")
    with tab_her:
        try:
            res = utils.supabase.table("Herramientas").select("*").order("id").execute(); df_her = pd.DataFrame(res.data)
            if not df_her.empty:
                df_her["QR_Img"] = df_her["codigo"].apply(get_qr_data_url); df_her["Seleccionar"] = False
                df_her = df_her.rename(columns={"Herramienta": "descripcion"})
                edited_her = st.data_editor(df_her[["Seleccionar", "QR_Img", "codigo", "descripcion"]], column_config={"QR_Img": st.column_config.ImageColumn("QR")}, use_container_width=True, hide_index=True)
                if st.button("🖨️ Generar PDF Herramientas"):
                    sel = edited_her[edited_her["Seleccionar"] == True]
                    if not sel.empty: pdf = generar_pdf_etiquetas_qr(sel, "Herramientas"); st.download_button("📥 PDF", pdf, "Etiquetas.pdf")
        except: st.error("Error")
