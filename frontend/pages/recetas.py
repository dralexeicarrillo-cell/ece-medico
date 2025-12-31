import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="Recetas", page_icon="💊", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>💊 Gestión de Recetas Médicas</h1></div>", unsafe_allow_html=True)

if st.session_state.usuario['rol'] not in ['medico', 'admin']:
    st.error("❌ Solo médicos pueden emitir recetas.")
else:
    tab1, tab2 = st.tabs(["➕ Nueva Receta", "📋 Historial"])
    
    with tab1:
        st.subheader("📝 Emitir Nueva Receta")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                with st.form("form_receta"):
                    st.markdown("#### 💊 Medicamento 1 (Obligatorio)")
                    col1, col2 = st.columns(2)
                    with col1:
                        med1_nombre = st.text_input("Nombre *", key="med1_nombre")
                        med1_dosis = st.text_input("Dosis *", placeholder="500mg", key="med1_dosis")
                        med1_frecuencia = st.text_input("Frecuencia *", placeholder="Cada 8 horas", key="med1_frecuencia")
                    with col2:
                        med1_duracion = st.text_input("Duración *", placeholder="7 días", key="med1_duracion")
                        med1_via = st.selectbox("Vía de Administración *", 
                                         ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                         key="med1_via")
                    
                    # Medicamentos adicionales
                    num_medicamentos = st.number_input("Medicamentos adicionales", min_value=0, max_value=4, value=0)
                    
                    medicamentos_extra = []
                    for i in range(2, min(num_medicamentos + 2, 6)):
                        with st.expander(f"➕ Medicamento {i} (Opcional)"):
                            col1, col2 = st.columns(2)
                            with col1:
                                nombre = st.text_input("Nombre", key=f"med{i}_nombre")
                                dosis = st.text_input("Dosis", placeholder="500mg", key=f"med{i}_dosis")
                                frecuencia = st.text_input("Frecuencia", placeholder="Cada 8 horas", key=f"med{i}_frecuencia")
                            with col2:
                                duracion = st.text_input("Duración", placeholder="7 días", key=f"med{i}_duracion")
                                via = st.selectbox("Vía de Administración", 
                                                 ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                                 key=f"med{i}_via")
                            
                            if nombre:
                                medicamentos_extra.append({
                                    'numero': i,
                                    'nombre': nombre,
                                    'dosis': dosis,
                                    'frecuencia': frecuencia,
                                    'duracion': duracion,
                                    'via': via
                                })
                    
                    indicaciones = st.text_area("📋 Indicaciones Generales", height=100)
                    
                    submitted = st.form_submit_button("✅ Emitir Receta", use_container_width=True)
                    
                    if submitted:
                        if not med1_nombre or not med1_dosis or not med1_frecuencia or not med1_duracion:
                            st.error("Debes completar al menos el medicamento 1")
                        else:
                            datos_receta = {
                                "paciente_id": paciente_id,
                                "medicamento1_nombre": med1_nombre,
                                "medicamento1_dosis": med1_dosis,
                                "medicamento1_frecuencia": med1_frecuencia,
                                "medicamento1_duracion": med1_duracion,
                                "medicamento1_via": med1_via,
                                "indicaciones_generales": indicaciones
                            }
                            
                            # Agregar medicamentos adicionales
                            for med in medicamentos_extra:
                                datos_receta[f"medicamento{med['numero']}_nombre"] = med['nombre']
                                datos_receta[f"medicamento{med['numero']}_dosis"] = med['dosis']
                                datos_receta[f"medicamento{med['numero']}_frecuencia"] = med['frecuencia']
                                datos_receta[f"medicamento{med['numero']}_duracion"] = med['duracion']
                                datos_receta[f"medicamento{med['numero']}_via"] = med['via']
                            
                            response = api_request("POST", "/api/recetas", datos_receta)
                            if response and response.status_code == 200:
                                st.success("✅ Receta emitida exitosamente")
                                st.balloons()
                            elif response:
                                st.error(f"❌ Error: {response.json().get('detail')}")
    
    with tab2:
        st.subheader("📋 Historial de Recetas")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Buscar recetas del paciente", list(opciones_pacientes.keys()), key="historial_paciente")
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                if st.button("🔍 Buscar Recetas"):
                    response = api_request("GET", f"/api/recetas/paciente/{paciente_id}")
                    
                    if response and response.status_code == 200:
                        recetas = response.json()
                        
                        if recetas:
                            st.info(f"📊 Total: {len(recetas)} receta(s)")
                            
                            for r in recetas:
                                with st.expander(f"📄 Receta #{r['id']} - {r['fecha_emision'][:10]} - Dr. {r.get('medico_nombre', 'N/A')}"):
                                    st.write("**Medicamentos:**")
                                    
                                    for i in range(1, 6):
                                        nombre_key = f"medicamento{i}_nombre"
                                        if r.get(nombre_key):
                                            st.markdown(f"**{i}. {r[nombre_key]}**")
                                            st.write(f"   • Dosis: {r[f'medicamento{i}_dosis']}")
                                            st.write(f"   • Frecuencia: {r[f'medicamento{i}_frecuencia']}")
                                            st.write(f"   • Duración: {r[f'medicamento{i}_duracion']}")
                                            st.write(f"   • Vía: {r[f'medicamento{i}_via']}")
                                    
                                    if r.get('indicaciones_generales'):
                                        st.markdown("**Indicaciones Generales:**")
                                        st.info(r['indicaciones_generales'])
                                    
                                    st.divider()
                                    
                                    # Botón para descargar PDF
                                    pdf_response = api_request("GET", f"/api/recetas/{r['id']}/pdf")
                                    if pdf_response and pdf_response.status_code == 200:
                                        st.download_button(
                                            label="📄 Descargar PDF",
                                            data=pdf_response.content,
                                            file_name=f"receta_{r['id']}.pdf",
                                            mime="application/pdf",
                                            key=f"download_pdf_{r['id']}",
                                            use_container_width=True
                                        )
                        else:
                            st.info("📭 No hay recetas para este paciente")
            else:
                st.warning("⚠️ No hay pacientes registrados")