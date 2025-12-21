from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os

def generar_receta_pdf(receta_data, output_path="recetas"):
    """
    Genera PDF de receta médica
    receta_data: dict con todos los datos de la receta
    """
    os.makedirs(output_path, exist_ok=True)
    
    filename = f"{output_path}/receta_{receta_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # --- ENCABEZADO ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "RECETA MÉDICA")
    
    # Línea divisoria
    c.line(1*inch, height - 1.2*inch, width - 1*inch, height - 1.2*inch)
    
    # --- DATOS DEL MÉDICO ---
    y_pos = height - 1.5*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y_pos, "Médico:")
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, y_pos - 0.2*inch, receta_data['medico_nombre'])
    c.drawString(1*inch, y_pos - 0.4*inch, f"Código: {receta_data['medico_codigo']}")
    
    # --- DATOS DEL PACIENTE ---
    y_pos -= 0.8*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y_pos, "Paciente:")
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, y_pos - 0.2*inch, receta_data['paciente_nombre'])
    c.drawString(1*inch, y_pos - 0.4*inch, f"ID: {receta_data['paciente_id']}")
    
    # Fecha
    c.drawString(width - 3*inch, y_pos, f"Fecha: {receta_data['fecha']}")
    
    # Línea divisoria
    y_pos -= 0.7*inch
    c.line(1*inch, y_pos, width - 1*inch, y_pos)
    
    # --- MEDICAMENTOS ---
    y_pos -= 0.4*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y_pos, "Rx")
    
    y_pos -= 0.3*inch
    c.setFont("Helvetica", 10)
    
    for i, med in enumerate(receta_data['medicamentos'], 1):
        if y_pos < 2*inch:  # Nueva página si no hay espacio
            c.showPage()
            y_pos = height - 1*inch
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.2*inch, y_pos, f"{i}. {med['nombre']}")
        y_pos -= 0.2*inch
        
        c.setFont("Helvetica", 9)
        c.drawString(1.4*inch, y_pos, f"Dosis: {med['dosis']}")
        y_pos -= 0.15*inch
        c.drawString(1.4*inch, y_pos, f"Frecuencia: {med['frecuencia']}")
        y_pos -= 0.15*inch
        c.drawString(1.4*inch, y_pos, f"Duración: {med['duracion']}")
        y_pos -= 0.15*inch
        c.drawString(1.4*inch, y_pos, f"Vía: {med['via']}")
        y_pos -= 0.3*inch
    
    # --- INDICACIONES ---
    if receta_data.get('indicaciones'):
        y_pos -= 0.2*inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, y_pos, "Indicaciones Generales:")
        y_pos -= 0.2*inch
        c.setFont("Helvetica", 9)
        
        # Dividir texto largo
        texto = receta_data['indicaciones']
        max_width = width - 2.5*inch
        palabras = texto.split()
        linea = ""
        
        for palabra in palabras:
            test_linea = f"{linea} {palabra}".strip()
            if c.stringWidth(test_linea, "Helvetica", 9) < max_width:
                linea = test_linea
            else:
                c.drawString(1.2*inch, y_pos, linea)
                y_pos -= 0.15*inch
                linea = palabra
        
        if linea:
            c.drawString(1.2*inch, y_pos, linea)
            y_pos -= 0.3*inch
    
    # --- FIRMA ---
    y_pos = 1.5*inch
    c.line(width - 3.5*inch, y_pos, width - 1*inch, y_pos)
    c.setFont("Helvetica", 9)
    c.drawString(width - 3.5*inch, y_pos - 0.2*inch, "Firma y Sello del Médico")
    
    # Pie de página
    c.setFont("Helvetica", 8)
    c.drawString(1*inch, 0.5*inch, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.save()
    return filename