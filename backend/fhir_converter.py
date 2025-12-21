from datetime import datetime
from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.encounter import Encounter
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.identifier import Identifier
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from backend import models

def paciente_to_fhir(paciente: models.Paciente) -> dict:
    """Convierte un paciente del modelo interno a FHIR Patient"""
    
    # Crear nombre en formato FHIR
    name = HumanName(
        family=paciente.apellidos,
        given=[paciente.nombre],
        use="official"
    )
    
    # Crear contacto (teléfono)
    telecom = []
    if paciente.telefono:
        telecom.append(ContactPoint(
            system="phone",
            value=paciente.telefono,
            use="mobile"
        ))
    if paciente.email:
        telecom.append(ContactPoint(
            system="email",
            value=paciente.email
        ))
    
    # Crear dirección
    address = []
    if paciente.direccion:
        address.append(Address(
            use="home",
            text=paciente.direccion
        ))
    
    # Crear identificador
    identifier = [Identifier(
        system="urn:oid:ece-medico",
        value=paciente.identificacion
    )]
    
    # Determinar género en formato FHIR
    gender_map = {
        "Masculino": "male",
        "Femenino": "female",
        "Otro": "other"
    }
    
    # Crear recurso Patient FHIR
    fhir_patient = Patient(
        id=str(paciente.id),
        identifier=identifier,
        name=[name],
        telecom=telecom,
        gender=gender_map.get(paciente.genero, "unknown"),
        birthDate=paciente.fecha_nacimiento.date() if paciente.fecha_nacimiento else None,
        address=address,
        active=True
    )
    
    return fhir_patient.dict()

def fhir_to_paciente(fhir_patient: dict) -> dict:
    """Convierte un FHIR Patient a formato interno"""
    
    # Extraer nombre
    nombre = ""
    apellidos = ""
    if fhir_patient.get("name"):
        name = fhir_patient["name"][0]
        nombre = " ".join(name.get("given", []))
        apellidos = name.get("family", "")
    
    # Extraer identificación
    identificacion = ""
    if fhir_patient.get("identifier"):
        identificacion = fhir_patient["identifier"][0].get("value", "")
    
    # Extraer teléfono y email
    telefono = ""
    email = ""
    if fhir_patient.get("telecom"):
        for contact in fhir_patient["telecom"]:
            if contact.get("system") == "phone":
                telefono = contact.get("value", "")
            elif contact.get("system") == "email":
                email = contact.get("value", "")
    
    # Extraer dirección
    direccion = ""
    if fhir_patient.get("address"):
        direccion = fhir_patient["address"][0].get("text", "")
    
    # Mapear género
    gender_map = {
        "male": "Masculino",
        "female": "Femenino",
        "other": "Otro",
        "unknown": "Otro"
    }
    genero = gender_map.get(fhir_patient.get("gender", "unknown"), "Otro")
    
    # Extraer fecha de nacimiento
    birth_date = fhir_patient.get("birthDate", "")
    
    return {
        "identificacion": identificacion,
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": birth_date,
        "genero": genero,
        "telefono": telefono,
        "email": email,
        "direccion": direccion
    }

def consulta_to_fhir_encounter(consulta: models.Consulta, paciente: models.Paciente) -> dict:
    """Convierte una consulta a FHIR Encounter"""
    
    # Crear referencia al paciente
    patient_reference = Reference(
        reference=f"Patient/{paciente.id}",
        display=f"{paciente.nombre} {paciente.apellidos}"
    )
    
    # Crear Encounter
    encounter = Encounter(
        id=str(consulta.id),
        status="finished",
        class_fhir=Coding(
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code="AMB",
            display="ambulatory"
        ),
        subject=patient_reference,
        period={
            "start": consulta.fecha.isoformat()
        },
        reasonCode=[CodeableConcept(
            text=consulta.motivo
        )]
    )
    
    return encounter.dict()

