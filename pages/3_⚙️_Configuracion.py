import streamlit as st
import pandas as pd
import utils 
import time
import datetime

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- 🔒 SEGURIDAD ACTIVADA ---
utils.validar_login()
# -----------------------------

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores"]
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
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nombre obligatorio")

    with t2:
        column_config = {
            "id": st.column_config.NumberColumn(disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Nombre", width=None), 
            "puesto": st.column_config.SelectboxColumn("Puesto", options=["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"], width="small"),
            "fecha_ingreso": st.column_config.DateColumn("Ingreso", format="DD/MM/YYYY", width="small"),
            "activo": st.column_config.CheckboxColumn("Activo", width="small"),
            "anio_nacimiento": st.column_config.TextColumn("Año", width="small"),
            "domicilio": st.column_config.TextColumn("Domicilio", width="medium"),
            "curp": st.column_config.TextColumn("CURP", width="small"),
            "rfc": st.column_config.TextColumn("RFC", width="small")
        }
        
        cols_ver = ["id", "nombre", "puesto", "anio_nacimiento", "domicilio", "curp", "rfc", "fecha_ingreso", "activo"]
        cols_reales = [c for c in cols_ver if c in df.columns]

        edited_df = st.data_editor(
            df[cols_reales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True, 
            key="editor_personal"
        )

        if st.button("💾 Actualizar Personal"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
                    if "fecha_ingreso" in datos and datos["fecha_ingreso"]:
                         datos["fecha_ingreso"] = str(datos["fecha_ingreso"])

                    if pd.notna(row["id"]):
                        utils.supabase.table("Personal").update(datos).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table("Personal").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Base actualizada")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# 2. INSUMOS
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            if "Descripcion" not in df.columns: df["Descripcion"] = None
            for col_sucia in ["Insumo", "nombre", "Nombre"]:
                if col_sucia in df.columns: df["Descripcion"] = df["Descripcion"].fillna(df[col_sucia])
            if "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
            else: df["codigo"] = df["codigo"].fillna(df["id"].astype(str))
            if "stock_minimo" not in df.columns: df["stock_minimo"] = 5.0
            if "Stock_Minimo" in df.columns: df["stock_minimo"] = df["stock_minimo"].fillna(df["Stock_Minimo"])
            
            cols_a_borrar = ["Insumo", "nombre", "Nombre", "Stock_Minimo"]
            df = df.drop(columns=[c for c in cols_a_borrar if c in df.columns], errors='ignore')

    except Exception as e: 
        st.error(f"Error de limpieza: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2 = st.tabs(["➕ Alta de Insumo", "📋 Inventario Maestro"])

    with t1:
        with st.form("alta_insumo", clear_on_submit=True):
            st.write("Datos del Insumo")
            col_cod, col_nom = st.columns([1, 3]) 
            nuevo_codigo = col_cod.text_input("Código / SKU", placeholder="Ej. HEM-CL-001", help="Código único alfanumérico")
            nuevo_nombre = col_nom.text_input("Descripción del Insumo")
            
            c1, c2, c3 = st.columns(3)
            nueva_unidad = c1.selectbox("Unidad", lista_unidades)
            nueva_cant = c2.number_input("Cantidad", min_value=0.0, step=1.0)
            nuevo_min = c3.number_input("Stock Mínimo", value=5.0)
            
            if st.form_submit_button("Guardar Insumo"):
                if nuevo_nombre and nuevo_codigo:
                    duplicado_codigo = False
                    if not df.empty:
                        if nuevo_codigo.strip() in df["codigo"].astype(str).str.strip().values:
                            st.error(f"⛔ Error: El código '{nuevo_codigo}' ya existe.")
                            duplicado_codigo = True
                    
                    if not duplicado_codigo:
                        try:
                            datos_insert = {
                                "codigo": nuevo_codigo, "Descripcion": nuevo_nombre, "Insumo": nuevo_nombre,
                                "Unidad": nueva_unidad, "Cantidad": nueva_cant, "stock_minimo": nuevo_min
                            }
                            utils.supabase.table("Insumos").insert(datos_insert).execute()
                            st.success(f"✅ Insumo {nuevo_codigo} agregado.")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            if "column \"Insumo\"" in str(e):
                                datos_insert.pop("Insumo")
                                utils.supabase.table("Insumos").insert(datos_insert).execute()
                                st.success(f"✅ Insumo {nuevo_codigo} agregado.")
                                st.rerun()
                            else: st.error(f"Error al guardar: {e}")
                else: st.warning("Código y Descripción obligatorios.")

    with t2:
        col_search, _ = st.columns([1, 1])
        busqueda = col_search.text_input("🔍 Buscar Insumo", placeholder="Escribe código o descripción...")

        df_display = df.copy()
        if busqueda:
            mask = (df_display["codigo"].astype(str).str.contains(busqueda, case=False, na=False) | 
                    df_display["Descripcion"].astype(str).str.contains(busqueda, case=False, na=False))
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
            
        edited_df = st.data_editor(
            df_display[cols_ver], column_config=column_config, num_rows="dynamic",
            use_container_width=True, height=500, key="editor_insumos_codigos_v3"
        )

        if st.button("💾 Guardar Cambios en Inventario"):
            codigos = edited_df["codigo"].astype(str).tolist()
            if len(codigos) != len(set(codigos)): st.error("⛔ Error: Códigos duplicados.")
            else:
                bar = st.progress(0, text="Guardando...")
                total = len(edited_df)
                for index, row in edited_df.iterrows():
                    try:
                        datos = {"codigo": row["codigo"], "Descripcion": row["Descripcion"], "Insumo": row["Descripcion"],
                                 "Cantidad": row["Cantidad"], "Unidad": row["Unidad"], "stock_minimo": row["stock_minimo"]}
                        if pd.notna(row["id"]): utils.supabase.table("Insumos").update(datos).eq("id", row["id"]).execute()
                        else: utils.supabase.table("Insumos").insert(datos).execute()
                    except:
                        try:
                            datos.pop("Insumo")
                            if pd.notna(row["id"]): utils.supabase.table("Insumos").update(datos).eq("id", row["id"]).execute()
                            else: utils.supabase.table("Insumos").insert(datos).execute()
                        except: pass
                    bar.progress((index+1)/total)
                bar.empty()
                st.success("✅ Actualizado.")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# ==========================================
# 3. HERRAMIENTAS
# ==========================================
elif opcion == "Herramientas":
    st.markdown("### 🛠️ Gestión de Herramientas")
    try:
        response = utils.supabase.table("Herramientas").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            if "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
            else: df["codigo"] = df["codigo"].fillna(df["id"].astype(str))
    except Exception as e:
        st.error(f"Error cargando herramientas: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "codigo", "Herramienta", "descripcion", "marca", "Estado"])

    t1, t2 = st.tabs(["➕ Alta Herramienta", "📋 Lista Completa"])

    with t1:
        with st.form("alta_herramienta", clear_on_submit=True):
            st.write("Ficha de Herramienta")
            c1, c2 = st.columns([1, 3])
            nuevo_sku = c1.text_input("Código SKU", placeholder="Ej. TAL-MAK-01")
            nuevo_nombre = c2.text_input("Nombre de la Herramienta")
            c3, c4, c5 = st.columns(3)
            nueva_marca = c3.text_input("Marca")
            nuevo_estado = c4.selectbox("Estado", ["BUEN ESTADO", "MAL ESTADO", "EN REPARACIÓN", "BAJA"])
            nueva_desc = c5.text_input("Descripción Corta")

            if st.form_submit_button("Guardar Herramienta"):
                if nuevo_nombre and nuevo_sku:
                    duplicado = False
                    if not df.empty:
                         if nuevo_sku.strip() in df["codigo"].astype(str).str.strip().values:
                             st.error(f"⛔ El código {nuevo_sku} ya existe.")
                             duplicado = True
                    if not duplicado:
                        try:
                            datos = {"codigo": nuevo_sku, "Herramienta": nuevo_nombre, "marca": nueva_marca,
                                     "Estado": nuevo_estado, "descripcion": nueva_desc}
                            utils.supabase.table("Herramientas").insert(datos).execute()
                            st.success(f"✅ {nuevo_nombre} agregado.")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Error al guardar: {e}")
                else: st.warning("Código y Nombre obligatorios.")

    with t2:
        col_b, _ = st.columns([1, 1])
        busqueda = col_b.text_input("🔍 Buscar Herramienta", placeholder="SKU, Nombre, Marca...")
        df_show = df.copy()
        if busqueda:
            mask = (df_show["codigo"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_show["Herramienta"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_show["marca"].astype(str).str.contains(busqueda, case=False, na=False))
            df_show = df_show[mask]

        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "codigo": st.column_config.TextColumn("Código SKU", required=True, width="medium"),
            "Herramienta": st.column_config.TextColumn("Nombre Herramienta", width=None),
            "descripcion": st.column_config.TextColumn("Descripción", width="medium"),
            "marca": st.column_config.TextColumn("Marca", width="small"),
            "Estado": st.column_config.SelectboxColumn("Estado", options=["BUEN ESTADO", "MAL ESTADO", "EN REPARACIÓN", "BAJA"], width="small")
        }
        cols_ver = ["id", "codigo", "Herramienta", "descripcion", "marca", "Estado"]
        for c in cols_ver:
             if c not in df_show.columns: df_show[c] = None

        edited_df = st.data_editor(df_show[cols_ver], column_config=column_config, num_rows="dynamic", use_container_width=True, height=500, key="editor_herramientas")

        if st.button("💾 Actualizar Herramientas"):
            skus = edited_df["codigo"].astype(str).tolist()
            if len(skus) != len(set(skus)): st.error("⛔ Error: Códigos SKU duplicados.")
            else:
                bar = st.progress(0, text="Guardando...")
                total = len(edited_df)
                for index, row in edited_df.iterrows():
                    try:
                        datos = {"codigo": row["codigo"], "Herramienta": row["Herramienta"], "descripcion": row["descripcion"],
                                 "marca": row["marca"], "Estado": row["Estado"]}
                        if pd.notna(row["id"]): utils.supabase.table("Herramientas").update(datos).eq("id", row["id"]).execute()
                        else: utils.supabase.table("Herramientas").insert(datos).execute()
                    except: pass
                    bar.progress((index+1)/total)
                bar.empty()
                st.success("✅ Lista actualizada.")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# ==========================================
# 4. CLIENTES
# ==========================================
elif opcion == "Clientes":
    st.markdown("### 🏢 Gestión de Clientes")
    try:
        response = utils.supabase.table("Clientes").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error cargando clientes: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "nombre", "direccion", "colonia", "codigo_postal", "rfc", "estado"])

    t1, t2 = st.tabs(["➕ Alta Cliente", "📋 Lista de Clientes"])

    with t1:
        with st.form("alta_cliente", clear_on_submit=True):
            st.write("Datos de la Empresa / Cliente")
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Nombre de la Empresa")
            nuevo_rfc = c2.text_input("RFC")
            c3, c4 = st.columns(2)
            nueva_direccion = c3.text_input("Domicilio (Calle y Número)")
            nueva_colonia = c4.text_input("Colonia")
            c5, c6 = st.columns(2)
            nuevo_cp = c5.text_input("Código Postal")
            nuevo_estado = c6.text_input("Estado")

            if st.form_submit_button("Guardar Cliente"):
                if nuevo_nombre:
                    try:
                        datos = {"nombre": nuevo_nombre, "direccion": nueva_direccion, "rfc": nuevo_rfc,
                                 "colonia": nueva_colonia, "codigo_postal": nuevo_cp, "estado": nuevo_estado}
                        utils.supabase.table("Clientes").insert(datos).execute()
                        st.success(f"✅ {nuevo_nombre} registrado.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Error al guardar: {e}")
                else: st.warning("Nombre obligatorio.")

    with t2:
        col_bus, _ = st.columns([1,1])
        busqueda = col_bus.text_input("🔍 Buscar Cliente", placeholder="Empresa o RFC...")
        df_show = df.copy()
        if busqueda:
             mask = (df_show["nombre"].astype(str).str.contains(busqueda, case=False, na=False) |
                     df_show["rfc"].astype(str).str.contains(busqueda, case=False, na=False))
             df_show = df_show[mask]

        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Empresa", width="medium", required=True),
            "direccion": st.column_config.TextColumn("Domicilio", width="medium"), 
            "colonia": st.column_config.TextColumn("Colonia", width="medium"),
            "codigo_postal": st.column_config.TextColumn("C.P.", width="small"),
            "rfc": st.column_config.TextColumn("RFC", width="medium"),
            "estado": st.column_config.TextColumn("Estado", width="small")
        }
        cols_ver = ["id", "nombre", "direccion", "colonia", "codigo_postal", "rfc", "estado"]
        for c in cols_ver:
            if c not in df_show.columns: df_show[c] = None

        edited_df = st.data_editor(df_show[cols_ver], column_config=column_config, num_rows="dynamic", use_container_width=True, key="editor_clientes")

        if st.button("💾 Actualizar Clientes"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {"nombre": row["nombre"], "direccion": row["direccion"], "colonia": row["colonia"],
                             "codigo_postal": row["codigo_postal"], "rfc": row["rfc"], "estado": row["estado"]}
                    if pd.notna(row["id"]): utils.supabase.table("Clientes").update(datos).eq("id", row["id"]).execute()
                    else: utils.supabase.table("Clientes").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Actualizado.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# 5. PROVEEDORES
# ==========================================
elif opcion == "Proveedores":
    st.markdown("### 🚚 Gestión de Proveedores")
    try:
        response = utils.supabase.table("Proveedores").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            if "empresa" in df.columns and "nombre" not in df.columns:
                 df["nombre"] = df["empresa"] 
    except Exception as e:
        st.error(f"Error cargando proveedores: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "nombre", "domicilio", "colonia", "rfc", "codigo_postal"])

    t1, t2 = st.tabs(["➕ Alta Proveedor", "📋 Lista de Proveedores"])

    with t1:
        with st.form("alta_proveedor", clear_on_submit=True):
            st.write("Datos del Proveedor")
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Nombre / Empresa")
            nuevo_rfc = c2.text_input("RFC")
            c3, c4 = st.columns(2)
            nuevo_dom = c3.text_input("Domicilio (Calle y Número)")
            nueva_col = c4.text_input("Colonia")
            c5 = st.columns(1)[0]
            nuevo_cp = c5.text_input("Código Postal")

            if st.form_submit_button("Guardar Proveedor"):
                if nuevo_nombre:
                    try:
                        datos = {"domicilio": nuevo_dom, "colonia": nueva_col, "rfc": nuevo_rfc, "codigo_postal": nuevo_cp}
                        datos["nombre"] = nuevo_nombre
                        datos["empresa"] = nuevo_nombre 
                        utils.supabase.table("Proveedores").insert(datos).execute()
                        st.success(f"✅ {nuevo_nombre} registrado.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        if "column \"nombre\"" in str(e):
                             datos.pop("nombre")
                             utils.supabase.table("Proveedores").insert(datos).execute()
                             st.success("✅ Registrado.")
                             st.rerun()
                        elif "column \"empresa\"" in str(e):
                             datos.pop("empresa")
                             utils.supabase.table("Proveedores").insert(datos).execute()
                             st.success("✅ Registrado.")
                             st.rerun()
                        else: st.error(f"Error al guardar: {e}")
                else: st.warning("El Nombre es obligatorio.")

    with t2:
        col_bus, _ = st.columns([1,1])
        busqueda = col_bus.text_input("🔍 Buscar Proveedor", placeholder="Nombre o RFC...")
        df_show = df.copy()
        if busqueda:
             mask = (df_show["nombre"].astype(str).str.contains(busqueda, case=False, na=False) |
                     df_show["rfc"].astype(str).str.contains(busqueda, case=False, na=False))
             df_show = df_show[mask]

        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Proveedor", width="medium", required=True),
            "domicilio": st.column_config.TextColumn("Domicilio", width="medium"), 
            "colonia": st.column_config.TextColumn("Colonia", width="medium"),
            "rfc": st.column_config.TextColumn("RFC", width="medium"),
            "codigo_postal": st.column_config.TextColumn("C.P.", width="small")
        }
        cols_ver = ["id", "nombre", "domicilio", "colonia", "rfc", "codigo_postal"]
        for c in cols_ver:
            if c not in df_show.columns: df_show[c] = None

        edited_df = st.data_editor(df_show[cols_ver], column_config=column_config, num_rows="dynamic", use_container_width=True, key="editor_proveedores")

        if st.button("💾 Actualizar Proveedores"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {"domicilio": row["domicilio"], "colonia": row["colonia"],
                             "rfc": row["rfc"], "codigo_postal": row["codigo_postal"],
                             "nombre": row["nombre"], "empresa": row["nombre"]}
                    if pd.notna(row["id"]): utils.supabase.table("Proveedores").update(datos).eq("id", row["id"]).execute()
                    else: utils.supabase.table("Proveedores").insert(datos).execute()
                except: 
                     try:
                        datos.pop("nombre")
                        if pd.notna(row["id"]): utils.supabase.table("Proveedores").update(datos).eq("id", row["id"]).execute()
                        else: utils.supabase.table("Proveedores").insert(datos).execute()
                     except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Actualizado.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
