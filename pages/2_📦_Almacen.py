import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import os
import utils 
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central - HEMORE", page_icon="📦", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login() 
supabase = utils.supabase 

# ==========================================
# 🛠️ MEJORA: CARGA DE CATÁLOGOS CON CACHÉ
# ==========================================
@st.cache_data(ttl=300)
def cargar_catalogos():
    try:
        p = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        c = pd.DataFrame(supabase.table("Clientes").select("*").execute().data)
        pr = pd.DataFrame(supabase.table("Proveedores").select("*").execute().data)
        return p, c, pr
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_personal_cat, df_clientes_cat, df_proveedores_cat = cargar_catalogos()

# --- HELPERS PARA LISTAS ---
lista_personal = df_personal_cat['nombre'].tolist() if not df_personal_cat.empty else []
lista_clientes = df_clientes_cat['nombre'].tolist() if not df_clientes_cat.empty else []
col_p = 'empresa' if not df_proveedores_cat.empty and 'empresa' in df_proveedores_cat.columns else 'nombre'
lista_proveedores = df_proveedores_cat[col_p].tolist() if not df_proveedores_cat.empty else []

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
    return pdf.output(dest='S').encode('latin-1', errors='replace')

def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Constancia de Entrada', 0, 1, 'C')
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    _bloque_cajas_prov_cli(pdf, "Proveedor (Origen)", datos_cabecera['prov_texto'], "Receptor (Destino)", datos_cabecera['hemore_texto'])
    _dibujar_tabla_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1', errors='replace')

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
    return pdf.output(dest='S').encode('latin-1', errors='replace')

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
# 🧱 OPCIÓN 1: INSUMOS (INCLUYE UBICACIÓN)
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
            if "ubicacion" not in df_ins.columns: df_ins["ubicacion"] = "S/U"
    except Exception as e: 
        st.error(f"Error cargando base de datos: {e}")
        df_ins = pd.DataFrame()

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial"])
    
    with tab_op:
        if df_ins.empty: st.warning("No hay insumos registrados.")
        else:
            tipo_operacion = st.radio("Acción:", ["📤 Entrega (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True)
            c_form, c_info = st.columns([2, 1])
            with c_form:
                lista_busqueda = [f"{row['codigo']} | {row['descripcion']}" for i, row in df_ins.iterrows()]
                seleccion = st.selectbox("Buscar:", lista_busqueda)
                
                if seleccion:
                    codigo_sel = seleccion.split(" | ")[0]
                    item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                    cant_mov = st.number_input("Cantidad", min_value=0.1, value=1.0)
                    
                    if "Entrega" in tipo_operacion:
                        responsable = st.selectbox("Entregar a:", lista_personal)
                        if st.button("Confirmar Salida", type="primary"):
                            if item_actual['cantidad'] >= cant_mov:
                                try:
                                    new_st = float(item_actual['cantidad'] - cant_mov)
                                    supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                    supabase.table("Historial_Insumos").insert({
                                        "fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), 
                                        "codigo": str(item_actual['codigo']), 
                                        "descripcion": str(item_actual['descripcion']), 
                                        "tipo_movimiento": "Salida", 
                                        "cantidad": float(cant_mov), 
                                        "responsable": responsable
                                    }).execute()
                                    st.success("✅ Salida registrada"); time.sleep(1); st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                            else: st.error("Stock insuficiente")
                    else:
                        if st.button("Confirmar Entrada"):
                            try:
                                new_st = float(item_actual['cantidad'] + cant_mov)
                                supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                supabase.table("Historial_Insumos").insert({
                                    "fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), 
                                    "codigo": str(item_actual['codigo']), 
                                    "descripcion": str(item_actual['descripcion']), 
                                    "tipo_movimiento": "Re-stock", 
                                    "cantidad": float(cant_mov), 
                                    "responsable": "Almacén"
                                }).execute()
                                st.success("✅ Entrada registrada"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
            
            with c_info: 
                if seleccion: 
                    st.metric("Stock Actual", f"{item_actual['cantidad']} {item_actual['unidad']}")
                    st.info(f"📍 Ubicación: {item_actual['ubicacion']}")

    with tab_exist:
        if not df_ins.empty:
            df_view = df_ins[["codigo", "descripcion", "cantidad", "unidad", "ubicacion"]].rename(columns={
                "codigo": "Código", "descripcion": "Descripción", "cantidad": "Stock", "unidad": "Unidad", "ubicacion": "Ubicación"
            })
            st.download_button("📥 Excel", convertir_df_a_excel(df_view), "Existencias.xlsx")
            st.dataframe(df_view, use_container_width=True, hide_index=True)

# ==================================================
# 📑 OPCIÓN 3: RECIBOS DE ENTREGA OC (CORREGIDO SERIALIZACIÓN)
# ==================================================
elif "Recibos" in opcion_almacen:
    st.markdown("### 📑 Recibos de Entrega (Salidas a Clientes)")
    tab_nuevo, tab_historial = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    with tab_nuevo:
        with st.container(border=True):
            st.subheader("Datos de la Entrega")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_input = c1.text_input("Orden de Compra (O.C.)")
            fecha_input = c2.date_input("Fecha", value=datetime.now().date())
            prov_input = c3.selectbox("Proveedor (Origen):", lista_proveedores, index=None)
            cliente_input = st.selectbox("Cliente (Destino):", lista_clientes, index=None)
            
            st.divider()
            if "data_recibo" not in st.session_state: 
                st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            
            edited_df = st.data_editor(st.session_state["data_recibo"], num_rows="dynamic", use_container_width=True)
            observaciones = st.text_area("Observaciones:")
            col_firmas, col_accion = st.columns([1, 1])
            usuario_input = col_firmas.selectbox("Registrado por:", lista_personal)
            
            if col_accion.button("💾 Guardar y PDF", type="primary", use_container_width=True):
                if oc_input and cliente_input and prov_input:
                    items = edited_df[edited_df["Código"] != ""]
                    if not items.empty:
                        try:
                            ids_generados = []
                            for i, row in items.iterrows():
                                # MEJORA: Casting float() y str() para JSON
                                res = supabase.table("Recibos_OC").insert({
                                    "fecha": fecha_input.isoformat(), "oc": str(oc_input), 
                                    "cliente": str(cliente_input), "proveedor": str(prov_input), 
                                    "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), 
                                    "color": str(row["Color"]), "cantidad": float(row["Cantidad"]), 
                                    "usuario": str(usuario_input), "observaciones": str(observaciones)
                                }).execute()
                                if res.data: ids_generados.append(res.data[0]['id'])
                            
                            folio_real = ids_generados[0] if ids_generados else 1
                            cli_data = df_clientes_cat[df_clientes_cat['nombre'] == cliente_input].iloc[0]
                            prov_data = df_proveedores_cat[df_proveedores_cat[col_p] == prov_input].iloc[0]
                            
                            prov_text = f"{prov_input}\n{prov_data.get('domicilio', '')}\nRFC: {prov_data.get('rfc', '')}"
                            cli_text = f"{cliente_input}\n{cli_data.get('direccion', '')}\nRFC: {cli_data.get('rfc', '')}"
                            
                            datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_texto": prov_text, "cli_texto": cli_text}
                            pdf_bytes = generar_pdf_entrega(datos_pdf, items, folio_real)
                            
                            st.success(f"✅ Guardado. Folio: {folio_real}")
                            st.download_button("🖨️ PDF", pdf_bytes, f"Recibo_{oc_input}.pdf", "application/pdf")
                            st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                        except Exception as e: st.error(f"Error JSON: {e}")

# ==================================================
# 📥 OPCIÓN 4: ENTRADA DE MATERIAL (CORREGIDO SERIALIZACIÓN)
# ==================================================
elif "Entrada" in opcion_almacen:
    st.markdown("### 📥 Registro de Entrada de Material")
    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial"])
    with tab_ent_new:
        with st.container(border=True):
            st.subheader("Datos de la Entrada")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_in = c1.text_input("Folio Remisión")
            fecha_in = c2.date_input("Fecha Llegada", value=datetime.now().date())
            prov_in = c3.selectbox("Proveedor:", lista_proveedores, index=None)
            
            st.divider()
            if "data_entrada" not in st.session_state: 
                st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            
            edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True)
            obs_in = st.text_area("Observaciones:")
            col_f, col_a = st.columns([1, 1])
            user_in = col_f.selectbox("Recibe:", lista_personal)
            
            if col_a.button("💾 Registrar Entrada", type="primary", use_container_width=True):
                if oc_in and prov_in:
                    items_in = edited_df_in[edited_df_in["Código"] != ""]
                    if not items_in.empty:
                        try:
                            # MEJORA: Casting explícito para evitar int64 error
                            for i, row in items_in.iterrows():
                                res_in = supabase.table("Entradas_Material").insert({
                                    "fecha": fecha_in.isoformat(), "oc": str(oc_in), 
                                    "proveedor": str(prov_in), "codigo": str(row["Código"]), 
                                    "descripcion": str(row["Descripción"]), "color": str(row["Color"]), 
                                    "cantidad": float(row["Cantidad"]), "usuario": str(user_in), 
                                    "observaciones": str(obs_in)
                                }).execute()

                            nuevo_id_in = res_in.data[0]['id'] if res_in.data else 1
                            prov_data = df_proveedores_cat[df_proveedores_cat[col_p] == prov_in].iloc[0]
                            prov_text = f"{prov_in}\n{prov_data.get('domicilio', '')}\nRFC: {prov_data.get('rfc', '')}"
                            hemore_text = "HEMORE INDUSTRIAS\nAlmacén Puebla"
                            
                            datos_pdf = {"fecha": fecha_in.strftime("%d/%m/%Y"), "oc": oc_in, "observaciones": obs_in, "prov_texto": prov_text, "hemore_texto": hemore_text}
                            pdf_bytes = generar_pdf_entrada(datos_pdf, items_in, nuevo_id_in)
                            
                            st.success(f"✅ Registrado. Folio: {nuevo_id_in}")
                            st.download_button("🖨️ PDF", pdf_bytes, f"Entrada_{oc_in}.pdf", "application/pdf")
                            st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                        except Exception as e: st.error(f"Error JSON: {e}")

# ==================================================
# 💰 OPCIÓN 5: RECIBOS DE DINERO (CORREGIDO SERIALIZACIÓN)
# ==================================================
elif "Dinero" in opcion_almacen:
    st.markdown("### 💰 Recibos de Dinero")
    tab_money_new, tab_money_hist = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    with tab_money_new:
        with st.container(border=True):
            st.subheader("Detalles del Pago")
            c1, c2 = st.columns(2)
            fecha_pago = c1.date_input("Fecha Recepción")
            cliente_pago = c2.selectbox("Cliente:", lista_clientes, index=None)
            metodo = st.selectbox("Método:", ["Transferencia", "Efectivo", "Cheque", "Depósito"])
            
            if "data_money" not in st.session_state:
                st.session_state["data_money"] = pd.DataFrame([{"Concepto": "", "Monto": 0.0}], columns=["Concepto", "Monto"])
                
            edited_money = st.data_editor(st.session_state["data_money"], num_rows="dynamic", use_container_width=True)
            total_money = edited_money["Monto"].sum()
            st.markdown(f"#### Total: :green[$ {total_money:,.2f}]")
            
            if st.button("💾 Generar Recibo", type="primary"):
                if cliente_pago and total_money > 0:
                    items_m = edited_money[edited_money["Concepto"] != ""]
                    try:
                        for i, row in items_m.iterrows():
                            # MEJORA: Casting float() para JSON
                            res_m = supabase.table("Recibos_Dinero").insert({
                                "fecha": fecha_pago.isoformat(), "cliente": str(cliente_pago), 
                                "concepto": str(row["Concepto"]), "monto": float(row["Monto"]), 
                                "metodo_pago": str(metodo), "usuario": "Almacén", "observaciones": ""
                            }).execute()

                        id_dinero = res_m.data[0]['id'] if res_m.data else 1
                        datos_pdf = {"fecha": fecha_pago.strftime("%d/%m/%Y"), "cliente": cliente_pago, "metodo": metodo, "observaciones": ""}
                        pdf_bytes = generar_pdf_dinero(datos_pdf, items_m, id_dinero)
                        st.success(f"✅ Generado. Folio: {id_dinero}")
                        st.download_button("🖨️ PDF", pdf_bytes, f"Recibo_Dinero_{id_dinero}.pdf", "application/pdf")
                        st.session_state["data_money"] = pd.DataFrame([{"Concepto": "", "Monto": 0.0}], columns=["Concepto", "Monto"])
                    except Exception as e: st.error(f"Error JSON: {e}")
