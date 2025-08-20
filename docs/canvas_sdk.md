# Loading Secrets

Every protocol that interacts with the Tellescope API must first load secrets. If secrets are not defined, the protocol should return early. Here's an example illustrating how secrets are loaded:
```python
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.effects import Effect

class Protocol(BaseProtocol):
    def compute(self) -> list[Effect]:
        tellescope_api_key = self.secrets["TELLESCOPE_API_KEY"]
        tellescope_api_url = self.secrets["TELLESCOPE_API_URL"]
```

If testing Tellescope API utilities locally, you can pull these values from the local .env as follows:
```python
import os

tellescope_api_key = os.getenv("TELLESCOPE_API_KEY")
tellescope_api_url = os.getenv("TELLESCOPE_API_URL")

if not tellescope_api_key or not tellescope_api_url:
  raise EnvironmentError("Missing Tellescope API credentials in environment variables.")
```

# Canvas SDK

## Architecture Overview

The Canvas Medical SDK is an event-driven framework that allows customization of medical workflows through plugins. Key architectural concepts:

### Core Components
- **Protocols**: Event-driven workflow definitions that respond to Canvas events
- **Events**: Runtime notifications emitted by the Canvas application
- **Effects**: Instructions returned by protocols to modify application state
- **Data Models**: Django ORM-like classes providing read-only access to medical data

### Event-Driven Flow
1. Canvas application emits events during runtime
2. Protocols listen for specific events
3. Protocols process events and return effects
4. Effects modify application state (UI, data, workflows)

### Plugin Environment
- Runs in sandboxed environment on Canvas instance
- Secure access to PHI and non-PHI data
- Integration with standard medical terminologies (ICD-10, SNOMED-CT, CPT)

## Protocol Implementation Patterns

### Basic Protocol Structure
```python
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.effects import Effect

class MyProtocol(BaseProtocol):
    def compute(self) -> list[Effect]:
        # Load secrets (required for Tellescope integration)
        tellescope_api_key = self.secrets["TELLESCOPE_API_KEY"]
        tellescope_api_url = self.secrets["TELLESCOPE_API_URL"]
        
        # Access event data
        event_data = self.event
        
        # Process business logic
        # ...
        
        # Return effects to modify Canvas state
        return [Effect(type="EFFECT_TYPE", payload={})]
```

### Event Handling Patterns
```python
# Access event type and data
event_type = self.event.type
event_payload = self.event.payload

# Common event-driven checks
if event_type == "APPOINTMENT_SCHEDULED":
    appointment = event_payload.get("appointment")
    # Handle appointment scheduling
elif event_type == "PATIENT_UPDATED":
    patient = event_payload.get("patient")
    # Handle patient updates
```

### Error Handling and Validation
```python
def compute(self) -> list[Effect]:
    # Always validate secrets first
    if not self.secrets.get("TELLESCOPE_API_KEY"):
        # Return early if secrets missing
        return []
    
    try:
        # Protocol logic here
        pass
    except Exception as e:
        # Log error and return appropriate effect
        return [Effect(type="ADD_BANNER_ALERT", payload={
            "type": "error",
            "message": f"Protocol error: {str(e)}"
        })]
```

## Data Model Access Patterns

### Importing Data Models
```python
from canvas_sdk.data import Patient, Appointment, Medication, Condition
from canvas_sdk.data import Labs, Tasks, Messages, Notes, CareTeam
```

### Querying Patient Data
```python
# Get patient from event
patient_id = self.event.payload.get("patient_id")
patient = Patient.objects.get(id=patient_id)

# Access patient fields
patient_name = f"{patient.first_name} {patient.last_name}"
patient_dob = patient.date_of_birth
patient_mrn = patient.medical_record_number
```

### Querying Related Medical Data
```python
# Get patient's appointments
appointments = Appointment.objects.filter(patient=patient)
upcoming_appointments = appointments.filter(
    scheduled_datetime__gte=timezone.now()
)

# Get patient's medications
medications = Medication.objects.filter(patient=patient)
active_medications = medications.filter(status="active")

# Get patient's conditions
conditions = Condition.objects.filter(patient=patient)

# Get patient's lab results
labs = Labs.objects.filter(patient=patient)
recent_labs = labs.filter(
    date__gte=timezone.now() - timedelta(days=30)
)
```

### QuerySet Patterns
```python
# Use Django QuerySet methods for efficient queries
patients_with_diabetes = Patient.objects.filter(
    condition__icd10_code__startswith="E11"
)

# Complex filtering
high_risk_patients = Patient.objects.filter(
    age__gte=65,
    medication__name__icontains="insulin"
).distinct()

# Accessing related objects
for patient in patients_with_diabetes:
    care_team = CareTeam.objects.filter(patient=patient)
    primary_provider = care_team.filter(role="primary").first()
```

