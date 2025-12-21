from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from backend.database import engine, get_db, Base
from backend import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ECE Médico API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class PacienteCreate(BaseModel):
    identificacion: str
    nombre: str
    apellidos: str
    fecha_nacimiento: str
    genero: str
    telefono: str = ""
    email: str = ""
    direccion: str = ""

class ConsultaCreate(BaseModel):
    paciente_id: int
    motivo: str
    signos_vitales: Optional[str] = ""
    sintomas: Optional[str] = ""
    diagnostico: Optional[str] = ""
    tratamiento: Optional[str] = ""
    observaciones: Optional[str] = ""
    medico: str

@app.get("/")
def root():
    return {"mensaje": "API del Expediente Clínico Electrónico"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}

@app.get("/api/pacientes")
def listar_pacientes(db: Session = Depends(get_db)):
    pacientes = db.query(models.Paciente).all()
    return pacientes

@app.get("/api/pacientes/{paciente_id}")
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@app.post("/api/pacientes")
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    existe = db.query(models.Paciente).filter(
        models.Paciente.identificacion == paciente.identificacion
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Paciente ya existe")
    
    db_paciente = models.Paciente(
        identificacion=paciente.identificacion,
        nombre=paciente.nombre,
        apellidos=paciente.apellidos,
        fecha_nacimiento=datetime.fromisoformat(paciente.fecha_nacimiento),
        genero=paciente.genero,
        telefono=paciente.telefono,
        email=paciente.email,
        direccion=paciente.direccion
    )
    
    db.add(db_paciente)
    db.commit()
    db.refresh(db_paciente)
    
    return {"mensaje": "Paciente creado exitosamente", "id": db_paciente.id}

@app.post("/api/consultas")
def crear_consulta(consulta: ConsultaCreate, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == consulta.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    db_consulta = models.Consulta(
        paciente_id=consulta.paciente_id,
        motivo=consulta.motivo,
        signos_vitales=consulta.signos_vitales,
        sintomas=consulta.sintomas,
        diagnostico=consulta.diagnostico,
        tratamiento=consulta.tratamiento,
        observaciones=consulta.observaciones,
        medico=consulta.medico
    )
    
    db.add(db_consulta)
    db.commit()
    db.refresh(db_consulta)
    
    return {"mensaje": "Consulta creada exitosamente", "id": db_consulta.id}

@app.get("/api/consultas/paciente/{paciente_id}")
def obtener_consultas_paciente(paciente_id: int, db: Session = Depends(get_db)):
    consultas = db.query(models.Consulta).filter(
        models.Consulta.paciente_id == paciente_id
    ).order_by(models.Consulta.fecha.desc()).all()
    
    return consultas

@app.get("/api/consultas/{consulta_id}")
def obtener_consulta(consulta_id: int, db: Session = Depends(get_db)):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return consulta