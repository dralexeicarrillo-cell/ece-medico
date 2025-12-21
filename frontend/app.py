import streamlit as st
import requests
from datetime import datetime, date

st.set_page_config(page_title="ECE Médico", page_icon="🏥", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🏥 Expediente Clínico Electrónico")

menu = st.sidebar.selectbox(
    "Menú Principal",
    ["Inicio", "Registrar Paciente", "Lista de Pacientes", "Nueva Consulta", "Historial de Consultas"]
)

if menu == "Inicio":
    st.header("Bienvenido al Sistema ECE")
    
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success("✅ Conexión con el servidor exitosa")
        else:
            st.error("❌ Error de conexión")
    except:
        st.error("❌ No se puede conectar. Verifica que el backend esté corriendo.")
    
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
                
                try:
                    response = requests.post(f"{API_URL}/api/pacientes", json=datos)
                    if response.status_code == 200:
                        st.success(f"✅ Paciente {nombre} {apellidos} registrado exitosamente")
                        st.balloons()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")

elif menu == "Lista de Pacientes":
    st.header("👥 Pacientes Registrados")
    
    buscar = st.text_input("🔍 Buscar paciente por nombre o identificación")
    
    try:
        response = requests.get(f"{API_URL}/api/pacientes")
        if response.status_code == 200:
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
    except Exception as e:
        st.error(f"Error al cargar pacientes: {str(e)}")

elif menu == "Nueva Consulta":
    st.header("🩺 Registrar Nueva Consulta")
    
    try:
        response = requests.get(f"{API_URL}/api/pacientes")
        pacientes = response.json() if response.status_code == 200 else []
        
        if not pacientes:
            st.warning("⚠️ No hay pacientes registrados. Por favor registra un paciente primero.")
        else:
            opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                 for p in pacientes}
            
            paciente_seleccionado = st.selectbox("Seleccionar Paciente *", list(opciones_pacientes.keys()))
            paciente_id = opciones_pacientes[paciente_seleccionado]
            
            with st.form("form_consulta"):
                st.subheader("Datos de la Consulta")
                
                medico = st.text_input("Médico Tratante *", value="Dr. Usuario")
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
                    if not motivo or not medico:
                        st.error("Por favor completa los campos obligatorios (*)")
                    else:
                        datos = {
                            "paciente_id": paciente_id,
                            "motivo": motivo,
                            "signos_vitales": signos_vitales,
                            "sintomas": sintomas,
                            "diagnostico": diagnostico,
                            "tratamiento": tratamiento,
                            "observaciones": observaciones,
                            "medico": medico
                        }
                        
                        try:
                            response = requests.post(f"{API_URL}/api/consultas", json=datos)
                            if response.status_code == 200:
                                st.success("✅ Consulta registrada exitosamente")
                                st.balloons()
                            else:
                                st.error(f"❌ Error: {response.json().get('detail')}")
                        except Exception as e:
                            st.error(f"❌ Error de conexión: {str(e)}")
    except Exception as e:
        st.error(f"Error al cargar pacientes: {str(e)}")

elif menu == "Historial de Consultas":
    st.header("📚 Historial de Consultas")
    
    try:
        response = requests.get(f"{API_URL}/api/pacientes")
        pacientes = response.json() if response.status_code == 200 else []
        
        if not pacientes:
            st.warning("⚠️ No hay pacientes registrados.")
        else:
            opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] 
                                 for p in pacientes}
            
            paciente_seleccionado = st.selectbox("Seleccionar Paciente", list(opciones_pacientes.keys()))
            paciente_id = opciones_pacientes[paciente_seleccionado]
            
            # Buscar automáticamente al seleccionar paciente
            try:
                response = requests.get(f"{API_URL}/api/consultas/paciente/{paciente_id}")
                if response.status_code == 200:
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
            except Exception as e:
                st.error(f"Error al cargar consultas: {str(e)}")
    except Exception as e:
        st.error(f"Error al cargar pacientes: {str(e)}")