import streamlit as st
import requests
from datetime import datetime, date, timedelta
import json
import pandas as pd

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
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
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
            new_rol = st.selectbox("Rol *", ["medico", "enfermera", "recepcion", "admin"])
            
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
        ["Inicio", "Agendamiento", "Registrar Paciente", "Lista de Pacientes", "Editar Paciente", "Nueva Consulta", "Historial de Consultas", "FHIR - Interoperabilidad"]
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
            st.metric("Citas Hoy", "...")
    
    elif menu == "Agendamiento":
        st.header("📅 Sistema de Agendamiento")
        
        tab1, tab2, tab3 = st.tabs(["Nueva Cita", "Calendario", "Gestionar Citas"])
        
        with tab1:
            st.subheader("Agendar Nueva Cita")
            
            # Verificar permisos
            if st.session_state.usuario['rol'] not in ['recepcion', 'admin', 'medico']:
                st.error("❌ No tienes permisos para agendar citas.")
            else:
                response_pacientes = api_request("GET", "/api/pacientes")
                response_medicos = api_request("GET", "/api/usuarios")
                
                if response_pacientes and response_pacientes.status_code == 200:
                    pacientes = response_pacientes.json()
                else:
                    pacientes = []
                
                if response_medicos and response_medicos.status_code == 200:
                    medicos = [m for m in response_medicos.json() if m['rol'] == 'medico']
                else:
                    medicos = []
                
                if not pacientes:
                    st.warning("⚠️ No hay pacientes registrados. Registra un paciente primero.")
                elif not medicos:
                    st.warning("⚠️ No hay médicos registrados.")
                else:
                    with st.form("form_cita"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                                 for p in pacientes}
                            paciente_seleccionado = st.selectbox("Paciente *", list(opciones_pacientes.keys()))
                            paciente_id = opciones_pacientes[paciente_seleccionado]
                            
                            opciones_medicos = {m['nombre_completo']: m['id'] for m in medicos}
                            medico_seleccionado = st.selectbox("Médico *", list(opciones_medicos.keys()))
                            medico_id = opciones_medicos[medico_seleccionado]
                        
                        with col2:
                            fecha_cita = st.date_input("Fecha *", min_value=date.today())
                            hora_cita = st.time_input("Hora *", value=datetime.strptime("09:00", "%H:%M").time())
                            duracion = st.selectbox("Duración (minutos) *", [15, 30, 45, 60], index=1)
                        
                        motivo = st.text_area("Motivo de la Cita *", height=100)
                        notas = st.text_area("Notas Adicionales", height=80)
                        
                        submitted = st.form_submit_button("✅ Agendar Cita")
                        
                        if submitted:
                            if not motivo:
                                st.error("Por favor completa el motivo de la cita")
                            else:
                                fecha_hora = datetime.combine(fecha_cita, hora_cita)
                                
                                datos = {
                                    "paciente_id": paciente_id,
                                    "medico_id": medico_id,
                                    "fecha_hora": fecha_hora.isoformat(),
                                    "duracion_minutos": duracion,
                                    "motivo": motivo,
                                    "notas": notas
                                }
                                
                                response = api_request("POST", "/api/citas", datos)
                                if response and response.status_code == 200:
                                    st.success("✅ Cita agendada exitosamente")
                                    st.balloons()
                                elif response:
                                    error = response.json().get('detail', 'Error desconocido')
                                    st.error(f"❌ {error}")
        
        with tab2:
            st.subheader("Calendario de Citas")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input("Desde", value=date.today())
            with col2:
                fecha_hasta = st.date_input("Hasta", value=date.today() + timedelta(days=7))
            
            response_medicos = api_request("GET", "/api/usuarios")
            if response_medicos and response_medicos.status_code == 200:
                medicos = [m for m in response_medicos.json() if m['rol'] == 'medico']
                opciones_medicos = {"Todos los médicos": None}
                opciones_medicos.update({m['nombre_completo']: m['id'] for m in medicos})
                
                medico_filtro = st.selectbox("Filtrar por médico", list(opciones_medicos.keys()))
                medico_id_filtro = opciones_medicos[medico_filtro]
            else:
                medico_id_filtro = None
            
            endpoint = f"/api/citas?fecha_desde={fecha_desde.isoformat()}&fecha_hasta={fecha_hasta.isoformat()}"
            if medico_id_filtro:
                endpoint += f"&medico_id={medico_id_filtro}"
            
            response = api_request("GET", endpoint)
            
            if response and response.status_code == 200:
                citas = response.json()
                
                if citas:
                    st.write(f"**Total: {len(citas)} cita(s)**")
                    
                    df_data = []
                    for c in citas:
                        fecha_hora = datetime.fromisoformat(c['fecha_hora'])
                        df_data.append({
                            "Fecha": fecha_hora.strftime("%d/%m/%Y"),
                            "Hora": fecha_hora.strftime("%H:%M"),
                            "Paciente": c['paciente_nombre'],
                            "Médico": c['medico_nombre'],
                            "Motivo": c['motivo'][:50] + "..." if len(c['motivo']) > 50 else c['motivo'],
                            "Estado": c['estado'],
                            "Duración": f"{c['duracion_minutos']} min"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.subheader("Detalles de Citas")
                    
                    for c in citas:
                        fecha_hora = datetime.fromisoformat(c['fecha_hora'])
                        
                        emoji_estado = {
                            "programada": "🗓️",
                            "confirmada": "✅",
                            "atendida": "🏥",
                            "cancelada": "❌"
                        }
                        
                        with st.expander(f"{emoji_estado.get(c['estado'], '📋')} {fecha_hora.strftime('%d/%m/%Y %H:%M')} - {c['paciente_nombre']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Paciente:** {c['paciente_nombre']}")
                                st.write(f"**Médico:** {c['medico_nombre']}")
                                st.write(f"**Estado:** {c['estado']}")
                            with col2:
                                st.write(f"**Duración:** {c['duracion_minutos']} minutos")
                                st.write(f"**Motivo:** {c['motivo']}")
                                if c['notas']:
                                    st.write(f"**Notas:** {c['notas']}")
                else:
                    st.info("📭 No hay citas programadas en este período")
        
        with tab3:
            st.subheader("Gestionar Citas Existentes")
            
            # Verificar permisos
            if st.session_state.usuario['rol'] not in ['recepcion', 'admin', 'medico']:
                st.error("❌ No tienes permisos para gestionar citas.")
            else:
                response = api_request("GET", "/api/citas?estado=programada")
                citas_programadas = response.json() if response and response.status_code == 200 else []
                
                response = api_request("GET", "/api/citas?estado=confirmada")
                citas_confirmadas = response.json() if response and response.status_code == 200 else []
                
                todas_citas = citas_programadas + citas_confirmadas
                
                if todas_citas:
                    opciones_citas = {
                        f"{datetime.fromisoformat(c['fecha_hora']).strftime('%d/%m/%Y %H:%M')} - {c['paciente_nombre']} con {c['medico_nombre']}": c['id'] 
                        for c in todas_citas
                    }
                    
                    cita_seleccionada = st.selectbox("Seleccionar Cita", list(opciones_citas.keys()))
                    cita_id = opciones_citas[cita_seleccionada]
                    
                    response = api_request("GET", f"/api/citas/{cita_id}")
                    if response and response.status_code == 200:
                        cita_detalle = response.json()
                        
                        st.divider()
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✅ Confirmar Cita", use_container_width=True):
                                response = api_request("PUT", f"/api/citas/{cita_id}", {"estado": "confirmada"})
                                if response and response.status_code == 200:
                                    st.success("Cita confirmada")
                                    st.rerun()
                        
                        with col2:
                            if st.button("🏥 Marcar como Atendida", use_container_width=True):
                                response = api_request("PUT", f"/api/citas/{cita_id}", {"estado": "atendida"})
                                if response and response.status_code == 200:
                                    st.success("Cita marcada como atendida")
                                    st.rerun()
                        
                        with col3:
                            if st.button("❌ Cancelar Cita", use_container_width=True, type="secondary"):
                                response = api_request("DELETE", f"/api/citas/{cita_id}")
                                if response and response.status_code == 200:
                                    st.warning("Cita cancelada")
                                    st.rerun()
                else:
                    st.info("No hay citas activas para gestionar")
    
    elif menu == "Registrar Paciente":
        st.header("📝 Registrar Nuevo Paciente")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['recepcion', 'admin', 'medico']:
            st.error("❌ No tienes permisos para registrar pacientes.")
        else:
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
    
    elif menu == "Editar Paciente":
        st.header("✏️ Editar Datos de Contacto del Paciente")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['recepcion', 'admin']:
            st.error("❌ No tienes permisos para editar pacientes. Esta función es solo para recepción y administradores.")
        else:
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
                    
                    response = api_request("GET", f"/api/pacientes/{paciente_id}")
                    if response and response.status_code == 200:
                        paciente_actual = response.json()
                        
                        st.divider()
                        st.subheader("Datos Actuales")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Nombre:** {paciente_actual['nombre']} {paciente_actual['apellidos']}")
                            st.write(f"**Identificación:** {paciente_actual['identificacion']}")
                            st.write(f"**Género:** {paciente_actual['genero']}")
                        with col2:
                            st.write(f"**Teléfono:** {paciente_actual.get('telefono', 'N/A')}")
                            st.write(f"**Email:** {paciente_actual.get('email', 'N/A')}")
                            st.write(f"**Dirección:** {paciente_actual.get('direccion', 'N/A')}")
                        
                        st.divider()
                        st.subheader("Actualizar Datos de Contacto")
                        st.info("ℹ️ Solo puedes modificar teléfono, email y dirección")
                        
                        with st.form("form_editar_paciente"):
                            nuevo_telefono = st.text_input("Nuevo Teléfono", value=paciente_actual.get('telefono', ''))
                            nuevo_email = st.text_input("Nuevo Email", value=paciente_actual.get('email', ''))
                            nueva_direccion = st.text_area("Nueva Dirección", value=paciente_actual.get('direccion', ''))
                            
                            submitted = st.form_submit_button("✅ Guardar Cambios")
                            
                            if submitted:
                                datos_actualizados = {
                                    "telefono": nuevo_telefono,
                                    "email": nuevo_email,
                                    "direccion": nueva_direccion
                                }
                                
                                response = api_request("PUT", f"/api/pacientes/{paciente_id}", datos_actualizados)
                                if response and response.status_code == 200:
                                    st.success("✅ Datos actualizados exitosamente")
                                    st.rerun()
                                elif response:
                                    st.error(f"❌ Error: {response.json().get('detail')}")
    
    elif menu == "Nueva Consulta":
        st.header("🩺 Registrar Nueva Consulta")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'admin']:
            st.error("❌ No tienes permisos para crear consultas médicas. Esta función es solo para médicos.")
        else:
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
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
            st.error("❌ No tienes permisos para ver el historial médico. Esta función es solo para personal médico.")
        else:
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
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
            st.error("❌ No tienes permisos para exportar datos FHIR. Esta función es solo para personal médico.")
        else:
            st.info("📋 FHIR (Fast Healthcare Interoperability Resources) es el estándar internacional para intercambio de información médica")