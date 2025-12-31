import streamlit as st
from datetime import datetime, date
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.api import api_request
from utils.styles import apply_custom_css
from utils.auth import check_authentication, show_user_info

st.set_page_config(page_title="Imagenología", page_icon="🔬", layout="wide")
apply_custom_css()
check_authentication()
show_user_info()

st.markdown("<div class='main-header'><h1>🔬 Órdenes de Imagenología</h1></div>", unsafe_allow_html=True)

if st.session_state.usuario['rol'] not in ['medico', 'admin']:
    st.error("❌ Solo médicos pueden crear órdenes de imagenología.")
else:
    tab1, tab2, tab3 = st.tabs(["➕ Nueva Orden", "📋 Historial", "📚 Catálogo de Estudios"])
    
    with tab1:
        st.subheader("📝 Crear Nueva Orden de Imagenología")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if not pacientes:
                st.warning("⚠️ No hay pacientes registrados.")
            else:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Seleccionar Paciente", list(opciones_pacientes.keys()))
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                # Catálogo de estudios de imagen
                estudios_catalogo = {
                    "Radiología Simple": [
                        "Radiografía de Tórax (PA y Lateral)",
                        "Radiografía de Abdomen",
                        "Radiografía de Columna Cervical",
                        "Radiografía de Columna Lumbar",
                        "Radiografía de Extremidades Superiores",
                        "Radiografía de Extremidades Inferiores",
                        "Radiografía de Cráneo",
                        "Radiografía de Senos Paranasales"
                    ],
                    "Tomografía Computarizada (TAC)": [
                        "TAC de Cráneo Simple",
                        "TAC de Cráneo con Contraste",
                        "TAC de Tórax Simple",
                        "TAC de Tórax con Contraste",
                        "TAC de Abdomen y Pelvis Simple",
                        "TAC de Abdomen y Pelvis con Contraste",
                        "TAC de Columna Cervical",
                        "TAC de Columna Lumbar",
                        "Angio-TAC Cerebral",
                        "Angio-TAC Torácico",
                        "Angio-TAC Abdominal"
                    ],
                    "Resonancia Magnética (RM)": [
                        "RM de Cerebro Simple",
                        "RM de Cerebro con Contraste",
                        "RM de Columna Cervical",
                        "RM de Columna Dorsal",
                        "RM de Columna Lumbar",
                        "RM de Rodilla",
                        "RM de Hombro",
                        "RM Cardíaca",
                        "RM de Abdomen"
                    ],
                    "Ultrasonido": [
                        "Ultrasonido Abdominal",
                        "Ultrasonido Pélvico",
                        "Ultrasonido Obstétrico",
                        "Ultrasonido Renal",
                        "Ultrasonido Hepático",
                        "Ultrasonido de Tiroides",
                        "Ultrasonido de Partes Blandas",
                        "Ecocardiograma Transtorácico",
                        "Doppler Vascular de Extremidades"
                    ],
                    "Estudios Especializados": [
                        "Mamografía Bilateral",
                        "Densitometría Ósea",
                        "Fluoroscopia",
                        "Serie Esófago-Gastro-Duodenal",
                        "Colon por Enema",
                        "Urografía Excretora",
                        "Histerosalpingografía"
                    ]
                }
                
                with st.form("form_orden_imagen"):
                    st.subheader("🔬 Seleccionar Estudios del Catálogo")
                    
                    estudios_seleccionados = []
                    
                    # Mostrar por categorías
                    for categoria, estudios in estudios_catalogo.items():
                        with st.expander(f"📁 {categoria}", expanded=False):
                            for estudio in estudios:
                                if st.checkbox(estudio, key=f"img_{categoria}_{estudio}"):
                                    estudios_seleccionados.append({
                                        "categoria": categoria,
                                        "nombre": estudio
                                    })
                    
                    st.divider()
                    st.subheader("✍️ Agregar Estudios Personalizados")
                    st.info("💡 Usa esta sección para estudios no incluidos en el catálogo")
                    
                    num_personalizados = st.number_input("¿Cuántos estudios personalizados?", 
                                                        min_value=0, max_value=3, value=0)
                    
                    for i in range(num_personalizados):
                        col1, col2 = st.columns(2)
                        with col1:
                            cat_pers = st.selectbox(f"Categoría #{i+1}", 
                                                   list(estudios_catalogo.keys()) + ["Otro"],
                                                   key=f"cat_pers_{i}")
                        with col2:
                            nombre_pers = st.text_input(f"Nombre del estudio #{i+1}", 
                                                       key=f"nombre_pers_{i}")
                        
                        if nombre_pers:
                            estudios_seleccionados.append({
                                "categoria": cat_pers,
                                "nombre": nombre_pers
                            })
                    
                    st.divider()
                    st.subheader("📋 Información Clínica")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        diagnostico_presuntivo = st.text_area("Diagnóstico Presuntivo", height=100)
                        uso_contraste = st.checkbox("Requiere medio de contraste")
                    with col2:
                        indicaciones_clinicas = st.text_area("Indicaciones Clínicas / Datos Clínicos Relevantes", height=100)
                        urgente = st.checkbox("⚠️ Marcar como URGENTE")
                    
                    observaciones = st.text_area("Observaciones Adicionales", height=80,
                                                placeholder="Ej: Paciente claustrofóbico, alergia a contraste, etc.")
                    
                    submitted = st.form_submit_button("✅ Crear Orden de Imagenología", use_container_width=True)
                    
                    if submitted:
                        if not estudios_seleccionados:
                            st.error("Debes seleccionar al menos un estudio")
                        elif len(estudios_seleccionados) > 5:
                            st.error("Máximo 5 estudios por orden")
                        else:
                            datos_orden = {
                                "paciente_id": paciente_id,
                                "estudios": estudios_seleccionados,
                                "diagnostico_presuntivo": diagnostico_presuntivo,
                                "indicaciones_clinicas": indicaciones_clinicas,
                                "uso_contraste": uso_contraste,
                                "urgente": urgente,
                                "observaciones": observaciones
                            }
                            
                            response = api_request("POST", "/api/imagenologia/orden", datos_orden)
                            if response and response.status_code == 200:
                                st.success("✅ Orden de imagenología creada exitosamente")
                                st.info(f"Total de estudios: {len(estudios_seleccionados)}")
                                st.balloons()
                            elif response:
                                st.error(f"❌ Error: {response.json().get('detail')}")
    
    with tab2:
        st.subheader("📋 Historial de Órdenes")
        
        response = api_request("GET", "/api/pacientes")
        if response and response.status_code == 200:
            pacientes = response.json()
            
            if pacientes:
                opciones_pacientes = {f"{p['nombre']} {p['apellidos']} - {p['identificacion']}": p['id'] for p in pacientes}
                
                paciente_seleccionado = st.selectbox("👤 Buscar órdenes del paciente", 
                                                    list(opciones_pacientes.keys()), 
                                                    key="hist_img_paciente")
                paciente_id = opciones_pacientes[paciente_seleccionado]
                
                if st.button("🔍 Buscar Órdenes"):
                    response = api_request("GET", f"/api/imagenologia/paciente/{paciente_id}")
                    
                    if response and response.status_code == 200:
                        ordenes = response.json()
                        
                        if ordenes:
                            st.info(f"📊 Total: {len(ordenes)} orden(es)")
                            
                            for orden in ordenes:
                                # Emoji según estado
                                emoji_estado = {
                                    "pendiente": "⏳", 
                                    "programado": "📅",
                                    "en_proceso": "🔬", 
                                    "completado": "✅", 
                                    "cancelado": "❌"
                                }
                                
                                urgente_badge = " 🚨 URGENTE" if orden['urgente'] else ""
                                contraste_badge = " 💉 CON CONTRASTE" if orden.get('uso_contraste') else ""
                                
                                with st.expander(f"{emoji_estado.get(orden['estado'], '📋')} Orden #{orden['id']} - {orden['fecha_orden'][:10]} - {orden['estado'].upper()}{urgente_badge}{contraste_badge}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Médico:** {orden['medico_nombre']}")
                                        st.write(f"**Estado:** {orden['estado']}")
                                        if orden.get('fecha_resultado'):
                                            st.write(f"**Fecha Resultado:** {orden['fecha_resultado'][:10]}")
                                    with col2:
                                        if orden.get('diagnostico_presuntivo'):
                                            st.write(f"**Diagnóstico:** {orden['diagnostico_presuntivo']}")
                                        if orden.get('indicaciones_clinicas'):
                                            st.write(f"**Indicaciones:** {orden['indicaciones_clinicas']}")
                                    
                                    if orden.get('observaciones'):
                                        st.info(f"📝 **Observaciones:** {orden['observaciones']}")
                                    
                                    st.divider()
                                    st.markdown("### 🔬 Estudios Solicitados")
                                    
                                    # Agrupar por categoría
                                    estudios_por_categoria = {}
                                    for estudio in orden['estudios']:
                                        cat = estudio.get('categoria', 'Sin categoría')
                                        if cat not in estudios_por_categoria:
                                            estudios_por_categoria[cat] = []
                                        estudios_por_categoria[cat].append(estudio)
                                    
                                    for categoria, estudios in estudios_por_categoria.items():
                                        st.markdown(f"**📁 {categoria}**")
                                        for estudio in estudios:
                                            col1, col2 = st.columns([2, 1])
                                            with col1:
                                                st.write(f"• {estudio['nombre']}")
                                            with col2:
                                                if estudio.get('resultado'):
                                                    st.success("✅ Completado")
                                                else:
                                                    st.warning("⏳ Pendiente")
                                    
                                    st.divider()
                                    
                                    # Ver informe (si existe)
                                    if orden.get('informe_url'):
                                        st.download_button(
                                            label="📄 Descargar Informe",
                                            data=orden['informe_url'],
                                            file_name=f"informe_imagen_{orden['id']}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                                    
                                    # Cancelar orden
                                    if st.session_state.usuario['rol'] in ['medico', 'admin'] and orden['estado'] not in ['completado', 'cancelado']:
                                        if st.button(f"❌ Cancelar Orden", key=f"cancel_img_{orden['id']}"):
                                            response = api_request("DELETE", f"/api/imagenologia/{orden['id']}")
                                            if response and response.status_code == 200:
                                                st.warning("Orden cancelada")
                                                st.rerun()
                        else:
                            st.info("📭 No hay órdenes de imagenología para este paciente")
            else:
                st.warning("⚠️ No hay pacientes registrados")
    
    with tab3:
        st.subheader("📚 Catálogo de Estudios de Imagenología")
        
        # Catálogo completo
        estudios_catalogo = {
            "Radiología Simple": [
                "Radiografía de Tórax (PA y Lateral)",
                "Radiografía de Abdomen",
                "Radiografía de Columna Cervical",
                "Radiografía de Columna Lumbar",
                "Radiografía de Extremidades Superiores",
                "Radiografía de Extremidades Inferiores",
                "Radiografía de Cráneo",
                "Radiografía de Senos Paranasales"
            ],
            "Tomografía Computarizada (TAC)": [
                "TAC de Cráneo Simple",
                "TAC de Cráneo con Contraste",
                "TAC de Tórax Simple",
                "TAC de Tórax con Contraste",
                "TAC de Abdomen y Pelvis Simple",
                "TAC de Abdomen y Pelvis con Contraste",
                "TAC de Columna Cervical",
                "TAC de Columna Lumbar",
                "Angio-TAC Cerebral",
                "Angio-TAC Torácico",
                "Angio-TAC Abdominal"
            ],
            "Resonancia Magnética (RM)": [
                "RM de Cerebro Simple",
                "RM de Cerebro con Contraste",
                "RM de Columna Cervical",
                "RM de Columna Dorsal",
                "RM de Columna Lumbar",
                "RM de Rodilla",
                "RM de Hombro",
                "RM Cardíaca",
                "RM de Abdomen"
            ],
            "Ultrasonido": [
                "Ultrasonido Abdominal",
                "Ultrasonido Pélvico",
                "Ultrasonido Obstétrico",
                "Ultrasonido Renal",
                "Ultrasonido Hepático",
                "Ultrasonido de Tiroides",
                "Ultrasonido de Partes Blandas",
                "Ecocardiograma Transtorácico",
                "Doppler Vascular de Extremidades"
            ],
            "Estudios Especializados": [
                "Mamografía Bilateral",
                "Densitometría Ósea",
                "Fluoroscopia",
                "Serie Esófago-Gastro-Duodenal",
                "Colon por Enema",
                "Urografía Excretora",
                "Histerosalpingografía"
            ]
        }
        
        termino_busqueda = st.text_input("🔍 Buscar estudio", placeholder="Ej: tórax, resonancia, ultrasonido")
        
        total_estudios = sum(len(estudios) for estudios in estudios_catalogo.values())
        st.info(f"📊 El catálogo contiene {total_estudios} estudios organizados en {len(estudios_catalogo)} categorías")
        
        if termino_busqueda:
            resultados = []
            for categoria, estudios in estudios_catalogo.items():
                for estudio in estudios:
                    if termino_busqueda.lower() in estudio.lower():
                        resultados.append((categoria, estudio))
            
            if resultados:
                st.success(f"✅ {len(resultados)} resultado(s) encontrado(s)")
                for categoria, estudio in resultados:
                    st.write(f"**{categoria}:** {estudio}")
            else:
                st.warning("No se encontraron resultados")
        else:
            # Mostrar catálogo completo
            for categoria, estudios in estudios_catalogo.items():
                with st.expander(f"📁 {categoria} ({len(estudios)} estudios)"):
                    for estudio in estudios:
                        st.write(f"• {estudio}")