## Effects Implementation Patterns

### Common Effect Types
```python
from canvas_sdk.effects import Effect

# User Interface Effects
banner_alert = Effect(type="ADD_BANNER_ALERT", payload={
    "type": "info",  # "info", "warning", "error", "success"
    "message": "Patient has been synchronized with Tellescope"
})

action_button = Effect(type="SHOW_ACTION_BUTTON", payload={
    "text": "Sync to Tellescope",
    "handler": "sync_handler"
})

modal_launch = Effect(type="LAUNCH_MODAL", payload={
    "title": "Tellescope Integration",
    "content": "Patient data synchronized successfully"
})

# Task and Workflow Effects
create_task = Effect(type="CREATE_TASK", payload={
    "title": "Follow up on Tellescope sync",
    "description": "Verify patient data synchronization",
    "assignee_id": provider_id,
    "due_date": "2024-01-15"
})

# Data Modification Effects
medication_statement = Effect(type="ORIGINATE_MEDICATION_STATEMENT_COMMAND", payload={
    "patient_id": patient.id,
    "medication_name": "Metformin",
    "dosage": "500mg twice daily"
})
```

### Effect Construction Patterns
```python
def create_success_effects(message: str) -> list[Effect]:
    """Helper function to create success notification effects"""
    return [
        Effect(type="ADD_BANNER_ALERT", payload={
            "type": "success",
            "message": message
        })
    ]

def create_error_effects(error: str) -> list[Effect]:
    """Helper function to create error notification effects"""
    return [
        Effect(type="ADD_BANNER_ALERT", payload={
            "type": "error", 
            "message": f"Error: {error}"
        })
    ]

# Usage in protocol
def compute(self) -> list[Effect]:
    try:
        # Business logic here
        sync_patient_to_tellescope(patient)
        return create_success_effects("Patient synchronized successfully")
    except Exception as e:
        return create_error_effects(str(e))
```

### Conditional Effects
```python
def compute(self) -> list[Effect]:
    effects = []
    
    # Conditional effect based on patient data
    if patient.age >= 65:
        effects.append(Effect(type="ADD_BANNER_ALERT", payload={
            "type": "info",
            "message": "Senior patient - consider special protocols"
        }))
    
    # Conditional effect based on event type
    if self.event.type == "APPOINTMENT_SCHEDULED":
        effects.append(Effect(type="CREATE_TASK", payload={
            "title": "Prepare for appointment",
            "patient_id": patient.id
        }))
    
    return effects
```

## Best Practices for AI Assistant Development

### 1. Code Structure and Organization
- Always inherit from `BaseProtocol` for protocol implementations
- Use descriptive class and method names following the project's naming conventions
- Organize imports logically: Canvas SDK imports first, then external libraries
- Keep protocol logic focused and single-purpose

### 2. Error Handling and Validation
- **Always** validate `TELLESCOPE_API_KEY` and `TELLESCOPE_API_URL` at the start of `compute()`
- Return empty list `[]` if secrets are missing (fail gracefully)
- Use try-catch blocks around external API calls and data access
- Return user-friendly error effects rather than letting exceptions propagate

### 3. Data Access Patterns
- Use `.get()` for single objects, `.filter()` for multiple objects
- Always check if objects exist before accessing properties: `patient = Patient.objects.filter(id=patient_id).first()`
- Use Django QuerySet methods efficiently to minimize database queries
- Respect PHI data handling requirements - only access necessary patient data

### 4. Effect Implementation
- Return effects as a list, even if returning a single effect: `return [effect]`
- Use appropriate effect types for the intended action (UI modification, task creation, etc.)
- Provide clear, actionable messages in banner alerts
- Consider the user experience when designing effect sequences

### 5. Integration with Tellescope API
- Always load Tellescope credentials from `self.secrets`
- Use existing utilities from the `utilities/` folder when available
- Follow the patterns established in `tellescope_api.md` for API interactions
- Handle API rate limits and connection errors gracefully

### 6. Testing Considerations
- Write unit tests that mock Canvas SDK data models and Tellescope API calls
- Test both success and error scenarios
- Use the test environment variables from `.env` for integration tests
- Validate that protocols return expected effect types and payloads

### 7. Protocol-Specific Guidelines
- Event handling: Always check `self.event.type` before processing event data
- Patient data: Validate patient exists before accessing related data
- Appointment data: Check appointment status and timing constraints
- Medical data: Respect clinical workflows and provider preferences

### 8. Common Pitfalls to Avoid
- Don't access `self.event.payload` without checking if the event type matches your expectations
- Don't return effects that could cause infinite loops (some event/effect combinations are restricted)
- Don't hard-code patient IDs, provider IDs, or other Canvas instance-specific data
- Don't forget to handle cases where related objects (appointments, medications) don't exist

