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
    
    ancho_etiqueta, alto_etiqueta = 25.0, 35.0   
    margen_izq, margen_sup, separacion = 10, 15, 2 
    cols_por_fila = 7 
    
    x, y, col_count = margen_izq, margen_sup, 0
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f"Catálogo {tipo} (2.5x3.5cm)", 0, 1, 'C')
    pdf.ln(2)
    y = pdf.get_y()
    
    for index, row in df_items.iterrows():
        sku, desc = str(row['codigo']), str(row['descripcion'])[:40] 
        pdf.set_draw_color(180, 180, 180)
        pdf.rect(x, y, ancho_etiqueta, alto_etiqueta)
        
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku); qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        temp_qr_path = f"temp_qr_{index}.png"; img_qr.save(temp_qr_path)
        
        qr_size = 16 
        pdf.image(temp_qr_path, x=x+(ancho_etiqueta-qr_size)/2, y=y+2, w=qr_size, h=qr_size)
        pdf.set_xy(x, y+qr_size+3); pdf.set_font('Arial', 'B', 7) 
        pdf.cell(ancho_etiqueta, 3, sku, 0, 1, 'C')
        pdf.set_xy(x+1, y+qr_size+6); pdf.set_font('Arial', '', 5) 
        pdf.multi_cell(ancho_etiqueta-2, 2.5, desc, align='C')
        
        if os.path.exists(temp_qr_path): os.remove(temp_qr_path)
            
        col_count += 1
        if col_count < cols_por_fila: x += ancho_etiqueta + separacion
        else:
            col_count, x = 0, margen_izq
            y += alto_etiqueta + separacion
            if y + alto_etiqueta > 285: pdf.add_page(); y = margen_sup

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio("Módulo:", ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores", "📂 Catálogos & Etiquetas QR"])

# ==========================================
# 1. PERSONAL
# ==========================================
if opcion == "Personal":
    st.markdown("### 👥 Gestión de Personal")
    try:
        df = pd.DataFrame(supabase.table("Personal").select("*").order("id").execute().data)
        if not df.empty and "fecha_ingreso" in df.columns:
            df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors='coerce').dt.date
    except: df = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])
    
    t1, t2 = st.tabs(["➕ Alta", "📋 Kardex"])
    with t1:
        with st.form("a_p", clear_on_submit=True):
            c1, c2 = st.columns(2); nombre = c1.text_input("Nombre"); puesto = c2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            if st.form_submit_button("Guardar"):
                supabase.table("Personal").insert({"nombre": nombre, "puesto": puesto, "activo": True}).execute()
                st.success(f"✅ Procedimiento realizado: {nombre} registrado."); st.toast("Personal guardado"); time.sleep(1); st.rerun()
    with t2:
        ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Personal"):
            for i, r in ed.iterrows():
                try:
                    d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                    if pd.notna(r['id']): supabase.table("Personal").update(d).eq("id", r['id']).execute()
                    else: supabase.table("Personal").insert(d).execute()
                except: continue
            st.success("✅ Procedimiento realizado: Base actualizada."); st.toast("Cambios guardados"); time.sleep(1); st.rerun()

