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
# 1. PERSONAL (INTACTO)
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
# 2. INSUMOS (CORREGIDO PARA EVITAR NULOS)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        # Limpieza de columnas para mostrar
        if not df.empty:
            if "Descripcion" not in df.columns and "Insumo" in df.columns:
                df["Descripcion"] = df["Insumo"]
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Manual", "📋 Inventario Maestro"])
    
    with t1:
        with st.form("alta_insumo"):
            c1, c2 = st.columns([1, 3]); cod = c1.text_input("Código / SKU"); nom = c2.text_input("Descripción")
            c3, c4, c5 = st.columns(3); uni = c3.selectbox("Unidad", lista_unidades); cant = c4.number_input("Cantidad", min_value=0.0); mini = c5.number_input("Min", value=5.0)
            ubi = st.text_input("Ubicación")
            
            if st.form_submit_button("Guardar Insumo"):
                if cod and nom:
                    # FORZAMOS el valor en la columna 'Insumo' para evitar el error de tus fotos
                    datos_insumo = {
                        "codigo": cod, 
                        "Descripcion": nom, 
                        "Insumo": nom,  # <--- Esto arregla el error de "null value"
                        "Unidad": uni, 
                        "Cantidad": cant, 
                        "stock_minimo": mini, 
                        "ubicacion": ubi
                    }
                    try:
                        utils.supabase.table("Insumos").insert(datos_insumo).execute()
                        st.success("✅ Guardado"); time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error al insertar: {e}")
    
    with t2:
        if not df.empty:
            # Aseguramos que la columna 'ubicacion' exista visualmente
            if "ubicacion" not in df.columns: df["ubicacion"] = None
            if "Descripcion" not in df.columns: df["Descripcion"] = df["Insumo"]
            
            columnas_orden = ["id", "codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo", "ubicacion"]
            edited = st.data_editor(df[columnas_orden], num_rows="dynamic", use_container_width=True)
            
            if st.button("💾 Guardar Cambios en Inventario"):
                for i, r in edited.iterrows():
                    # Mapeo manual para asegurar que 'Insumo' no sea nulo
                    d = {
                        "codigo": r["codigo"], 
                        "Descripcion": r["Descripcion"], 
                        "Insumo": r["Descripcion"], # Sincronizamos la columna obligatoria
                        "Cantidad": r["Cantidad"], 
                        "Unidad": r["Unidad"], 
                        "stock_minimo": r["stock_minimo"], 
                        "ubicacion": r["ubicacion"]
                    }
                    try:
                        if pd.notna(r["id"]): 
                            utils.supabase.table("Insumos").update(d).eq("id", r["id"]).execute()
                        else: 
                            utils.supabase.table("Insumos").insert(d).execute()
                    except Exception as e:
                        st.error(f"Error en fila {r['codigo']}: {e}")
                st.success("✅ Cambios aplicados"); time.sleep(1); st.rerun()

# ==========================================
# 3. HERRAMIENTAS (INTACTO)
# ==========================================
elif opcion == "Herramientas":
    st.markdown("### 🛠️ Gestión de Herramientas (Activos)")
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()
    t1, t2 = st.tabs(["➕ Alta de Herramienta", "📋 Inventario de Activos"])
    with t1:
        with st.form("alta_herramienta_form", clear_on_submit=True):
            c1, c2 = st.columns([1, 2]); sku_h = c1.text_input("Código SKU"); nombre_h = c2.text_input("Nombre Herramienta")
            desc_h = st.text_area("Descripción"); c3, c4, c5 = st.columns(3)
            marca_h = c3.text_input("Marca"); estado_h = c4.selectbox("Estado", ["NUEVO", "BUEN ESTADO", "REGULAR", "BAJA"]); ubicacion_h = c5.text_input("Ubicación")
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Herramientas").insert({"codigo": sku_h, "Herramienta": nombre_h, "descripcion": desc_h, "marca": marca_h, "Estado": estado_h, "ubicacion": ubicacion_h, "Responsable": "BODEGA"}).execute()
                st.success("✅ Registrado."); st.rerun()
    with t2:
        edited_h = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Actualizar Catálogo"):
            for i, r in edited_h.iterrows():
                d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
                if pd.notna(r['id']): utils.supabase.table("Herramientas").update(d).eq("id", r['id']).execute()
                else: d["Responsable"] = "BODEGA"; utils.supabase.table("Herramientas").insert(d).execute()
            st.success("✅ Sincronizado"); st.rerun()

# ==========================================
# 4. CLIENTES / 5. PROVEEDORES (INTACTOS)
# ==========================================
elif opcion == "Clientes":
    st.markdown("### 🏢 Clientes")
    df = pd.DataFrame(utils.supabase.table("Clientes").select("*").execute().data)
    ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Guardar"):
        for i, r in ed.iterrows():
            d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
            if pd.notna(r['id']): utils.supabase.table("Clientes").update(d).eq("id", r['id']).execute()
            else: utils.supabase.table("Clientes").insert(d).execute()
        st.rerun()

elif opcion == "Proveedores":
    st.markdown("### 🚚 Proveedores")
    df = pd.DataFrame(utils.supabase.table("Proveedores").select("*").execute().data)
    ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Guardar"):
        for i, r in ed.iterrows():
            d = {k: v for k, v in r.items() if k != 'id' and pd.notna(v)}
            if pd.notna(r['id']): utils.supabase.table("Proveedores").update(d).eq("id", r['id']).execute()
            else: utils.supabase.table("Proveedores").insert(d).execute()
        st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR (INTACTO)
# ==========================================
elif "Etiquetas" in opcion:
    st.markdown("### 📂 Catálogos y Etiquetas QR")
    tab_ins, tab_her = st.tabs(["📦 Insumos", "🛠️ Herramientas"])
    with tab_ins:
        res = utils.supabase.table("Insumos").select("*").order("id").execute(); df_ins = pd.DataFrame(res.data)
        if not df_ins.empty:
            if "Descripcion" not in df_ins.columns: df_ins["Descripcion"] = df_ins["Insumo"]
            df_ins["QR"] = df_ins["codigo"].apply(get_qr_data_url); df_ins["Sel"] = False
            ed = st.data_editor(df_ins[["Sel", "QR", "codigo", "Descripcion"]], column_config={"QR": st.column_config.ImageColumn()}, use_container_width=True, hide_index=True)
            if st.button("🖨️ PDF Insumos"):
                sel = ed[ed["Sel"] == True].rename(columns={"Descripcion": "descripcion"})
                if not sel.empty: st.download_button("📥 Descargar", generar_pdf_etiquetas_qr(sel, "Insumos"), "Etiquetas.pdf")
    with tab_her:
        res = utils.supabase.table("Herramientas").select("*").order("id").execute(); df_her = pd.DataFrame(res.data)
        if not df_her.empty:
            df_her["QR"] = df_her["codigo"].apply(get_qr_data_url); df_her["Sel"] = False
            df_her_tag = df_her.rename(columns={"Herramienta": "descripcion"})
            ed = st.data_editor(df_her_tag[["Sel", "QR", "codigo", "descripcion"]], column_config={"QR": st.column_config.ImageColumn()}, use_container_width=True, hide_index=True)
            if st.button("🖨️ PDF Herramientas"):
                sel = ed[ed["Sel"] == True]
                if not sel.empty: st.download_button("📥 Descargar", generar_pdf_etiquetas_qr(sel, "Herramientas"), "Etiquetas.pdf")
