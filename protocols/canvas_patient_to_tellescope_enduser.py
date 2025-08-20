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

from utilities.tellescope_api import TellescopeAPI


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
        self.tellescope_api = TellescopeAPI()

    def compute(self) -> list[Effect]:
        """
        Handle patient creation event by creating corresponding Tellescope enduser
        """
        try:
            # Get the patient instance from the event
            patient = self.event.target.instance
            
            if not patient:
                log.error("No patient instance found in event")
                return [self._create_error_effect("Patient instance not available")]

            log.info(f"Processing patient creation for Canvas patient ID: {patient.id}")

            # Check if enduser already exists in Tellescope (avoid duplicates)
            existing_enduser = self._find_existing_enduser(patient.id)
            if existing_enduser:
                log.info(f"Enduser already exists in Tellescope with ID: {existing_enduser['id']}")
                return [self._create_success_effect(
                    f"Enduser already exists in Tellescope",
                    existing_enduser['id'],
                    patient.id
                )]

            # Map Canvas patient data to Tellescope enduser format
            enduser_data = self._map_patient_to_enduser(patient)
            
            # Create enduser in Tellescope
            created_enduser = self.tellescope_api.create("enduser", enduser_data)
            
            log.info(f"Successfully created Tellescope enduser: {created_enduser['id']} for Canvas patient: {patient.id}")
            
            return [self._create_success_effect(
                "Successfully created Tellescope enduser",
                created_enduser['id'],
                patient.id
            )]

        except Exception as e:
            log.error(f"Error creating Tellescope enduser for patient {getattr(patient, 'id', 'unknown')}: {str(e)}")
            return [self._create_error_effect(f"Failed to create Tellescope enduser: {str(e)}")]

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
            return self.tellescope_api.find_by("endusers", mongodb_filter)
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
            "gender": gender_mapping.get(getattr(patient, 'sex', None), 'Unknown'),
            
            # Metadata
            "tags": ["canvas-patient", "auto-synced"],
            "fields": {
                "canvas_patient_id": str(patient.id),
                "sync_timestamp": datetime.now().isoformat(),
                "sync_source": "canvas_patient_creation_protocol"
            }
        }

        # Add additional Canvas-specific fields if available
        if hasattr(patient, 'address'):
            enduser_data["fields"]["canvas_address"] = str(patient.address)
        
        if hasattr(patient, 'date_created'):
            enduser_data["fields"]["canvas_created_date"] = str(patient.date_created)

        # Remove empty string values and None values
        enduser_data = {k: v for k, v in enduser_data.items() if v != '' and v is not None}
        
        return enduser_data

    def _create_success_effect(self, message: str, tellescope_enduser_id: str, canvas_patient_id: str) -> Effect:
        """
        Create a success effect for logging
        
        Args:
            message: Success message
            tellescope_enduser_id: Created Tellescope enduser ID
            canvas_patient_id: Canvas patient ID
            
        Returns:
            Effect object for logging
        """
        payload = {
            "status": "success",
            "message": message,
            "tellescope_enduser_id": tellescope_enduser_id,
            "canvas_patient_id": canvas_patient_id,
            "timestamp": datetime.now().isoformat(),
            "protocol": "canvas_patient_to_tellescope_enduser"
        }
        
        return Effect(type=EffectType.LOG, payload=json.dumps(payload))

    def _create_error_effect(self, error_message: str) -> Effect:
        """
        Create an error effect for logging
        
        Args:
            error_message: Error description
            
        Returns:
            Effect object for error logging
        """
        payload = {
            "status": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "protocol": "canvas_patient_to_tellescope_enduser"
        }
        
        return Effect(type=EffectType.LOG, payload=json.dumps(payload))