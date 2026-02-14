import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import os
import utils 
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login() 
# --------------------

supabase = utils.supabase 

# --- CLASE PDF PERSONALIZADA ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33) 
        else:
            self.set_font('Arial', 'B', 20)
            self.cell(40, 10, 'HEMORE', 0, 0, 'L')
        self.ln(1)

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', '', 8)
        self.cell(90, 0, '_______________________________', 0, 0, 'C')
        self.cell(10, 0, '', 0, 0)
        self.cell(90, 0, '_______________________________', 0, 1, 'C')
        self.ln(4)
        self.cell(90, 5, 'Entrega / Autoriza', 0, 0, 'C')
        self.cell(10, 5, '', 0, 0)
        self.cell(90, 5, 'Recibe / Caja', 0, 1, 'C')
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- GENERADORES DE PDF ---
def generar_pdf_entrega(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Recibo de Entrega', 0, 1, 'C')
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    _bloque_cajas_prov_cli(pdf, "Proveedor (Origen)", datos_cabecera['prov_texto'], "Cliente (Destino)", datos_cabecera['cli_texto'])
    _dibujar_tabla_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Constancia de Entrada', 0, 1, 'C')
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    _bloque_cajas_prov_cli(pdf, "Proveedor (Origen)", datos_cabecera['prov_texto'], "Receptor (Destino)", datos_cabecera['hemore_texto'])
    _dibujar_tabla_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_dinero(datos_cabecera, df_conceptos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Recibo de Dinero', 0, 1, 'C')
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    pdf.set_y(45)
    pdf.set_fill_color(240, 240, 240); pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "  Información del Pago", 1, 1, 'L', True)
    pdf.set_font('Arial', '', 10); pdf.cell(40, 8, "Recibimos de:", 0, 0)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 8, datos_cabecera['cliente'], 0, 1)
    pdf.set_font('Arial', '', 10); pdf.cell(40, 8, "La cantidad de:", 0, 0)
    total = df_conceptos["Monto"].sum()
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 8, f"$ {total:,.2f} MXN", 0, 1)
    pdf.set_font('Arial', '', 10); pdf.cell(40, 8, "Método de Pago:", 0, 0)
    pdf.cell(0, 8, datos_cabecera['metodo'], 0, 1); pdf.ln(5)
    pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(200, 200, 200)
    pdf.cell(140, 8, "Concepto / Descripción", 1, 0, 'C', True); pdf.cell(50, 8, "Importe", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 9)
    for index, row in df_conceptos.iterrows():
        pdf.cell(140, 8, str(row['Concepto']), 1, 0, 'L')
        pdf.cell(50, 8, f"$ {row['Monto']:,.2f}", 1, 1, 'R')
    pdf.set_font('Arial', 'B', 9); pdf.cell(140, 8, "TOTAL RECIBIDO", 1, 0, 'R'); pdf.cell(50, 8, f"$ {total:,.2f}", 1, 1, 'R')
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

# --- HELPERS PDF ---
def _bloque_folio_fecha(pdf, folio, fecha):
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25); pdf.cell(25, 6, "Folio:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(folio), 0, 1, 'L')
    pdf.set_xy(140, 31); pdf.set_font('Arial', 'B', 10); pdf.cell(25, 6, "Fecha:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, fecha, 0, 1, 'L')

def _bloque_cajas_prov_cli(pdf, titulo1, texto1, titulo2, texto2):
    pdf.set_y(45); y_start = pdf.get_y()
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, f" {titulo1}", 1, 0, 'L', True); pdf.cell(95, 6, f" {titulo2}", 1, 1, 'L', True)
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 25, "", 1, 0); pdf.cell(95, 25, "", 1, 0)
    pdf.set_xy(12, y_start + 8); pdf.multi_cell(90, 4, texto1)
    pdf.set_xy(107, y_start + 8); pdf.multi_cell(90, 4, texto2)
    pdf.set_xy(10, y_start + 35)

def _dibujar_tabla_productos(pdf, oc, df_productos):
    pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 7, "O.C.", 1, 0, 'C', True); pdf.cell(30, 7, "Codigo", 1, 0, 'C', True)
    pdf.cell(95, 7, "Descripcion", 1, 0, 'C', True); pdf.cell(20, 7, "Color", 1, 0, 'C', True); pdf.cell(20, 7, "Cant", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8)
    for index, row in df_productos.iterrows():
        pdf.cell(25, 7, str(oc), 1, 0, 'C'); pdf.cell(30, 7, str(row['Código']), 1, 0, 'C')
        pdf.cell(95, 7, str(row['Descripción'])[:55], 1, 0, 'L'); pdf.cell(20, 7, str(row['Color']), 1, 0, 'C'); pdf.cell(20, 7, str(row['Cantidad']), 1, 1, 'C')

