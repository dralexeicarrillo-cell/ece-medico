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
    rol = Column(String)  # medico, enfermera, admin
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    citas_medico = relationship("Cita", back_populates="medico_rel", foreign_keys="Cita.medico_id")

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