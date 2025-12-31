from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    nombre_completo = Column(String)
    rol = Column(String)  # medico, enfermera, recepcion, admin
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


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
    direccion = Column(String)
    fecha_registro = Column(DateTime, default=datetime.utcnow)


class Consulta(Base):
    __tablename__ = "consultas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    motivo = Column(String)
    signos_vitales = Column(String)
    sintomas = Column(Text)
    diagnostico = Column(Text)
    tratamiento = Column(Text)
    observaciones = Column(Text)
    medico = Column(String)


class Cita(Base):
    __tablename__ = "citas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_hora = Column(DateTime)
    duracion_minutos = Column(Integer, default=30)
    motivo = Column(String)
    notas = Column(Text)
    estado = Column(String, default="programada")  # programada, confirmada, atendida, cancelada
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Receta(Base):
    __tablename__ = "recetas"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    
    # Hasta 5 medicamentos
    medicamento1_nombre = Column(String)
    medicamento1_dosis = Column(String)
    medicamento1_frecuencia = Column(String)
    medicamento1_duracion = Column(String)
    medicamento1_via = Column(String)
    
    medicamento2_nombre = Column(String, nullable=True)
    medicamento2_dosis = Column(String, nullable=True)
    medicamento2_frecuencia = Column(String, nullable=True)
    medicamento2_duracion = Column(String, nullable=True)
    medicamento2_via = Column(String, nullable=True)
    
    medicamento3_nombre = Column(String, nullable=True)
    medicamento3_dosis = Column(String, nullable=True)
    medicamento3_frecuencia = Column(String, nullable=True)
    medicamento3_duracion = Column(String, nullable=True)
    medicamento3_via = Column(String, nullable=True)
    
    medicamento4_nombre = Column(String, nullable=True)
    medicamento4_dosis = Column(String, nullable=True)
    medicamento4_frecuencia = Column(String, nullable=True)
    medicamento4_duracion = Column(String, nullable=True)
    medicamento4_via = Column(String, nullable=True)
    
    medicamento5_nombre = Column(String, nullable=True)
    medicamento5_dosis = Column(String, nullable=True)
    medicamento5_frecuencia = Column(String, nullable=True)
    medicamento5_duracion = Column(String, nullable=True)
    medicamento5_via = Column(String, nullable=True)
    
    indicaciones_generales = Column(Text, nullable=True)


class OrdenLaboratorio(Base):
    __tablename__ = "ordenes_laboratorio"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_orden = Column(DateTime, default=datetime.utcnow)
    diagnostico_presuntivo = Column(String)
    indicaciones_clinicas = Column(String)
    urgente = Column(Boolean, default=False)
    estado = Column(String, default="pendiente")  # pendiente, en_proceso, completado, cancelado
    fecha_resultado = Column(DateTime, nullable=True)


class ExamenLaboratorio(Base):
    __tablename__ = "examenes_laboratorio"
    
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_laboratorio.id"))
    numero = Column(Integer)
    codigo_loinc = Column(String)
    nombre = Column(String)
    valor_referencia = Column(String)
    unidad = Column(String)
    resultado = Column(String, nullable=True)


class OrdenImagenologia(Base):
    __tablename__ = "ordenes_imagenologia"
    
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_orden = Column(DateTime, default=datetime.utcnow)
    diagnostico_presuntivo = Column(String)
    indicaciones_clinicas = Column(String)
    uso_contraste = Column(Boolean, default=False)
    urgente = Column(Boolean, default=False)
    observaciones = Column(String)
    estado = Column(String, default="pendiente")  # pendiente, programado, en_proceso, completado, cancelado
    fecha_resultado = Column(DateTime, nullable=True)
    informe_url = Column(String, nullable=True)


class EstudioImagenologia(Base):
    __tablename__ = "estudios_imagenologia"
    
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_imagenologia.id"))
    numero = Column(Integer)
    categoria = Column(String)
    nombre = Column(String)
    resultado = Column(String, nullable=True)
    estado = Column(String, default="pendiente")