# ==========================================
# 2. INSUMOS (SOLUCIÓN API ERROR)
# ==========================================
elif opcion == "Insumos":
    st.markdown("### 📦 Insumos")
    try: df = pd.DataFrame(supabase.table("Insumos").select("*").order("id").execute().data)
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Manual", "📋 Inventario"])
    with t1:
        with st.form("a_i", clear_on_submit=True):
            c1, c2 = st.columns([1, 3]); cod = c1.text_input("SKU"); nom = c2.text_input("Descripción")
            c3, c4 = st.columns(2); cant = c4.number_input("Cantidad", min_value=0.0); ubi = st.text_input("Ubicación")
            if st.form_submit_button("Guardar"):
                try:
                    d = {"codigo": cod, "Descripcion": nom, "Insumo": nom, "Cantidad": cant, "ubicacion": ubi}
                    supabase.table("Insumos").insert(d).execute()
                    st.success(f"✅ Procedimiento realizado: Insumo {cod} guardado."); st.toast("Insumo registrado"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error en procedimiento: {e}")
    with t2:
        if not df.empty:
            cols = ["id", "codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo", "ubicacion"]
            for c in cols: 
                if c not in df.columns: df[c] = None
            ed = st.data_editor(df[cols], num_rows="dynamic", use_container_width=True)
            if st.button("💾 Guardar Cambios Maestro"):
                success_count = 0
                for i, r in ed.iterrows():
                    try:
                        d = {"codigo": r["codigo"], "Descripcion": r["Descripcion"], "Insumo": r["Descripcion"], "Cantidad": r["Cantidad"], "Unidad": r["Unidad"], "stock_minimo": r["stock_minimo"], "ubicacion": r["ubicacion"]}
                        if pd.notna(r["id"]): supabase.table("Insumos").update(d).eq("id", r["id"]).execute()
                        else: supabase.table("Insumos").insert(d).execute()
                        success_count += 1
                    except: continue
                st.success(f"✅ Procedimiento realizado: {success_count} registros procesados."); st.toast("Inventario actualizado"); time.sleep(1); st.rerun()

# ==========================================
# 3. HERRAMIENTAS
# ==========================================
elif opcion == "Herramientas":
    st.markdown("### 🛠️ Herramientas")
    try: df = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
    except: df = pd.DataFrame()
    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("a_h", clear_on_submit=True):
            sku = st.text_input("SKU"); nom = st.text_input("Nombre")
            if st.form_submit_button("Guardar"):
                supabase.table("Herramientas").insert({"codigo": sku, "Herramienta": nom, "Responsable": "BODEGA"}).execute()
                st.success("✅ Procedimiento realizado: Herramienta registrada."); st.toast("Guardado"); time.sleep(1); st.rerun()
    with t2:
        ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Herramientas"):
            for i, r in ed.iterrows():
                try:
                    d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                    if pd.notna(r['id']): supabase.table("Herramientas").update(d).eq("id", r['id']).execute()
                    else: supabase.table("Herramientas").insert(d).execute()
                except: continue
            st.success("✅ Procedimiento realizado: Activos actualizados."); st.rerun()

# ==========================================
# 4. CLIENTES / 5. PROVEEDORES
# ==========================================
elif opcion == "Clientes":
    st.markdown("### 🏢 Clientes")
    try: df = pd.DataFrame(supabase.table("Clientes").select("*").execute().data)
    except: df = pd.DataFrame()
    ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Clientes"):
        for i, r in ed.iterrows():
            try:
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): supabase.table("Clientes").update(d).eq("id", r['id']).execute()
                else: supabase.table("Clientes").insert(d).execute()
            except: continue
        st.success("✅ Procedimiento realizado: Clientes actualizados."); st.rerun()

elif opcion == "Proveedores":
    st.markdown("### 🚚 Proveedores")
    try: df = pd.DataFrame(supabase.table("Proveedores").select("*").execute().data)
    except: df = pd.DataFrame()
    ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Proveedores"):
        for i, r in ed.iterrows():
            try:
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): supabase.table("Proveedores").update(d).eq("id", r['id']).execute()
                else: supabase.table("Proveedores").insert(d).execute()
            except: continue
        st.success("✅ Procedimiento realizado: Proveedores actualizados."); st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR
# ==========================================
elif "Etiquetas" in opcion:
    st.markdown("### 📂 Catálogos QR")
    t1, t2 = st.tabs(["Insumos", "Herramientas"])
    with t1:
        try:
            res = supabase.table("Insumos").select("*").execute(); df_i = pd.DataFrame(res.data)
            if not df_i.empty:
                df_i["QR"] = df_i["codigo"].apply(get_qr_data_url); df_i["Sel"] = False
                df_i = df_i.rename(columns={"Descripcion": "descripcion"})
                ed = st.data_editor(df_i[["Sel", "QR", "codigo", "descripcion"]], column_config={"QR": st.column_config.ImageColumn()}, use_container_width=True, hide_index=True)
                if st.button("🖨️ Generar PDF Insumos"):
                    sel = ed[ed["Sel"] == True]
                    if not sel.empty: 
                        pdf = generar_pdf_etiquetas_qr(sel, "Insumos"); st.download_button("📥 Descargar Etiquetas", pdf, "Etiquetas_Insumos.pdf")
                        st.success("✅ Procedimiento realizado: PDF generado."); st.toast("PDF Listo")
        except: st.error("Error al cargar insumos")
    with t2:
        try:
            res = supabase.table("Herramientas").select("*").execute(); df_h = pd.DataFrame(res.data)
            if not df_h.empty:
                df_h["QR"] = df_h["codigo"].apply(get_qr_data_url); df_h["Sel"] = False
                df_h = df_h.rename(columns={"Herramienta": "descripcion"})
                ed = st.data_editor(df_h[["Sel", "QR", "codigo", "descripcion"]], column_config={"QR": st.column_config.ImageColumn()}, use_container_width=True, hide_index=True)
                if st.button("🖨️ Generar PDF Herramientas"):
                    sel = ed[ed["Sel"] == True]
                    if not sel.empty: 
                        pdf = generar_pdf_etiquetas_qr(sel, "Herramientas"); st.download_button("📥 Descargar Etiquetas", pdf, "Etiquetas_Herramientas.pdf")
                        st.success("✅ Procedimiento realizado: PDF generado."); st.toast("PDF Listo")
        except: st.error("Error al cargar herramientas")
