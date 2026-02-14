import streamlit as st
import pandas as pd
import utils 
import time
import datetime
import io

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- 🔒 SEGURIDAD ACTIVADA ---
utils.validar_login()
# -----------------------------

supabase = utils.supabase

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores"]
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
                    if pd.notna(row["id"]): utils.supabase.table("Personal").update(datos).eq("id", row["id"]).execute()
                    else: utils.supabase.table("Personal").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Base actualizada")
            time.sleep(1)
            st.rerun()

# ==========================================
# 2. INSUMOS (VERSIÓN COPIAR-PEGAR INFALIBLE)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    
    # Cargar datos actuales
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            if "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
            else: df["codigo"] = df["codigo"].fillna(df["id"].astype(str))
    except: df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2, t3, t4 = st.tabs(["➕ Alta Manual", "📋 PEGAR DESDE EXCEL (RÁPIDO)", "📋 Inventario Maestro", "🗑️ Eliminar"])

    # 1. ALTA MANUAL
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

    # 2. CARGA MASIVA (MÉTODO COPIAR Y PEGAR)
    with t2:
        st.markdown("""
        ### 📋 Instrucciones (La forma más fácil y segura):
        1. Ve a tu Excel.
        2. Selecciona tus datos (incluyendo la fila de títulos: código, descripción, etc).
        3. Presiona `Ctrl + C` (Copiar).
        4. Presiona `Ctrl + V` (Pegar) en el recuadro de abajo.
        5. Dale click al botón rojo.
        """)
        
        texto_pegado = st.text_area("👇 Pega aquí tus datos:", height=200)
        
        if st.button("🚀 Procesar Datos Pegados", type="primary"):
            if texto_pegado:
                try:
                    # Intentamos leer como si fuera copiado de Excel (separado por tabulaciones)
                    try:
                        df_upload = pd.read_csv(io.StringIO(texto_pegado), sep='\t')
                    except:
                        # Si falla, intentamos por comas (CSV)
                        df_upload = pd.read_csv(io.StringIO(texto_pegado), sep=',')

                    # --- CORRECCIÓN DE ERRORES (LIMPIEZA DE COLUMNAS) ---
                    # 1. Convertir todo a minúsculas
                    df_upload.columns = df_upload.columns.str.lower()
                    # 2. Quitar espacios invisibles (Ej: "codigo " -> "codigo")
                    df_upload.columns = df_upload.columns.str.strip()
                    
                    # 3. Mapeo de nombres para que coincidan con la Base de Datos
                    mapeo = {
                        "unidad": "Unidad", 
                        "cantidad": "Cantidad",
                        "descripcion": "Descripcion", 
                        "descripción": "Descripcion",
                        "stock_minimo": "stock_minimo", 
                        "stock minimo": "stock_minimo", 
                        "minimo": "stock_minimo"
                    }
                    for col in df_upload.columns:
                        if col in mapeo: df_upload.rename(columns={col: mapeo[col]}, inplace=True)

                    # --- VALIDACIÓN ---
                    if "codigo" in df_upload.columns and "Descripcion" in df_upload.columns:
                        progress = st.progress(0, text="Iniciando carga...")
                        
                        # Mapa de existentes para saber si Actualizar o Insertar
                        mapa_ids = {}
                        if not df.empty:
                            for idx, row in df.iterrows():
                                mapa_ids[str(row['codigo']).strip()] = row['id']
                        
                        count_ok = 0
                        count_upd = 0
                        errores = []
                        total = len(df_upload)
                        
                        for i, row in df_upload.iterrows():
                            try:
                                # Conversión segura de datos
                                cod_val = str(row["codigo"]).strip()
                                desc_val = str(row["Descripcion"]).strip()
                                
                                # Si faltan columnas opcionales, poner valores por defecto
                                uni_val = str(row["Unidad"]) if "Unidad" in df_upload.columns else "Pzas"
                                
                                # Limpiar números (quitar $ o comas si las hay)
                                try: cant_val = float(str(row["Cantidad"]).replace(',', '').replace('$', '')) 
                                except: cant_val = 0.0
                                
                                try: min_val = float(str(row["stock_minimo"]).replace(',', '')) if "stock_minimo" in df_upload.columns else 5.0
                                except: min_val = 5.0

                                datos_row = {
                                    "codigo": cod_val,
                                    "Descripcion": desc_val,
                                    "Unidad": uni_val,
                                    "Cantidad": cant_val,
                                    "stock_minimo": min_val
                                }

                                if cod_val in mapa_ids:
                                    # UPDATE (Si ya existe)
                                    id_real = int(mapa_ids[cod_val])
                                    utils.supabase.table("Insumos").update(datos_row).eq("id", id_real).execute()
                                    count_upd += 1
                                else:
                                    # INSERT (Si es nuevo)
                                    utils.supabase.table("Insumos").insert(datos_row).execute()
                                    count_ok += 1
                                    
                            except Exception as e:
                                errores.append(f"{cod_val}: {e}")
                            
                            progress.progress((i+1)/total)
                        
                        progress.empty()
                        
                        if not errores:
                            st.success(f"✅ ¡Éxito Total! {count_ok} nuevos registros, {count_upd} actualizados.")
                            time.sleep(2); st.rerun()
                        else:
                            st.warning(f"⚠️ Proceso terminado. {count_ok} creados, {count_upd} actualizados.")
                            st.error(f"Se encontraron {len(errores)} errores. Verifica que no haya celdas vacías en los códigos.")
                    else:
                        st.error("⛔ No encuentro las columnas **'codigo'** y **'descripcion'**. Revisa los títulos de tu Excel.")
                        st.write("Columnas que leí:", list(df_upload.columns))
                except Exception as e:
                    st.error(f"Error procesando el texto: {e}")
            else:
                st.info("El cuadro de texto está vacío. Copia tus celdas de Excel y pégalas arriba.")

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

        if st.button("💾 Guardar Cambios en Inventario"):
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
                if pd.notna(row.get('id')): utils.supabase.table("Herramientas").update(d).eq("id", row['id']).execute()
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
                if pd.notna(row.get('id')): utils.supabase.table("Clientes").update(d).eq("id", row['id']).execute()
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
                if pd.notna(row.get('id')): utils.supabase.table("Proveedores").update(d).eq("id", row['id']).execute()
                else: utils.supabase.table("Proveedores").insert(d).execute()
            st.success("Actualizado."); time.sleep(1); st.rerun()
