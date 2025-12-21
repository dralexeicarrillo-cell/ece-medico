from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
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
    rol = Column(String)
    creado_en = Column(DateTime, default=datetime.utcnow)

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