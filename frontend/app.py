import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="ECE Médico", page_icon="🏥", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🏥 Expediente Clínico Electrónico")

menu = st.sidebar.selectbox(
    "Menú Principal",
    ["Inicio", "Registrar Paciente", "Lista de Pacientes"]
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
    
    st.info("Selecciona una opción del menú lateral")

elif menu == "Registrar Paciente":
    st.header("Registrar Nuevo Paciente")
    
    with st.form("form_paciente"):
        col1, col2 = st.columns(2)
        
        with col1:
            identificacion = st.text_input("Identificación *")
            nombre = st.text_input("Nombre *")
            apellidos = st.text_input("Apellidos *")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento *")
        
        with col2:
            genero = st.selectbox("Género *", ["Masculino", "Femenino", "Otro"])
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
        
        direccion = st.text_area("Dirección")
        
        submitted = st.form_submit_button("Registrar Paciente")
        
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
                    else:
                        st.error(f"❌ Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")

elif menu == "Lista de Pacientes":
    st.header("Pacientes Registrados")
    
    try:
        response = requests.get(f"{API_URL}/api/pacientes")
        if response.status_code == 200:
            pacientes = response.json()
            if pacientes:
                for p in pacientes:
                    with st.expander(f"{p['nombre']} {p['apellidos']} - {p['identificacion']}"):
                        st.write(f"**Género:** {p['genero']}")
                        st.write(f"**Teléfono:** {p['telefono']}")
                        st.write(f"**Email:** {p['email']}")
            else:
                st.info("No hay pacientes registrados")
    except:
        st.error("Error al cargar pacientes")