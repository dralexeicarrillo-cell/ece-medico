import streamlit as st

def check_authentication():
    """Verifica si el usuario está autenticado, si no redirige a login"""
    if 'token' not in st.session_state or st.session_state.token is None:
        st.error("❌ Debes iniciar sesión para acceder a esta página")
        st.info("👉 Por favor, ve a la página principal para iniciar sesión")
        st.stop()

def get_user_info():
    """Retorna la información del usuario actual"""
    if 'usuario' in st.session_state:
        return st.session_state.usuario
    return None

def check_role(allowed_roles):
    """Verifica si el usuario tiene uno de los roles permitidos"""
    user = get_user_info()
    if user and user['rol'] in allowed_roles:
        return True
    return False

def show_user_info():
    """Muestra información del usuario en el sidebar"""
    if 'usuario' in st.session_state and st.session_state.usuario:
        user = st.session_state.usuario
        st.sidebar.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: #2E86AB; margin: 0;'>👤 {user['nombre_completo']}</h3>
            <p style='color: #6c757d; margin: 0.5rem 0 0 0;'>🏷️ {user['rol'].title()}</p>
            <p style='color: #6c757d; margin: 0.5rem 0 0 0; font-size: 0.8rem;'>📧 {user['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.token = None
            st.session_state.usuario = None
            st.rerun()