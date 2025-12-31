import streamlit as st
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="Laboratorio", page_icon="🧪", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>🧪 Órdenes de Laboratorio</h1></div>", unsafe_allow_html=True)

if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
    st.error("❌ No tienes permisos completos. Enfermeras pueden ver y agregar resultados.")

tab1, tab2, tab3 = st.tabs(["➕ Nueva Orden", "📋 Historial de Órdenes", "📚 Catálogo LOINC"])

with tab1:
    st.subheader("📝 Crear Nueva Orden de Laboratorio")
    
    if st.session_state.usuario['rol'] not in ['medico', 'admin']:
        st.error("❌ Solo médicos pueden crear órdenes de laboratorio.")
    else:
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                # Obtener catálogo
                response_catalogo = api_request("GET", "/api/laboratorio/catalogo")
                if response_catalogo and response_catalogo.status_code == 200:
                    catalogo = response_catalogo.json()
                    
                    with st.form("form_orden_lab"):
                        st.subheader("🔬 Seleccionar Exámenes del Catálogo LOINC")
                        
                        examenes_seleccionados = []
                        
                        # Mostrar por categorías
                        for categoria, examenes in catalogo.items():
                            with st.expander(f"📁 {categoria}", expanded=False):
                                for examen in examenes:
                                    if st.checkbox(f"{examen['nombre']} (LOINC: {examen['codigo']})", key=f"exam_{examen['key']}"):
                                        examenes_seleccionados.append({
                                            "codigo_loinc": examen['codigo'],
                                            "nombre": examen['nombre'],
                                            "valor_referencia": examen['valor_referencia'],
                                            "unidad": examen['unidad']
                                        })
                        
                        st.divider()
                        st.subheader("✍️ Agregar Exámenes Personalizados")
                        st.info("💡 Usa esta sección para agregar exámenes que no estén en el catálogo LOINC")
                        
                        num_personalizados = st.number_input("¿Cuántos exámenes personalizados quieres agregar?", 
                                                            min_value=0, max_value=5, value=0)
                        
                        for i in range(num_personalizados):
                            st.markdown(f"**Examen Personalizado #{i+1}**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                nombre_pers = st.text_input(f"Nombre del examen", key=f"pers_nombre_{i}")
                            with col2:
                                unidad_pers = st.text_input(f"Unidad", placeholder="mg/dL, U/L, etc", key=f"pers_unidad_{i}")
                            with col3:
                                valor_ref_pers = st.text_input(f"Valor de referencia", placeholder="Ej: 70-100", key=f"pers_valor_{i}")
                            
                            if nombre_pers:
                                examenes_seleccionados.append({
                                    "codigo_loinc": f"CUSTOM-{i+1}",
                                    "nombre": nombre_pers,
                                    "valor_referencia": valor_ref_pers or "Por definir",
                                    "unidad": unidad_pers or ""
                                })
                        
                        st.divider()
                        st.subheader("📋 Información Clínica")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            diagnostico = st.text_area("Diagnóstico Presuntivo", height=100)
                        with col2:
                            indicaciones = st.text_area("Indicaciones Clínicas", height=100)
                        
                        urgente = st.checkbox("⚠️ Marcar como URGENTE")
                        
                        submitted = st.form_submit_button("✅ Crear Orden de Laboratorio", use_container_width=True)
                        
                        if submitted:
                            if not examenes_seleccionados:
                                st.error("Debes seleccionar al menos un examen (del catálogo o personalizado)")
                            elif len(examenes_seleccionados) > 10:
                                st.error("Máximo 10 exámenes por orden")
                            else:
                                datos_orden = {
                                    "paciente_id": paciente_id,
                                    "examenes": examenes_seleccionados,
                                    "diagnostico_presuntivo": diagnostico,
                                    "indicaciones_clinicas": indicaciones,
                                    "urgente": urgente
                                }
                                
                                response = api_request("POST", "/api/laboratorio/orden", datos_orden)
                                if response and response.status_code == 200:
                                    st.success("✅ Orden de laboratorio creada exitosamente")
                                    st.info(f"Total de exámenes: {len(examenes_seleccionados)}")
                                    st.balloons()
                                elif response:
                                    st.error(f"❌ Error: {response.json().get('detail')}")

with tab2:
    st.subheader("📋 Historial de Órdenes de Laboratorio")
    
    response = api_request("GET", "/api/pacientes")
    if response and response.status_code == 200:
        pacientes = response.json()
        
        if pacientes:
            opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
            
            paciente_seleccionado = st.selectbox("👤 Buscar órdenes del paciente", list(opciones_pacientes.keys()), key="hist_lab_paciente")
            paciente_id = opciones_pacientes[paciente_seleccionado]
            
            if st.button("🔍 Buscar Órdenes"):
                response = api_request("GET", f"/api/laboratorio/paciente/{paciente_id}")
                
                if response and response.status_code == 200:
                    ordenes = response.json()
                    
                    if ordenes:
                        st.info(f"📊 Total: {len(ordenes)} orden(es)")
                        
                        for orden in ordenes:
                            # Emoji según estado
                            emoji_estado = {"pendiente": "⏳", "en_proceso": "🔬", "completado": "✅", "cancelado": "❌"}
                            
                            urgente_badge = " 🚨 URGENTE" if orden['urgente'] else ""
                            
                            with st.expander(f"{emoji_estado.get(orden['estado'], '📋')} Orden #{orden['id']} - {orden['fecha_orden'][:10]} - {orden['estado'].upper()}{urgente_badge}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Médico:** {orden['medico_nombre']}")
                                    st.write(f"**Estado:** {orden['estado']}")
                                    if orden['fecha_resultado']:
                                        st.write(f"**Fecha Resultado:** {orden['fecha_resultado'][:10]}")
                                with col2:
                                    if orden['diagnostico_presuntivo']:
                                        st.write(f"**Diagnóstico:** {orden['diagnostico_presuntivo']}")
                                    if orden['indicaciones_clinicas']:
                                        st.write(f"**Indicaciones:** {orden['indicaciones_clinicas']}")
                                
                                st.divider()
                                st.markdown("### 🔬 Exámenes Solicitados")
                                
                                # Mostrar exámenes
                                for exam in orden['examenes']:
                                    st.markdown(f"**{exam['numero']}. {exam['nombre']}**")
                                    if exam['codigo_loinc'].startswith('CUSTOM'):
                                        st.caption("🔖 Examen Personalizado")
                                    else:
                                        st.caption(f"LOINC: {exam['codigo_loinc']}")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if exam['resultado']:
                                            st.success(f"**Resultado:** {exam['resultado']} {exam['unidad'] or ''}")
                                        else:
                                            st.warning("Resultado: Pendiente")
                                    with col2:
                                        st.info(f"**V. Referencia:** {exam['valor_referencia']}")
                                    with col3:
                                        if exam['unidad']:
                                            st.write(f"**Unidad:** {exam['unidad']}")
                                
                                st.divider()
                                
                                # Agregar resultados (solo personal médico)
                                if st.session_state.usuario['rol'] in ['medico', 'enfermera', 'admin'] and orden['estado'] != 'cancelado':
                                    with st.form(key=f"form_resultado_{orden['id']}"):
                                        st.markdown("#### 💾 Agregar/Actualizar Resultados")
                                        
                                        resultados = []
                                        for exam in orden['examenes']:
                                            resultado = st.text_input(
                                                f"{exam['nombre']}",
                                                value=exam['resultado'] or "",
                                                key=f"res_{orden['id']}_{exam['numero']}"
                                            )
                                            if resultado:
                                                resultados.append({"examen_numero": exam['numero'], "resultado": resultado})
                                        
                                        if st.form_submit_button("💾 Guardar Resultados"):
                                            if resultados:
                                                response = api_request("PUT", f"/api/laboratorio/{orden['id']}/resultado", resultados)
                                                if response and response.status_code == 200:
                                                    st.success("✅ Resultados guardados exitosamente")
                                                    st.rerun()
                                                else:
                                                    st.error("Error al guardar resultados")
                                            else:
                                                st.warning("No hay resultados para guardar")
                                
                                # Cancelar orden
                                if st.session_state.usuario['rol'] in ['medico', 'admin'] and orden['estado'] not in ['completado', 'cancelado']:
                                    if st.button(f"❌ Cancelar Orden", key=f"cancel_{orden['id']}"):
                                        response = api_request("DELETE", f"/api/laboratorio/{orden['id']}")
                                        if response and response.status_code == 200:
                                            st.warning("Orden cancelada")
                                            st.rerun()
                    else:
                        st.info("📭 No hay órdenes de laboratorio para este paciente")

with tab3:
    st.subheader("📚 Catálogo de Exámenes LOINC")
    
    # Buscador
    termino_busqueda = st.text_input("🔍 Buscar examen", placeholder="Ej: glucosa, hemograma, colesterol")
    
    if termino_busqueda:
        response = api_request("GET", f"/api/laboratorio/buscar/{termino_busqueda}")
        if response and response.status_code == 200:
            resultados = response.json()
            
            if resultados:
                st.write(f"**{len(resultados)} resultado(s) encontrado(s)**")
                
                for exam in resultados:
                    with st.expander(f"{exam['nombre']} - {exam['categoria']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Código LOINC:** {exam['codigo']}")
                            st.write(f"**Categoría:** {exam['categoria']}")
                        with col2:
                            st.write(f"**Unidad:** {exam['unidad']}")
                            st.write(f"**Valor Referencia:** {exam['valor_referencia']}")
            else:
                st.info("No se encontraron resultados")
    else:
        # Mostrar catálogo completo por categorías
        response = api_request("GET", "/api/laboratorio/catalogo")
        if response and response.status_code == 200:
            catalogo = response.json()
            
            st.info(f"📊 El catálogo contiene {sum(len(exams) for exams in catalogo.values())} exámenes organizados en {len(catalogo)} categorías")
            
            for categoria, examenes in catalogo.items():
                with st.expander(f"📁 {categoria} ({len(examenes)} exámenes)"):
                    for exam in examenes:
                        st.markdown(f"**{exam['nombre']}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"LOINC: {exam['codigo']}")
                        with col2:
                            st.caption(f"Unidad: {exam['unidad']}")
                        with col3:
                            st.caption(f"Ref: {exam['valor_referencia']}")
                        st.divider()