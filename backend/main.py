from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from backend.database import engine, get_db, Base
from backend import models, fhir_converter
from backend.pdf_generator import generar_receta_pdf
from backend.loinc_catalog import EXAMENES_LOINC, obtener_examenes_por_categoria, buscar_examen
from backend.auth import (
    get_current_user, 
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    require_roles,
    get_current_admin,
    get_current_medico,
    get_current_recepcion_or_admin,
    get_current_medico_or_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

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

class PacienteUpdate(BaseModel):
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

class ConsultaCreate(BaseModel):
    paciente_id: int
    motivo: str
    signos_vitales: Optional[str] = ""
    sintomas: Optional[str] = ""
    diagnostico: Optional[str] = ""
    tratamiento: Optional[str] = ""
    observaciones: Optional[str] = ""
    medico: str

class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha_hora: str  # ISO format
    duracion_minutos: int = 30
    motivo: str
    notas: Optional[str] = ""

class CitaUpdate(BaseModel):
    fecha_hora: Optional[str] = None
    duracion_minutos: Optional[int] = None
    motivo: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class RecetaCreate(BaseModel):
    paciente_id: int
    medicamento1_nombre: str
    medicamento1_dosis: str
    medicamento1_frecuencia: str
    medicamento1_duracion: str
    medicamento1_via: str
    medicamento2_nombre: Optional[str] = None
    medicamento2_dosis: Optional[str] = None
    medicamento2_frecuencia: Optional[str] = None
    medicamento2_duracion: Optional[str] = None
    medicamento2_via: Optional[str] = None
    medicamento3_nombre: Optional[str] = None
    medicamento3_dosis: Optional[str] = None
    medicamento3_frecuencia: Optional[str] = None
    medicamento3_duracion: Optional[str] = None
    medicamento3_via: Optional[str] = None
    medicamento4_nombre: Optional[str] = None
    medicamento4_dosis: Optional[str] = None
    medicamento4_frecuencia: Optional[str] = None
    medicamento4_duracion: Optional[str] = None
    medicamento4_via: Optional[str] = None
    medicamento5_nombre: Optional[str] = None
    medicamento5_dosis: Optional[str] = None
    medicamento5_frecuencia: Optional[str] = None
    medicamento5_duracion: Optional[str] = None
    medicamento5_via: Optional[str] = None
    indicaciones_generales: Optional[str] = None
class ExamenLaboratorio(BaseModel):
    codigo_loinc: str
    nombre: str
    resultado: Optional[str] = None
    valor_referencia: Optional[str] = None
    unidad: Optional[str] = None

class OrdenLaboratorioCreate(BaseModel):
    paciente_id: int
    consulta_id: Optional[int] = None
    examenes: List[ExamenLaboratorio]
    indicaciones_clinicas: Optional[str] = None
    diagnostico_presuntivo: Optional[str] = None
    urgente: bool = False

class ResultadoExamen(BaseModel):
    examen_numero: int
    resultado: str
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
    
    # Validar rol
    roles_validos = ["medico", "enfermera", "recepcion", "admin"]
    if usuario.rol not in roles_validos:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {', '.join(roles_validos)}")
    
    password_hash = get_password_hash(usuario.password)
    new_user = models.Usuario(
        username=usuario.username,
        email=usuario.email,
        password_hash=password_hash,
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
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
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
def get_me(current_user: models.Usuario = Depends(get_current_user)):
    return current_user

# ==================== USUARIOS ====================

@app.get("/api/usuarios")
def listar_usuarios(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios activos"""
    usuarios = db.query(models.Usuario).filter(models.Usuario.activo == True).all()
    return usuarios

# ==================== PACIENTES ====================

@app.get("/api/pacientes")
def listar_pacientes(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar pacientes - Acceso para todos los roles autenticados"""
    pacientes = db.query(models.Paciente).all()
    return pacientes

@app.get("/api/pacientes/{paciente_id}")
def obtener_paciente(
    paciente_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener paciente - Acceso para todos los roles autenticados"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@app.post("/api/pacientes")
def crear_paciente(
    paciente: PacienteCreate,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin", "medico"])),
    db: Session = Depends(get_db)
):
    """Crear paciente - Solo recepción, médicos y admin"""
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

@app.put("/api/pacientes/{paciente_id}")
def actualizar_paciente(
    paciente_id: int,
    paciente_update: PacienteUpdate,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin"])),
    db: Session = Depends(get_db)
):
    """Actualizar datos de contacto del paciente - Solo recepción y admin"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Actualizar solo campos permitidos (datos de contacto)
    if paciente_update.telefono is not None:
        paciente.telefono = paciente_update.telefono
    if paciente_update.email is not None:
        paciente.email = paciente_update.email
    if paciente_update.direccion is not None:
        paciente.direccion = paciente_update.direccion
    
    db.commit()
    db.refresh(paciente)
    
    return {"mensaje": "Datos de contacto actualizados exitosamente"}

# ==================== CONSULTAS ====================

@app.post("/api/consultas")
def crear_consulta(
    consulta: ConsultaCreate,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Crear consulta - Solo médicos y admin"""
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
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Ver consultas - Solo personal médico"""
    consultas = db.query(models.Consulta).filter(
        models.Consulta.paciente_id == paciente_id
    ).order_by(models.Consulta.fecha.desc()).all()
    
    return consultas

@app.get("/api/consultas/{consulta_id}")
def obtener_consulta(
    consulta_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Ver consulta específica - Solo personal médico"""
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return consulta

# ==================== CITAS ====================

@app.post("/api/citas")
def crear_cita(
    cita: CitaCreate,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin", "medico"])),
    db: Session = Depends(get_db)
):
    """Crear cita - Recepción, médicos y admin"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == cita.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    medico = db.query(models.Usuario).filter(models.Usuario.id == cita.medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    fecha_hora = datetime.fromisoformat(cita.fecha_hora)
    fecha_fin = fecha_hora + timedelta(minutes=cita.duracion_minutos)
    
    conflictos = db.query(models.Cita).filter(
        models.Cita.medico_id == cita.medico_id,
        models.Cita.estado.in_(["programada", "confirmada"]),
        models.Cita.fecha_hora < fecha_fin,
        models.Cita.fecha_hora >= fecha_hora - timedelta(minutes=60)
    ).first()
    
    if conflictos:
        raise HTTPException(status_code=400, detail="El médico ya tiene una cita en ese horario")
    
    db_cita = models.Cita(
        paciente_id=cita.paciente_id,
        medico_id=cita.medico_id,
        fecha_hora=fecha_hora,
        duracion_minutos=cita.duracion_minutos,
        motivo=cita.motivo,
        notas=cita.notas,
        estado="programada"
    )
    
    db.add(db_cita)
    db.commit()
    db.refresh(db_cita)
    
    return {"mensaje": "Cita creada exitosamente", "id": db_cita.id}

@app.get("/api/citas")
def listar_citas(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    medico_id: Optional[int] = None,
    paciente_id: Optional[int] = None,
    estado: Optional[str] = None,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar citas - Todos los roles autenticados"""
    query = db.query(models.Cita)
    
    if fecha_desde:
        query = query.filter(models.Cita.fecha_hora >= datetime.fromisoformat(fecha_desde))
    
    if fecha_hasta:
        query = query.filter(models.Cita.fecha_hora <= datetime.fromisoformat(fecha_hasta))
    
    if medico_id:
        query = query.filter(models.Cita.medico_id == medico_id)
    
    if paciente_id:
        query = query.filter(models.Cita.paciente_id == paciente_id)
    
    if estado:
        query = query.filter(models.Cita.estado == estado)
    
    citas = query.order_by(models.Cita.fecha_hora).all()
    
    resultado = []
    for cita in citas:
        paciente = db.query(models.Paciente).filter(models.Paciente.id == cita.paciente_id).first()
        medico = db.query(models.Usuario).filter(models.Usuario.id == cita.medico_id).first()
        
        resultado.append({
            "id": cita.id,
            "paciente_id": cita.paciente_id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}" if paciente else "Desconocido",
            "medico_id": cita.medico_id,
            "medico_nombre": medico.nombre_completo if medico else "Desconocido",
            "fecha_hora": cita.fecha_hora.isoformat(),
            "duracion_minutos": cita.duracion_minutos,
            "motivo": cita.motivo,
            "estado": cita.estado,
            "notas": cita.notas,
            "creado_en": cita.creado_en.isoformat()
        })
    
    return resultado

@app.get("/api/citas/{cita_id}")
def obtener_cita(
    cita_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener cita - Todos los roles autenticados"""
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == cita.paciente_id).first()
    medico = db.query(models.Usuario).filter(models.Usuario.id == cita.medico_id).first()
    
    return {
        "id": cita.id,
        "paciente_id": cita.paciente_id,
        "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}" if paciente else "Desconocido",
        "medico_id": cita.medico_id,
        "medico_nombre": medico.nombre_completo if medico else "Desconocido",
        "fecha_hora": cita.fecha_hora.isoformat(),
        "duracion_minutos": cita.duracion_minutos,
        "motivo": cita.motivo,
        "estado": cita.estado,
        "notas": cita.notas
    }

@app.put("/api/citas/{cita_id}")
def actualizar_cita(
    cita_id: int,
    cita_update: CitaUpdate,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin", "medico"])),
    db: Session = Depends(get_db)
):
    """Actualizar cita - Recepción, médicos y admin"""
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if cita_update.fecha_hora:
        cita.fecha_hora = datetime.fromisoformat(cita_update.fecha_hora)
    if cita_update.duracion_minutos:
        cita.duracion_minutos = cita_update.duracion_minutos
    if cita_update.motivo:
        cita.motivo = cita_update.motivo
    if cita_update.estado:
        cita.estado = cita_update.estado
    if cita_update.notas is not None:
        cita.notas = cita_update.notas
    
    cita.actualizado_en = datetime.utcnow()
    
    db.commit()
    db.refresh(cita)
    
    return {"mensaje": "Cita actualizada exitosamente", "id": cita.id}

@app.delete("/api/citas/{cita_id}")
def cancelar_cita(
    cita_id: int,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin", "medico"])),
    db: Session = Depends(get_db)
):
    """Cancelar cita - Recepción, médicos y admin"""
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    cita.estado = "cancelada"
    cita.actualizado_en = datetime.utcnow()
    
    db.commit()
    
    return {"mensaje": "Cita cancelada exitosamente"}

# ==================== RECETAS MÉDICAS ====================

@app.post("/api/recetas")
def crear_receta(
    receta: RecetaCreate,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Crear receta médica - Solo médicos y admin"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == receta.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    db_receta = models.Receta(
        paciente_id=receta.paciente_id,
        medico_id=current_user.id,
        medicamento1_nombre=receta.medicamento1_nombre,
        medicamento1_dosis=receta.medicamento1_dosis,
        medicamento1_frecuencia=receta.medicamento1_frecuencia,
        medicamento1_duracion=receta.medicamento1_duracion,
        medicamento1_via=receta.medicamento1_via,
        medicamento2_nombre=receta.medicamento2_nombre,
        medicamento2_dosis=receta.medicamento2_dosis,
        medicamento2_frecuencia=receta.medicamento2_frecuencia,
        medicamento2_duracion=receta.medicamento2_duracion,
        medicamento2_via=receta.medicamento2_via,
        medicamento3_nombre=receta.medicamento3_nombre,
        medicamento3_dosis=receta.medicamento3_dosis,
        medicamento3_frecuencia=receta.medicamento3_frecuencia,
        medicamento3_duracion=receta.medicamento3_duracion,
        medicamento3_via=receta.medicamento3_via,
        medicamento4_nombre=receta.medicamento4_nombre,
        medicamento4_dosis=receta.medicamento4_dosis,
        medicamento4_frecuencia=receta.medicamento4_frecuencia,
        medicamento4_duracion=receta.medicamento4_duracion,
        medicamento4_via=receta.medicamento4_via,
        medicamento5_nombre=receta.medicamento5_nombre,
        medicamento5_dosis=receta.medicamento5_dosis,
        medicamento5_frecuencia=receta.medicamento5_frecuencia,
        medicamento5_duracion=receta.medicamento5_duracion,
        medicamento5_via=receta.medicamento5_via,
        indicaciones_generales=receta.indicaciones_generales,
        activa=True
    )
    
    db.add(db_receta)
    db.commit()
    db.refresh(db_receta)
    
    return {"mensaje": "Receta creada exitosamente", "id": db_receta.id}

@app.get("/api/recetas/paciente/{paciente_id}")
def obtener_recetas_paciente(
    paciente_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Ver recetas del paciente - Personal médico"""
    recetas = db.query(models.Receta).filter(
        models.Receta.paciente_id == paciente_id
    ).order_by(models.Receta.fecha_emision.desc()).all()
    
    resultado = []
    for r in recetas:
        medico = db.query(models.Usuario).filter(models.Usuario.id == r.medico_id).first()
        resultado.append({
            "id": r.id,
            "paciente_id": r.paciente_id,
            "medico_id": r.medico_id,
            "medico_nombre": medico.nombre_completo if medico else "Desconocido",
            "fecha_emision": r.fecha_emision.isoformat(),
            "medicamento1_nombre": r.medicamento1_nombre,
            "medicamento1_dosis": r.medicamento1_dosis,
            "medicamento1_frecuencia": r.medicamento1_frecuencia,
            "medicamento1_duracion": r.medicamento1_duracion,
            "medicamento1_via": r.medicamento1_via,
            "medicamento2_nombre": r.medicamento2_nombre,
            "medicamento2_dosis": r.medicamento2_dosis,
            "medicamento2_frecuencia": r.medicamento2_frecuencia,
            "medicamento2_duracion": r.medicamento2_duracion,
            "medicamento2_via": r.medicamento2_via,
            "medicamento3_nombre": r.medicamento3_nombre,
            "medicamento3_dosis": r.medicamento3_dosis,
            "medicamento3_frecuencia": r.medicamento3_frecuencia,
            "medicamento3_duracion": r.medicamento3_duracion,
            "medicamento3_via": r.medicamento3_via,
            "medicamento4_nombre": r.medicamento4_nombre,
            "medicamento4_dosis": r.medicamento4_dosis,
            "medicamento4_frecuencia": r.medicamento4_frecuencia,
            "medicamento4_duracion": r.medicamento4_duracion,
            "medicamento4_via": r.medicamento4_via,
            "medicamento5_nombre": r.medicamento5_nombre,
            "medicamento5_dosis": r.medicamento5_dosis,
            "medicamento5_frecuencia": r.medicamento5_frecuencia,
            "medicamento5_duracion": r.medicamento5_duracion,
            "medicamento5_via": r.medicamento5_via,
            "indicaciones_generales": r.indicaciones_generales,
            "activa": r.activa
        })
    
    return resultado

@app.get("/api/recetas/{receta_id}/pdf")
async def descargar_receta_pdf(
    receta_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera y descarga PDF de receta"""
    
    receta = db.query(models.Receta).filter(models.Receta.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == receta.paciente_id).first()
    medico = db.query(models.Usuario).filter(models.Usuario.id == receta.medico_id).first()
    
    # Preparar datos
    medicamentos = []
    if receta.medicamento1_nombre:
        medicamentos.append({
            'nombre': receta.medicamento1_nombre,
            'dosis': receta.medicamento1_dosis,
            'frecuencia': receta.medicamento1_frecuencia,
            'duracion': receta.medicamento1_duracion,
            'via': receta.medicamento1_via
        })
    if receta.medicamento2_nombre:
        medicamentos.append({
            'nombre': receta.medicamento2_nombre,
            'dosis': receta.medicamento2_dosis,
            'frecuencia': receta.medicamento2_frecuencia,
            'duracion': receta.medicamento2_duracion,
            'via': receta.medicamento2_via
        })
    if receta.medicamento3_nombre:
        medicamentos.append({
            'nombre': receta.medicamento3_nombre,
            'dosis': receta.medicamento3_dosis,
            'frecuencia': receta.medicamento3_frecuencia,
            'duracion': receta.medicamento3_duracion,
            'via': receta.medicamento3_via
        })
    if receta.medicamento4_nombre:
        medicamentos.append({
            'nombre': receta.medicamento4_nombre,
            'dosis': receta.medicamento4_dosis,
            'frecuencia': receta.medicamento4_frecuencia,
            'duracion': receta.medicamento4_duracion,
            'via': receta.medicamento4_via
        })
    if receta.medicamento5_nombre:
        medicamentos.append({
            'nombre': receta.medicamento5_nombre,
            'dosis': receta.medicamento5_dosis,
            'frecuencia': receta.medicamento5_frecuencia,
            'duracion': receta.medicamento5_duracion,
            'via': receta.medicamento5_via
        })
    
    receta_data = {
        'id': receta.id,
        'fecha': receta.fecha_emision.strftime('%d/%m/%Y'),
        'medico_nombre': medico.nombre_completo,
        'medico_codigo': medico.codigo_medico or "N/A",
        'paciente_nombre': f"{paciente.nombre} {paciente.apellidos}",
        'paciente_id': paciente.identificacion,
        'medicamentos': medicamentos,
        'indicaciones': receta.indicaciones_generales
    }
    
    # Generar PDF
    pdf_path = generar_receta_pdf(receta_data)
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=f"receta_{receta_id}.pdf"
    )
# ==================== ÓRDENES DE LABORATORIO ====================

@app.get("/api/laboratorio/catalogo")
def obtener_catalogo_loinc(
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener catálogo de exámenes LOINC por categorías"""
    return obtener_examenes_por_categoria()

@app.get("/api/laboratorio/buscar/{termino}")
def buscar_examenes_loinc(
    termino: str,
    current_user: models.Usuario = Depends(get_current_user)
):
    """Buscar exámenes por término"""
    return buscar_examen(termino)

@app.post("/api/laboratorio/orden")
def crear_orden_laboratorio(
    orden: OrdenLaboratorioCreate,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Crear orden de laboratorio - Solo médicos"""
    paciente = db.query(models.Paciente).filter(models.Paciente.id == orden.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    if not orden.examenes or len(orden.examenes) == 0:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un examen")
    
    if len(orden.examenes) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 exámenes por orden")
    
    # Crear orden
    db_orden = models.OrdenLaboratorio(
        paciente_id=orden.paciente_id,
        medico_id=current_user.id,
        consulta_id=orden.consulta_id,
        indicaciones_clinicas=orden.indicaciones_clinicas,
        diagnostico_presuntivo=orden.diagnostico_presuntivo,
        urgente=orden.urgente,
        estado="pendiente"
    )
    
    # Agregar exámenes
    for i, examen in enumerate(orden.examenes, 1):
        setattr(db_orden, f"examen{i}_codigo_loinc", examen.codigo_loinc)
        setattr(db_orden, f"examen{i}_nombre", examen.nombre)
        setattr(db_orden, f"examen{i}_valor_referencia", examen.valor_referencia)
        setattr(db_orden, f"examen{i}_unidad", examen.unidad)
    
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    
    return {"mensaje": "Orden de laboratorio creada exitosamente", "id": db_orden.id}

@app.get("/api/laboratorio/paciente/{paciente_id}")
def obtener_ordenes_paciente(
    paciente_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Ver órdenes de laboratorio del paciente"""
    ordenes = db.query(models.OrdenLaboratorio).filter(
        models.OrdenLaboratorio.paciente_id == paciente_id
    ).order_by(models.OrdenLaboratorio.fecha_orden.desc()).all()
    
    resultado = []
    for orden in ordenes:
        medico = db.query(models.Usuario).filter(models.Usuario.id == orden.medico_id).first()
        
        # Recopilar exámenes
        examenes = []
        for i in range(1, 11):
            codigo = getattr(orden, f"examen{i}_codigo_loinc")
            if codigo:
                examenes.append({
                    "numero": i,
                    "codigo_loinc": codigo,
                    "nombre": getattr(orden, f"examen{i}_nombre"),
                    "resultado": getattr(orden, f"examen{i}_resultado"),
                    "valor_referencia": getattr(orden, f"examen{i}_valor_referencia"),
                    "unidad": getattr(orden, f"examen{i}_unidad")
                })
        
        resultado.append({
            "id": orden.id,
            "fecha_orden": orden.fecha_orden.isoformat(),
            "medico_nombre": medico.nombre_completo if medico else "Desconocido",
            "estado": orden.estado,
            "urgente": orden.urgente,
            "indicaciones_clinicas": orden.indicaciones_clinicas,
            "diagnostico_presuntivo": orden.diagnostico_presuntivo,
            "examenes": examenes,
            "fecha_resultado": orden.fecha_resultado.isoformat() if orden.fecha_resultado else None
        })
    
    return resultado

@app.put("/api/laboratorio/{orden_id}/resultado")
def agregar_resultado(
    orden_id: int,
    resultados: List[ResultadoExamen],
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Agregar resultados a una orden - Personal médico"""
    orden = db.query(models.OrdenLaboratorio).filter(models.OrdenLaboratorio.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Actualizar resultados
    for res in resultados:
        setattr(orden, f"examen{res.examen_numero}_resultado", res.resultado)
    
    # Verificar si todos los exámenes tienen resultado
    todos_completos = True
    for i in range(1, 11):
        codigo = getattr(orden, f"examen{i}_codigo_loinc")
        if codigo:
            resultado = getattr(orden, f"examen{i}_resultado")
            if not resultado:
                todos_completos = False
                break
    
    if todos_completos:
        orden.estado = "completado"
        orden.fecha_resultado = datetime.utcnow()
    else:
        orden.estado = "en_proceso"
    
    db.commit()
    
    return {"mensaje": "Resultados actualizados exitosamente"}

@app.delete("/api/laboratorio/{orden_id}")
def cancelar_orden(
    orden_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Cancelar orden de laboratorio"""
    orden = db.query(models.OrdenLaboratorio).filter(models.OrdenLaboratorio.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    orden.estado = "cancelado"
    db.commit()
    
    return {"mensaje": "Orden cancelada exitosamente"}

# ==================== ÓRDENES LABORATORIO - FHIR ====================

@app.get("/api/laboratorio/{orden_id}/fhir")
def exportar_orden_fhir(
    orden_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Exportar orden de laboratorio a formato FHIR Bundle (DiagnosticReport + Observations)"""
    orden = db.query(models.OrdenLaboratorio).filter(models.OrdenLaboratorio.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == orden.paciente_id).first()
    medico = db.query(models.Usuario).filter(models.Usuario.id == orden.medico_id).first()
    
    return fhir_converter.orden_laboratorio_to_fhir_bundle(orden, paciente, medico)


@app.post("/api/laboratorio/fhir/import")
def importar_orden_fhir(
    fhir_bundle: dict,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Importar orden de laboratorio desde formato FHIR Bundle"""
    try:
        orden_data = fhir_converter.fhir_to_orden_laboratorio(fhir_bundle, db)
        
        if "paciente_id" not in orden_data:
            raise HTTPException(status_code=400, detail="No se pudo identificar al paciente en el Bundle FHIR")
        
        if not orden_data.get("examenes"):
            raise HTTPException(status_code=400, detail="La orden debe tener al menos un examen")
        
        # Crear orden
        db_orden = models.OrdenLaboratorio(
            paciente_id=orden_data["paciente_id"],
            medico_id=current_user.id,
            diagnostico_presuntivo=orden_data.get("diagnostico_presuntivo"),
            estado="pendiente"
        )
        
        # Agregar exámenes (máximo 10)
        for i, exam in enumerate(orden_data["examenes"][:10], 1):
            setattr(db_orden, f"examen{i}_codigo_loinc", exam["codigo_loinc"])
            setattr(db_orden, f"examen{i}_nombre", exam["nombre"])
            setattr(db_orden, f"examen{i}_resultado", exam.get("resultado"))
            setattr(db_orden, f"examen{i}_valor_referencia", exam.get("valor_referencia"))
            setattr(db_orden, f"examen{i}_unidad", exam.get("unidad"))
        
        # Si todos los exámenes tienen resultado, marcar como completado
        if all(exam.get("resultado") for exam in orden_data["examenes"]):
            db_orden.estado = "completado"
            db_orden.fecha_resultado = datetime.utcnow()
        
        db.add(db_orden)
        db.commit()
        db.refresh(db_orden)
        
        return {
            "mensaje": "Orden de laboratorio importada exitosamente desde FHIR",
            "id": db_orden.id
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando FHIR: {str(e)}")
# ==================== RECETAS - FHIR ====================

@app.get("/api/recetas/{receta_id}/fhir")
def exportar_receta_fhir(
    receta_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    """Exportar receta a formato FHIR Bundle"""
    receta = db.query(models.Receta).filter(models.Receta.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == receta.paciente_id).first()
    medico = db.query(models.Usuario).filter(models.Usuario.id == receta.medico_id).first()
    
    return fhir_converter.receta_to_fhir_bundle(receta, paciente, medico)


@app.post("/api/recetas/fhir/import")
def importar_receta_fhir(
    fhir_bundle: dict,
    current_user: models.Usuario = Depends(require_roles(["medico", "admin"])),
    db: Session = Depends(get_db)
):
    """Importar receta desde formato FHIR Bundle"""
    try:
        receta_data = fhir_converter.fhir_to_receta(fhir_bundle, db)
        
        if "paciente_id" not in receta_data:
            raise HTTPException(status_code=400, detail="No se pudo identificar al paciente en el Bundle FHIR")
        
        # Validar que al menos tenga medicamento1
        if not receta_data.get("medicamento1_nombre"):
            raise HTTPException(status_code=400, detail="La receta debe tener al menos un medicamento")
        
        # Crear receta
        db_receta = models.Receta(
            paciente_id=receta_data["paciente_id"],
            medico_id=current_user.id,
            medicamento1_nombre=receta_data.get("medicamento1_nombre"),
            medicamento1_dosis=receta_data.get("medicamento1_dosis", ""),
            medicamento1_frecuencia=receta_data.get("medicamento1_frecuencia", ""),
            medicamento1_duracion=receta_data.get("medicamento1_duracion", ""),
            medicamento1_via=receta_data.get("medicamento1_via", "Oral"),
            medicamento2_nombre=receta_data.get("medicamento2_nombre"),
            medicamento2_dosis=receta_data.get("medicamento2_dosis"),
            medicamento2_frecuencia=receta_data.get("medicamento2_frecuencia"),
            medicamento2_duracion=receta_data.get("medicamento2_duracion"),
            medicamento2_via=receta_data.get("medicamento2_via"),
            medicamento3_nombre=receta_data.get("medicamento3_nombre"),
            medicamento3_dosis=receta_data.get("medicamento3_dosis"),
            medicamento3_frecuencia=receta_data.get("medicamento3_frecuencia"),
            medicamento3_duracion=receta_data.get("medicamento3_duracion"),
            medicamento3_via=receta_data.get("medicamento3_via"),
            medicamento4_nombre=receta_data.get("medicamento4_nombre"),
            medicamento4_dosis=receta_data.get("medicamento4_dosis"),
            medicamento4_frecuencia=receta_data.get("medicamento4_frecuencia"),
            medicamento4_duracion=receta_data.get("medicamento4_duracion"),
            medicamento4_via=receta_data.get("medicamento4_via"),
            medicamento5_nombre=receta_data.get("medicamento5_nombre"),
            medicamento5_dosis=receta_data.get("medicamento5_dosis"),
            medicamento5_frecuencia=receta_data.get("medicamento5_frecuencia"),
            medicamento5_duracion=receta_data.get("medicamento5_duracion"),
            medicamento5_via=receta_data.get("medicamento5_via"),
            indicaciones_generales=receta_data.get("indicaciones_generales"),
            activa=True
        )
        
        db.add(db_receta)
        db.commit()
        db.refresh(db_receta)
        
        return {
            "mensaje": "Receta importada exitosamente desde FHIR",
            "id": db_receta.id
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando FHIR: {str(e)}")

# ==================== FHIR ENDPOINTS ====================

@app.get("/fhir/Patient/{paciente_id}")
def get_fhir_patient(
    paciente_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return fhir_converter.paciente_to_fhir(paciente)

@app.post("/fhir/Patient")
def create_fhir_patient(
    fhir_patient: dict,
    current_user: models.Usuario = Depends(require_roles(["recepcion", "admin", "medico"])),
    db: Session = Depends(get_db)
):
    try:
        paciente_data = fhir_converter.fhir_to_paciente(fhir_patient)
        
        existe = db.query(models.Paciente).filter(
            models.Paciente.identificacion == paciente_data["identificacion"]
        ).first()
        
        if existe:
            raise HTTPException(status_code=400, detail="Paciente ya existe")
        
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
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == consulta.paciente_id).first()
    
    return fhir_converter.consulta_to_fhir_encounter(consulta, paciente)

@app.get("/fhir/Bundle/consulta/{consulta_id}")
def get_fhir_bundle(
    consulta_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == consulta.paciente_id).first()
    
    return fhir_converter.consulta_to_fhir_bundle(consulta, paciente)

@app.get("/fhir/Bundle/paciente/{paciente_id}")
def get_patient_bundle(
    paciente_id: int,
    current_user: models.Usuario = Depends(require_roles(["medico", "enfermera", "admin"])),
    db: Session = Depends(get_db)
):
    from fhir.resources.bundle import Bundle, BundleEntry
    
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    consultas = db.query(models.Consulta).filter(
        models.Consulta.paciente_id == paciente_id
    ).order_by(models.Consulta.fecha.desc()).all()
    
    entries = []
    
    patient_fhir = fhir_converter.paciente_to_fhir(paciente)
    entries.append(BundleEntry(
        fullUrl=f"urn:uuid:patient-{paciente.id}",
        resource=patient_fhir
    ))
    
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
# ==================== IMAGENOLOGÍA ====================

@app.post("/api/imagenologia/orden")
async def crear_orden_imagenologia(
    datos: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva orden de imagenología"""
    try:
        nueva_orden = models.OrdenImagenologia(
            paciente_id=datos["paciente_id"],
            medico_id=current_user.id,
            diagnostico_presuntivo=datos.get("diagnostico_presuntivo", ""),
            indicaciones_clinicas=datos.get("indicaciones_clinicas", ""),
            uso_contraste=datos.get("uso_contraste", False),
            urgente=datos.get("urgente", False),
            observaciones=datos.get("observaciones", ""),
            estado="pendiente"
        )
        
        db.add(nueva_orden)
        db.flush()
        
        for idx, estudio in enumerate(datos["estudios"], 1):
            nuevo_estudio = models.EstudioImagenologia(
                orden_id=nueva_orden.id,
                numero=idx,
                categoria=estudio["categoria"],
                nombre=estudio["nombre"],
                estado="pendiente"
            )
            db.add(nuevo_estudio)
        
        db.commit()
        db.refresh(nueva_orden)
        
        return {"mensaje": "Orden creada exitosamente", "id": nueva_orden.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/imagenologia/paciente/{paciente_id}")
async def obtener_ordenes_imagenologia(
    paciente_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener órdenes de imagenología de un paciente"""
    ordenes = db.query(models.OrdenImagenologia).filter(
        models.OrdenImagenologia.paciente_id == paciente_id
    ).all()
    
    resultado = []
    for orden in ordenes:
        medico = db.query(models.Usuario).filter(models.Usuario.id == orden.medico_id).first()
        estudios = db.query(models.EstudioImagenologia).filter(
            models.EstudioImagenologia.orden_id == orden.id
        ).all()
        
        resultado.append({
            "id": orden.id,
            "fecha_orden": orden.fecha_orden.isoformat(),
            "medico_nombre": medico.nombre_completo if medico else "N/A",
            "diagnostico_presuntivo": orden.diagnostico_presuntivo,
            "indicaciones_clinicas": orden.indicaciones_clinicas,
            "uso_contraste": orden.uso_contraste,
            "urgente": orden.urgente,
            "observaciones": orden.observaciones,
            "estado": orden.estado,
            "fecha_resultado": orden.fecha_resultado.isoformat() if orden.fecha_resultado else None,
            "informe_url": orden.informe_url,
            "estudios": [{
                "numero": e.numero,
                "categoria": e.categoria,
                "nombre": e.nombre,
                "resultado": e.resultado,
                "estado": e.estado
            } for e in estudios]
        })
    
    return resultado


@app.delete("/api/imagenologia/{orden_id}")
async def cancelar_orden_imagenologia(
    orden_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancelar orden de imagenología"""
    if current_user.rol not in ["medico", "admin"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    orden = db.query(models.OrdenImagenologia).filter(models.OrdenImagenologia.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    orden.estado = "cancelado"
    db.commit()
    
    return {"mensaje": "Orden cancelada"}