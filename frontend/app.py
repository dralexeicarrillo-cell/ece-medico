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
        ["Inicio", "Agendamiento", "Registrar Paciente", "Lista de Pacientes", "Editar Paciente", "Nueva Consulta", "Historial de Consultas", "Recetas Médicas", "Órdenes de Laboratorio", "FHIR - Interoperabilidad"]
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
    
    elif menu == "Recetas Médicas":
        st.header("💊 Gestión de Recetas Médicas")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'admin']:
            st.error("❌ No tienes permisos para emitir recetas. Esta función es solo para médicos.")
        else:
            tab1, tab2 = st.tabs(["Nueva Receta", "Historial de Recetas"])
            
            with tab1:
                st.subheader("📝 Emitir Nueva Receta")
                
                response = api_request("GET", "/api/pacientes")
                if response and response.status_code == 200:
                    pacientes = response.json()
                    
                    if not pacientes:
                        st.warning("⚠️ No hay pacientes registrados.")
                    else:
                        opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                             for p in pacientes}
                        
                        paciente_seleccionado = st.selectbox("Seleccionar Paciente *", list(opciones_pacientes.keys()))
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        with st.form("form_receta"):
                            st.subheader("Medicamentos (mínimo 1, máximo 5)")
                            
                            # Medicamento 1 (obligatorio)
                            st.markdown("#### Medicamento 1 *")
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
                            
                            # Medicamentos opcionales 2-5
                            with st.expander("Medicamento 2 (opcional)"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    med2_nombre = st.text_input("Nombre", key="med2_nombre")
                                    med2_dosis = st.text_input("Dosis", placeholder="500mg", key="med2_dosis")
                                    med2_frecuencia = st.text_input("Frecuencia", placeholder="Cada 8 horas", key="med2_frecuencia")
                                with col2:
                                    med2_duracion = st.text_input("Duración", placeholder="7 días", key="med2_duracion")
                                    med2_via = st.selectbox("Vía de Administración", 
                                                     ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                                     key="med2_via")
                            
                            with st.expander("Medicamento 3 (opcional)"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    med3_nombre = st.text_input("Nombre", key="med3_nombre")
                                    med3_dosis = st.text_input("Dosis", placeholder="500mg", key="med3_dosis")
                                    med3_frecuencia = st.text_input("Frecuencia", placeholder="Cada 8 horas", key="med3_frecuencia")
                                with col2:
                                    med3_duracion = st.text_input("Duración", placeholder="7 días", key="med3_duracion")
                                    med3_via = st.selectbox("Vía de Administración", 
                                                     ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                                     key="med3_via")
                            
                            with st.expander("Medicamento 4 (opcional)"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    med4_nombre = st.text_input("Nombre", key="med4_nombre")
                                    med4_dosis = st.text_input("Dosis", placeholder="500mg", key="med4_dosis")
                                    med4_frecuencia = st.text_input("Frecuencia", placeholder="Cada 8 horas", key="med4_frecuencia")
                                with col2:
                                    med4_duracion = st.text_input("Duración", placeholder="7 días", key="med4_duracion")
                                    med4_via = st.selectbox("Vía de Administración", 
                                                     ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                                     key="med4_via")
                            
                            with st.expander("Medicamento 5 (opcional)"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    med5_nombre = st.text_input("Nombre", key="med5_nombre")
                                    med5_dosis = st.text_input("Dosis", placeholder="500mg", key="med5_dosis")
                                    med5_frecuencia = st.text_input("Frecuencia", placeholder="Cada 8 horas", key="med5_frecuencia")
                                with col2:
                                    med5_duracion = st.text_input("Duración", placeholder="7 días", key="med5_duracion")
                                    med5_via = st.selectbox("Vía de Administración", 
                                                     ["Oral", "Intramuscular", "Intravenosa", "Subcutánea", "Tópica", "Oftálmica", "Ótica"],
                                                     key="med5_via")
                            
                            indicaciones = st.text_area("Indicaciones Generales", height=100)
                            
                            submitted = st.form_submit_button("✅ Emitir Receta")
                            
                            if submitted:
                                if not med1_nombre or not med1_dosis or not med1_frecuencia or not med1_duracion:
                                    st.error("Debes completar al menos el medicamento 1 con todos sus campos obligatorios")
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
                                    
                                    # Agregar medicamentos opcionales solo si tienen nombre
                                    if med2_nombre:
                                        datos_receta.update({
                                            "medicamento2_nombre": med2_nombre,
                                            "medicamento2_dosis": med2_dosis,
                                            "medicamento2_frecuencia": med2_frecuencia,
                                            "medicamento2_duracion": med2_duracion,
                                            "medicamento2_via": med2_via
                                        })
                                    
                                    if med3_nombre:
                                        datos_receta.update({
                                            "medicamento3_nombre": med3_nombre,
                                            "medicamento3_dosis": med3_dosis,
                                            "medicamento3_frecuencia": med3_frecuencia,
                                            "medicamento3_duracion": med3_duracion,
                                            "medicamento3_via": med3_via
                                        })
                                    
                                    if med4_nombre:
                                        datos_receta.update({
                                            "medicamento4_nombre": med4_nombre,
                                            "medicamento4_dosis": med4_dosis,
                                            "medicamento4_frecuencia": med4_frecuencia,
                                            "medicamento4_duracion": med4_duracion,
                                            "medicamento4_via": med4_via
                                        })
                                    
                                    if med5_nombre:
                                        datos_receta.update({
                                            "medicamento5_nombre": med5_nombre,
                                            "medicamento5_dosis": med5_dosis,
                                            "medicamento5_frecuencia": med5_frecuencia,
                                            "medicamento5_duracion": med5_duracion,
                                            "medicamento5_via": med5_via
                                        })
                                    
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
                        opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                             for p in pacientes}
                        
                        paciente_seleccionado = st.selectbox("Buscar recetas del paciente", list(opciones_pacientes.keys()), key="historial_paciente")
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        if st.button("🔍 Buscar Recetas"):
                            response = api_request("GET", f"/api/recetas/paciente/{paciente_id}")
                            
                            if response and response.status_code == 200:
                                recetas = response.json()
                                
                                if recetas:
                                    st.write(f"**Total: {len(recetas)} receta(s)**")
                                    st.divider()
                                    
                                    for r in recetas:
                                        with st.expander(f"📄 Receta #{r['id']} - {r['fecha_emision'][:10]} - Dr. {r.get('medico_nombre', 'N/A')}"):
                                            st.write("**Medicamentos:**")
                                            
                                            if r.get('medicamento1_nombre'):
                                                st.markdown(f"**1. {r['medicamento1_nombre']}**")
                                                st.write(f"   • Dosis: {r['medicamento1_dosis']}")
                                                st.write(f"   • Frecuencia: {r['medicamento1_frecuencia']}")
                                                st.write(f"   • Duración: {r['medicamento1_duracion']}")
                                                st.write(f"   • Vía: {r['medicamento1_via']}")
                                            
                                            if r.get('medicamento2_nombre'):
                                                st.markdown(f"**2. {r['medicamento2_nombre']}**")
                                                st.write(f"   • Dosis: {r['medicamento2_dosis']}")
                                                st.write(f"   • Frecuencia: {r['medicamento2_frecuencia']}")
                                                st.write(f"   • Duración: {r['medicamento2_duracion']}")
                                                st.write(f"   • Vía: {r['medicamento2_via']}")
                                            
                                            if r.get('medicamento3_nombre'):
                                                st.markdown(f"**3. {r['medicamento3_nombre']}**")
                                                st.write(f"   • Dosis: {r['medicamento3_dosis']}")
                                                st.write(f"   • Frecuencia: {r['medicamento3_frecuencia']}")
                                                st.write(f"   • Duración: {r['medicamento3_duracion']}")
                                                st.write(f"   • Vía: {r['medicamento3_via']}")
                                            
                                            if r.get('medicamento4_nombre'):
                                                st.markdown(f"**4. {r['medicamento4_nombre']}**")
                                                st.write(f"   • Dosis: {r['medicamento4_dosis']}")
                                                st.write(f"   • Frecuencia: {r['medicamento4_frecuencia']}")
                                                st.write(f"   • Duración: {r['medicamento4_duracion']}")
                                                st.write(f"   • Vía: {r['medicamento4_via']}")
                                            
                                            if r.get('medicamento5_nombre'):
                                                st.markdown(f"**5. {r['medicamento5_nombre']}**")
                                                st.write(f"   • Dosis: {r['medicamento5_dosis']}")
                                                st.write(f"   • Frecuencia: {r['medicamento5_frecuencia']}")
                                                st.write(f"   • Duración: {r['medicamento5_duracion']}")
                                                st.write(f"   • Vía: {r['medicamento5_via']}")
                                            
                                            if r.get('indicaciones_generales'):
                                                st.markdown("**Indicaciones Generales:**")
                                                st.info(r['indicaciones_generales'])
                                            
                                            st.divider()
                                            
                                            st.divider()
                                            
                                            # BOTÓN PARA GENERAR Y DESCARGAR PDF DIRECTAMENTE
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
                                                st.error("Error al generar PDF. Verifica que el backend esté corriendo.")


    elif menu == "Órdenes de Laboratorio":
        st.header("🧪 Órdenes de Laboratorio")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
            st.error("❌ No tienes permisos completos. Enfermeras pueden ver y agregar resultados.")
        
        tab1, tab2, tab3 = st.tabs(["Nueva Orden", "Historial de Órdenes", "Catálogo LOINC"])
        
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
                        
                        paciente_seleccionado = st.selectbox("Seleccionar Paciente *", list(opciones_pacientes.keys()))
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        # Obtener catálogo
                        response_catalogo = api_request("GET", "/api/laboratorio/catalogo")
                        if response_catalogo and response_catalogo.status_code == 200:
                            catalogo = response_catalogo.json()
                            
                            with st.form("form_orden_lab"):
                                st.subheader("Seleccionar Exámenes")
                                
                                examenes_seleccionados = []
                                
                                # Mostrar por categorías
                                for categoria, examenes in catalogo.items():
                                    with st.expander(f"📁 {categoria}"):
                                        for examen in examenes:
                                            if st.checkbox(f"{examen['nombre']} (LOINC: {examen['codigo']})", key=f"exam_{examen['key']}"):
                                                examenes_seleccionados.append({
                                                    "codigo_loinc": examen['codigo'],
                                                    "nombre": examen['nombre'],
                                                    "valor_referencia": examen['valor_referencia'],
                                                    "unidad": examen['unidad']
                                                })
                                
                                st.divider()
                                st.subheader("Información Clínica")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    diagnostico = st.text_area("Diagnóstico Presuntivo", height=100)
                                with col2:
                                    indicaciones = st.text_area("Indicaciones Clínicas", height=100)
                                
                                urgente = st.checkbox("⚠️ Marcar como URGENTE")
                                
                                submitted = st.form_submit_button("✅ Crear Orden de Laboratorio")
                                
                                if submitted:
                                    if not examenes_seleccionados:
                                        st.error("Debes seleccionar al menos un examen")
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
                    
                    paciente_seleccionado = st.selectbox("Buscar órdenes del paciente", list(opciones_pacientes.keys()), key="hist_lab_paciente")
                    paciente_id = opciones_pacientes[paciente_seleccionado]
                    
                    if st.button("🔍 Buscar Órdenes"):
                        response = api_request("GET", f"/api/laboratorio/paciente/{paciente_id}")
                        
                        if response and response.status_code == 200:
                            ordenes = response.json()
                            
                            if ordenes:
                                st.write(f"**Total: {len(ordenes)} orden(es)**")
                                st.divider()
                                
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
                                        st.markdown("### Exámenes Solicitados")
                                        
                                        # Mostrar exámenes
                                        for exam in orden['examenes']:
                                            st.markdown(f"**{exam['numero']}. {exam['nombre']}** (LOINC: {exam['codigo_loinc']})")
                                            
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
                                                st.markdown("#### Agregar/Actualizar Resultados")
                                                
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
    
    elif menu == "FHIR - Interoperabilidad":
        st.header("🌐 FHIR - Interoperabilidad de Datos")
        
        # Verificar permisos
        if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
            st.error("❌ No tienes permisos para exportar datos FHIR. Esta función es solo para personal médico.")
        else:
            st.info("📋 FHIR (Fast Healthcare Interoperability Resources) es el estándar internacional para intercambio de información médica")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Exportar Paciente", "Exportar Receta", "Exportar Orden Lab", "Importar FHIR"])
            
            with tab1:
                st.subheader("📤 Exportar Paciente a FHIR")
                
                response = api_request("GET", "/api/pacientes")
                if response and response.status_code == 200:
                    pacientes = response.json()
                    
                    if pacientes:
                        opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                        
                        paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()))
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        if st.button("📥 Exportar a FHIR"):
                            response = api_request("GET", f"/fhir/Patient/{paciente_id}")
                            
                            if response and response.status_code == 200:
                                fhir_data = response.json()
                                st.success("✅ Paciente exportado a FHIR")
                                
                                st.json(fhir_data)
                                
                                st.download_button(
                                    label="⬇️ Descargar JSON",
                                    data=json.dumps(fhir_data, indent=2),
                                    file_name=f"paciente_{paciente_id}_fhir.json",
                                    mime="application/json"
                                )
            
            with tab2:
                st.subheader("📤 Exportar Receta a FHIR")
                
                response = api_request("GET", "/api/pacientes")
                if response and response.status_code == 200:
                    pacientes = response.json()
                    
                    if pacientes:
                        opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                        
                        paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()), key="export_receta_paciente")
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        # Obtener recetas del paciente
                        response = api_request("GET", f"/api/recetas/paciente/{paciente_id}")
                        if response and response.status_code == 200:
                            recetas = response.json()
                            
                            if recetas:
                                opciones_recetas = {f"Receta #{r['id']} - {r['fecha_emision'][:10]}": r['id'] for r in recetas}
                                
                                receta_seleccionada = st.selectbox("Seleccionar Receta", list(opciones_recetas.keys()))
                                receta_id = opciones_recetas[receta_seleccionada]
                                
                                if st.button("📥 Exportar Receta a FHIR"):
                                    response = api_request("GET", f"/api/recetas/{receta_id}/fhir")
                                    
                                    if response and response.status_code == 200:
                                        fhir_data = response.json()
                                        st.success("✅ Receta exportada a FHIR Bundle")
                                        
                                        st.json(fhir_data)
                                        
                                        st.download_button(
                                            label="⬇️ Descargar FHIR Bundle (JSON)",
                                            data=json.dumps(fhir_data, indent=2),
                                            file_name=f"receta_{receta_id}_fhir_bundle.json",
                                            mime="application/json"
                                        )
                            else:
                                st.info("No hay recetas para este paciente")
            
            with tab3:
                st.subheader("📤 Exportar Orden de Laboratorio a FHIR")
                
                response = api_request("GET", "/api/pacientes")
                if response and response.status_code == 200:
                    pacientes = response.json()
                    
                    if pacientes:
                        opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                        
                        paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()), key="export_lab_paciente")
                        paciente_id = opciones_pacientes[paciente_seleccionado]
                        
                        # Obtener órdenes del paciente
                        response = api_request("GET", f"/api/laboratorio/paciente/{paciente_id}")
                        if response and response.status_code == 200:
                            ordenes = response.json()
                            
                            if ordenes:
                                opciones_ordenes = {f"Orden #{o['id']} - {o['fecha_orden'][:10]} - {o['estado']}": o['id'] for o in ordenes}
                                
                                orden_seleccionada = st.selectbox("Seleccionar Orden", list(opciones_ordenes.keys()))
                                orden_id = opciones_ordenes[orden_seleccionada]
                                
                                if st.button("📥 Exportar Orden a FHIR DiagnosticReport"):
                                    response = api_request("GET", f"/api/laboratorio/{orden_id}/fhir")
                                    
                                    if response and response.status_code == 200:
                                        fhir_data = response.json()
                                        st.success("✅ Orden exportada a FHIR Bundle (DiagnosticReport + Observations)")
                                        
                                        # Mostrar resumen
                                        st.info(f"📊 Bundle contiene: 1 Paciente, 1 DiagnosticReport, {len(fhir_data.get('entry', [])) - 2} Observations")
                                        
                                        st.json(fhir_data)
                                        
                                        st.download_button(
                                            label="⬇️ Descargar FHIR Bundle (JSON)",
                                            data=json.dumps(fhir_data, indent=2),
                                            file_name=f"orden_lab_{orden_id}_fhir_bundle.json",
                                            mime="application/json"
                                        )
                            else:
                                st.info("No hay órdenes de laboratorio para este paciente")
            
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
                    
                    if st.button("⬆️ Importar desde FHIR"):
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