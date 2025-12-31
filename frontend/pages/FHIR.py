import streamlit as st
import json
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="FHIR", page_icon="🌐", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>🌐 FHIR - Interoperabilidad</h1></div>", unsafe_allow_html=True)

if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
    st.error("❌ No tienes permisos para exportar datos FHIR.")
else:
    st.info("📋 FHIR (Fast Healthcare Interoperability Resources) es el estándar internacional para intercambio de información médica")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Exportar Paciente", "📤 Exportar Receta", "📤 Exportar Orden Lab", "📥 Importar FHIR"])
    
    with tab1:
        st.subheader("📤 Exportar Paciente a FHIR")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                if st.button("📥 Exportar a FHIR", use_container_width=True):
                    response = api_request("GET", f"/fhir/Patient/{paciente_id}")
                    
                    if response and response.status_code == 200:
                        fhir_data = response.json()
                        st.success("✅ Paciente exportado a FHIR")
                        
                        st.json(fhir_data)
                        
                        st.download_button(
                            label="⬇️ Descargar JSON",
                            data=json.dumps(fhir_data, indent=2),
                            file_name=f"paciente_{paciente_id}_fhir.json",
                            mime="application/json",
                            use_container_width=True
                        )
            else:
                st.warning("⚠️ No hay pacientes registrados")
    
    with tab2:
        st.subheader("📤 Exportar Receta a FHIR")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()), key="export_receta_pac")
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                # Obtener recetas del paciente
                response = api_request("GET", f"/api/recetas/paciente/{paciente_id}")
                if response and response.status_code == 200:
                    recetas = response.json()
                    
                    if recetas:
                        opciones_recetas = {f"Receta #{r['id']} - {r['fecha_emision'][:10]}": r['id'] for r in recetas}
                        
                        receta_seleccionada = st.selectbox("💊 Seleccionar Receta", list(opciones_recetas.keys()))
                        receta_id = opciones_recetas[receta_seleccionada]
                        
                        if st.button("📥 Exportar Receta a FHIR", use_container_width=True):
                            response = api_request("GET", f"/api/recetas/{receta_id}/fhir")
                            
                            if response and response.status_code == 200:
                                fhir_data = response.json()
                                st.success("✅ Receta exportada a FHIR Bundle")
                                
                                st.json(fhir_data)
                                
                                st.download_button(
                                    label="⬇️ Descargar FHIR Bundle (JSON)",
                                    data=json.dumps(fhir_data, indent=2),
                                    file_name=f"receta_{receta_id}_fhir_bundle.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                    else:
                        st.info("📭 No hay recetas para este paciente")
                else:
                    st.warning("⚠️ Error al obtener recetas")
            else:
                st.warning("⚠️ No hay pacientes registrados")
    
    with tab3:
        st.subheader("📤 Exportar Orden de Laboratorio a FHIR")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()), key="export_lab_pac")
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                # Obtener órdenes del paciente
                response = api_request("GET", f"/api/laboratorio/paciente/{paciente_id}")
                if response and response.status_code == 200:
                    ordenes = response.json()
                    
                    if ordenes:
                        opciones_ordenes = {f"Orden #{o['id']} - {o['fecha_orden'][:10]} - {o['estado']}": o['id'] for o in ordenes}
                        
                        orden_seleccionada = st.selectbox("🧪 Seleccionar Orden", list(opciones_ordenes.keys()))
                        orden_id = opciones_ordenes[orden_seleccionada]
                        
                        if st.button("📥 Exportar Orden a FHIR DiagnosticReport", use_container_width=True):
                            response = api_request("GET", f"/api/laboratorio/{orden_id}/fhir")
                            
                            if response and response.status_code == 200:
                                fhir_data = response.json()
                                st.success("✅ Orden exportada a FHIR Bundle (DiagnosticReport + Observations)")
                                
                                # Mostrar resumen
                                num_observations = len(fhir_data.get('entry', [])) - 2
                                st.info(f"📊 Bundle contiene: 1 Paciente, 1 DiagnosticReport, {num_observations} Observations")
                                
                                st.json(fhir_data)
                                
                                st.download_button(
                                    label="⬇️ Descargar FHIR Bundle (JSON)",
                                    data=json.dumps(fhir_data, indent=2),
                                    file_name=f"orden_lab_{orden_id}_fhir_bundle.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                    else:
                        st.info("📭 No hay órdenes de laboratorio para este paciente")
                else:
                    st.warning("⚠️ Error al obtener órdenes")
            else:
                st.warning("⚠️ No hay pacientes registrados")
    
    with tab4:
        st.subheader("📥 Importar desde FHIR Bundle")
        
        tipo_import = st.radio("Tipo de importación:", ["Receta", "Orden de Laboratorio"])
        
        if st.session_state.usuario['rol'] not in ['medico', 'admin']:
            st.error("❌ Solo médicos y administradores pueden importar datos.")
        else:
            st.info("⚠️ El paciente debe estar previamente registrado en el sistema")
            
            fhir_json = st.text_area(
                "Pegar JSON de FHIR Bundle aquí:",
                height=300,
                placeholder='{"resourceType": "Bundle", "type": "collection", ...}'
            )
            
            if st.button("⬆️ Importar desde FHIR", use_container_width=True):
                if not fhir_json:
                    st.error("Por favor pega el JSON del FHIR Bundle")
                else:
                    try:
                        fhir_data = json.loads(fhir_json)
                        
                        if tipo_import == "Receta":
                            response = api_request("POST", "/api/recetas/fhir/import", fhir_data)
                        else:
                            response = api_request("POST", "/api/laboratorio/fhir/import", fhir_data)
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['mensaje']}")
                            st.info(f"ID: {result['id']}")
                            st.balloons()
                        elif response:
                            st.error(f"❌ Error: {response.json().get('detail')}")
                    except json.JSONDecodeError:
                        st.error("❌ El JSON proporcionado no es válido")