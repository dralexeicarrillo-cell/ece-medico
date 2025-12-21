import streamlit as st
import requests
from datetime import datetime, date
import json

st.set_page_config(page_title="ECE Médico", page_icon="🏥", layout="wide")

API_URL = "http://127.0.0.1:8000"

# Inicializar session_state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# Función para hacer requests con autenticación
def api_request(method, endpoint, data=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        return response
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

# ==================== PÁGINA DE LOGIN ====================
if st.session_state.token is None:
    st.title("🏥 ECE Médico - Sistema de Login")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.header("Iniciar Sesión")
        
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar")
            
            if submit:
                if not username or not password:
                    st.error("Por favor completa todos los campos")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/api/auth/login",
                            data={"username": username, "password": password}
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.usuario = data["usuario"]
                            st.success("✅ Inicio de sesión exitoso")
                            st.rerun()
                        else:
                            error = response.json().get("detail", "Error desconocido")
                            st.error(f"❌ {error}")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {str(e)}")
    
    with tab2:
        st.header("Crear Cuenta Nueva")
        
        with st.form("register_form"):
            new_username = st.text_input("Usuario *")
            new_email = st.text_input("Email *")
            new_password = st.text_input("Contraseña *", type="password")
            new_password2 = st.text_input("Confirmar Contraseña *", type="password")
            new_nombre = st.text_input("Nombre Completo *")
            new_rol = st.selectbox("Rol *", ["medico", "enfermera", "admin"])
            
            submit_register = st.form_submit_button("Registrarse")
            
            if submit_register:
                if not all([new_username, new_email, new_password, new_nombre]):
                    st.error("Por favor completa todos los campos obligatorios")
                elif new_password != new_password2:
                    st.error("Las contraseñas no coinciden")
                elif len(new_password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/api/auth/register",
                            json={
                                "username": new_username,
                                "email": new_email,
                                "password": new_password,
                                "nombre_completo": new_nombre,
                                "rol": new_rol
                            }
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Usuario registrado exitosamente. Ahora puedes iniciar sesión.")
                        else:
                            error = response.json().get("detail", "Error desconocido")
                            st.error(f"❌ {error}")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {str(e)}")

# ==================== PÁGINA PRINCIPAL (AUTENTICADO) ====================
else:
    # Barra lateral con información del usuario
    with st.sidebar:
        st.write(f"👤 **{st.session_state.usuario['nombre_completo']}**")
        st.write(f"🏷️ Rol: {st.session_state.usuario['rol']}")
        st.write(f"📧 {st.session_state.usuario['email']}")
        st.divider()
        
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.token = None
            st.session_state.usuario = None
            st.rerun()
    
    st.title("🏥 Expediente Clínico Electrónico")
    
    menu = st.sidebar.selectbox(
        "Menú Principal",
        ["Inicio", "Registrar Paciente", "Lista de Pacientes", "Nueva Consulta", "Historial de Consultas", "FHIR - Interoperabilidad"]
    )
    
    if menu == "Inicio":
        st.header("Bienvenido al Sistema ECE")
        
        response = api_request("GET", "/health")
        if response and response.status_code == 200:
            data = response.json()
            st.success(f"✅ Conexión con el servidor exitosa - FHIR: {data.get('fhir', 'disabled')}")
        else:
            st.error("❌ Error de conexión con el servidor")
        
        st.info("📋 Selecciona una opción del menú lateral para comenzar")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pacientes Registrados", "...")
        with col2:
            st.metric("Consultas Hoy", "...")
        with col3:
            st.metric("Pendientes", "...")
    
    elif menu == "Registrar Paciente":
        st.header("📝 Registrar Nuevo Paciente")
        
        with st.form("form_paciente"):
            col1, col2 = st.columns(2)
            
            with col1:
                identificacion = st.text_input("Identificación *")
                nombre = st.text_input("Nombre *")
                apellidos = st.text_input("Apellidos *")
                fecha_nacimiento = st.date_input("Fecha de Nacimiento *", max_value=date.today())
            
            with col2:
                genero = st.selectbox("Género *", ["Masculino", "Femenino", "Otro"])
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
            
            direccion = st.text_area("Dirección")
            
            submitted = st.form_submit_button("✅ Registrar Paciente")
            
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
                        st.error(f"❌ Error: {response.json().get('detail')}")
    
    elif menu == "Lista de Pacientes":
        st.header("👥 Pacientes Registrados")
        
        buscar = st.text_input("🔍 Buscar paciente por nombre o identificación")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if buscar:
                pacientes = [p for p in pacientes if 
                           buscar.lower() in p['nombre'].lower() or 
                           buscar.lower() in p['apellidos'].lower() or 
                           buscar in p['identificacion']]
            
            if pacientes:
                st.write(f"**Total: {len(pacientes)} paciente(s)**")
                
                for p in pacientes:
                    with st.expander(f"👤 {p['nombre']} {p['apellidos']} - {p['identificacion']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ID:** {p['id']}")
                            st.write(f"**Género:** {p['genero']}")
                            st.write(f"**Teléfono:** {p['telefono']}")
                        with col2:
                            st.write(f"**Email:** {p['email']}")
                            st.write(f"**Dirección:** {p['direccion']}")
            else:
                st.info("No hay pacientes registrados o no se encontraron resultados")
        elif response and response.status_code == 401:
            st.error("❌ Sesión expirada. Por favor inicia sesión de nuevo.")
            st.session_state.token = None
            st.session_state.usuario = None
            st.rerun()
    
    elif menu == "Nueva Consulta":
        st.header("🩺 Registrar Nueva Consulta")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados. Por favor registra un paciente primero.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                     for p in pacientes}
                
                paciente_seleccionado = st.selectbox("Seleccionar Paciente *", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                with st.form("form_consulta"):
                    st.subheader("Datos de la Consulta")
                    
                    motivo = st.text_area("Motivo de Consulta *", height=100)
                    
                    st.subheader("Signos Vitales")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        presion = st.text_input("Presión Arterial", placeholder="120/80")
                        temperatura = st.text_input("Temperatura (°C)", placeholder="36.5")
                    with col2:
                        frecuencia_cardiaca = st.text_input("Frecuencia Cardíaca", placeholder="70")
                        frecuencia_respiratoria = st.text_input("Frecuencia Respiratoria", placeholder="16")
                    with col3:
                        peso = st.text_input("Peso (kg)", placeholder="70")
                        altura = st.text_input("Altura (cm)", placeholder="170")
                    
                    signos_vitales = f"PA: {presion}, T: {temperatura}°C, FC: {frecuencia_cardiaca}, FR: {frecuencia_respiratoria}, Peso: {peso}kg, Altura: {altura}cm"
                    
                    sintomas = st.text_area("Síntomas y Exploración Física", height=150)
                    diagnostico = st.text_area("Diagnóstico", height=100)
                    tratamiento = st.text_area("Tratamiento y Prescripciones", height=150)
                    observaciones = st.text_area("Observaciones Adicionales", height=100)
                    
                    submitted = st.form_submit_button("✅ Guardar Consulta")
                    
                    if submitted:
                        if not motivo:
                            st.error("Por favor completa el motivo de consulta")
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
                                st.success("✅ Consulta registrada exitosamente")
                                st.balloons()
                            elif response:
                                st.error(f"❌ Error: {response.json().get('detail')}")
    
    elif menu == "Historial de Consultas":
        st.header("📚 Historial de Consultas")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                     for p in pacientes}
                
                paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                response = api_request("GET", f"/api/consultas/paciente/{paciente_id}")
                if response and response.status_code == 200:
                    consultas = response.json()
                    
                    if consultas:
                        st.write(f"**Total: {len(consultas)} consulta(s)**")
                        st.divider()
                        
                        for c in consultas:
                            fecha = datetime.fromisoformat(c['fecha'].replace('Z', '+00:00'))
                            
                            with st.expander(f"📅 {fecha.strftime('%d/%m/%Y %H:%M')} - Dr. {c['medico']}", expanded=False):
                                st.markdown(f"### {c['motivo']}")
                                
                                if c['signos_vitales']:
                                    st.markdown("**📊 Signos Vitales:**")
                                    st.info(c['signos_vitales'])
                                
                                if c['sintomas']:
                                    st.markdown("**🩺 Síntomas y Exploración:**")
                                    st.write(c['sintomas'])
                                
                                if c['diagnostico']:
                                    st.markdown("**🔬 Diagnóstico:**")
                                    st.success(c['diagnostico'])
                                
                                if c['tratamiento']:
                                    st.markdown("**💊 Tratamiento:**")
                                    st.write(c['tratamiento'])
                                
                                if c['observaciones']:
                                    st.markdown("**📝 Observaciones:**")
                                    st.write(c['observaciones'])
                    else:
                        st.info("📭 No hay consultas registradas para este paciente")
    
    elif menu == "FHIR - Interoperabilidad":
        st.header("🌐 FHIR - Interoperabilidad de Datos")
        
        st.info("📋 FHIR (Fast Healthcare Interoperability Resources) es el estándar internacional para intercambio de información médica")
        
        tab1, tab2, tab3 = st.tabs(["Exportar Paciente", "Exportar Consulta", "Exportar Expediente Completo"])
        
        with tab1:
            st.subheader("Exportar Paciente a formato FHIR")
            
            response = api_request("GET", "/api/pacientes")
            if response and response.status_code == 200:
                pacientes = response.json()
                
                if pacientes:
                    opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                         for p in pacientes}
                    
                    paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()), key="fhir_patient")
                    paciente_id = opciones_pacientes[paciente_seleccionado]
                    
                    if st.button("🔄 Convertir a FHIR Patient"):
                        response = api_request("GET", f"/fhir/Patient/{paciente_id}")
                        if response and response.status_code == 200:
                            fhir_data = response.json()
                            st.success("✅ Conversión exitosa a formato FHIR")
                            st.json(fhir_data)
                            
                            # Opción para descargar
                            st.download_button(
                                label="📥 Descargar JSON FHIR",
                                data=json.dumps(fhir_data, indent=2),
                                file_name=f"patient_{paciente_id}_fhir.json",
                                mime="application/json"
                            )
                else:
                    st.warning("No hay pacientes registrados")
        
        with tab2:
            st.subheader("Exportar Consulta a formato FHIR Bundle")
            
            response = api_request("GET", "/api/pacientes")
            if response and response.status_code == 200:
                pacientes = response.json()
                
                if pacientes:
                    opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                         for p in pacientes}
                    
                    paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()), key="fhir_encounter")
                    paciente_id = opciones_pacientes[paciente_seleccionado]
                    
                    # Obtener consultas del paciente
                    response = api_request("GET", f"/api/consultas/paciente/{paciente_id}")
                    if response and response.status_code == 200:
                        consultas = response.json()
                        
                        if consultas:
                            opciones_consultas = {f"{datetime.fromisoformat(c['fecha'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')} - {c['motivo'][:30]}...": c['id'] 
                                                for c in consultas}
                            
                            consulta_seleccionada = st.selectbox("Seleccionar Consulta", list(opciones_consultas.keys()))
                            consulta_id = opciones_consultas[consulta_seleccionada]
                            
                            if st.button("🔄 Convertir a FHIR Bundle"):
                                response = api_request("GET", f"/fhir/Bundle/consulta/{consulta_id}")
                                if response and response.status_code == 200:
                                    fhir_data = response.json()
                                    st.success("✅ Conversión exitosa a formato FHIR Bundle")
                                    st.json(fhir_data)
                                    
                                    st.download_button(
                                        label="📥 Descargar Bundle FHIR",
                                        data=json.dumps(fhir_data, indent=2),
                                        file_name=f"consulta_{consulta_id}_fhir_bundle.json",
                                        mime="application/json"
                                    )
                        else:
                            st.info("No hay consultas para este paciente")
        
        with tab3:
            st.subheader("Exportar Expediente Completo a formato FHIR Bundle")
            
            response = api_request("GET", "/api/pacientes")
            if response and response.status_code == 200:
                pacientes = response.json()
                
                if pacientes:
                    opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                         for p in pacientes}
                    
                    paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()), key="fhir_bundle")
                    paciente_id = opciones_pacientes[paciente_seleccionado]
                    
                    if st.button("🔄 Exportar Expediente Completo"):
                        response = api_request("GET", f"/fhir/Bundle/paciente/{paciente_id}")
                        if response and response.status_code == 200:
                            fhir_data = response.json()
                            st.success("✅ Expediente completo exportado a formato FHIR Bundle")
                            
                            # Mostrar resumen
                            num_entries = len(fhir_data.get('entry', []))
                            st.info(f"📦 Bundle contiene {num_entries} recursos FHIR")
                            
                            st.json(fhir_data)
                            
                            st.download_button(
                                label="📥 Descargar Expediente Completo FHIR",
                                data=json.dumps(fhir_data, indent=2),
                                file_name=f"expediente_paciente_{paciente_id}_fhir.json",
                                mime="application/json"
                            )
                else:
                    st.warning("No hay pacientes registrados")