def _bloque_observaciones(pdf, texto):
    pdf.ln(8); pdf.set_font('Arial', 'B', 9); pdf.write(5, "Observaciones: "); pdf.set_font('Arial', '', 9)
    pdf.write(5, texto if texto else "_"*110)

def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer: df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# ==========================================
# MENÚ LATERAL
# ==========================================
st.sidebar.title("🏭 Almacén Central")
opcion_almacen = st.sidebar.radio(
    "Selecciona Operación:",
    ["Insumos (Consumibles)", "Herramientas (Activos)", "Recibos de Entrega OC", "Entrada de Material", "Recibos de Dinero"]
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: INSUMOS (CON MEJORA DE UBICACIÓN)
# ==================================================
if "Insumos" in opcion_almacen:
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        if not df_ins.empty:
            df_ins.columns = df_ins.columns.str.lower()
            if "descripcion" not in df_ins.columns: df_ins["descripcion"] = "Sin Nombre"
            if "cantidad" not in df_ins.columns: df_ins["cantidad"] = 0
            if "unidad" not in df_ins.columns: df_ins["unidad"] = "Pzas"
            # Aseguramos que 'ubicacion' exista para mostrarla
            if "ubicacion" not in df_ins.columns: df_ins["ubicacion"] = "S/U"

        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except Exception as e: 
        st.error(f"Error cargando base de datos: {e}")
        df_ins = pd.DataFrame()
        lista_personal = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial"])
    
    with tab_op:
        if df_ins.empty: st.warning("No hay insumos registrados. Ve a Configuración para cargar datos.")
        else:
            tipo_operacion = st.radio("Acción:", ["📤 Entrega (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True)
            c_form, c_info = st.columns([2, 1])
            with c_form:
                lista_busqueda = [f"{row['codigo']} | {row['descripcion']}" for i, row in df_ins.iterrows()]
                seleccion = st.selectbox("Buscar:", lista_busqueda)
                
                if seleccion:
                    codigo_sel = seleccion.split(" | ")[0]
                    item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                    cant_mov = st.number_input("Cantidad", min_value=1.0, value=1.0)
                    
                    if "Entrega" in tipo_operacion:
                        responsable = st.selectbox("Entregar a:", lista_personal)
                        if st.button("Confirmar Salida", type="primary"):
                            if item_actual['cantidad'] >= cant_mov:
                                new_st = float(item_actual['cantidad'] - cant_mov) # MEJORA: float nativo
                                supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Salida", "cantidad": float(cant_mov), "responsable": responsable}).execute()
                                except: pass
                                st.success("✅ Salida registrada"); time.sleep(1); st.rerun()
                            else: st.error("Stock insuficiente")
                    else:
                        if st.button("Confirmar Entrada"):
                            new_st = float(item_actual['cantidad'] + cant_mov) # MEJORA: float nativo
                            supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                            try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Re-stock", "cantidad": float(cant_mov), "responsable": "Almacén"}).execute()
                            except: pass
                            st.success("✅ Entrada registrada"); time.sleep(1); st.rerun()
            
            with c_info: 
                if seleccion: 
                    st.metric("Stock Actual", item_actual['cantidad'])
                    st.write(f"📍 Ubicación: {item_actual['ubicacion']}")

    with tab_exist:
        if not df_ins.empty:
            try:
                # MEJORA SOLICITADA: Incluir Ubicación
                df_view = df_ins[["codigo", "descripcion", "cantidad", "unidad", "ubicacion"]].rename(columns={"codigo": "Código", "descripcion": "Descripción", "cantidad": "Stock", "unidad": "Unidad", "ubicacion": "Ubicación"})
                excel_data = convertir_df_a_excel(df_view)
                st.download_button("📥 Descargar Existencias", excel_data, "Existencias.xlsx")
                st.dataframe(df_view, use_container_width=True)
            except Exception as e: st.error(f"Error visualizando: {e}")
        else: st.info("El inventario está vacío.")

    with tab_hist:
        try:
            h = pd.DataFrame(supabase.table("Historial_Insumos").select("*").order("id", desc=True).limit(100).execute().data)
            if not h.empty:
                cols_deseadas = ["fecha", "codigo", "descripcion", "tipo_movimiento", "cantidad", "responsable"]
                cols_reales = [c for c in cols_deseadas if c in h.columns]
                h_final = h[cols_reales].rename(columns={"fecha": "Fecha", "codigo": "Código", "descripcion": "Descripción", "tipo_movimiento": "Movimiento", "cantidad": "Cant", "responsable": "Responsable"})
                st.dataframe(h_final, use_container_width=True, hide_index=True)
            else: st.info("No hay movimientos registrados.")
        except Exception as e: st.error(f"Error cargando historial: {e}")

# ==================================================
# 🔧 OPCIÓN 2: HERRAMIENTAS
# ==================================================
elif "Herramientas" in opcion_almacen:
    try:
        df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: df_her = pd.DataFrame(); lista_personal = []

    if df_her.empty: df_her = pd.DataFrame(columns=["id", "codigo", "Herramienta", "Responsable", "Estado"])
    if "Responsable" not in df_her.columns: df_her["Responsable"] = "Bodega"
    df_her["Responsable"].fillna("Bodega", inplace=True)

    tab1, tab2, tab3 = st.tabs(["Movimientos", "Inventario", "Historial"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.info("Prestar")
            bodega = df_her[df_her["Responsable"]=="Bodega"]
            if not bodega.empty:
                sel = st.selectbox("Herramienta", bodega["Herramienta"].tolist())
                resp = st.selectbox("A quien", lista_personal)
                if st.button("Prestar"):
                    id_h = bodega[bodega["Herramienta"]==sel].iloc[0]["id"]
                    supabase.table("Herramientas").update({"Responsable": resp}).eq("id", int(id_h)).execute()
                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": sel, "Movimiento": "Préstamo", "Responsable": resp}).execute()
                    except: pass
                    st.success("Prestado"); time.sleep(1); st.rerun()
        with c2:
            st.warning("Devolver")
            prestadas = df_her[df_her["Responsable"]!="Bodega"]
            if not prestadas.empty:
                sel_d = st.selectbox("Devolver", prestadas["Herramienta"].tolist())
                if st.button("Devolver"):
                    id_h = prestadas[prestadas["Herramienta"]==sel_d].iloc[0]["id"]
                    supabase.table("Herramientas").update({"Responsable": "Bodega"}).eq("id", int(id_h)).execute()
                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": sel_d, "Movimiento": "Devolución", "Responsable": "Bodega"}).execute()
                    except: pass
                    st.success("Devuelto"); time.sleep(1); st.rerun()
    with tab2: st.dataframe(df_her, use_container_width=True)
    with tab3:
        try:
            h_her = pd.DataFrame(supabase.table("Historial_Herramientas").select("*").order("id", desc=True).limit(100).execute().data)
            st.dataframe(h_her, use_container_width=True)
        except: pass

# ==================================================
# 📑 OPCIÓN 3: RECIBOS DE ENTREGA OC
# ==================================================
elif "Recibos" in opcion_almacen:
    st.markdown("### 📑 Recibos de Entrega (Salidas a Clientes)")
    try:
        res_cli = supabase.table("Clientes").select("*").execute(); df_clientes = pd.DataFrame(res_cli.data)
        lista_nombres_cli = df_clientes['nombre'].tolist() if not df_clientes.empty else []
        res_prov = supabase.table("Proveedores").select("*").execute(); df_proveedores = pd.DataFrame(res_prov.data)
        col_p_name = 'empresa' if 'empresa' in df_proveedores.columns else 'nombre'
        lista_nombres_prov = df_proveedores[col_p_name].tolist() if not df_proveedores.empty else []
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: lista_nombres_cli = []; lista_nombres_prov = []; lista_personal = []; df_clientes = pd.DataFrame(); df_proveedores = pd.DataFrame()

    tab_nuevo, tab_historial = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    with tab_nuevo:
        with st.container(border=True):
            st.subheader("Datos de la Entrega")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_input = c1.text_input("Orden de Compra (O.C.)", placeholder="Ej. 2183")
            fecha_input = c2.date_input("Fecha", value=datetime.now().date())
            prov_input = c3.selectbox("Proveedor (Origen):", lista_nombres_prov, index=None, placeholder="Hemore...")
            cliente_input = st.selectbox("Cliente (Destino):", lista_nombres_cli, index=None)
            
            st.divider()
            if "data_recibo" not in st.session_state: st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            edited_df = st.data_editor(st.session_state["data_recibo"], num_rows="dynamic", use_container_width=True, column_config={"Cantidad": st.column_config.NumberColumn(min_value=0)})
            observaciones = st.text_area("Observaciones:")
            col_firmas, col_accion = st.columns([1, 1])
            usuario_input = col_firmas.selectbox("Registrado por:", lista_personal)
            
            if col_accion.button("💾 Guardar y PDF", type="primary", use_container_width=True):
                if oc_input and cliente_input and prov_input and not edited_df.empty:
                    items = edited_df[edited_df["Código"] != ""]
                    if not items.empty:
                        for i, row in items.iterrows():
                            # MEJORA: float() nativo para evitar error int64
                            supabase.table("Recibos_OC").insert({"fecha": fecha_input.isoformat(), "oc": str(oc_input), "cliente": str(cliente_input), "proveedor": str(prov_input), "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), "color": str(row["Color"]), "cantidad": float(row["Cantidad"]), "usuario": str(usuario_input), "observaciones": str(observaciones)}).execute()
                        
                        cli_data = df_clientes[df_clientes['nombre'] == cliente_input].iloc[0]
                        prov_data = df_proveedores[df_proveedores[col_p_name] == prov_input].iloc[0]
                        try: last_id = supabase.table("Recibos_OC").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        prov_text = f"{prov_input}\n{prov_data.get('domicilio', '')}\nRFC: {prov_data.get('rfc', '')}"
                        cli_text = f"{cliente_input}\n{cli_data.get('direccion', '')}\nRFC: {cli_data.get('rfc', '')}"
                        
                        datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_texto": prov_text, "cli_texto": cli_text}
                        pdf_bytes = generar_pdf_entrega(datos_pdf, items, last_id)
                        st.success("Guardado."); st.download_button("🖨️ PDF", pdf_bytes, f"Recibo_{oc_input}.pdf", "application/pdf")
                    else: st.warning("Tabla vacía.")
                else: st.warning("Faltan datos.")

    with tab_historial:
        try:
            h = pd.DataFrame(supabase.table("Recibos_OC").select("*").order("id", desc=True).limit(200).execute().data)
            if not h.empty:
                st.dataframe(h[["oc", "fecha", "cliente", "proveedor", "codigo", "descripcion", "cantidad", "usuario"]], use_container_width=True, hide_index=True)
        except: pass

# ==================================================
# 📥 OPCIÓN 4: ENTRADA DE MATERIAL (CON MEJORA DE SERIALIZACIÓN)
# ==================================================
elif "Entrada" in opcion_almacen:
    st.markdown("### 📥 Registro de Entrada de Material")
    try:
        res_prov = supabase.table("Proveedores").select("*").execute(); df_provs = pd.DataFrame(res_prov.data)
        col_p_name = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
        lista_provs = df_provs[col_p_name].tolist() if not df_provs.empty else []
        df_pers = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_pers = df_pers['nombre'].tolist() if not df_pers.empty else []
    except: lista_provs = []; lista_pers = []; df_provs = pd.DataFrame()

    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial"])
    with tab_ent_new:
        with st.container(border=True):
            st.subheader("Datos de la Entrada")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_in = c1.text_input("Orden de Compra / Remisión", placeholder="Folio del Proveedor")
            fecha_in = c2.date_input("Fecha de Llegada", value=datetime.now().date())
            prov_in = c3.selectbox("Proveedor (Origen):", lista_provs, index=None)
            
            st.divider()
            if "data_entrada" not in st.session_state: st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True)
            obs_in = st.text_area("Observaciones de llegada:", key="obs_in")
            col_f, col_a = st.columns([1, 1])
            user_in = col_f.selectbox("Recibido por (Hemore):", lista_pers, key="user_in")
            
            if col_a.button("💾 Registrar Entrada y PDF", type="primary", use_container_width=True):
                if oc_in and prov_in and not edited_df_in.empty:
                    items_in = edited_df_in[edited_df_in["Código"] != ""]
                    if not items_in.empty:
                        for i, row in items_in.iterrows():
                            # MEJORA: float() nativo para corregir error int64
                            supabase.table("Entradas_Material").insert({"fecha": fecha_in.isoformat(), "oc": str(oc_in), "proveedor": str(prov_in), "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), "color": str(row["Color"]), "cantidad": float(row["Cantidad"]), "usuario": str(user_in), "observaciones": str(obs_in)}).execute()
                        
                        prov_data = df_provs[df_provs[col_p_name] == prov_in].iloc[0]
                        try: last_id = supabase.table("Entradas_Material").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        prov_text = f"{prov_in}\n{prov_data.get('domicilio', '')}\nRFC: {prov_data.get('rfc', '')}"
                        hemore_text = "HEMORE INDUSTRIAS\nAlmacén Central"
                        datos_pdf = {"fecha": fecha_in.strftime("%d/%m/%Y"), "oc": oc_in, "observaciones": obs_in, "prov_texto": prov_text, "hemore_texto": hemore_text}
                        pdf_bytes = generar_pdf_entrada(datos_pdf, items_in, last_id)
                        st.success("✅ Entrada Registrada."); st.download_button("🖨️ PDF", pdf_bytes, f"Entrada_{oc_in}.pdf", "application/pdf")
                    else: st.warning("Tabla vacía.")

    with tab_ent_hist:
        try:
            h_in = pd.DataFrame(supabase.table("Entradas_Material").select("*").order("id", desc=True).limit(200).execute().data)
            if not h_in.empty:
                st.dataframe(h_in[["oc", "fecha", "proveedor", "codigo", "descripcion", "cantidad", "usuario"]], use_container_width=True, hide_index=True)
        except: pass

# ==================================================
# 💰 OPCIÓN 5: RECIBOS DE DINERO (CON MEJORA DE SERIALIZACIÓN)
# ==================================================
elif "Dinero" in opcion_almacen:
    st.markdown("### 💰 Recibos de Dinero")
    try:
        res_cli = supabase.table("Clientes").select("nombre").execute(); df_c = pd.DataFrame(res_cli.data)
        lista_clientes = df_c['nombre'].tolist() if not df_c.empty else []
        df_p = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_p = df_p['nombre'].tolist() if not df_p.empty else []
    except: lista_clientes = []; lista_p = []

    tab_money_new, tab_money_hist = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    with tab_money_new:
        with st.container(border=True):
            st.subheader("Detalles del Pago")
            c1, c2 = st.columns(2)
            fecha_pago = c1.date_input("Fecha de Recepción", value=datetime.now().date())
            cliente_pago = c2.selectbox("Recibimos de (Cliente):", lista_clientes, index=None)
            metodo = st.selectbox("Método de Pago", ["Transferencia", "Efectivo", "Cheque", "Depósito"], index=0)
            usuario_pago = st.selectbox("Recibe (Hemore):", lista_p)
            
            st.divider()
            if "data_money" not in st.session_state: st.session_state["data_money"] = pd.DataFrame([{"Concepto": "", "Monto": 0.0}], columns=["Concepto", "Monto"])
            edited_money = st.data_editor(st.session_state["data_money"], num_rows="dynamic", use_container_width=True)
            total_money = edited_money["Monto"].sum()
            st.markdown(f"#### Total: :green[$ {total_money:,.2f}]")
            obs_money = st.text_area("Observaciones:", key="obs_money")
            
            if st.button("💾 Generar Recibo", type="primary", use_container_width=True):
                if cliente_pago and total_money > 0:
                    items_m = edited_money[edited_money["Concepto"] != ""]
                    if not items_m.empty:
                        for i, row in items_m.iterrows():
                            # MEJORA: float() nativo para corregir error int64
                            supabase.table("Recibos_Dinero").insert({"fecha": fecha_pago.isoformat(), "cliente": str(cliente_pago), "concepto": str(row["Concepto"]), "monto": float(row["Monto"]), "metodo_pago": str(metodo), "usuario": str(usuario_pago), "observaciones": str(obs_money)}).execute()
                        
                        try: last_id = supabase.table("Recibos_Dinero").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        datos_pdf = {"fecha": fecha_pago.strftime("%d/%m/%Y"), "cliente": cliente_pago, "metodo": metodo, "observaciones": obs_money}
                        pdf_bytes = generar_pdf_dinero(datos_pdf, items_m, last_id)
                        st.success("✅ Recibo Generado."); st.download_button("🖨️ PDF", pdf_bytes, f"Recibo_Dinero_{last_id}.pdf", "application/pdf")
                else: st.warning("Datos faltantes.")

    with tab_money_hist:
        try:
            h_mon = pd.DataFrame(supabase.table("Recibos_Dinero").select("*").order("id", desc=True).limit(200).execute().data)
            if not h_mon.empty:
                st.dataframe(h_mon[["id", "fecha", "cliente", "concepto", "monto", "metodo_pago", "usuario"]], use_container_width=True, hide_index=True)
        except: pass
