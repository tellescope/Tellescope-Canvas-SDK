# Description:
# This protocol automatically creates an Enduser in Tellescope when a patient is created in Canvas.
# It maps Canvas patient data to Tellescope enduser format and handles potential conflicts.

import json
from datetime import datetime
from typing import Optional

from canvas_sdk.effects import Effect, EffectType
from canvas_sdk.events import EventType
from canvas_sdk.protocols import BaseProtocol
from logger import log

from tellescope.utilities.tellescope_api import TellescopeAPI

class Protocol(BaseProtocol):
    """
    Canvas Patient to Tellescope Enduser Sync Protocol
    
    Automatically creates a corresponding Enduser in Tellescope when a patient is created in Canvas.
    This enables seamless patient data synchronization between the two systems.
    """

    # Respond to patient creation events in Canvas
    RESPONDS_TO = EventType.Name(EventType.PATIENT_CREATED)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Validate secrets - initialize TellescopeAPI only if secrets are available
        if self.secrets.get("TELLESCOPE_API_KEY"):
            self.tellescope_api = TellescopeAPI(self.secrets.get("TELLESCOPE_API_KEY"), self.secrets.get("TELLESCOPE_API_URL"))
        else:
            self.tellescope_api = None

    def compute(self) -> list[Effect]:
        """
        Handle patient creation event by creating corresponding Tellescope enduser
        """
        # Return early if secrets are not available
        if not self.tellescope_api:
            return []
            
        patient_id = None
        try:
            # Get the patient instance from the event
            patient = self.event.target.instance
            
            if not patient:
                log.error("No patient instance found in event")
                return [self._create_error_effect("Patient instance not available", "missing_patient_instance")]

            patient_id = patient.id
            log.info(f"Processing patient creation for Canvas patient ID: {patient_id}")

            # Return early if patient already has Tellescope FHIR identifier
            if self._has_tellescope_identifier(patient):
                tellescope_id = self._get_tellescope_identifier_value(patient)
                log.info(f"Patient {patient_id} already has Tellescope FHIR identifier: {tellescope_id}")
                return [self._create_success_effect(
                    f"Patient already has Tellescope identifier: {tellescope_id}",
                    tellescope_id or "unknown",
                    patient_id,
                    "fhir_identifier_exists"
                )]

            # Check if enduser already exists in Tellescope (avoid duplicates)
            existing_enduser = self._find_existing_enduser(patient_id)
            if existing_enduser:
                log.info(f"Enduser already exists in Tellescope with ID: {existing_enduser['id']}")
                return [self._create_success_effect(
                    f"Enduser already exists in Tellescope",
                    existing_enduser['id'],
                    patient_id,
                    "duplicate_handling"
                )]

            # Map Canvas patient data to Tellescope enduser format
            enduser_data = self._map_patient_to_enduser(patient)
            log.debug(f"Mapped patient data for Canvas ID {patient_id}")
            
            # Create enduser in Tellescope
            created_enduser = self.tellescope_api.create("enduser", enduser_data)
            
            log.info(f"Successfully created Tellescope enduser: {created_enduser['id']} for Canvas patient: {patient_id}")
            
            return [self._create_success_effect(
                "Successfully created Tellescope enduser",
                created_enduser['id'],
                patient_id,
                "enduser_creation"
            )]

        except ValueError as e:
            # API validation errors (400 responses)
            log.error(f"Validation error creating Tellescope enduser for patient {patient_id}: {str(e)}")
            return [self._create_error_effect(f"Data validation failed: {str(e)}", "validation_error")]
        except ConnectionError as e:
            # Network or rate limiting errors
            log.error(f"Connection error creating Tellescope enduser for patient {patient_id}: {str(e)}")
            return [self._create_error_effect(f"Connection failed: {str(e)}", "connection_error")]
        except Exception as e:
            # Unexpected errors
            log.error(f"Unexpected error creating Tellescope enduser for patient {patient_id}: {str(e)}")
            return [self._create_error_effect(f"Unexpected error: {str(e)}", "unexpected_error")]

    def _find_existing_enduser(self, canvas_patient_id: str) -> Optional[dict]:
        """
        Check if an enduser already exists in Tellescope for this Canvas patient
        
        Args:
            canvas_patient_id: Canvas patient identifier
            
        Returns:
            Existing enduser record or None if not found
        """
        try:
            # Use MongoDB filter to find enduser by Canvas external ID
            mongodb_filter = {"externalId": str(canvas_patient_id)}
            log.debug(f"Checking for existing enduser with Canvas ID {canvas_patient_id}")
            result = self.tellescope_api.find_by("endusers", mongodb_filter)
            
            if result:
                log.debug(f"Found existing enduser {result['id']} for Canvas patient {canvas_patient_id}")
            else:
                log.debug(f"No existing enduser found for Canvas patient {canvas_patient_id}")
            
            return result
        except Exception as e:
            log.warning(f"Error checking for existing enduser: {str(e)}")
            return None

    def _map_patient_to_enduser(self, patient) -> dict:
        """
        Map Canvas patient data to Tellescope enduser format
        
        Args:
            patient: Canvas patient instance
            
        Returns:
            Dictionary with Tellescope enduser data
        """
        # Map Canvas sex field to Tellescope gender field
        gender_mapping = {
            'M': 'Male',
            'F': 'Female', 
            'O': 'Other',
            'Other': 'Other'
        }
        
        # Format date of birth to MM-DD-YYYY if available
        date_of_birth = None
        if hasattr(patient, 'date_of_birth') and patient.date_of_birth:
            if isinstance(patient.date_of_birth, str):
                # If already a string, keep as is
                date_of_birth = patient.date_of_birth
            else:
                # If datetime object, format to MM-DD-YYYY
                date_of_birth = patient.date_of_birth.strftime("%m-%d-%Y")

        # Build enduser data with required and available fields
        enduser_data = {
            # Core identification
            "externalId": str(patient.id),  # Store Canvas patient ID for future lookups
            "source": "Canvas",
            
            # Personal information
            "fname": getattr(patient, 'first_name', ''),
            "lname": getattr(patient, 'last_name', ''),
            "email": getattr(patient, 'email', None) or f"patient{patient.id}@canvas.medical",
            
            # Contact information
            "phone": getattr(patient, 'phone_number', None),
            
            # Demographics
            "dateOfBirth": date_of_birth,
            "gender": gender_mapping.get(getattr(patient, 'sex', None), 'Unknown')
        }

        # Remove empty string values and None values
        enduser_data = {k: v for k, v in enduser_data.items() if v != '' and v is not None}
        
        return enduser_data

    def _has_tellescope_identifier(self, patient) -> bool:
        """
        Check if patient has a FHIR identifier with system='Tellescope'
        
        Args:
            patient: Canvas patient instance
            
        Returns:
            True if patient has a Tellescope FHIR identifier, False otherwise
        """
        # Check if patient has identifier attribute (FHIR-style)
        if hasattr(patient, 'identifier') and patient.identifier:
            for identifier in patient.identifier:
                if (isinstance(identifier, dict) and 
                    identifier.get('system') == 'Tellescope'):
                    return True
        
        # Check if patient has identifiers attribute (alternative naming)
        if hasattr(patient, 'identifiers') and patient.identifiers:
            for identifier in patient.identifiers:
                if (isinstance(identifier, dict) and 
                    identifier.get('system') == 'Tellescope'):
                    return True
        
        return False

    def _get_tellescope_identifier_value(self, patient) -> Optional[str]:
        """
        Get the value of the Tellescope identifier if it exists
        
        Args:
            patient: Canvas patient instance
            
        Returns:
            The Tellescope identifier value or None if not found
        """
        # Check identifier attribute
        if hasattr(patient, 'identifier') and patient.identifier:
            for identifier in patient.identifier:
                if (isinstance(identifier, dict) and 
                    identifier.get('system') == 'Tellescope'):
                    return identifier.get('value')
        
        # Check identifiers attribute
        if hasattr(patient, 'identifiers') and patient.identifiers:
            for identifier in patient.identifiers:
                if (isinstance(identifier, dict) and 
                    identifier.get('system') == 'Tellescope'):
                    return identifier.get('value')
        
        return None

    def _create_success_effect(self, message: str, tellescope_enduser_id: str, canvas_patient_id: str, operation_type: str = "unknown") -> Effect:
        """
        Create a success effect for logging
        
        Args:
            message: Success message
            tellescope_enduser_id: Created Tellescope enduser ID
            canvas_patient_id: Canvas patient ID
            operation_type: Type of operation performed
            
        Returns:
            Effect object for logging
        """
        payload = {
            "status": "success",
            "message": message,
            "tellescope_enduser_id": tellescope_enduser_id,
            "canvas_patient_id": canvas_patient_id,
            "operation_type": operation_type,
            "timestamp": datetime.now().isoformat(),
            "protocol": "canvas_patient_to_tellescope_enduser",
            "event_type": "PATIENT_CREATED",
            "resource_id": canvas_patient_id,
            "target_system": "tellescope",
            "source_system": "canvas"
        }
        
        return Effect(type=EffectType.LOG, payload=json.dumps(payload))

    def _create_error_effect(self, error_message: str, error_category: str = "unknown") -> Effect:
        """
        Create an error effect for logging
        
        Args:
            error_message: Error description
            error_category: Category of error for better tracking
            
        Returns:
            Effect object for error logging
        """
        payload = {
            "status": "error",
            "message": error_message,
            "error_category": error_category,
            "timestamp": datetime.now().isoformat(),
            "protocol": "canvas_patient_to_tellescope_enduser",
            "event_type": "PATIENT_CREATED",
            "target_system": "tellescope",
            "source_system": "canvas",
            "retry_recommended": error_category in ["connection_error", "unexpected_error"]
        }
        
        return Effect(type=EffectType.LOG, payload=json.dumps(payload))