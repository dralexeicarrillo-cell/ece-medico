import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import sys
import os

# Agregar paths necesarios
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Importar después de agregar al path
import utils.api as api_module
import utils.styles as styles_module
import utils.auth as auth_module

api_request = api_module.api_request
apply_custom_css = styles_module.apply_custom_css
check_authentication = auth_module.check_authentication
show_user_info = auth_module.show_user_info

# Configuración
st.set_page_config(page_title="Agendamiento", page_icon="📅", layout="wide")
apply_custom_css()

# Verificar autenticación
check_authentication()

# Mostrar info del usuario
show_user_info()

# Header
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
                
                with st.expander(f"📅 {dia_semana}, {fecha_obj.strftime('%d de %B de %Y')} ({len(citas_por_dia[fecha_str])} citas)", 
                               expanded=fecha_str == date.today().isoformat()):
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
                        
                        col1, col2, col3 = st.columns([1, 3, 2])
                        
                        with col1:
                            st.markdown(f"**{hora}**")
                        
                        with col2:
                            st.write(f"{emoji} **{c['paciente_nombre']}**")
                            st.caption(f"Dr. {c['medico_nombre']}")
                        
                        with col3:
                            st.caption(f"Motivo: {c['motivo'][:30]}...")
                            st.caption(f"Estado: {c['estado']}")
                        
                        st.divider()
        else:
            st.info("📭 No hay citas en este período")

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
            st.warning("⚠️ No hay pacientes registrados.")
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