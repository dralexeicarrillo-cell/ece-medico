# Catálogo de exámenes de laboratorio más comunes con códigos LOINC

EXAMENES_LOINC = {
    # Hematología
    "HEMOGRAMA_COMPLETO": {
        "codigo": "58410-2",
        "nombre": "Hemograma Completo (CBC)",
        "categoria": "Hematología",
        "unidad": "",
        "valor_referencia": "Ver valores individuales"
    },
    "HEMOGLOBINA": {
        "codigo": "718-7",
        "nombre": "Hemoglobina",
        "categoria": "Hematología",
        "unidad": "g/dL",
        "valor_referencia": "M: 13.5-17.5, F: 12.0-16.0"
    },
    "HEMATOCRITO": {
        "codigo": "4544-3",
        "nombre": "Hematocrito",
        "categoria": "Hematología",
        "unidad": "%",
        "valor_referencia": "M: 38.3-48.6, F: 35.5-44.9"
    },
    "LEUCOCITOS": {
        "codigo": "6690-2",
        "nombre": "Leucocitos (Glóbulos Blancos)",
        "categoria": "Hematología",
        "unidad": "10^3/µL",
        "valor_referencia": "4.5-11.0"
    },
    "PLAQUETAS": {
        "codigo": "777-3",
        "nombre": "Plaquetas",
        "categoria": "Hematología",
        "unidad": "10^3/µL",
        "valor_referencia": "150-400"
    },
    "VSG": {
        "codigo": "30341-2",
        "nombre": "Velocidad de Sedimentación Globular (VSG)",
        "categoria": "Hematología",
        "unidad": "mm/h",
        "valor_referencia": "M: 0-15, F: 0-20"
    },
    
    # Química Sanguínea
    "GLUCOSA": {
        "codigo": "2345-7",
        "nombre": "Glucosa en Ayunas",
        "categoria": "Química Sanguínea",
        "unidad": "mg/dL",
        "valor_referencia": "70-100"
    },
    "GLUCOSA_POSTPRANDIAL": {
        "codigo": "1518-9",
        "nombre": "Glucosa Postprandial (2h)",
        "categoria": "Química Sanguínea",
        "unidad": "mg/dL",
        "valor_referencia": "<140"
    },
    "HBA1C": {
        "codigo": "4548-4",
        "nombre": "Hemoglobina Glicosilada (HbA1c)",
        "categoria": "Química Sanguínea",
        "unidad": "%",
        "valor_referencia": "4.0-5.6"
    },
    "CREATININA": {
        "codigo": "2160-0",
        "nombre": "Creatinina Sérica",
        "categoria": "Química Sanguínea",
        "unidad": "mg/dL",
        "valor_referencia": "M: 0.7-1.3, F: 0.6-1.1"
    },
    "UREA": {
        "codigo": "3094-0",
        "nombre": "Urea (BUN)",
        "categoria": "Química Sanguínea",
        "unidad": "mg/dL",
        "valor_referencia": "7-20"
    },
    "ACIDO_URICO": {
        "codigo": "3084-1",
        "nombre": "Ácido Úrico",
        "categoria": "Química Sanguínea",
        "unidad": "mg/dL",
        "valor_referencia": "M: 3.4-7.0, F: 2.4-6.0"
    },
    
    # Perfil Lipídico
    "COLESTEROL_TOTAL": {
        "codigo": "2093-3",
        "nombre": "Colesterol Total",
        "categoria": "Perfil Lipídico",
        "unidad": "mg/dL",
        "valor_referencia": "<200"
    },
    "HDL": {
        "codigo": "2085-9",
        "nombre": "Colesterol HDL",
        "categoria": "Perfil Lipídico",
        "unidad": "mg/dL",
        "valor_referencia": "M: >40, F: >50"
    },
    "LDL": {
        "codigo": "18262-6",
        "nombre": "Colesterol LDL (Calculado)",
        "categoria": "Perfil Lipídico",
        "unidad": "mg/dL",
        "valor_referencia": "<100"
    },
    "TRIGLICERIDOS": {
        "codigo": "2571-8",
        "nombre": "Triglicéridos",
        "categoria": "Perfil Lipídico",
        "unidad": "mg/dL",
        "valor_referencia": "<150"
    },
    
    # Función Hepática
    "TGO_AST": {
        "codigo": "1920-8",
        "nombre": "TGO (AST)",
        "categoria": "Función Hepática",
        "unidad": "U/L",
        "valor_referencia": "M: 10-40, F: 9-32"
    },
    "TGP_ALT": {
        "codigo": "1742-6",
        "nombre": "TGP (ALT)",
        "categoria": "Función Hepática",
        "unidad": "U/L",
        "valor_referencia": "M: 10-55, F: 7-45"
    },
    "BILIRRUBINA_TOTAL": {
        "codigo": "1975-2",
        "nombre": "Bilirrubina Total",
        "categoria": "Función Hepática",
        "unidad": "mg/dL",
        "valor_referencia": "0.3-1.2"
    },
    "BILIRRUBINA_DIRECTA": {
        "codigo": "1968-7",
        "nombre": "Bilirrubina Directa",
        "categoria": "Función Hepática",
        "unidad": "mg/dL",
        "valor_referencia": "0.0-0.3"
    },
    "FOSFATASA_ALCALINA": {
        "codigo": "6768-6",
        "nombre": "Fosfatasa Alcalina",
        "categoria": "Función Hepática",
        "unidad": "U/L",
        "valor_referencia": "30-120"
    },
    
    # Electrolitos
    "SODIO": {
        "codigo": "2951-2",
        "nombre": "Sodio Sérico",
        "categoria": "Electrolitos",
        "unidad": "mmol/L",
        "valor_referencia": "136-145"
    },
    "POTASIO": {
        "codigo": "2823-3",
        "nombre": "Potasio Sérico",
        "categoria": "Electrolitos",
        "unidad": "mmol/L",
        "valor_referencia": "3.5-5.0"
    },
    "CLORO": {
        "codigo": "2075-0",
        "nombre": "Cloro Sérico",
        "categoria": "Electrolitos",
        "unidad": "mmol/L",
        "valor_referencia": "98-107"
    },
    "CALCIO": {
        "codigo": "17861-6",
        "nombre": "Calcio Sérico",
        "categoria": "Electrolitos",
        "unidad": "mg/dL",
        "valor_referencia": "8.5-10.5"
    },
    
    # Función Tiroidea
    "TSH": {
        "codigo": "3016-3",
        "nombre": "TSH (Hormona Estimulante de Tiroides)",
        "categoria": "Función Tiroidea",
        "unidad": "µIU/mL",
        "valor_referencia": "0.4-4.0"
    },
    "T4_LIBRE": {
        "codigo": "3024-7",
        "nombre": "T4 Libre (Tiroxina)",
        "categoria": "Función Tiroidea",
        "unidad": "ng/dL",
        "valor_referencia": "0.8-1.8"
    },
    "T3_TOTAL": {
        "codigo": "3051-0",
        "nombre": "T3 Total (Triyodotironina)",
        "categoria": "Función Tiroidea",
        "unidad": "ng/dL",
        "valor_referencia": "80-200"
    },
    
    # Otros
    "PCR": {
        "codigo": "1988-5",
        "nombre": "Proteína C Reactiva (PCR)",
        "categoria": "Marcadores Inflamatorios",
        "unidad": "mg/L",
        "valor_referencia": "<10"
    },
    "FERRITINA": {
        "codigo": "2276-4",
        "nombre": "Ferritina",
        "categoria": "Hierro",
        "unidad": "ng/mL",
        "valor_referencia": "M: 24-336, F: 11-307"
    },
    "VITAMINA_D": {
        "codigo": "1989-3",
        "nombre": "Vitamina D (25-OH)",
        "categoria": "Vitaminas",
        "unidad": "ng/mL",
        "valor_referencia": "30-100"
    },
    "VITAMINA_B12": {
        "codigo": "2132-9",
        "nombre": "Vitamina B12",
        "categoria": "Vitaminas",
        "unidad": "pg/mL",
        "valor_referencia": "200-900"
    },
    
    # Uroanálisis
    "UROANALISIS": {
        "codigo": "24357-6",
        "nombre": "Uroanálisis Completo",
        "categoria": "Uroanálisis",
        "unidad": "",
        "valor_referencia": "Ver valores individuales"
    },
    "UROCULTIVO": {
        "codigo": "630-4",
        "nombre": "Urocultivo",
        "categoria": "Microbiología",
        "unidad": "",
        "valor_referencia": "Negativo"
    }
}

def obtener_examenes_por_categoria():
    """Organiza exámenes por categoría"""
    categorias = {}
    for key, exam in EXAMENES_LOINC.items():
        cat = exam["categoria"]
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append({
            "key": key,
            **exam
        })
    return categorias

def buscar_examen(termino):
    """Busca exámenes por término"""
    resultados = []
    termino = termino.lower()
    for key, exam in EXAMENES_LOINC.items():
        if termino in exam["nombre"].lower() or termino in exam["codigo"].lower():
            resultados.append({
                "key": key,
                **exam
            })
    return resultados