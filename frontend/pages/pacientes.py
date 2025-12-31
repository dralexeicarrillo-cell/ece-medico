import streamlit as st
from datetime import date
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="Pacientes", page_icon="👥", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>👥 Gestión de Pacientes</h1></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Lista de Pacientes", "➕ Registrar Nuevo", "✏️ Editar Paciente"])

with tab1:
    st.subheader("📋 Pacientes Registrados")
    
    buscar = st.text_input("🔍 Buscar paciente", placeholder="Nombre, apellido o identificación")
    
    response = api_request("GET", "/api/pacientes")
    if response and response.status_code == 200:
        pacientes = response.json()
        
        if buscar:
            pacientes = [p for p in pacientes if 
                       buscar.lower() in p['nombre'].lower() or 
                       buscar.lower() in p['apellidos'].lower() or 
                       buscar in p['identificacion']]
        
        if pacientes:
            st.info(f"📊 Total: {len(pacientes)} paciente(s)")
            
            for p in pacientes:
                with st.expander(f"👤 {p['nombre']} {p['apellidos']} - {p['identificacion']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID Sistema:** {p['id']}")
                        st.write(f"**Género:** {p['genero']}")
                        st.write(f"**Teléfono:** {p['telefono']}")
                    with col2:
                        st.write(f"**Email:** {p['email']}")
                        st.write(f"**Dirección:** {p['direccion']}")
        else:
            st.warning("No se encontraron pacientes")

with tab2:
    st.subheader("📝 Registrar Nuevo Paciente")
    
    if st.session_state.usuario['rol'] not in ['recepcion', 'admin', 'medico']:
        st.error("❌ No tienes permisos para registrar pacientes.")
    else:
        with st.form("form_paciente"):
            col1, col2 = st.columns(2)
            
            with col1:
                identificacion = st.text_input("🆔 Identificación *")
                nombre = st.text_input("👤 Nombre *")
                apellidos = st.text_input("👤 Apellidos *")
                fecha_nacimiento = st.date_input("📅 Fecha de Nacimiento *", max_value=date.today())
            
            with col2:
                genero = st.selectbox("⚧️ Género *", ["Masculino", "Femenino", "Otro"])
                telefono = st.text_input("📞 Teléfono")
                email = st.text_input("📧 Email")
            
            direccion = st.text_area("🏠 Dirección")
            
            submitted = st.form_submit_button("✅ Registrar Paciente", use_container_width=True)
            
            if submitted:
                if not identificacion or not nombre or not apellidos:
                    st.error("Por favor completa los campos obligatorios (*)")
                else:
                    datos = {
                        "identificacion": identificacion,
                        "nombre": nombre,
                        "apellidos": apellidos,
                        "fecha_nacimiento": fecha_nacimiento.isoformat(),
                        "genero": genero,
                        "telefono": telefono,
                        "email": email,
                        "direccion": direccion
                    }
                    
                    response = api_request("POST", "/api/pacientes", datos)
                    if response and response.status_code == 200:
                        st.success(f"✅ Paciente {nombre} {apellidos} registrado exitosamente")
                        st.balloons()
                    elif response:
                        st.error(f"❌ {response.json().get('detail')}")

with tab3:
    st.subheader("✏️ Editar Datos de Contacto")
    
    if st.session_state.usuario['rol'] not in ['recepcion', 'admin']:
        st.error("❌ Solo recepción y administradores pueden editar pacientes.")
    else:
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                response = api_request("GET", f"/api/pacientes/{paciente_id}")
                if response and response.status_code == 200:
                    paciente_actual = response.json()
                    
                    st.info("ℹ️ Solo puedes modificar teléfono, email y dirección")
                    
                    with st.form("form_editar_paciente"):
                        nuevo_telefono = st.text_input("📞 Nuevo Teléfono", value=paciente_actual.get('telefono', ''))
                        nuevo_email = st.text_input("📧 Nuevo Email", value=paciente_actual.get('email', ''))
                        nueva_direccion = st.text_area("🏠 Nueva Dirección", value=paciente_actual.get('direccion', ''))
                        
                        submitted = st.form_submit_button("✅ Guardar Cambios", use_container_width=True)
                        
                        if submitted:
                            datos = {
                                "telefono": nuevo_telefono,
                                "email": nuevo_email,
                                "direccion": nueva_direccion
                            }
                            
                            response = api_request("PUT", f"/api/pacientes/{paciente_id}", datos)
                            if response and response.status_code == 200:
                                st.success("✅ Datos actualizados")
                                st.rerun()