def consulta_to_fhir_bundle(consulta: models.Consulta, paciente: models.Paciente) -> dict:
    """
    Convierte una consulta completa a un FHIR Bundle con:
    - Encounter (la consulta)
    - Observations (signos vitales)
    - Condition (diagnóstico)
    - MedicationRequest (tratamiento)
    """
    
    from fhir.resources.bundle import Bundle, BundleEntry
    from fhir.resources.quantity import Quantity
    
    entries = []
    
    # 1. Encounter (consulta)
    encounter = consulta_to_fhir_encounter(consulta, paciente)
    entries.append(BundleEntry(
        fullUrl=f"urn:uuid:encounter-{consulta.id}",
        resource=encounter
    ))
    
    # 2. Observations (signos vitales)
    if consulta.signos_vitales:
        # Parsear signos vitales (formato: "PA: 120/80, T: 36.5°C, ...")
        signos = {}
        for item in consulta.signos_vitales.split(','):
            if ':' in item:
                key, value = item.split(':', 1)
                signos[key.strip()] = value.strip()
        
        # Presión arterial
        if 'PA' in signos and signos['PA']:
            pa_obs = Observation(
                id=f"obs-pa-{consulta.id}",
                status="final",
                code=CodeableConcept(
                    coding=[Coding(
                        system="http://loinc.org",
                        code="85354-9",
                        display="Blood pressure panel"
                    )],
                    text="Presión Arterial"
                ),
                subject=Reference(reference=f"Patient/{paciente.id}"),
                valueString=signos['PA']
            )
            entries.append(BundleEntry(
                fullUrl=f"urn:uuid:obs-pa-{consulta.id}",
                resource=pa_obs.dict()
            ))
        
        # Temperatura
        if 'T' in signos and signos['T'] and signos['T'] != '°C':
            temp_obs = Observation(
                id=f"obs-temp-{consulta.id}",
                status="final",
                code=CodeableConcept(
                    coding=[Coding(
                        system="http://loinc.org",
                        code="8310-5",
                        display="Body temperature"
                    )],
                    text="Temperatura"
                ),
                subject=Reference(reference=f"Patient/{paciente.id}"),
                valueString=signos['T']
            )
            entries.append(BundleEntry(
                fullUrl=f"urn:uuid:obs-temp-{consulta.id}",
                resource=temp_obs.dict()
            ))
    
    # 3. Condition (diagnóstico)
    if consulta.diagnostico:
        condition = Condition(
            id=f"condition-{consulta.id}",
            clinicalStatus=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                    code="active"
                )]
            ),
            code=CodeableConcept(
                text=consulta.diagnostico
            ),
            subject=Reference(reference=f"Patient/{paciente.id}")
        )
        entries.append(BundleEntry(
            fullUrl=f"urn:uuid:condition-{consulta.id}",
            resource=condition.dict()
        ))
    
    # 4. MedicationRequest (tratamiento)
    if consulta.tratamiento:
        med_request = MedicationRequest(
            id=f"medication-{consulta.id}",
            status="active",
            intent="order",
            medicationCodeableConcept=CodeableConcept(
                text=consulta.tratamiento
            ),
            subject=Reference(reference=f"Patient/{paciente.id}"),
            authoredOn=consulta.fecha.isoformat()
        )
        entries.append(BundleEntry(
            fullUrl=f"urn:uuid:medication-{consulta.id}",
            resource=med_request.dict()
        ))
    
    # Crear Bundle
    bundle = Bundle(
        type="collection",
        entry=entries
    )
def receta_to_fhir_medication_request(receta: models.Receta, paciente: models.Paciente, medico: models.Usuario) -> dict:
    """Convierte una receta a FHIR MedicationRequest"""
    from fhir.resources.medicationrequest import MedicationRequest
    from fhir.resources.dosage import Dosage
    
    # Crear MedicationRequests para cada medicamento
    medication_requests = []
    
    # Función auxiliar para crear un MedicationRequest
    def create_med_request(nombre, dosis, frecuencia, duracion, via, index):
        dosage = Dosage(
            text=f"{dosis} - {frecuencia} - {duracion}",
            route=CodeableConcept(text=via),
            doseAndRate=[{
                "doseQuantity": {
                    "value": dosis,
                    "unit": "unidad"
                }
            }]
        )
        
        med_request = MedicationRequest(
            id=f"receta-{receta.id}-med-{index}",
            status="active" if receta.activa else "cancelled",
            intent="order",
            medicationCodeableConcept=CodeableConcept(text=nombre),
            subject=Reference(
                reference=f"Patient/{paciente.id}",
                display=f"{paciente.nombre} {paciente.apellidos}"
            ),
            requester=Reference(
                reference=f"Practitioner/{medico.id}",
                display=medico.nombre_completo
            ),
            authoredOn=receta.fecha_emision.isoformat(),
            dosageInstruction=[dosage],
            note=[{
                "text": receta.indicaciones_generales or ""
            }] if receta.indicaciones_generales else []
        )
        
        return med_request.dict()
    
    # Agregar medicamentos
    if receta.medicamento1_nombre:
        medication_requests.append(create_med_request(
            receta.medicamento1_nombre,
            receta.medicamento1_dosis,
            receta.medicamento1_frecuencia,
            receta.medicamento1_duracion,
            receta.medicamento1_via,
            1
        ))
    
    if receta.medicamento2_nombre:
        medication_requests.append(create_med_request(
            receta.medicamento2_nombre,
            receta.medicamento2_dosis,
            receta.medicamento2_frecuencia,
            receta.medicamento2_duracion,
            receta.medicamento2_via,
            2
        ))
    
    if receta.medicamento3_nombre:
        medication_requests.append(create_med_request(
            receta.medicamento3_nombre,
            receta.medicamento3_dosis,
            receta.medicamento3_frecuencia,
            receta.medicamento3_duracion,
            receta.medicamento3_via,
            3
        ))
    
    if receta.medicamento4_nombre:
        medication_requests.append(create_med_request(
            receta.medicamento4_nombre,
            receta.medicamento4_dosis,
            receta.medicamento4_frecuencia,
            receta.medicamento4_duracion,
            receta.medicamento4_via,
            4
        ))
    
    if receta.medicamento5_nombre:
        medication_requests.append(create_med_request(
            receta.medicamento5_nombre,
            receta.medicamento5_dosis,
            receta.medicamento5_frecuencia,
            receta.medicamento5_duracion,
            receta.medicamento5_via,
            5
        ))
    
    return medication_requests


