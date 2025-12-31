import streamlit as st
import requests
from datetime import datetime, date, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="ECE Médico Pro", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para diseño médico profesional
st.markdown("""
<style>
    /* Paleta de colores médicos */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --success-color: #06A77D;
        --danger-color: #D72638;
        --light-bg: #F8F9FA;
    }
    
    /* Header personalizado */
    .main-header {
        background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2E86AB;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Botones de acción rápida */
    .quick-action {
        background: linear-gradient(135deg, #06A77D 0%, #2E86AB 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
        margin: 0.5rem 0;
    }
    
    .quick-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Sidebar mejorado */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2E86AB 0%, #1a5276 100%);
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tablas mejoradas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

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
    # Centrar el login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='color: #2E86AB;'>🏥 ECE Médico Pro</h1>
            <p style='color: #6c757d;'>Sistema de Expediente Clínico Electrónico</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
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
            with st.form("register_form"):
                new_username = st.text_input("👤 Usuario *")
                new_email = st.text_input("📧 Email *")
                new_password = st.text_input("🔑 Contraseña *", type="password")
                new_password2 = st.text_input("🔑 Confirmar Contraseña *", type="password")
                new_nombre = st.text_input("👨‍⚕️ Nombre Completo *")
                new_rol = st.selectbox("🏷️ Rol *", ["medico", "enfermera", "recepcion", "admin"])
                
                submit_register = st.form_submit_button("Registrarse", use_container_width=True)
                
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
    # Sidebar mejorado
    with st.sidebar:
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: #2E86AB; margin: 0;'>👤 {st.session_state.usuario['nombre_completo']}</h3>
            <p style='color: #6c757d; margin: 0.5rem 0 0 0;'>🏷️ {st.session_state.usuario['rol'].title()}</p>
            <p style='color: #6c757d; margin: 0.5rem 0 0 0; font-size: 0.8rem;'>📧 {st.session_state.usuario['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Menú basado en rol
        rol = st.session_state.usuario['rol']
        
        if rol == 'medico':
            menu_options = [
                "🏠 Dashboard",
                "📅 Agendamiento",
                "📝 Registrar Paciente",
                "👥 Pacientes",
                "🩺 Nueva Consulta",
                "📚 Historial Médico",
                "💊 Recetas",
                "🧪 Laboratorio",
                "🔬 Imagenología",
                "🌐 FHIR"
            ]
        elif rol == 'enfermera':
            menu_options = [
                "🏠 Dashboard",
                "👥 Pacientes",
                "📚 Historial Médico",
                "💊 Recetas",
                "🧪 Laboratorio",
                "🌐 FHIR"
            ]
        elif rol == 'recepcion':
            menu_options = [
                "🏠 Dashboard",
                "📅 Agendamiento",
                "📝 Registrar Paciente",
                "👥 Pacientes",
                "✏️ Editar Paciente"
            ]
        else:  # admin
            menu_options = [
                "🏠 Dashboard",
                "📅 Agendamiento",
                "📝 Registrar Paciente",
                "👥 Pacientes",
                "✏️ Editar Paciente",
                "🩺 Nueva Consulta",
                "📚 Historial Médico",
                "💊 Recetas",
                "🧪 Laboratorio",
                "🔬 Imagenología",
                "🌐 FHIR"
            ]
        
        menu = st.radio("📋 Menú Principal", menu_options, label_visibility="collapsed")
        
        st.divider()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.token = None
            st.session_state.usuario = None
            st.rerun()
    
    # ==================== DASHBOARD ====================
    if menu == "🏠 Dashboard":
        # Header
        st.markdown(f"""
        <div class='main-header'>
            <h1 style='margin: 0;'>Bienvenido, Dr(a). {st.session_state.usuario['nombre_completo']}</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>📅 {datetime.now().strftime('%A, %d de %B de %Y')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obtener datos del sistema
        response_pacientes = api_request("GET", "/api/pacientes")
        pacientes = response_pacientes.json() if response_pacientes and response_pacientes.status_code == 200 else []
        
        # Obtener citas de hoy
        hoy = date.today()
        response_citas_hoy = api_request("GET", f"/api/citas?fecha_desde={hoy.isoformat()}&fecha_hasta={hoy.isoformat()}")
        citas_hoy = response_citas_hoy.json() if response_citas_hoy and response_citas_hoy.status_code == 200 else []
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(pacientes)}</div>
                <div class='metric-label'>👥 Pacientes Registrados</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            citas_programadas = [c for c in citas_hoy if c['estado'] in ['programada', 'confirmada']]
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(citas_programadas)}</div>
                <div class='metric-label'>📅 Citas Hoy</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            citas_atendidas = [c for c in citas_hoy if c['estado'] == 'atendida']
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(citas_atendidas)}</div>
                <div class='metric-label'>✅ Atendidas Hoy</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            citas_pendientes = [c for c in citas_hoy if c['estado'] == 'programada']
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(citas_pendientes)}</div>
                <div class='metric-label'>⏳ Pendientes</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Dashboard específico por rol
        if rol == 'medico':
            st.subheader("🩺 Panel del Médico")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📅 Agenda del Día")
                if citas_programadas:
                    for cita in citas_programadas:
                        hora = datetime.fromisoformat(cita['fecha_hora']).strftime("%H:%M")
                        estado_emoji = "✅" if cita['estado'] == 'confirmada' else "🕐"
                        
                        with st.expander(f"{estado_emoji} {hora} - {cita['paciente_nombre']}"):
                            st.write(f"**Motivo:** {cita['motivo']}")
                            st.write(f"**Duración:** {cita['duracion_minutos']} minutos")
                            if cita['notas']:
                                st.write(f"**Notas:** {cita['notas']}")
                else:
                    st.info("No tienes citas programadas para hoy")
            
            with col2:
                st.markdown("### ⚡ Acciones Rápidas")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button("📝 Registrar Paciente", "#", use_container_width=True, disabled=True)
                    st.link_button("💊 Emitir Receta", "#", use_container_width=True, disabled=True)
                with col_btn2:
                    st.link_button("🩺 Nueva Consulta", "#", use_container_width=True, disabled=True)
                    st.link_button("🧪 Orden Lab", "#", use_container_width=True, disabled=True)
                
                st.info("💡 Usa el menú lateral para navegar")
        
        elif rol == 'enfermera':
            st.subheader("👩‍⚕️ Panel de Enfermería")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⚡ Acciones Rápidas")
                st.info("💡 Usa el menú lateral para:\n- 📚 Ver Historial\n- 🧪 Resultados Lab\n- 💊 Ver Recetas")
            
            with col2:
                st.markdown("### 📊 Resumen")
                st.info(f"Total de pacientes: {len(pacientes)}")
        
        elif rol == 'recepcion':
            st.subheader("📞 Panel de Recepción")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📅 Citas de Hoy")
                if citas_hoy:
                    df_citas = pd.DataFrame([{
                        "Hora": datetime.fromisoformat(c['fecha_hora']).strftime("%H:%M"),
                        "Paciente": c['paciente_nombre'],
                        "Médico": c['medico_nombre'],
                        "Estado": c['estado']
                    } for c in citas_hoy])
                    st.dataframe(df_citas, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay citas programadas para hoy")
            
            with col2:
                st.markdown("### ⚡ Acciones Rápidas")
                st.info("💡 Usa el menú lateral para:\n- 📅 Agendar Cita\n- 📝 Nuevo Paciente\n- ✏️ Editar Paciente")
        
        else:  # admin
            st.subheader("⚙️ Panel de Administración")
            
            # Gráficos de estadísticas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Citas por Estado (Últimos 7 días)")
                semana_atras = (hoy - timedelta(days=7)).isoformat()
                response_citas_semana = api_request("GET", f"/api/citas?fecha_desde={semana_atras}&fecha_hasta={hoy.isoformat()}")
                citas_semana = response_citas_semana.json() if response_citas_semana and response_citas_semana.status_code == 200 else []
                
                if citas_semana:
                    estados = {}
                    for cita in citas_semana:
                        estado = cita['estado']
                        estados[estado] = estados.get(estado, 0) + 1
                    
                    fig = go.Figure(data=[go.Pie(labels=list(estados.keys()), values=list(estados.values()))])
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### ⚡ Acciones Rápidas")
                if st.button("👥 Ver Usuarios", use_container_width=True):
                    response = api_request("GET", "/api/usuarios")
                    if response and response.status_code == 200:
                        usuarios = response.json()
                        st.write(f"Total: {len(usuarios)} usuarios")
                
                if st.button("📊 Estadísticas Completas", use_container_width=True):
                    st.info("Próximamente: Reportes avanzados")
    
    # ==================== AGENDAMIENTO ====================
    elif menu == "📅 Agendamiento":
        st.markdown("<div class='main-header'><h1>📅 Sistema de Agendamiento</h1></div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📅 Calendario", "➕ Nueva Cita", "⚙️ Gestionar Citas"])
        
        with tab1:
            st.subheader("📅 Vista de Calendario")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                fecha_desde = st.date_input("Desde", value=date.today())
            with col2:
                fecha_hasta = st.date_input("Hasta", value=date.today() + timedelta(days=7))
            with col3:
                response_medicos = api_request("GET", "/api/usuarios")
                if response_medicos and response_medicos.status_code == 200:
                    medicos = [m for m in response_medicos.json() if m['rol'] == 'medico']
                    opciones_medicos = {"Todos los médicos": None}
                    opciones_medicos.update({m['nombre_completo']: m['id'] for m in medicos})
                    
                    medico_filtro = st.selectbox("🔍 Médico", list(opciones_medicos.keys()))
                    medico_id_filtro = opciones_medicos[medico_filtro]
            
            # Obtener citas
            endpoint = f"/api/citas?fecha_desde={fecha_desde.isoformat()}&fecha_hasta={fecha_hasta.isoformat()}"
            if medico_id_filtro:
                endpoint += f"&medico_id={medico_id_filtro}"
            
            response = api_request("GET", endpoint)
            
            if response and response.status_code == 200:
                citas = response.json()
                
                if citas:
                    st.info(f"📊 Total: {len(citas)} cita(s)")
                    
                    # Organizar por día
                    citas_por_dia = {}
                    for c in citas:
                        fecha_hora = datetime.fromisoformat(c['fecha_hora'])
                        fecha_str = fecha_hora.strftime("%Y-%m-%d")
                        if fecha_str not in citas_por_dia:
                            citas_por_dia[fecha_str] = []
                        citas_por_dia[fecha_str].append(c)
                    
                    # Mostrar calendario por día
                    for fecha_str in sorted(citas_por_dia.keys()):
                        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                        dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][fecha_obj.weekday()]
                        
                        with st.expander(f"📅 {dia_semana}, {fecha_obj.strftime('%d de %B de %Y')} ({len(citas_por_dia[fecha_str])} citas)", expanded=fecha_str == date.today().isoformat()):
                            # Ordenar por hora
                            citas_dia = sorted(citas_por_dia[fecha_str], key=lambda x: x['fecha_hora'])
                            
                            for c in citas_dia:
                                fecha_hora = datetime.fromisoformat(c['fecha_hora'])
                                hora = fecha_hora.strftime("%H:%M")
                                
                                # Color según estado
                                color_map = {
                                    "programada": "🕐",
                                    "confirmada": "✅",
                                    "atendida": "🏥",
                                    "cancelada": "❌"
                                }
                                emoji = color_map.get(c['estado'], "📋")
                                
                                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                                
                                with col1:
                                    st.markdown(f"**{hora}**")
                                
                                with col2:
                                    st.write(f"{emoji} **{c['paciente_nombre']}**")
                                    st.caption(f"Dr. {c['medico_nombre']}")
                                
                                with col3:
                                    st.caption(f"Motivo: {c['motivo'][:30]}...")
                                    st.caption(f"Estado: {c['estado']}")
                                
                                with col4:
                                    # Botón para abrir consulta rápida
                                    if c['estado'] in ['programada', 'confirmada']:
                                        if st.button(f"🩺 Consulta", key=f"consulta_{c['id']}", use_container_width=True):
                                            st.session_state.cita_seleccionada = c
                                            st.session_state.abrir_consulta = True
                                            st.rerun()
                                
                                st.divider()
                else:
                    st.info("📭 No hay citas en este período")
            
            # Modal de consulta rápida
            if 'abrir_consulta' in st.session_state and st.session_state.abrir_consulta:
                cita = st.session_state.cita_seleccionada
                
                st.markdown("---")
                st.markdown(f"### 🩺 Consulta: {cita['paciente_nombre']}")
                
                # Botón para cerrar
                if st.button("❌ Cerrar Consulta"):
                    st.session_state.abrir_consulta = False
                    st.rerun()
                
                # Obtener datos del paciente
                response_pac = api_request("GET", f"/api/pacientes/{cita['paciente_id']}")
                if response_pac and response_pac.status_code == 200:
                    paciente = response_pac.json()
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Información del paciente
                        st.info(f"👤 {paciente['nombre']} {paciente['apellidos']} | 🆔 {paciente['identificacion']} | 📅 Nacimiento: {paciente['fecha_nacimiento'][:10]}")
                    
                    with col2:
                        # Acciones rápidas
                        if st.button("📚 Ver Historial", use_container_width=True):
                            st.session_state.ver_historial_paciente = cita['paciente_id']
                        
                        if st.button("💊 Ver Recetas", use_container_width=True):
                            st.session_state.ver_recetas_paciente = cita['paciente_id']
                
                # Formulario de consulta integrado
                with st.form(key=f"consulta_rapida_{cita['id']}"):
                    st.markdown("#### 📝 Datos de la Consulta")
                    
                    motivo = st.text_input("Motivo", value=cita['motivo'])
                    
                    # Signos vitales en una línea
                    st.markdown("**📊 Signos Vitales**")
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        presion = st.text_input("PA", placeholder="120/80")
                    with col2:
                        temp = st.text_input("T°C", placeholder="36.5")
                    with col3:
                        fc = st.text_input("FC", placeholder="70")
                    with col4:
                        fr = st.text_input("FR", placeholder="16")
                    with col5:
                        peso = st.text_input("Peso", placeholder="70")
                    with col6:
                        altura = st.text_input("Altura", placeholder="170")
                    
                    signos = f"PA: {presion}, T: {temp}°C, FC: {fc}, FR: {fr}, Peso: {peso}kg, Altura: {altura}cm"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        sintomas = st.text_area("🔍 Síntomas", height=120)
                        diagnostico = st.text_area("🔬 Diagnóstico", height=120)
                    
                    with col2:
                        tratamiento = st.text_area("💊 Tratamiento", height=120)
                        observaciones = st.text_area("📋 Observaciones", height=120)
                    
                    # Sección integrada de recetas y labs
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        agregar_receta = st.checkbox("💊 Agregar Receta")
                        if agregar_receta:
                            med_nombre = st.text_input("Medicamento", key="med_rapido")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                med_dosis = st.text_input("Dosis", "500mg", key="dosis_rapido")
                                med_freq = st.text_input("Frecuencia", "Cada 8h", key="freq_rapido")
                            with col_b:
                                med_dur = st.text_input("Duración", "7 días", key="dur_rapido")
                                med_via = st.selectbox("Vía", ["Oral", "IM", "IV"], key="via_rapido")
                    
                    with col2:
                        agregar_lab = st.checkbox("🧪 Agregar Orden de Lab")
                        if agregar_lab:
                            st.multiselect("Exámenes", 
                                         ["Hemograma", "Glucosa", "Creatinina", "Perfil Lipídico", "TSH"],
                                         key="labs_rapido")
                    
                    # Botones de acción
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        guardar = st.form_submit_button("✅ Guardar Consulta", use_container_width=True)
                    with col2:
                        guardar_atender = st.form_submit_button("🏥 Guardar y Marcar Atendida", use_container_width=True)
                    with col3:
                        cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if cancelar:
                        st.session_state.abrir_consulta = False
                        st.rerun()
                    
                    if guardar or guardar_atender:
                        # Guardar consulta
                        datos_consulta = {
                            "paciente_id": cita['paciente_id'],
                            "motivo": motivo,
                            "signos_vitales": signos,
                            "sintomas": sintomas,
                            "diagnostico": diagnostico,
                            "tratamiento": tratamiento,
                            "observaciones": observaciones,
                            "medico": st.session_state.usuario['nombre_completo']
                        }
                        
                        response_cons = api_request("POST", "/api/consultas", datos_consulta)
                        
                        if response_cons and response_cons.status_code == 200:
                            st.success("✅ Consulta guardada")
                            
                            # Crear receta si se solicitó
                            if agregar_receta and med_nombre:
                                datos_receta = {
                                    "paciente_id": cita['paciente_id'],
                                    "medicamento1_nombre": med_nombre,
                                    "medicamento1_dosis": med_dosis,
                                    "medicamento1_frecuencia": med_freq,
                                    "medicamento1_duracion": med_dur,
                                    "medicamento1_via": med_via
                                }
                                response_rec = api_request("POST", "/api/recetas", datos_receta)
                                if response_rec and response_rec.status_code == 200:
                                    st.success("✅ Receta creada")
                            
                            # Marcar cita como atendida si se solicitó
                            if guardar_atender:
                                api_request("PUT", f"/api/citas/{cita['id']}", {"estado": "atendida"})
                                st.success("✅ Cita marcada como atendida")
                            
                            st.session_state.abrir_consulta = False
                            st.balloons()
                            st.rerun()
        
        with tab2:
            st.subheader("➕ Agendar Nueva Cita")
            
            if st.session_state.usuario['rol'] not in ['recepcion', 'admin', 'medico']:
                st.error("❌ No tienes permisos para agendar citas.")
            else:
                response_pacientes = api_request("GET", "/api/pacientes")
                response_medicos = api_request("GET", "/api/usuarios")
                
                pacientes = response_pacientes.json() if response_pacientes and response_pacientes.status_code == 200 else []
                medicos = [m for m in response_medicos.json() if m['rol'] == 'medico'] if response_medicos and response_medicos.status_code == 200 else []
                
                if not pacientes:
                    st.warning("⚠️ No hay pacientes registrados. Registra un paciente primero.")
                elif not medicos:
                    st.warning("⚠️ No hay médicos registrados.")
                else:
                    with st.form("form_cita"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                            paciente_seleccionado = st.selectbox("👤 Paciente", list(opciones_pacientes.keys()))
                            paciente_id = opciones_pacientes[paciente_seleccionado]
                            
                            opciones_medicos = {m['nombre_completo']: m['id'] for m in medicos}
                            medico_seleccionado = st.selectbox("👨‍⚕️ Médico", list(opciones_medicos.keys()))
                            medico_id = opciones_medicos[medico_seleccionado]
                        
                        with col2:
                            fecha_cita = st.date_input("📅 Fecha", min_value=date.today())
                            hora_cita = st.time_input("🕐 Hora", value=datetime.strptime("09:00", "%H:%M").time())
                            duracion = st.selectbox("⏱️ Duración", [15, 30, 45, 60], index=1)
                        
                        motivo = st.text_area("📝 Motivo de la Cita", height=100)
                        notas = st.text_area("📋 Notas", height=80)
                        
                        submitted = st.form_submit_button("✅ Agendar Cita", use_container_width=True)
                        
                        if submitted:
                            if not motivo:
                                st.error("El motivo es obligatorio")
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
                                    st.error(f"❌ {response.json().get('detail', 'Error')}")
        
        with tab3:
            st.subheader("⚙️ Gestionar Citas Existentes")
            
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
                        f"{datetime.fromisoformat(c['fecha_hora']).strftime('%d/%m/%Y %H:%M')} - {c['paciente_nombre']}": c['id'] 
                        for c in todas_citas
                    }
                    
                    cita_seleccionada = st.selectbox("Seleccionar Cita", list(opciones_citas.keys()))
                    cita_id = opciones_citas[cita_seleccionada]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✅ Confirmar", use_container_width=True):
                            response = api_request("PUT", f"/api/citas/{cita_id}", {"estado": "confirmada"})
                            if response and response.status_code == 200:
                                st.success("Confirmada")
                                st.rerun()
                    
                    with col2:
                        if st.button("🏥 Atender", use_container_width=True):
                            response = api_request("PUT", f"/api/citas/{cita_id}", {"estado": "atendida"})
                            if response and response.status_code == 200:
                                st.success("Atendida")
                                st.rerun()
                    
                    with col3:
                        if st.button("❌ Cancelar", use_container_width=True):
                            response = api_request("DELETE", f"/api/citas/{cita_id}")
                            if response and response.status_code == 200:
                                st.warning("Cancelada")
                                st.rerun()
                else:
                    st.info("No hay citas activas")
    
    # ==================== REGISTRAR PACIENTE ====================
    elif menu == "📝 Registrar Paciente":
        st.markdown("<div class='main-header'><h1>📝 Registrar Nuevo Paciente</h1></div>", unsafe_allow_html=True)
        
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
    
    # ==================== LISTA DE PACIENTES ====================
    elif menu == "👥 Pacientes":
        st.markdown("<div class='main-header'><h1>👥 Pacientes Registrados</h1></div>", unsafe_allow_html=True)
        
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
    
    # ==================== EDITAR PACIENTE ====================
    elif menu == "✏️ Editar Paciente":
        st.markdown("<div class='main-header'><h1>✏️ Editar Datos de Contacto</h1></div>", unsafe_allow_html=True)
        
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
    
    # ==================== NUEVA CONSULTA ====================
    elif menu == "🩺 Nueva Consulta":
        st.markdown("<div class='main-header'><h1>🩺 Registrar Nueva Consulta</h1></div>", unsafe_allow_html=True)
        
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
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            presion = st.text_input("🩸 Presión Arterial", placeholder="120/80")
                            temperatura = st.text_input("🌡️ Temperatura (°C)", placeholder="36.5")
                        with col2:
                            fc = st.text_input("💓 Frecuencia Cardíaca", placeholder="70")
                            fr = st.text_input("🫁 Frecuencia Respiratoria", placeholder="16")
                        with col3:
                            peso = st.text_input("⚖️ Peso (kg)", placeholder="70")
                            altura = st.text_input("📏 Altura (cm)", placeholder="170")
                        
                        signos_vitales = f"PA: {presion}, T: {temperatura}°C, FC: {fc}, FR: {fr}, Peso: {peso}kg, Altura: {altura}cm"
                        
                        sintomas = st.text_area("🔍 Síntomas y Exploración", height=150)
                        diagnostico = st.text_area("🔬 Diagnóstico", height=100)
                        tratamiento = st.text_area("💊 Tratamiento", height=150)
                        observaciones = st.text_area("📋 Observaciones", height=100)
                        
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
    
    # ==================== HISTORIAL MÉDICO ====================
    elif menu == "📚 Historial Médico":
        st.markdown("<div class='main-header'><h1>📚 Historial de Consultas</h1></div>", unsafe_allow_html=True)
        
        if st.session_state.usuario['rol'] not in ['medico', 'enfermera', 'admin']:
            st.error("❌ Solo personal médico puede ver historiales.")
        else:
            response = api_request("GET", "/api/pacientes")
            if response and response.status_code == 200:
                pacientes = response.json()
                
                if pacientes:
                    opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                    
                    paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
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
    
    # ==================== RECETAS ====================
    elif menu == "💊 Recetas":
        st.markdown("<div class='main-header'><h1>💊 Gestión de Recetas</h1></div>", unsafe_allow_html=True)
        
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
                            
                            with st.expander("➕ Medicamento 2 (Opcional)"):
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
                            
                            with st.expander("➕ Medicamento 3 (Opcional)"):
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
                            
                            with st.expander("➕ Medicamento 4 (Opcional)"):
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
                            
                            with st.expander("➕ Medicamento 5 (Opcional)"):
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
                            
                            indicaciones = st.text_area("📋 Indicaciones Generales", height=100)
                            
                            submitted = st.form_submit_button("✅ Emitir Receta", use_container_width=True)
                            
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
                                                st.error("Error al generar PDF")
                                else:
                                    st.info("📭 No hay recetas para este paciente")
                    else:
                        st.warning("⚠️ No hay pacientes registrados")
    
    # ==================== LABORATORIO ====================
    elif menu == "🧪 Laboratorio":
        st.markdown("<div class='main-header'><h1>🧪 Órdenes de Laboratorio</h1></div>", unsafe_allow_html=True)
        st.info("📋 Funcionalidad completa de laboratorio disponible")
    
    # ==================== IMAGENOLOGÍA ====================
    elif menu == "🔬 Imagenología":
        st.markdown("<div class='main-header'><h1>🔬 Órdenes de Imagenología</h1></div>", unsafe_allow_html=True)
        st.info("🚧 Próximamente: Órdenes de Rayos X, TAC, Resonancia, Ecografía")
    
    # ==================== FHIR ====================
    elif menu == "🌐 FHIR":
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