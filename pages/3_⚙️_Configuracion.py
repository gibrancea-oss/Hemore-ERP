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

# Generar QR en Base64 para mostrar en la tabla (Vista Previa)
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
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_etiquetas_qr(df_items, tipo="Insumos"):
    pdf = PDFEtiquetas()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Configuración de etiquetas (3 por fila)
    ancho_etiqueta = 63 
    alto_etiqueta = 45
    margen_x = 10
    margen_y = 15
    
    x = margen_x
    y = margen_y
    col_count = 0
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Catálogo de {tipo} - Etiquetas QR", 0, 1, 'C')
    pdf.ln(5)
    y = pdf.get_y()
    
    for index, row in df_items.iterrows():
        sku = str(row['codigo'])
        desc = str(row['descripcion'])[:50]
        
        # Borde
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x, y, ancho_etiqueta, alto_etiqueta)
        
        # QR Alta Calidad para PDF
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        temp_qr_path = f"temp_qr_{index}.png"
        img_qr.save(temp_qr_path)
        
        # Imagen
        pos_qr_x = x + (ancho_etiqueta - 25) / 2
        pdf.image(temp_qr_path, x=pos_qr_x, y=y+3, w=25, h=25)
        
        # Textos
        pdf.set_xy(x, y + 29)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(ancho_etiqueta, 4, sku, 0, 1, 'C')
        
        pdf.set_xy(x+1, y + 34)
        pdf.set_font('Arial', '', 7)
        pdf.multi_cell(ancho_etiqueta-2, 3, desc, align='C')
        
        if os.path.exists(temp_qr_path): os.remove(temp_qr_path)
            
        col_count += 1
        if col_count < 3:
            x += ancho_etiqueta + 2
        else:
            col_count = 0
            x = margen_x
            y += alto_etiqueta + 2
            if y > 250:
                pdf.add_page()
                y = margen_y

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
# 1. PERSONAL
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

    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex Completo"])

    with t1:
        with st.form("alta_personal", clear_on_submit=True):
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

            if st.form_submit_button("Guardar Empleado"):
                if nombre:
                    datos = {"nombre": nombre, "puesto": puesto, "anio_nacimiento": nacimiento, "domicilio": domicilio, "curp": curp, "rfc": rfc, "fecha_ingreso": fecha_ingreso.isoformat(), "activo": True}
                    utils.supabase.table("Personal").insert(datos).execute()
                    st.success(f"✅ {nombre} registrado."); time.sleep(1); st.rerun()
                else: st.warning("Nombre obligatorio")

    with t2:
        column_config = {
            "id": st.column_config.NumberColumn(disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Nombre", width=None), 
            "puesto": st.column_config.SelectboxColumn("Puesto", options=["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"], width="small"),
            "fecha_ingreso": st.column_config.DateColumn("Ingreso", format="DD/MM/YYYY", width="small"),
            "activo": st.column_config.CheckboxColumn("Activo", width="small")
        }
        cols_ver = ["id", "nombre", "puesto", "anio_nacimiento", "domicilio", "curp", "rfc", "fecha_ingreso", "activo"]
        cols_reales = [c for c in cols_ver if c in df.columns]
        edited_df = st.data_editor(df[cols_reales], column_config=column_config, num_rows="dynamic", use_container_width=True, key="editor_personal")

        if st.button("💾 Actualizar Personal"):
            bar = st.progress(0, text="Guardando...")
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
                    if "fecha_ingreso" in datos and datos["fecha_ingreso"]: datos["fecha_ingreso"] = str(datos["fecha_ingreso"])
                    if pd.notna(row["id"]): utils.supabase.table("Personal").update(datos).eq("id", int(row["id"])).execute()
                    else: utils.supabase.table("Personal").insert(datos).execute()
                except: pass
                bar.progress((index+1)/len(edited_df))
            bar.empty(); st.success("✅ Actualizado"); time.sleep(1); st.rerun()

# ==========================================
# 2. INSUMOS (CON CUADRÍCULA PEGADO)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            if "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
            else: df["codigo"] = df["codigo"].fillna(df["id"].astype(str))
    except: df = pd.DataFrame()

    if df.empty: df = pd.DataFrame(columns=["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2, t3, t4 = st.tabs(["➕ Alta Manual", "📋 PEGAR DESDE EXCEL", "📋 Inventario Maestro", "🗑️ Eliminar"])

    with t1:
        with st.form("alta_insumo"):
            c1, c2 = st.columns([1, 3]) 
            nuevo_codigo = c1.text_input("Código / SKU")
            nuevo_nombre = c2.text_input("Descripción")
            c3, c4, c5 = st.columns(3)
            nueva_unidad = c3.selectbox("Unidad", lista_unidades)
            nueva_cant = c4.number_input("Cantidad", min_value=0.0)
            nuevo_min = c5.number_input("Min", value=5.0)
            if st.form_submit_button("Guardar"):
                if nuevo_nombre and nuevo_codigo:
                    # Validar
                    existe = False
                    if not df.empty and nuevo_codigo.strip() in df["codigo"].astype(str).str.strip().values: existe = True
                    if not existe:
                        utils.supabase.table("Insumos").insert({"codigo": nuevo_codigo, "Descripcion": nuevo_nombre, "Unidad": nueva_unidad, "Cantidad": nueva_cant, "stock_minimo": nuevo_min}).execute()
                        st.success("Agregado."); time.sleep(1); st.rerun()
                    else: st.error("Código repetido.")
                else: st.warning("Datos faltantes.")

    with t2:
        st.info("Copia tus datos de Excel y pégalos aquí:")
        # Grid vacío para pegar
        df_template = pd.DataFrame(columns=["codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo"])
        edited_grid = st.data_editor(df_template, num_rows="dynamic", use_container_width=True, key="grid_carga")
        
        if st.button("🚀 Guardar Pegado"):
            if not edited_grid.empty:
                prog = st.progress(0, text="Procesando...")
                mapa_ids = {str(row['codigo']).strip(): row['id'] for i, row in df.iterrows()} if not df.empty else {}
                
                count_ok, count_upd = 0, 0
                for i, row in edited_grid.iterrows():
                    try:
                        if not row["codigo"] or str(row["codigo"]).strip() == "": continue
                        cod = str(row["codigo"]).strip()
                        desc = str(row["Descripcion"]).strip()
                        uni = str(row["Unidad"]) if row["Unidad"] else "Pzas"
                        cant = float(row["Cantidad"]) if row["Cantidad"] else 0.0
                        mini = float(row["stock_minimo"]) if row["stock_minimo"] else 5.0
                        
                        d = {"codigo": cod, "Descripcion": desc, "Unidad": uni, "Cantidad": cant, "stock_minimo": mini}
                        
                        if cod in mapa_ids:
                            utils.supabase.table("Insumos").update(d).eq("id", int(mapa_ids[cod])).execute(); count_upd += 1
                        else:
                            utils.supabase.table("Insumos").insert(d).execute(); count_ok += 1
                    except: pass
                    prog.progress((i+1)/len(edited_grid))
                prog.empty(); st.success(f"✅ {count_ok} nuevos, {count_upd} actualizados."); time.sleep(2); st.rerun()

    with t3:
        # Inventario
        search = st.text_input("🔍 Buscar:", key="search_inv_ins")
        df_view = df.copy()
        if search:
            mask = df_view["codigo"].astype(str).str.contains(search, case=False, na=False) | df_view["Descripcion"].astype(str).str.contains(search, case=False, na=False)
            df_view = df_view[mask]
            
        cols_inv = ["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
        for c in cols_inv: 
            if c not in df_view.columns: df_view[c] = None
            
        edited_inv = st.data_editor(df_view[cols_inv], column_config={"id": st.column_config.NumberColumn(disabled=True)}, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Guardar Cambios Inv."):
            for i, row in edited_inv.iterrows():
                d = {"codigo": row["codigo"], "Descripcion": row["Descripcion"], "Cantidad": row["Cantidad"], "Unidad": row["Unidad"], "stock_minimo": row["stock_minimo"]}
                if pd.notna(row["id"]): utils.supabase.table("Insumos").update(d).eq("id", int(row["id"])).execute()
                else: utils.supabase.table("Insumos").insert(d).execute()
            st.success("Guardado."); time.sleep(1); st.rerun()

    with t4:
        st.warning("⚠️ Eliminar")
        if not df.empty:
            sel_del = st.selectbox("Insumo a borrar:", [f"{r['codigo']} | {r['Descripcion']}" for i, r in df.iterrows()])
            if sel_del and st.button("🗑️ Borrar"):
                cod = sel_del.split(" | ")[0]
                idd = df[df["codigo"]==cod].iloc[0]["id"]
                utils.supabase.table("Insumos").delete().eq("id", int(idd)).execute()
                st.success("Borrado."); time.sleep(1); st.rerun()

# ==========================================
# 3. HERRAMIENTAS
# ==========================================
elif opcion == "Herramientas":
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()
    if df.empty: df = pd.DataFrame(columns=["id", "codigo", "Herramienta", "descripcion", "marca", "Estado"])

    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("alta_her"):
            c1, c2 = st.columns([1, 3])
            sku = c1.text_input("SKU")
            nom = c2.text_input("Nombre")
            c3, c4 = st.columns(2)
            marca = c3.text_input("Marca")
            est = c4.selectbox("Estado", ["BUEN ESTADO", "MAL ESTADO", "BAJA"])
            desc = st.text_input("Descripción")
            if st.form_submit_button("Guardar"):
                if sku and nom:
                    utils.supabase.table("Herramientas").insert({"codigo": sku, "Herramienta": nom, "marca": marca, "Estado": est, "descripcion": desc}).execute()
                    st.success("Guardado."); time.sleep(1); st.rerun()
    with t2:
        cols = ["id", "codigo", "Herramienta", "descripcion", "marca", "Estado"]
        edited_df = st.data_editor(df[cols] if not df.empty else df, num_rows="dynamic", use_container_width=True)
        if st.button("Actualizar Herramientas"):
            for i, row in edited_df.iterrows():
                d = {c: row[c] for c in cols if c!='id'}
                if pd.notna(row.get('id')): utils.supabase.table("Herramientas").update(d).eq("id", int(row['id'])).execute()
                else: utils.supabase.table("Herramientas").insert(d).execute()
            st.success("Actualizado."); time.sleep(1); st.rerun()

# ==========================================
# 4. CLIENTES
# ==========================================
elif opcion == "Clientes":
    try: df = pd.DataFrame(utils.supabase.table("Clientes").select("*").order("id").execute().data)
    except: df = pd.DataFrame()
    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("alta_c"):
            nom = st.text_input("Empresa")
            rfc = st.text_input("RFC")
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Clientes").insert({"nombre": nom, "rfc": rfc}).execute(); st.success("Ok"); time.sleep(1); st.rerun()
    with t2:
        cols = ["id", "nombre", "rfc", "direccion", "colonia", "codigo_postal"]
        for c in cols: 
            if c not in df.columns: df[c] = None
        edited_df = st.data_editor(df[cols], num_rows="dynamic", use_container_width=True)
        if st.button("Actualizar Clientes"):
            for i, row in edited_df.iterrows():
                d = {c: row[c] for c in cols if c!='id'}
                if pd.notna(row.get('id')): utils.supabase.table("Clientes").update(d).eq("id", int(row['id'])).execute()
                else: utils.supabase.table("Clientes").insert(d).execute()
            st.success("Ok"); time.sleep(1); st.rerun()

# ==========================================
# 5. PROVEEDORES
# ==========================================
elif opcion == "Proveedores":
    try: 
        df = pd.DataFrame(utils.supabase.table("Proveedores").select("*").order("id").execute().data)
        if "empresa" in df.columns and "nombre" not in df.columns: df["nombre"] = df["empresa"]
    except: df = pd.DataFrame()
    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("alta_p"):
            nom = st.text_input("Nombre")
            rfc = st.text_input("RFC")
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Proveedores").insert({"nombre": nom, "empresa": nom, "rfc": rfc}).execute(); st.success("Ok"); time.sleep(1); st.rerun()
    with t2:
        cols = ["id", "nombre", "rfc", "domicilio"]
        for c in cols: 
            if c not in df.columns: df[c] = None
        edited_df = st.data_editor(df[cols], num_rows="dynamic", use_container_width=True)
        if st.button("Actualizar Prov."):
            for i, row in edited_df.iterrows():
                d = {c: row[c] for c in cols if c!='id'}
                d["empresa"] = d["nombre"]
                if pd.notna(row.get('id')): utils.supabase.table("Proveedores").update(d).eq("id", int(row['id'])).execute()
                else: utils.supabase.table("Proveedores").insert(d).execute()
            st.success("Ok"); time.sleep(1); st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR (NUEVO CON COLUMNA QR)
# ==========================================
elif "Etiquetas" in opcion:
    st.markdown("### 📂 Catálogos y Etiquetas QR")
    
    tab_ins, tab_her = st.tabs(["📦 Etiquetas Insumos", "🛠️ Etiquetas Herramientas"])
    
    # --- INSUMOS ---
    with tab_ins:
        try:
            res = utils.supabase.table("Insumos").select("*").order("id").execute()
            df_ins = pd.DataFrame(res.data)
            if not df_ins.empty:
                df_ins.columns = df_ins.columns.str.lower()
                if "descripcion" not in df_ins.columns: df_ins["descripcion"] = "Sin Desc"
                
                # GENERAR COLUMNA DE IMAGEN QR
                df_ins["QR_Img"] = df_ins["codigo"].apply(get_qr_data_url)
                df_ins["Seleccionar"] = False
                
                st.info("Selecciona para imprimir:")
                
                filtro = st.text_input("🔎 Filtrar:", key="f_qr_ins")
                if filtro:
                    mask = df_ins["codigo"].astype(str).str.contains(filtro, case=False) | df_ins["descripcion"].astype(str).str.contains(filtro, case=False)
                    df_ins = df_ins[mask]

                edited_ins = st.data_editor(
                    df_ins[["Seleccionar", "QR_Img", "codigo", "descripcion", "unidad"]],
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("Print", width="small"),
                        "QR_Img": st.column_config.ImageColumn("QR Vista Previa", width="small"),
                        "codigo": st.column_config.TextColumn("SKU", width="medium"),
                        "descripcion": st.column_config.TextColumn("Descripción", width="large")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=600
                )
                
                if st.button("🖨️ Generar PDF (Seleccionados)"):
                    seleccionados = edited_ins[edited_ins["Seleccionar"] == True]
                    if not seleccionados.empty:
                        pdf_bytes = generar_pdf_etiquetas_qr(seleccionados, "Insumos")
                        st.success(f"Generando {len(seleccionados)} etiquetas...")
                        st.download_button("📥 Descargar PDF", pdf_bytes, "Etiquetas_Insumos.pdf", "application/pdf")
                    else: st.warning("Selecciona algo.")
            else: st.warning("Sin datos.")
        except Exception as e: st.error(f"Error: {e}")

    # --- HERRAMIENTAS ---
    with tab_her:
        try:
            res = utils.supabase.table("Herramientas").select("*").order("id").execute()
            df_her = pd.DataFrame(res.data)
            if not df_her.empty:
                if "herramienta" in df_her.columns and "descripcion" not in df_her.columns:
                    df_her["descripcion"] = df_her["herramienta"]
                
                # GENERAR QR
                df_her["QR_Img"] = df_her["codigo"].apply(get_qr_data_url)
                df_her["Seleccionar"] = False
                
                filtro_h = st.text_input("🔎 Filtrar:", key="f_qr_her")
                if filtro_h:
                    mask = df_her["codigo"].astype(str).str.contains(filtro_h, case=False) | df_her["herramienta"].astype(str).str.contains(filtro_h, case=False)
                    df_her = df_her[mask]

                edited_her = st.data_editor(
                    df_her[["Seleccionar", "QR_Img", "codigo", "herramienta", "marca"]],
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("Print", width="small"),
                        "QR_Img": st.column_config.ImageColumn("QR Vista Previa", width="small"),
                        "codigo": st.column_config.TextColumn("SKU", width="medium"),
                        "herramienta": st.column_config.TextColumn("Herramienta", width="large")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                if st.button("🖨️ Generar PDF Herramientas"):
                    sel_h = edited_her[edited_her["Seleccionar"] == True]
                    if not sel_h.empty:
                        sel_h = sel_h.rename(columns={"herramienta": "descripcion"})
                        pdf_bytes = generar_pdf_etiquetas_qr(sel_h, "Herramientas")
                        st.download_button("📥 Descargar PDF", pdf_bytes, "Etiquetas_Herramientas.pdf", "application/pdf")
                    else: st.warning("Selecciona algo.")
            else: st.warning("Sin herramientas.")
        except Exception as e: st.error(f"Error: {e}")
