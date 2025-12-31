import streamlit as st

def apply_custom_css():
    """Aplica los estilos CSS personalizados para todo el sistema"""
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