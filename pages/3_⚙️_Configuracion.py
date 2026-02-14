import streamlit as st
import pandas as pd
import utils 
import time
import datetime
import io
import qrcode
import os
from fpdf import FPDF

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- 🔒 SEGURIDAD ACTIVADA ---
utils.validar_login()
# -----------------------------

supabase = utils.supabase

# ==========================================
# FUNCIONES PARA ETIQUETAS QR
# ==========================================
class PDFEtiquetas(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_etiquetas_qr(df_items, tipo="Insumos"):
    pdf = PDFEtiquetas()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Configuración de la cuadrícula de etiquetas (Ajustado para hoja Carta/A4)
    # 3 Etiquetas por fila
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
    
    # Recalcular Y después del título
    y = pdf.get_y()
    
    for index, row in df_items.iterrows():
        sku = str(row['codigo'])
        desc = str(row['descripcion'])[:50] # Cortar si es muy largo
        
        # 1. Dibujar Borde de la etiqueta
        pdf.set_draw_color(200, 200, 200) # Gris suave
        pdf.rect(x, y, ancho_etiqueta, alto_etiqueta)
        
        # 2. Generar QR en memoria
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar temporalmente
        temp_qr_path = f"temp_qr_{index}.png"
        img_qr.save(temp_qr_path)
        
        # 3. Poner Imagen QR en el PDF (Centrada en la etiqueta)
        # Tamaño QR: 25x25 aprox
        pos_qr_x = x + (ancho_etiqueta - 25) / 2
        pdf.image(temp_qr_path, x=pos_qr_x, y=y+3, w=25, h=25)
        
        # 4. Texto SKU y Descripción
        pdf.set_xy(x, y + 29)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(ancho_etiqueta, 4, sku, 0, 1, 'C')
        
        pdf.set_xy(x+1, y + 34)
        pdf.set_font('Arial', '', 7)
        pdf.multi_cell(ancho_etiqueta-2, 3, desc, align='C')
        
        # Borrar temporal
        if os.path.exists(temp_qr_path):
            os.remove(temp_qr_path)
            
        # Mover cursor para siguiente etiqueta
        col_count += 1
        if col_count < 3:
            x += ancho_etiqueta + 2 # +2 mm de separación
        else:
            # Salto de línea (Nueva fila)
            col_count = 0
            x = margen_x
            y += alto_etiqueta + 2
            
            # Si se acaba la hoja, nueva página
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

    if df.empty:
        df = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])

    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex Completo"])

    with t1:
        with st.form("alta_personal", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Completo")
            puesto = col2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            col3, col4 = st.columns(2)
            nacimiento = col3.text_input("Año Nacimiento")
            domicilio = col4.text_input("Domicilio")
            col5, col6 = st.columns(2)
            curp = col5.text_input("CURP")
            rfc = col6.text_input("RFC")
            fecha_ingreso = st.date_input("Fecha de Ingreso", value=datetime.date.today())

            if st.form_submit_button("Guardar Empleado"):
                if nombre:
                    datos = {
                        "nombre": nombre, "puesto": puesto, 
                        "anio_nacimiento": nacimiento, "domicilio": domicilio,
                        "curp": curp, "rfc": rfc, 
                        "fecha_ingreso": fecha_ingreso.isoformat(),
                        "activo": True
                    }
                    utils.supabase.table("Personal").insert(datos).execute()
                    st.success(f"✅ {nombre} registrado.")
                    time.sleep(1)
                    st.rerun()
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
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
                    if "fecha_ingreso" in datos and datos["fecha_ingreso"]: datos["fecha_ingreso"] = str(datos["fecha_ingreso"])
                    if pd.notna(row["id"]): utils.supabase.table("Personal").update(datos).eq("id", int(row["id"])).execute()
                    else: utils.supabase.table("Personal").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Base actualizada")
            time.sleep(1)
            st.rerun()

# ==========================================
# 2. INSUMOS (INTACTO)
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

    if df.empty:
        df = pd.DataFrame(columns=["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2, t3, t4 = st.tabs(["➕ Alta Manual", "📋 PEGAR DESDE EXCEL", "📋 Inventario Maestro", "🗑️ Eliminar"])

    with t1:
        with st.form("alta_insumo", clear_on_submit=True):
            col_cod, col_nom = st.columns([1, 3]) 
            nuevo_codigo = col_cod.text_input("Código / SKU", placeholder="Ej. HEM-CL-001")
            nuevo_nombre = col_nom.text_input("Descripción del Insumo")
            c1, c2, c3 = st.columns(3)
            nueva_unidad = c1.selectbox("Unidad", lista_unidades)
            nueva_cant = c2.number_input("Cantidad Inicial", min_value=0.0, step=1.0)
            nuevo_min = c3.number_input("Stock Mínimo", value=5.0)
            
            if st.form_submit_button("Guardar Insumo"):
                if nuevo_nombre and nuevo_codigo:
                    existe = False
                    if not df.empty:
                        if nuevo_codigo.strip() in df["codigo"].astype(str).str.strip().values: existe = True
                    if not existe:
                        try:
                            datos_insert = {"codigo": nuevo_codigo, "Descripcion": nuevo_nombre, "Unidad": nueva_unidad, "Cantidad": nueva_cant, "stock_minimo": nuevo_min}
                            utils.supabase.table("Insumos").insert(datos_insert).execute()
                            st.success(f"✅ Insumo {nuevo_codigo} agregado.")
                            time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.error("⛔ El código ya existe.")
                else: st.warning("Datos incompletos.")

    with t2:
        st.markdown("""### 📋 Modo Pegado Directo
        1. Copia tus datos de Excel (Títulos + Datos).
        2. Pégalos abajo y presiona el botón rojo.""")
        texto_pegado = st.text_area("👇 Pega aquí tus datos:", height=200)
        
        if st.button("🚀 Procesar Datos Pegados", type="primary"):
            if texto_pegado:
                try:
                    try: df_upload = pd.read_csv(io.StringIO(texto_pegado), sep='\t')
                    except: df_upload = pd.read_csv(io.StringIO(texto_pegado), sep=',')

                    df_upload.columns = df_upload.columns.str.lower().str.strip()
                    mapeo = {"unidad": "Unidad", "cantidad": "Cantidad", "descripcion": "Descripcion", "descripción": "Descripcion", "stock_minimo": "stock_minimo", "minimo": "stock_minimo"}
                    for col in df_upload.columns:
                        if col in mapeo: df_upload.rename(columns={col: mapeo[col]}, inplace=True)

                    if "codigo" in df_upload.columns and "Descripcion" in df_upload.columns:
                        progress = st.progress(0, text="Cargando...")
                        mapa_ids = {}
                        if not df.empty:
                            for idx, row in df.iterrows(): mapa_ids[str(row['codigo']).strip()] = row['id']
                        
                        count_ok, count_upd, total = 0, 0, len(df_upload)
                        for i, row in df_upload.iterrows():
                            try:
                                if not row["codigo"] or str(row["codigo"]).strip() == "": continue
                                cod_val = str(row["codigo"]).strip()
                                desc_val = str(row["Descripcion"]).strip()
                                uni_val = str(row["Unidad"]) if "Unidad" in df_upload.columns else "Pzas"
                                try: cant_val = float(str(row["Cantidad"]).replace(',', '')) 
                                except: cant_val = 0.0
                                try: min_val = float(str(row["stock_minimo"]).replace(',', '')) if "stock_minimo" in df_upload.columns else 5.0
                                except: min_val = 5.0

                                datos_row = {"codigo": cod_val, "Descripcion": desc_val, "Unidad": uni_val, "Cantidad": cant_val, "stock_minimo": min_val}
                                if cod_val in mapa_ids:
                                    utils.supabase.table("Insumos").update(datos_row).eq("id", int(mapa_ids[cod_val])).execute(); count_upd += 1
                                else:
                                    utils.supabase.table("Insumos").insert(datos_row).execute(); count_ok += 1
                            except: pass
                            progress.progress((i+1)/total)
                        progress.empty()
                        st.success(f"✅ Terminado: {count_ok} nuevos, {count_upd} actualizados."); time.sleep(2); st.rerun()
                    else: st.error("⛔ Faltan columnas 'codigo' y 'descripcion'.")
                except Exception as e: st.error(f"Error: {e}")

    with t3:
        col_search, _ = st.columns([1, 1])
        busqueda = col_search.text_input("🔍 Buscar Insumo", placeholder="Escribe código o descripción...")
        df_display = df.copy()
        if busqueda:
            mask = (df_display["codigo"].astype(str).str.contains(busqueda, case=False, na=False) | 
                    df_display.get("Descripcion", pd.Series()).astype(str).str.contains(busqueda, case=False, na=False))
            df_display = df_display[mask]

        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "codigo": st.column_config.TextColumn("Código SKU", required=True, width="medium"),
            "Descripcion": st.column_config.TextColumn("Descripción", width=None),
            "Cantidad": st.column_config.NumberColumn("Stock", width="small", min_value=0),
            "Unidad": st.column_config.SelectboxColumn("Unidad", options=lista_unidades, required=True, width="small"),
            "stock_minimo": st.column_config.NumberColumn("Min ⚠️", width="small")
        }
        cols_ver = ["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
        for c in cols_ver: 
            if c not in df_display.columns: df_display[c] = None
        edited_df = st.data_editor(df_display[cols_ver], column_config=column_config, num_rows="dynamic", use_container_width=True, height=500, key="editor_insumos_v4")

        if st.button("💾 Guardar Cambios"):
            for index, row in edited_df.iterrows():
                try:
                    datos = {"codigo": row["codigo"], "Descripcion": row["Descripcion"], "Cantidad": row["Cantidad"], "Unidad": row["Unidad"], "stock_minimo": row["stock_minimo"]}
                    if pd.notna(row["id"]): utils.supabase.table("Insumos").update(datos).eq("id", int(row["id"])).execute()
                    else: utils.supabase.table("Insumos").insert(datos).execute()
                except: pass
            st.success("✅ Actualizado."); time.sleep(1); st.rerun()

    with t4:
        st.warning("⚠️ Eliminar Insumo")
        if not df.empty:
            lista_eliminar = [f"{row['codigo']} | {row.get('Descripcion', '')}" for i, row in df.iterrows()]
            sel_eliminar = st.selectbox("Selecciona:", lista_eliminar, index=None)
            if sel_eliminar and st.button("🗑️ Eliminar Definitivamente", type="primary"):
                cod_e = sel_eliminar.split(" | ")[0]
                try:
                    id_borrar = df[df["codigo"] == cod_e].iloc[0]["id"]
                    utils.supabase.table("Insumos").delete().eq("id", int(id_borrar)).execute()
                    st.success("✅ Eliminado."); time.sleep(1); st.rerun()
                except: st.error("Error al eliminar.")

# ==========================================
# 3. HERRAMIENTAS (INTACTO)
# ==========================================
elif opcion == "Herramientas":
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()

    if df.empty: df = pd.DataFrame(columns=["id", "codigo", "Herramienta", "descripcion", "marca", "Estado"])

    t1, t2 = st.tabs(["➕ Alta Herramienta", "📋 Lista Completa"])
    with t1:
        with st.form("alta_herramienta", clear_on_submit=True):
            c1, c2 = st.columns([1, 3])
            nuevo_sku = c1.text_input("Código SKU")
            nuevo_nombre = c2.text_input("Nombre")
            c3, c4, c5 = st.columns(3)
            nueva_marca = c3.text_input("Marca")
            nuevo_estado = c4.selectbox("Estado", ["BUEN ESTADO", "MAL ESTADO", "EN REPARACIÓN", "BAJA"])
            nueva_desc = c5.text_input("Descripción")
            if st.form_submit_button("Guardar"):
                if nuevo_nombre and nuevo_sku:
                    utils.supabase.table("Herramientas").insert({"codigo": nuevo_sku, "Herramienta": nuevo_nombre, "marca": nueva_marca, "Estado": nuevo_estado, "descripcion": nueva_desc, "Responsable": "Bodega"}).execute()
                    st.success("Agregado."); time.sleep(1); st.rerun()
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
# 4. CLIENTES (INTACTO)
# ==========================================
elif opcion == "Clientes":
    try:
        df = pd.DataFrame(utils.supabase.table("Clientes").select("*").order("id").execute().data)
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("alta_cli"):
            nom = st.text_input("Empresa")
            rfc = st.text_input("RFC")
            dir = st.text_input("Dirección")
            col = st.text_input("Colonia")
            cp = st.text_input("CP")
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Clientes").insert({"nombre": nom, "rfc": rfc, "direccion": dir, "colonia": col, "codigo_postal": cp}).execute()
                st.success("Guardado."); time.sleep(1); st.rerun()
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
            st.success("Actualizado."); time.sleep(1); st.rerun()

# ==========================================
# 5. PROVEEDORES (INTACTO)
# ==========================================
elif opcion == "Proveedores":
    try:
        df = pd.DataFrame(utils.supabase.table("Proveedores").select("*").order("id").execute().data)
        if "empresa" in df.columns and "nombre" not in df.columns: df["nombre"] = df["empresa"]
    except: df = pd.DataFrame()

    t1, t2 = st.tabs(["➕ Alta", "📋 Lista"])
    with t1:
        with st.form("alta_prov"):
            nom = st.text_input("Empresa/Nombre")
            rfc = st.text_input("RFC")
            dir = st.text_input("Dirección")
            if st.form_submit_button("Guardar"):
                utils.supabase.table("Proveedores").insert({"nombre": nom, "empresa": nom, "rfc": rfc, "domicilio": dir}).execute()
                st.success("Guardado."); time.sleep(1); st.rerun()
    with t2:
        cols = ["id", "nombre", "rfc", "domicilio", "colonia", "codigo_postal"]
        for c in cols: 
            if c not in df.columns: df[c] = None
        edited_df = st.data_editor(df[cols], num_rows="dynamic", use_container_width=True)
        if st.button("Actualizar Proveedores"):
            for i, row in edited_df.iterrows():
                d = {c: row[c] for c in cols if c!='id'}
                d["empresa"] = d["nombre"]
                if pd.notna(row.get('id')): utils.supabase.table("Proveedores").update(d).eq("id", int(row['id'])).execute()
                else: utils.supabase.table("Proveedores").insert(d).execute()
            st.success("Actualizado."); time.sleep(1); st.rerun()

# ==========================================
# 6. CATÁLOGOS & ETIQUETAS QR (NUEVO)
# ==========================================
elif "Etiquetas" in opcion:
    st.markdown("### 📂 Catálogos y Generador de Etiquetas QR")
    
    tab_ins, tab_her = st.tabs(["📦 Etiquetas Insumos", "🛠️ Etiquetas Herramientas"])
    
    # --- ETIQUETAS INSUMOS ---
    with tab_ins:
        try:
            res = utils.supabase.table("Insumos").select("*").order("id").execute()
            df_ins = pd.DataFrame(res.data)
            if not df_ins.empty:
                df_ins.columns = df_ins.columns.str.lower()
                # Asegurar columnas
                if "descripcion" not in df_ins.columns: df_ins["descripcion"] = "Sin Desc"
                if "codigo" not in df_ins.columns: df_ins["codigo"] = "S/N"
                
                # Selector de filas
                df_ins["Seleccionar"] = False
                st.info("Selecciona los insumos para generar sus etiquetas:")
                
                # Filtro rápido
                filtro = st.text_input("🔎 Filtrar Insumos:", key="filtro_qr_ins")
                if filtro:
                    mask = (df_ins["codigo"].astype(str).str.contains(filtro, case=False)) | (df_ins["descripcion"].astype(str).str.contains(filtro, case=False))
                    df_ins = df_ins[mask]

                # Editor para seleccionar
                edited_ins = st.data_editor(
                    df_ins[["Seleccionar", "codigo", "descripcion"]],
                    column_config={"Seleccionar": st.column_config.CheckboxColumn("Imprimir", default=False)},
                    hide_index=True,
                    use_container_width=True
                )
                
                if st.button("🖨️ Generar PDF de Insumos Seleccionados"):
                    seleccionados = edited_ins[edited_ins["Seleccionar"] == True]
                    if not seleccionados.empty:
                        pdf_bytes = generar_pdf_etiquetas_qr(seleccionados, "Insumos")
                        st.success(f"✅ {len(seleccionados)} etiquetas generadas.")
                        st.download_button("📥 Descargar Etiquetas PDF", pdf_bytes, "Etiquetas_Insumos.pdf", "application/pdf")
                    else:
                        st.warning("Selecciona al menos un insumo.")
            else:
                st.warning("No hay insumos registrados.")
        except Exception as e: st.error(f"Error: {e}")

    # --- ETIQUETAS HERRAMIENTAS ---
    with tab_her:
        try:
            res = utils.supabase.table("Herramientas").select("*").order("id").execute()
            df_her = pd.DataFrame(res.data)
            if not df_her.empty:
                # Estandarizar
                if "herramienta" in df_her.columns and "descripcion" not in df_her.columns:
                    df_her["descripcion"] = df_her["herramienta"]
                
                df_her["Seleccionar"] = False
                st.info("Selecciona las herramientas para etiquetar:")
                
                filtro_h = st.text_input("🔎 Filtrar Herramientas:", key="filtro_qr_her")
                if filtro_h:
                    mask = (df_her["codigo"].astype(str).str.contains(filtro_h, case=False)) | (df_her["herramienta"].astype(str).str.contains(filtro_h, case=False))
                    df_her = df_her[mask]

                edited_her = st.data_editor(
                    df_her[["Seleccionar", "codigo", "herramienta", "marca"]],
                    column_config={"Seleccionar": st.column_config.CheckboxColumn("Imprimir", default=False)},
                    hide_index=True,
                    use_container_width=True
                )
                
                if st.button("🖨️ Generar PDF de Herramientas"):
                    sel_h = edited_her[edited_her["Seleccionar"] == True]
                    if not sel_h.empty:
                        # Adaptar columnas para la función generadora
                        sel_h = sel_h.rename(columns={"herramienta": "descripcion"})
                        pdf_bytes = generar_pdf_etiquetas_qr(sel_h, "Herramientas")
                        st.success(f"✅ {len(sel_h)} etiquetas generadas.")
                        st.download_button("📥 Descargar Etiquetas PDF", pdf_bytes, "Etiquetas_Herramientas.pdf", "application/pdf")
                    else:
                        st.warning("Selecciona al menos una herramienta.")
            else:
                st.warning("No hay herramientas registradas.")
        except Exception as e: st.error(f"Error: {e}")
