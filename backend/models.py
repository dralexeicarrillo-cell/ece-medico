from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    nombre_completo = Column(String)
    codigo_medico = Column(String, nullable=True)
    rol = Column(String)  # medico, enfermera, recepcion, admin
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    citas_medico = relationship("Cita", back_populates="medico_rel", foreign_keys="Cita.medico_id")
    recetas = relationship("Receta", back_populates="medico_rel")

class Paciente(Base):
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    identificacion = Column(String, unique=True, index=True)
    nombre = Column(String)
    apellidos = Column(String)
    fecha_nacimiento = Column(DateTime)
    genero = Column(String)
    telefono = Column(String)
    email = Column(String)
    direccion = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    consultas = relationship("Consulta", back_populates="paciente")
    citas = relationship("Cita", back_populates="paciente_rel")
    recetas = relationship("Receta", back_populates="paciente_rel")

class Consulta(Base):
    __tablename__ = "consultas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    motivo = Column(Text)
    signos_vitales = Column(Text)
    sintomas = Column(Text)
    diagnostico = Column(Text)
    tratamiento = Column(Text)
    observaciones = Column(Text)
    medico = Column(String)
    
    paciente = relationship("Paciente", back_populates="consultas")

class Cita(Base):
    __tablename__ = "citas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_hora = Column(DateTime)
    duracion_minutos = Column(Integer, default=30)
    motivo = Column(Text)
    estado = Column(String, default="programada")  # programada, confirmada, atendida, cancelada
    notas = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    paciente_rel = relationship("Paciente", back_populates="citas")
    medico_rel = relationship("Usuario", back_populates="citas_medico", foreign_keys=[medico_id])

class Receta(Base):
    __tablename__ = "recetas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    
    # Medicamento 1 (obligatorio)
    medicamento1_nombre = Column(String, nullable=False)
    medicamento1_dosis = Column(String, nullable=False)
    medicamento1_frecuencia = Column(String, nullable=False)
    medicamento1_duracion = Column(String, nullable=False)
    medicamento1_via = Column(String, nullable=False)
    
    # Medicamento 2 (opcional)
    medicamento2_nombre = Column(String, nullable=True)
    medicamento2_dosis = Column(String, nullable=True)
    medicamento2_frecuencia = Column(String, nullable=True)
    medicamento2_duracion = Column(String, nullable=True)
    medicamento2_via = Column(String, nullable=True)
    
    # Medicamento 3 (opcional)
    medicamento3_nombre = Column(String, nullable=True)
    medicamento3_dosis = Column(String, nullable=True)
    medicamento3_frecuencia = Column(String, nullable=True)
    medicamento3_duracion = Column(String, nullable=True)
    medicamento3_via = Column(String, nullable=True)
    
    # Medicamento 4 (opcional)
    medicamento4_nombre = Column(String, nullable=True)
    medicamento4_dosis = Column(String, nullable=True)
    medicamento4_frecuencia = Column(String, nullable=True)
    medicamento4_duracion = Column(String, nullable=True)
    medicamento4_via = Column(String, nullable=True)
    
    # Medicamento 5 (opcional)
    medicamento5_nombre = Column(String, nullable=True)
    medicamento5_dosis = Column(String, nullable=True)
    medicamento5_frecuencia = Column(String, nullable=True)
    medicamento5_duracion = Column(String, nullable=True)
    medicamento5_via = Column(String, nullable=True)
    
    # Indicaciones generales
    indicaciones_generales = Column(Text, nullable=True)
    
    # Estado
    activa = Column(Boolean, default=True)
    
    # Relaciones
    paciente_rel = relationship("Paciente", back_populates="recetas")
    medico_rel = relationship("Usuario", back_populates="recetas")

class OrdenLaboratorio(Base):
    __tablename__ = "ordenes_laboratorio"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=True)
    
    fecha_orden = Column(DateTime, default=datetime.utcnow)
    fecha_toma_muestra = Column(DateTime, nullable=True)
    fecha_resultado = Column(DateTime, nullable=True)
    
    # Exámenes solicitados (hasta 10 exámenes por orden)
    examen1_codigo_loinc = Column(String, nullable=True)
    examen1_nombre = Column(String, nullable=True)
    examen1_resultado = Column(Text, nullable=True)
    examen1_valor_referencia = Column(String, nullable=True)
    examen1_unidad = Column(String, nullable=True)
    
    examen2_codigo_loinc = Column(String, nullable=True)
    examen2_nombre = Column(String, nullable=True)
    examen2_resultado = Column(Text, nullable=True)
    examen2_valor_referencia = Column(String, nullable=True)
    examen2_unidad = Column(String, nullable=True)
    
    examen3_codigo_loinc = Column(String, nullable=True)
    examen3_nombre = Column(String, nullable=True)
    examen3_resultado = Column(Text, nullable=True)
    examen3_valor_referencia = Column(String, nullable=True)
    examen3_unidad = Column(String, nullable=True)
    
    examen4_codigo_loinc = Column(String, nullable=True)
    examen4_nombre = Column(String, nullable=True)
    examen4_resultado = Column(Text, nullable=True)
    examen4_valor_referencia = Column(String, nullable=True)
    examen4_unidad = Column(String, nullable=True)
    
    examen5_codigo_loinc = Column(String, nullable=True)
    examen5_nombre = Column(String, nullable=True)
    examen5_resultado = Column(Text, nullable=True)
    examen5_valor_referencia = Column(String, nullable=True)
    examen5_unidad = Column(String, nullable=True)
    
    examen6_codigo_loinc = Column(String, nullable=True)
    examen6_nombre = Column(String, nullable=True)
    examen6_resultado = Column(Text, nullable=True)
    examen6_valor_referencia = Column(String, nullable=True)
    examen6_unidad = Column(String, nullable=True)
    
    examen7_codigo_loinc = Column(String, nullable=True)
    examen7_nombre = Column(String, nullable=True)
    examen7_resultado = Column(Text, nullable=True)
    examen7_valor_referencia = Column(String, nullable=True)
    examen7_unidad = Column(String, nullable=True)
    
    examen8_codigo_loinc = Column(String, nullable=True)
    examen8_nombre = Column(String, nullable=True)
    examen8_resultado = Column(Text, nullable=True)
    examen8_valor_referencia = Column(String, nullable=True)
    examen8_unidad = Column(String, nullable=True)
    
    examen9_codigo_loinc = Column(String, nullable=True)
    examen9_nombre = Column(String, nullable=True)
    examen9_resultado = Column(Text, nullable=True)
    examen9_valor_referencia = Column(String, nullable=True)
    examen9_unidad = Column(String, nullable=True)
    
    examen10_codigo_loinc = Column(String, nullable=True)
    examen10_nombre = Column(String, nullable=True)
    examen10_resultado = Column(Text, nullable=True)
    examen10_valor_referencia = Column(String, nullable=True)
    examen10_unidad = Column(String, nullable=True)
    
    # Información adicional
    indicaciones_clinicas = Column(Text, nullable=True)
    diagnostico_presuntivo = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Estado
    estado = Column(String, default="pendiente")  # pendiente, en_proceso, completado, cancelado
    urgente = Column(Boolean, default=False)
    
    # Relaciones
    paciente_rel = relationship("Paciente")
    medico_rel = relationship("Usuario")