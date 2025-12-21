from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from backend.database import engine, get_db, Base
from backend import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ECE Médico API", version="1.0.0")

# Habilitar CORS para que Streamlit pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas para validación
class PacienteCreate(BaseModel):
    identificacion: str
    nombre: str
    apellidos: str
    fecha_nacimiento: str
    genero: str
    telefono: str = ""
    email: str = ""
    direccion: str = ""

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

@app.post("/api/pacientes")
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    # Verificar si ya existe
    existe = db.query(models.Paciente).filter(
        models.Paciente.identificacion == paciente.identificacion
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Paciente ya existe")
    
    # Crear nuevo paciente
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