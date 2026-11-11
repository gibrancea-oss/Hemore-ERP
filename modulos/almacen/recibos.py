import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar(tiene_permiso, _formatear_datos_contacto, generar_pdf_entrega):
    try:
        df_clientes = pd.DataFrame(supabase.table("Clientes").select("*").execute().data)
        lista_nombres_cli = df_clientes['nombre'].tolist() if not df_clientes.empty else []
        df_proveedores = pd.DataFrame(supabase.table("Proveedores").select("*").execute().data)
        col_p_name = 'empresa' if 'empresa' in df_proveedores.columns else 'nombre'
        lista_nombres_prov = df_proveedores[col_p_name].tolist() if not df_proveedores.empty else []
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: lista_nombres_cli = []; lista_nombres_prov = []; lista_personal = []; df_clientes = pd.DataFrame(); df_proveedores = pd.DataFrame()

    tab_nuevo, tab_historial = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    
    with tab_nuevo:
        if tiene_permiso("Almacén: Generar Recibos OC"):
            with st.container(border=True):
                st.subheader("Datos de la Entrega")
                if "recibo_guardado" not in st.session_state:
                    st.session_state["recibo_guardado"] = False
                    st.session_state["recibo_pdf"] = None
                    st.session_state["recibo_filename"] = ""

                if not st.session_state["recibo_guardado"]:
                    c1, c2, c3 = st.columns([1, 1, 1])
                    oc_input = c1.text_input("Orden de Compra (O.C.)", placeholder="Ej. 2183", key="new_ro_oc")
                    fecha_input = c2.date_input("Fecha", value=datetime.now(tz_cdmx).date(), key="new_ro_fecha")
                    prov_input = c3.selectbox("Proveedor (Origen):", lista_nombres_prov, index=None, placeholder="Hemore...", key="new_ro_prov")
                    cliente_input = st.selectbox("Cliente (Destino):", lista_nombres_cli, index=None, key="new_ro_cli")
                    
                    if "data_recibo" not in st.session_state: st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                    edited_df = st.data_editor(st.session_state["data_recibo"], num_rows="dynamic", use_container_width=True)
                    observaciones = st.text_area("Observaciones:", key="new_ro_obs")
                    quien_entrega_input = st.selectbox("Quien entrega:", lista_personal, key="new_ro_usr")
                    
                    if st.button("💾 Guardar y PDF", type="primary"):
                        items = edited_df[edited_df["Código"].astype(str).str.strip() != ""]
                        errores = []
                        if not oc_input: errores.append("- **Falta O.C.**")
                        if not prov_input: errores.append("- **Falta Proveedor**")
                        if not cliente_input: errores.append("- **Falta Cliente**")
                        if items.empty: errores.append("- **Tabla vacía**")

                        if errores:
                            st.error("⚠️ **No se pudo guardar:**\n\n" + "\n".join(errores))
                        else:
                            for _, row in items.iterrows():
                                val_cant = row.get("Cantidad", 0)
                                try: cant_f = float(val_cant) if val_cant is not None else 0.0
                                except: cant_f = 0.0

                                data_to_insert = {
                                    "fecha": str(fecha_input.isoformat()), "oc": str(oc_input), 
                                    "cliente": str(cliente_input), "proveedor": str(prov_input), 
                                    "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), 
                                    "color": str(row["Color"]), "cantidad": cant_f, 
                                    "usuario": str(quien_entrega_input), "observaciones": str(observaciones)
                                }
                                supabase.table("Recibos_OC").insert(data_to_insert).execute()
                            
                            try:
                                cli_data = df_clientes[df_clientes['nombre'] == cliente_input].iloc[0]
                                prov_data = df_proveedores[df_proveedores[col_p_name] == prov_input].iloc[0]
                                last_id = supabase.table("Recibos_OC").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                                prov_text = _formatear_datos_contacto(prov_input, prov_data)
                                cli_text = _formatear_datos_contacto(cliente_input, cli_data)
                                datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_texto": prov_text, "cli_texto": cli_text, "quien_entrega": quien_entrega_input}
                                pdf_bytes = generar_pdf_entrega(datos_pdf, items, last_id)
                                
                                st.session_state["recibo_pdf"] = pdf_bytes
                                st.session_state["recibo_filename"] = f"Recibo_{oc_input}.pdf"
                                st.session_state["recibo_guardado"] = True
                                st.toast("✅ Guardado correctamente.", icon="✅")
                                st.rerun()
                            except Exception as e: 
                                st.error(f"Error interno al generar PDF: {e}")
                else:
                    st.success("✅ Guardado correctamente. Modificaciones en el Historial.")
                    st.download_button("🖨️ Imprimir PDF", st.session_state["recibo_pdf"], st.session_state["recibo_filename"], "application/pdf")
                    if st.button("🔄 Crear Nuevo Recibo"):
                        st.session_state["recibo_guardado"] = False
                        st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                        for k in ["new_ro_oc", "new_ro_prov", "new_ro_cli", "new_ro_obs", "new_ro_usr", "new_ro_fecha"]: st.session_state.pop(k, None)
                        st.rerun()
        else:
            st.warning("🔒 No tienes permiso para generar nuevos recibos OC.")

    with tab_historial:
        @st.dialog("Detalles de Orden de Compra", width="large")
        def ver_editar_oc(oc_seleccionada, df_source):
            df_oc = df_source[df_source['oc'] == oc_seleccionada].copy()
            if not df_oc.empty:
                row_info = df_oc.iloc[0]
                st.markdown(f"#### 📄 Gestionar O.C. {oc_seleccionada}")
                
                try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
                except: fecha_dt = datetime.now(tz_cdmx).date()
                
                idx_cli = lista_nombres_cli.index(row_info['cliente']) if row_info['cliente'] in lista_nombres_cli else None
                idx_prov = lista_nombres_prov.index(row_info['proveedor']) if row_info['proveedor'] in lista_nombres_prov else None
                idx_usr = lista_personal.index(row_info.get('usuario', '')) if row_info.get('usuario', '') in lista_personal else None
                
                c1, c2, c3, c4 = st.columns(4)
                n_fecha = c1.date_input("Fecha", value=fecha_dt, key="d_fecha")
                n_cli = c2.selectbox("Cliente", lista_nombres_cli, index=idx_cli, key="d_cli")
                n_prov = c3.selectbox("Proveedor", lista_nombres_prov, index=idx_prov, key="d_prov")
                n_entrega = c4.selectbox("Quien entrega", lista_personal, index=idx_usr, key="d_usr")
                
                n_obs = st.text_area("Observaciones", value=row_info.get('observaciones', ''), key="d_obs")
                
                st.divider()
                st.write("**Productos:**")
                df_edit_prod = df_oc[['id', 'codigo', 'descripcion', 'color', 'cantidad']].copy()
                df_edit_prod.rename(columns={'codigo':'Código', 'descripcion':'Descripción', 'color':'Color', 'cantidad':'Cantidad'}, inplace=True)
                df_edit_prod["🗑️ Eliminar"] = False 
                
                edited_prods = st.data_editor(df_edit_prod, use_container_width=True, hide_index=True, disabled=['id'], num_rows="dynamic", key="d_editor", column_config={"🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)})
                
                col_g, col_p = st.columns(2)
                
                if tiene_permiso("Almacén: Editar/Eliminar Recibos OC"):
                    if col_g.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                        to_delete = []
                        for _, r in edited_prods.iterrows():
                            if r.get("🗑️ Eliminar", False):
                                if pd.notna(r.get("id")) and str(r.get("id")).strip() != "": to_delete.append(int(r["id"]))
                            else:
                                val_cant = r.get("Cantidad", 0)
                                try: cant_f = float(val_cant) if pd.notna(val_cant) else 0.0
                                except: cant_f = 0.0
                                
                                datos_update = {
                                    "fecha": str(n_fecha.isoformat()), "cliente": str(n_cli), "proveedor": str(n_prov),
                                    "observaciones": str(n_obs), "codigo": str(r.get("Código", "")), "descripcion": str(r.get("Descripción", "")),
                                    "color": str(r.get("Color", "")), "cantidad": cant_f, "usuario": str(n_entrega), "oc": str(oc_seleccionada) 
                                }
                                
                                if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                    supabase.table("Recibos_OC").update(datos_update).eq("id", r["id"]).execute()
                                else:
                                    if str(r.get("Código", "")).strip() != "": supabase.table("Recibos_OC").insert(datos_update).execute()
                        
                        if to_delete: supabase.table("Recibos_OC").delete().in_("id", to_delete).execute()
                        st.toast("✅ Cambios Guardados", icon="💾"); st.rerun()
                else:
                    col_g.warning("🔒 No tienes permiso para editar.")

                if n_cli in lista_nombres_cli and n_prov in lista_nombres_prov:
                    try:
                        cli_data = df_clientes[df_clientes['nombre'] == n_cli].iloc[0]
                        prov_data = df_proveedores[df_proveedores[col_p_name] == n_prov].iloc[0]
                        prov_text = _formatear_datos_contacto(n_prov, prov_data)
                        cli_text = _formatear_datos_contacto(n_cli, cli_data)
                        
                        df_pdf = edited_prods[~edited_prods["🗑️ Eliminar"]]
                        datos_pdf = {"oc": oc_seleccionada, "fecha": n_fecha.strftime("%d/%m/%Y"), "observaciones": n_obs, "prov_texto": prov_text, "cli_texto": cli_text, "quien_entrega": n_entrega}
                        pdf_bytes = generar_pdf_entrega(datos_pdf, df_pdf, row_info['id'])
                        col_p.download_button("🖨️ Reimprimir PDF", pdf_bytes, f"Recibo_{oc_seleccionada}.pdf", "application/pdf", use_container_width=True)
                    except: col_p.error("Error PDF")
                
                st.divider()
                if tiene_permiso("Almacén: Editar/Eliminar Recibos OC"):
                    def delete_oc(oc_a_borrar):
                        supabase.table("Recibos_OC").delete().eq("oc", oc_a_borrar).execute()
                        st.toast("Orden eliminada.", icon="🗑️")
                    st.button("🗑️ ELIMINAR ESTA ORDEN DE COMPRA POR COMPLETO", type="secondary", use_container_width=True, on_click=delete_oc, args=(oc_seleccionada,))

        try:
            res_h = supabase.table("Recibos_OC").select("*").order("id", desc=True).limit(500).execute()
            df_hist = pd.DataFrame(res_h.data)
            
            if not df_hist.empty:
                df_resumen = df_hist.drop_duplicates(subset=['oc'])[['fecha', 'oc', 'cliente']].reset_index(drop=True)
                df_resumen.columns = ['Fecha', 'Orden de Compra', 'Cliente']
                
                c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 3, 2])
                c_h1.markdown("**Fecha**"); c_h2.markdown("**Orden de Compra**"); c_h3.markdown("**Cliente**"); c_h4.markdown("**Acción**")
                
                for idx, row in df_resumen.iterrows():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                    c1.write(row['Fecha'])
                    c2.write(row['Orden de Compra'])
                    c3.write(row['Cliente'])
                    if c4.button("Ver Detalle", key=f"btn_oc_{row['Orden de Compra']}"):
                        ver_editar_oc(row['Orden de Compra'], df_hist)
            else:
                st.info("No hay recibos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")
