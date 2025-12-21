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
    codigo_medico = Column(String, nullable=True)  # Nuevo campo
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