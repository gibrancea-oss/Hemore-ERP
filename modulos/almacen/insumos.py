import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import io
import utils

# Configuración base
tz_cdmx = timezone(timedelta(hours=-6))
supabase = utils.supabase

def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer: 
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

def renderizar(tiene_permiso):
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        if not df_ins.empty:
            df_ins.columns = df_ins.columns.str.lower()
            if "descripcion" not in df_ins.columns: df_ins["descripcion"] = "Sin Nombre"
            if "cantidad" not in df_ins.columns: df_ins["cantidad"] = 0
            if "unidad" not in df_ins.columns: df_ins["unidad"] = "Pzas"
            if "ubicacion" not in df_ins.columns: df_ins["ubicacion"] = "S/U"

        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
        
        df_provs_insumos = pd.DataFrame(supabase.table("Proveedores").select("*").execute().data)
        col_p_name_ins = 'empresa' if 'empresa' in df_provs_insumos.columns else 'nombre'
        lista_provs_insumos = df_provs_insumos[col_p_name_ins].tolist() if not df_provs_insumos.empty else []
        
    except Exception as e: 
        st.error(f"Error cargando base de datos: {e}")
        df_ins = pd.DataFrame()
        lista_personal = []
        lista_provs_insumos = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial"])
    
    with tab_op:
        if tiene_permiso("Almacén: Movimientos Insumos"):
            if df_ins.empty: 
                st.warning("No hay insumos registrados.")
            else:
                if "insumo_mov_guardado" not in st.session_state: st.session_state["insumo_mov_guardado"] = False
                tipo_operacion = st.radio("Acción:", ["📤 Entrega (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True, key="insumo_tipo_op")
                
                if not st.session_state["insumo_mov_guardado"]:
                    c_form, c_info = st.columns([2, 1])
                    with c_form:
                        lista_busqueda = [f"{row['codigo']} | {row['descripcion']}" for i, row in df_ins.iterrows()]
                        seleccion = st.selectbox("Buscar:", lista_busqueda, key="insumo_sel")
                        
                        if seleccion:
                            codigo_sel = seleccion.split(" | ")[0]
                            item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                            cant_mov = st.number_input("Cantidad", min_value=1.0, value=1.0, key="insumo_cant")
                            
                            if "Entrega" in tipo_operacion:
                                responsable = st.selectbox("Entregar a:", lista_personal, key="insumo_resp")
                                if st.button("Confirmar Salida", type="primary"):
                                    res_check = supabase.table("Insumos").select("cantidad").eq("id", int(item_actual['id'])).execute()
                                    if res_check.data:
                                        stock_real = float(res_check.data[0]['cantidad'])
                                        if stock_real >= cant_mov:
                                            new_st = stock_real - cant_mov
                                            supabase.table("Insumos").update({"cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                            try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Salida", "cantidad": float(cant_mov), "responsable": str(responsable)}).execute()
                                            except: pass
                                            st.session_state["insumo_mov_guardado"] = True
                                            st.toast("✅ Salida registrada exitosamente.", icon="✅")
                                            st.rerun()
                                        else: 
                                            st.error(f"Stock insuficiente. Stock real: {stock_real}")
                                    else: 
                                        st.error("Error al verificar el stock.")
                            else:
                                st.markdown("**Detalles de la Entrada:**")
                                prov_in_insumo = st.selectbox("Proveedor:", lista_provs_insumos, index=None, key="prov_re_stock")
                                c_f1, c_f2 = st.columns(2)
                                factura_opcion = c_f1.radio("Comprobante:", ["Con factura", "Sin factura"], horizontal=True, key="fac_re_stock")
                                num_comprobante = c_f2.text_input("No. Factura / Ticket", key="num_re_stock")
                                
                                if st.button("Confirmar Entrada", type="primary"):
                                    res_check = supabase.table("Insumos").select("cantidad").eq("id", int(item_actual['id'])).execute()
                                    stock_actual = float(res_check.data[0]['cantidad']) if res_check.data else float(item_actual['cantidad'])
                                    new_st = stock_actual + cant_mov
                                    
                                    supabase.table("Insumos").update({"cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                    info_entrada = f"Proveedor: {prov_in_insumo if prov_in_insumo else 'S/P'} | {factura_opcion}: {num_comprobante}"
                                    
                                    try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Re-stock", "cantidad": float(cant_mov), "responsable": info_entrada}).execute()
                                    except: pass
                                    st.session_state["insumo_mov_guardado"] = True
                                    st.toast("✅ Entrada registrada exitosamente.", icon="✅")
                                    st.rerun()
                    
                    with c_info: 
                        if seleccion: 
                            st.metric("Stock Actual", item_actual['cantidad'])
                            st.write(f"📍 Ubicación: {item_actual['ubicacion']}")
                else:
                    tipo_str = "Salida" if "Entrega" in tipo_operacion else "Entrada"
                    st.success(f"✅ {tipo_str} registrada exitosamente. El inventario ha sido actualizado.")
                    if st.button(f"🔄 Hacer {'salida nueva' if 'Entrega' in tipo_operacion else 'entrada nueva'}"):
                        st.session_state["insumo_mov_guardado"] = False
                        for k in ["insumo_sel", "insumo_cant", "insumo_resp", "prov_re_stock", "fac_re_stock", "num_re_stock"]: st.session_state.pop(k, None)
                        st.rerun()
        else:
            st.warning("🔒 No tienes permiso para registrar movimientos de insumos.")

    with tab_exist:
        if tiene_permiso("Almacén: Ver Existencias Insumos"):
            if not df_ins.empty:
                df_view = df_ins[["codigo", "descripcion", "cantidad", "unidad", "ubicacion"]].rename(columns={"codigo": "Código", "descripcion": "Descripción", "cantidad": "Stock", "unidad": "Unidad", "ubicacion": "Ubicación"})
                st.download_button("📥 Descargar Existencias", convertir_df_a_excel(df_view), "Existencias.xlsx")
                st.dataframe(df_view, use_container_width=True)
        else:
            st.warning("🔒 No tienes permiso para ver el stock.")

    with tab_hist:
        @st.dialog("Detalles del Movimiento - Insumos")
        def ver_detalle_insumo(mov_id, df_source):
            row_info = df_source[df_source['id'] == mov_id].iloc[0]
            st.markdown("#### 📄 Información del Registro")
            st.write(f"**Fecha y Hora:** {row_info.get('fecha', '')}")
            st.write(f"**Código:** {row_info.get('codigo', '')}")
            st.write(f"**Descripción:** {row_info.get('descripcion', '')}")
            st.write(f"**Tipo de Movimiento:** {row_info.get('tipo_movimiento', '')}")
            st.write(f"**Cantidad:** {row_info.get('cantidad', '')}")
            st.write(f"**Responsable / Detalles:** {row_info.get('responsable', '')}")
            st.divider()
            
            if tiene_permiso("Almacén: Eliminar Historial Insumos"):
                def eliminar_registro(id_borrar):
                    supabase.table("Historial_Insumos").delete().eq("id", int(id_borrar)).execute()
                    st.toast("Registro eliminado.", icon="🗑️")
                st.button("🗑️ ELIMINAR ESTE REGISTRO", type="secondary", use_container_width=True, on_click=eliminar_registro, args=(mov_id,))
            else:
                st.warning("🔒 No tienes permiso para eliminar registros.")

        try:
            res_h = supabase.table("Historial_Insumos").select("*").order("id", desc=True).limit(200).execute()
            df_hist_ins = pd.DataFrame(res_h.data)
            if not df_hist_ins.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 2, 3, 1, 2])
                c_h1.markdown("**Fecha**"); c_h2.markdown("**Código**"); c_h3.markdown("**Movimiento**"); c_h4.markdown("**Cant**"); c_h5.markdown("**Acción**")
                
                for idx, row in df_hist_ins.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 1, 2])
                    c1.write(row.get('fecha', ''))
                    c2.write(row.get('codigo', ''))
                    c3.write(row.get('tipo_movimiento', ''))
                    c4.write(row.get('cantidad', ''))
                    if c5.button("Ver Detalle", key=f"btn_ins_{row['id']}"):
                        ver_detalle_insumo(row['id'], df_hist_ins)
            else:
                st.info("No hay movimientos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")