def receta_to_fhir_bundle(receta: models.Receta, paciente: models.Paciente, medico: models.Usuario) -> dict:
    """Convierte una receta completa a FHIR Bundle"""
    from fhir.resources.bundle import Bundle, BundleEntry
    
    entries = []
    
    # Agregar paciente
    patient_fhir = paciente_to_fhir(paciente)
    entries.append(BundleEntry(
        fullUrl=f"urn:uuid:patient-{paciente.id}",
        resource=patient_fhir
    ))
    
    # Agregar MedicationRequests
    medication_requests = receta_to_fhir_medication_request(receta, paciente, medico)
    for i, med_req in enumerate(medication_requests):
        entries.append(BundleEntry(
            fullUrl=f"urn:uuid:medication-request-{receta.id}-{i+1}",
            resource=med_req
        ))
    
    bundle = Bundle(
        type="collection",
        entry=entries
    )
    
    return bundle.dict()


def fhir_to_receta(fhir_bundle: dict, db) -> dict:
    """Convierte un FHIR Bundle a formato de receta interno"""
    
    receta_data = {
        "medicamentos": []
    }
    
    # Extraer paciente
    paciente_ref = None
    medicamentos = []
    
    for entry in fhir_bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        
        if resource_type == "Patient":
            # Buscar paciente por identificación
            if resource.get("identifier"):
                identificacion = resource["identifier"][0].get("value", "")
                paciente = db.query(models.Paciente).filter(
                    models.Paciente.identificacion == identificacion
                ).first()
                if paciente:
                    receta_data["paciente_id"] = paciente.id
        
        elif resource_type == "MedicationRequest":
            # Extraer información del medicamento
            med_name = ""
            if resource.get("medicationCodeableConcept"):
                med_name = resource["medicationCodeableConcept"].get("text", "")
            
            dosage_text = ""
            via = "Oral"
            
            if resource.get("dosageInstruction"):
                dosage = resource["dosageInstruction"][0]
                dosage_text = dosage.get("text", "")
                if dosage.get("route"):
                    via = dosage["route"].get("text", "Oral")
            
            # Parsear dosage_text (formato: "dosis - frecuencia - duracion")
            parts = dosage_text.split(" - ")
            dosis = parts[0] if len(parts) > 0 else ""
            frecuencia = parts[1] if len(parts) > 1 else ""
            duracion = parts[2] if len(parts) > 2 else ""
            
            medicamentos.append({
                "nombre": med_name,
                "dosis": dosis,
                "frecuencia": frecuencia,
                "duracion": duracion,
                "via": via
            })
            
            # Extraer indicaciones generales
            if resource.get("note"):
                receta_data["indicaciones_generales"] = resource["note"][0].get("text", "")
    
    # Asignar medicamentos (máximo 5)
    for i, med in enumerate(medicamentos[:5], 1):
        receta_data[f"medicamento{i}_nombre"] = med["nombre"]
        receta_data[f"medicamento{i}_dosis"] = med["dosis"]
        receta_data[f"medicamento{i}_frecuencia"] = med["frecuencia"]
        receta_data[f"medicamento{i}_duracion"] = med["duracion"]
        receta_data[f"medicamento{i}_via"] = med["via"]
    
    return receta_data

    return bundle.dict()