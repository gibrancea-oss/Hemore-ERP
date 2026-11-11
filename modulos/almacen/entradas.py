import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar(tiene_permiso, _formatear_datos_contacto, generar_pdf_entrada):
    try:
        df_provs = pd.DataFrame(supabase.table("Proveedores").select("*").execute().data)
        col_p_name = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
        lista_provs = df_provs[col_p_name].tolist() if not df_provs.empty else []
        df_pers = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_pers = df_pers['nombre'].tolist() if not df_pers.empty else []
    except: lista_provs = []; lista_pers = []; df_provs = pd.DataFrame()

    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial"])
    
    with tab_ent_new:
        if tiene_permiso("Almacén: Registrar Entrada Material"):
            with st.container(border=True):
                if "entrada_guardada" not in st.session_state: st.session_state["entrada_guardada"] = False

                if not st.session_state["entrada_guardada"]:
                    oc_in = st.text_input("Orden de Compra / Remisión", key="new_em_oc")
                    fecha_in = st.date_input("Fecha de Llegada", value=datetime.now(tz_cdmx).date(), key="new_em_fecha")
                    prov_in = st.selectbox("Proveedor (Origen):", lista_provs, index=None, key="new_em_prov")
                    
                    if "data_entrada" not in st.session_state: st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                    edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True)
                    observaciones_in = st.text_area("Observaciones:", key="new_em_obs")
                    quien_entrega_in = st.selectbox("Quien entrega:", lista_pers, key="new_em_usr")
                    
                    if st.button("💾 Registrar Entrada", type="primary"):
                        if oc_in and prov_in and not edited_df_in.empty:
                            items_in = edited_df_in[edited_df_in["Código"].notna() & (edited_df_in["Código"] != "")]
                            for _, row in items_in.iterrows():
                                val_cant_in = row.get("Cantidad", 0)
                                try: cant_f_in = float(val_cant_in) if val_cant_in is not None else 0.0
                                except: cant_f_in = 0.0

                                data_in = {
                                    "fecha": str(fecha_in.isoformat()), "oc": str(oc_in), "proveedor": str(prov_in), 
                                    "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), 
                                    "color": str(row["Color"]), "cantidad": cant_f_in, 
                                    "usuario": str(quien_entrega_in), "observaciones": str(observaciones_in)
                                }
                                supabase.table("Entradas_Material").insert(data_in).execute()
                            
                            st.session_state["entrada_guardada"] = True
                            st.toast("✅ Entrada registrada exitosamente.", icon="📥")
                            st.rerun()
                        else:
                            st.error("Faltan datos por llenar.")
                else:
                    st.success("✅ Entrada registrada exitosamente. Las modificaciones se hacen desde el Historial.")
                    if st.button("🔄 Crear Nueva Entrada"):
                        st.session_state["entrada_guardada"] = False
                        st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                        for k in ["new_em_oc", "new_em_fecha", "new_em_prov", "new_em_obs", "new_em_usr"]: st.session_state.pop(k, None)
                        st.rerun()
        else:
            st.warning("🔒 No tienes permiso para registrar nuevas entradas de material.")

    with tab_ent_hist:
        @st.dialog("Detalles de Entrada de Material", width="large")
        def ver_editar_entrada(oc_seleccionada, df_source):
            df_oc = df_source[df_source['oc'] == oc_seleccionada].copy()
            if not df_oc.empty:
                row_info = df_oc.iloc[0]
                st.markdown(f"#### 📥 Gestionar Entrada O.C. / Remisión {oc_seleccionada}")
                
                try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
                except: fecha_dt = datetime.now(tz_cdmx).date()
                
                idx_prov = lista_provs.index(row_info['proveedor']) if row_info['proveedor'] in lista_provs else None
                idx_usr = lista_pers.index(row_info.get('usuario', '')) if row_info.get('usuario', '') in lista_pers else None

                c1, c2, c3 = st.columns(3)
                n_fecha = c1.date_input("Fecha", value=fecha_dt, key="e_fecha")
                n_prov = c2.selectbox("Proveedor", lista_provs, index=idx_prov, key="e_prov")
                n_entrega = c3.selectbox("Quien entrega", lista_pers, index=idx_usr, key="e_usr")
                
                n_obs = st.text_area("Observaciones", value=row_info.get('observaciones', ''), key="e_obs")
                
                st.divider()
                st.write("**Productos:**")
                df_edit_prod = df_oc[['id', 'codigo', 'descripcion', 'color', 'cantidad']].copy()
                df_edit_prod.rename(columns={'codigo':'Código', 'descripcion':'Descripción', 'color':'Color', 'cantidad':'Cantidad'}, inplace=True)
                df_edit_prod["🗑️ Eliminar"] = False 

                edited_prods = st.data_editor(df_edit_prod, use_container_width=True, hide_index=True, disabled=['id'], num_rows="dynamic", key="e_editor", column_config={"🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️ Eliminar", default=False)})
                
                col_g, col_p = st.columns(2)
                
                if tiene_permiso("Almacén: Editar/Eliminar Entrada Material"):
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
                                    "fecha": str(n_fecha.isoformat()), "proveedor": str(n_prov), "observaciones": str(n_obs), "usuario": str(n_entrega),
                                    "codigo": str(r.get("Código", "")), "descripcion": str(r.get("Descripción", "")), "color": str(r.get("Color", "")), "cantidad": cant_f, "oc": str(oc_seleccionada) 
                                }
                                
                                if pd.notna(r.get("id")) and str(r.get("id")).strip() != "": supabase.table("Entradas_Material").update(datos_update).eq("id", r["id"]).execute()
                                else:
                                    if str(r.get("Código", "")).strip() != "": supabase.table("Entradas_Material").insert(datos_update).execute()
                        
                        if to_delete: supabase.table("Entradas_Material").delete().in_("id", to_delete).execute()
                        st.toast("✅ Cambios Guardados.", icon="💾"); st.rerun()
                else:
                    col_g.warning("🔒 No tienes permiso para editar.")

                if n_prov in lista_provs:
                    try:
                        prov_data = df_provs[df_provs[col_p_name] == n_prov].iloc[0]
                        prov_text = _formatear_datos_contacto(n_prov, prov_data)
                        hemore_text = "HEMORE INDUSTRIAS\nAlmacén Central" 
                        df_pdf = edited_prods[~edited_prods["🗑️ Eliminar"]]
                        datos_pdf = {"oc": oc_seleccionada, "fecha": n_fecha.strftime("%d/%m/%Y"), "observaciones": n_obs, "prov_texto": prov_text, "hemore_texto": hemore_text, "quien_entrega": n_entrega}
                        pdf_bytes = generar_pdf_entrada(datos_pdf, df_pdf, row_info['id'])
                        col_p.download_button("🖨️ Reimprimir PDF", pdf_bytes, f"Entrada_{oc_seleccionada}.pdf", "application/pdf", use_container_width=True)
                    except: col_p.error("Error PDF")
                
                st.divider()
                if tiene_permiso("Almacén: Editar/Eliminar Entrada Material"):
                    def del_entrada(oc_borrar):
                        supabase.table("Entradas_Material").delete().eq("oc", oc_borrar).execute()
                        st.toast("Entrada eliminada.", icon="🗑️")
                    st.button("🗑️ ELIMINAR ESTA ENTRADA POR COMPLETO", type="secondary", use_container_width=True, on_click=del_entrada, args=(oc_seleccionada,))

        try:
            res_h = supabase.table("Entradas_Material").select("*").order("id", desc=True).limit(500).execute()
            df_hist_ent = pd.DataFrame(res_h.data)
            if not df_hist_ent.empty:
                df_resumen_ent = df_hist_ent.drop_duplicates(subset=['oc'])[['fecha', 'oc', 'proveedor']].reset_index(drop=True)
                df_resumen_ent.columns = ['Fecha', 'OC / Remisión', 'Proveedor']
                
                c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 3, 2])
                c_h1.markdown("**Fecha**"); c_h2.markdown("**OC / Remisión**"); c_h3.markdown("**Proveedor**"); c_h4.markdown("**Acción**")
                for idx, row in df_resumen_ent.iterrows():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                    c1.write(row['Fecha'])
                    c2.write(row['OC / Remisión'])
                    c3.write(row['Proveedor'])
                    if c4.button("Ver Detalle", key=f"btn_ent_{row['OC / Remisión']}"):
                        ver_editar_entrada(row['OC / Remisión'], df_hist_ent)
            else:
                st.info("No hay entradas registradas.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")
