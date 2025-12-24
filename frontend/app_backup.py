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
                "🩺 Nueva Consulta",
                "📚 Historial Médico",
                "💊 Recetas",
                "🧪 Laboratorio",
                "🔬 Imagenología",
                "👥 Pacientes",
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
                if st.button("🩺 Nueva Consulta", use_container_width=True):
                    st.session_state.menu = "🩺 Nueva Consulta"
                    st.rerun()
                
                if st.button("💊 Emitir Receta", use_container_width=True):
                    st.session_state.menu = "💊 Recetas"
                    st.rerun()
                
                if st.button("🧪 Orden de Laboratorio", use_container_width=True):
                    st.session_state.menu = "🧪 Laboratorio"
                    st.rerun()
                
                if st.button("📅 Ver Agenda", use_container_width=True):
                    st.session_state.menu = "📅 Agendamiento"
                    st.rerun()
        
        elif rol == 'enfermera':
            st.subheader("👩‍⚕️ Panel de Enfermería")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⚡ Acciones Rápidas")
                if st.button("📚 Ver Historial", use_container_width=True):
                    st.session_state.menu = "📚 Historial Médico"
                    st.rerun()
                
                if st.button("🧪 Resultados Lab", use_container_width=True):
                    st.session_state.menu = "🧪 Laboratorio"
                    st.rerun()
            
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
                if st.button("📅 Agendar Cita", use_container_width=True):
                    st.session_state.menu = "📅 Agendamiento"
                    st.rerun()
                
                if st.button("📝 Nuevo Paciente", use_container_width=True):
                    st.session_state.menu = "📝 Registrar Paciente"
                    st.rerun()
                
                if st.button("✏️ Editar Paciente", use_container_width=True):
                    st.session_state.menu = "✏️ Editar Paciente"
                    st.rerun()
        
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
    
    # ==================== RESTO DEL CÓDIGO (mantener igual) ====================
    # Aquí irían todas las demás secciones del menú...
    # Por ahora te muestro solo el Dashboard mejorado
    
    else:
        st.info(f"Sección '{menu}' - En construcción con el nuevo diseño")
        st.write("Las demás secciones del menú mantienen su funcionalidad actual.")
        st.write("¿Quieres que continúe migrando las otras secciones al nuevo diseño?")