import streamlit as st
from datetime import datetime, date
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="Consultas", page_icon="🩺", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>🩺 Consultas Médicas</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["➕ Nueva Consulta", "📚 Historial"])

with tab1:
    st.subheader("📝 Registrar Nueva Consulta")
    
    if st.session_state.usuario['rol'] not in ['medico', 'admin']:
        st.error("❌ Solo médicos pueden crear consultas.")
    else:
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ Registra un paciente primero.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                with st.form("form_consulta"):
                    motivo = st.text_area("📝 Motivo de Consulta *", height=100)
                    
                    st.subheader("📊 Signos Vitales")
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        presion = st.text_input("🩸 PA", placeholder="120/80")
                    with col2:
                        temperatura = st.text_input("🌡️ T°C", placeholder="36.5")
                    with col3:
                        fc = st.text_input("💓 FC", placeholder="70")
                    with col4:
                        fr = st.text_input("🫁 FR", placeholder="16")
                    with col5:
                        peso = st.text_input("⚖️ Peso", placeholder="70")
                    with col6:
                        altura = st.text_input("📏 Alt", placeholder="170")
                    
                    signos_vitales = f"PA: {presion}, T: {temperatura}°C, FC: {fc}, FR: {fr}, Peso: {peso}kg, Altura: {altura}cm"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        sintomas = st.text_area("🔍 Síntomas y Exploración", height=150)
                        diagnostico = st.text_area("🔬 Diagnóstico", height=150)
                    with col2:
                        tratamiento = st.text_area("💊 Tratamiento", height=150)
                        observaciones = st.text_area("📋 Observaciones", height=150)
                    
                    submitted = st.form_submit_button("✅ Guardar Consulta", use_container_width=True)
                    
                    if submitted:
                        if not motivo:
                            st.error("El motivo es obligatorio")
                        else:
                            datos = {
                                "paciente_id": paciente_id,
                                "motivo": motivo,
                                "signos_vitales": signos_vitales,
                                "sintomas": sintomas,
                                "diagnostico": diagnostico,
                                "tratamiento": tratamiento,
                                "observaciones": observaciones,
                                "medico": st.session_state.usuario['nombre_completo']
                            }
                            
                            response = api_request("POST", "/api/consultas", datos)
                            if response and response.status_code == 200:
                                st.success("✅ Consulta registrada")
                                st.balloons()
                            elif response:
                                st.error(f"❌ {response.json().get('detail')}")

with tab2:
    st.subheader("📚 Historial de Consultas")
    
    if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
        st.error("❌ Solo personal médico puede ver historiales.")
    else:
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()), key="hist")
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                response = api_request("GET", f"/api/consultas/paciente/{paciente_id}")
                if response and response.status_code == 200:
                    consultas = response.json()
                    
                    if consultas:
                        st.info(f"📊 Total: {len(consultas)} consulta(s)")
                        
                        for c in consultas:
                            fecha = datetime.fromisoformat(c['fecha'].replace('Z', '+00:00'))
                            
                            with st.expander(f"📅 {fecha.strftime('%d/%m/%Y %H:%M')} - Dr. {c['medico']}"):
                                st.markdown(f"### {c['motivo']}")
                                
                                if c['signos_vitales']:
                                    st.markdown("**📊 Signos Vitales:**")
                                    st.info(c['signos_vitales'])
                                
                                if c['sintomas']:
                                    st.markdown("**🩺 Síntomas:**")
                                    st.write(c['sintomas'])
                                
                                if c['diagnostico']:
                                    st.markdown("**🔬 Diagnóstico:**")
                                    st.success(c['diagnostico'])
                                
                                if c['tratamiento']:
                                    st.markdown("**💊 Tratamiento:**")
                                    st.write(c['tratamiento'])
                    else:
                        st.info("📭 Sin consultas registradas")