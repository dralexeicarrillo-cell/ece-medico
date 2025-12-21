from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from backend.database import engine, get_db, Base
from backend import models, auth, fhir_converter

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
class UsuarioCreate(BaseModel):
    username: str
    email: str
    password: str
    nombre_completo: str
    rol: str

class UsuarioResponse(BaseModel):
    id: int
    username: str
    email: str
    nombre_completo: str
    rol: str
    activo: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

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
    return {"mensaje": "API del Expediente Clínico Electrónico con FHIR"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected", "fhir": "enabled"}

# ==================== AUTENTICACIÓN ====================

@app.post("/api/auth/register", response_model=UsuarioResponse)
def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    db_email = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    hashed_password = auth.get_password_hash(usuario.password)
    new_user = models.Usuario(
        username=usuario.username,
        email=usuario.email,
        hashed_password=hashed_password,
        nombre_completo=usuario.nombre_completo,
        rol=usuario.rol,
        activo=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nombre_completo": user.nombre_completo,
            "rol": user.rol,
            "activo": user.activo
        }
    }

@app.get("/api/auth/me", response_model=UsuarioResponse)
def get_me(current_user: models.Usuario = Depends(auth.get_current_user)):
    return current_user

# ==================== PACIENTES ====================

@app.get("/api/pacientes")
def listar_pacientes(
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    pacientes = db.query(models.Paciente).all()
    return pacientes

@app.get("/api/pacientes/{paciente_id}")
def obtener_paciente(
    paciente_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@app.post("/api/pacientes")
def crear_paciente(
    paciente: PacienteCreate,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
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

# ==================== CONSULTAS ====================

@app.post("/api/consultas")
def crear_consulta(
    consulta: ConsultaCreate,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
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
        medico=current_user.nombre_completo
    )
    
    db.add(db_consulta)
    db.commit()
    db.refresh(db_consulta)
    
    return {"mensaje": "Consulta creada exitosamente", "id": db_consulta.id}

@app.get("/api/consultas/paciente/{paciente_id}")
def obtener_consultas_paciente(
    paciente_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    consultas = db.query(models.Consulta).filter(
        models.Consulta.paciente_id == paciente_id
    ).order_by(models.Consulta.fecha.desc()).all()
    
    return consultas

@app.get("/api/consultas/{consulta_id}")
def obtener_consulta(
    consulta_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return consulta

# ==================== FHIR ENDPOINTS ====================

@app.get("/fhir/Patient/{paciente_id}")
def get_fhir_patient(
    paciente_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener paciente en formato FHIR"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return fhir_converter.paciente_to_fhir(paciente)

@app.post("/fhir/Patient")
def create_fhir_patient(
    fhir_patient: dict,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Crear paciente desde formato FHIR"""
    try:
        paciente_data = fhir_converter.fhir_to_paciente(fhir_patient)
        
        # Verificar si ya existe
        existe = db.query(models.Paciente).filter(
            models.Paciente.identificacion == paciente_data["identificacion"]
        ).first()
        
        if existe:
            raise HTTPException(status_code=400, detail="Paciente ya existe")
        
        # Crear paciente
        db_paciente = models.Paciente(
            identificacion=paciente_data["identificacion"],
            nombre=paciente_data["nombre"],
            apellidos=paciente_data["apellidos"],
            fecha_nacimiento=datetime.fromisoformat(paciente_data["fecha_nacimiento"]) if paciente_data["fecha_nacimiento"] else None,
            genero=paciente_data["genero"],
            telefono=paciente_data["telefono"],
            email=paciente_data["email"],
            direccion=paciente_data["direccion"]
        )
        
        db.add(db_paciente)
        db.commit()
        db.refresh(db_paciente)
        
        return fhir_converter.paciente_to_fhir(db_paciente)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando FHIR: {str(e)}")

@app.get("/fhir/Encounter/{consulta_id}")
def get_fhir_encounter(
    consulta_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener consulta en formato FHIR Encounter"""
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == consulta.paciente_id).first()
    
    return fhir_converter.consulta_to_fhir_encounter(consulta, paciente)

@app.get("/fhir/Bundle/consulta/{consulta_id}")
def get_fhir_bundle(
    consulta_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener consulta completa en formato FHIR Bundle"""
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == consulta.paciente_id).first()
    
    return fhir_converter.consulta_to_fhir_bundle(consulta, paciente)

@app.get("/fhir/Bundle/paciente/{paciente_id}")
def get_patient_bundle(
    paciente_id: int,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener expediente completo del paciente en formato FHIR Bundle"""
    from fhir.resources.bundle import Bundle, BundleEntry
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    consultas = db.query(models.Consulta).filter(
        models.Consulta.paciente_id == paciente_id
    ).order_by(models.Consulta.fecha.desc()).all()
    
    # Crear bundle con paciente y todas sus consultas
    entries = []
    
    # Agregar paciente
    patient_fhir = fhir_converter.paciente_to_fhir(paciente)
    entries.append(BundleEntry(
        fullUrl=f"urn:uuid:patient-{paciente.id}",
        resource=patient_fhir
    ))
    
    # Agregar todas las consultas
    for consulta in consultas:
        encounter = fhir_converter.consulta_to_fhir_encounter(consulta, paciente)
        entries.append(BundleEntry(
            fullUrl=f"urn:uuid:encounter-{consulta.id}",
            resource=encounter
        ))
    
    bundle = Bundle(
        type="collection",
        entry=entries
    )
    
    return bundle.dict()