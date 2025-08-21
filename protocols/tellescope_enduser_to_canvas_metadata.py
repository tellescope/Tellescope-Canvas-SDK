# Description:
# This protocol handles PATIENT_UPDATED events, looks up the corresponding Tellescope Enduser,
# and syncs the enduser's custom fields to Canvas PatientMetadata with 5-minute rate limiting.

import json
from datetime import datetime
from typing import Optional, Dict, Any

from canvas_sdk.effects import Effect, EffectType
from canvas_sdk.events import EventType
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.caching.plugins import get_cache
from logger import log

from tellescope.utilities.tellescope_api import TellescopeAPI
from tellescope.utilities.canvas_enduser_lookup import CanvasEnduserLookup


class Protocol(BaseProtocol):
    """
    Tellescope Enduser Custom Fields to Canvas PatientMetadata Sync Protocol
    
    Handles PATIENT_UPDATED events by:
    1. Looking up the corresponding Tellescope enduser
    2. Extracting custom fields from the enduser's fields JSON
    3. Syncing them to Canvas PatientMetadata
    4. Implementing 5-minute rate limiting per patient to avoid excessive updates
    """

    # Respond to patient update events in Canvas
    RESPONDS_TO = EventType.Name(EventType.PATIENT_UPDATED)

    # Rate limiting: cache patient updates for 5 minutes
    RATE_LIMIT_SECONDS = 300  # 5 minutes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize Tellescope API only if secrets are available
        if self.secrets.get("TELLESCOPE_API_KEY"):
            self.tellescope_api = TellescopeAPI(
                self.secrets.get("TELLESCOPE_API_KEY"), 
                self.secrets.get("TELLESCOPE_API_URL")
            )
            self.enduser_lookup = CanvasEnduserLookup(self.tellescope_api)
        else:
            self.tellescope_api = None
            self.enduser_lookup = None
            
        # Initialize Canvas cache
        self.cache = get_cache()

    def compute(self) -> list[Effect]:
        """
        Handle patient update event by syncing Tellescope enduser custom fields to Canvas PatientMetadata
        """
        # Return early if secrets are not available
        if not self.tellescope_api or not self.enduser_lookup:
            log.warning("Tellescope API credentials not configured, skipping metadata sync")
            return []
            
        patient_id = None
        try:
            # Get the patient instance from the event
            patient = self.event.target.instance
            
            if not patient:
                log.error("No patient instance found in PATIENT_UPDATED event")
                return [self._create_error_effect("Patient instance not available", "missing_patient_instance")]

            patient_id = patient.id
            log.debug(f"Processing PATIENT_UPDATED event for Canvas patient ID: {patient_id}")

            # Check rate limiting using Canvas cache - skip if updated within last 5 minutes
            cache_key = f"patient_metadata_sync:{patient_id}"
            if cache_key in self.cache:
                log.debug(f"Rate limited: Patient {patient_id} updated within last 5 minutes, skipping")
                return [self._create_success_effect(
                    "Skipped due to rate limiting (5 min)",
                    None,
                    patient_id,
                    "rate_limited"
                )]

            # Look up corresponding Tellescope enduser
            enduser = self.enduser_lookup.find_enduser_for_canvas_patient(patient_id)
            
            if not enduser:
                log.debug(f"No corresponding Tellescope enduser found for Canvas patient {patient_id}")
                # Update cache even for not found to avoid repeated lookups
                self.cache.set(cache_key, "no_enduser", self.RATE_LIMIT_SECONDS)
                return [self._create_success_effect(
                    "No corresponding Tellescope enduser found",
                    None,
                    patient_id,
                    "enduser_not_found"
                )]

            log.info(f"Found Tellescope enduser {enduser['id']} for Canvas patient {patient_id}")

            # Extract custom fields from enduser
            custom_fields = self._extract_custom_fields(enduser)
            
            if not custom_fields:
                log.debug(f"No custom fields found for enduser {enduser['id']}")
                self.cache.set(cache_key, "no_fields", self.RATE_LIMIT_SECONDS)
                return [self._create_success_effect(
                    "No custom fields to sync",
                    enduser['id'],
                    patient_id,
                    "no_custom_fields"
                )]

            # Sync custom fields to Canvas PatientMetadata
            metadata_effects = self._sync_custom_fields_to_metadata(patient_id, custom_fields)
            
            # Update rate limit cache with successful sync
            sync_data = {
                "enduser_id": enduser['id'],
                "fields_count": len(custom_fields),
                "timestamp": datetime.now().isoformat()
            }
            self.cache.set(cache_key, sync_data, self.RATE_LIMIT_SECONDS)
            
            log.info(f"Successfully synced {len(custom_fields)} custom fields from Tellescope enduser {enduser['id']} to Canvas patient {patient_id}")
            
            # Return metadata effects plus success log
            effects = metadata_effects + [self._create_success_effect(
                f"Successfully synced {len(custom_fields)} custom fields",
                enduser['id'],
                patient_id,
                "metadata_sync"
            )]
            
            return effects

        except Exception as e:
            log.error(f"Error syncing Tellescope enduser custom fields for patient {patient_id}: {str(e)}")
            return [self._create_error_effect(f"Sync failed: {str(e)}", "sync_error")]


    def _extract_custom_fields(self, enduser: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract custom fields from Tellescope enduser's fields JSON
        
        Args:
            enduser: Tellescope enduser record
            
        Returns:
            Dictionary of custom fields, empty dict if none found
        """
        try:
            fields = enduser.get("fields", {})
            
            if not fields:
                return {}
                
            # If fields is a string, parse it as JSON
            if isinstance(fields, str):
                try:
                    fields = json.loads(fields)
                except json.JSONDecodeError:
                    log.warning(f"Invalid JSON in enduser fields for enduser {enduser.get('id')}")
                    return {}
            
            # Return fields if it's a dict, otherwise empty dict
            return fields if isinstance(fields, dict) else {}
            
        except Exception as e:
            log.error(f"Error extracting custom fields from enduser {enduser.get('id')}: {str(e)}")
            return {}

    def _sync_custom_fields_to_metadata(self, patient_id: str, custom_fields: Dict[str, Any]) -> list[Effect]:
        """
        Sync custom fields to Canvas PatientMetadata effects
        
        Args:
            patient_id: Canvas patient identifier
            custom_fields: Dictionary of custom fields to sync
            
        Returns:
            List of PatientMetadata effects
        """
        effects = []
        
        for field_name, field_value in custom_fields.items():
            try:
                # Convert field value to string for PatientMetadata
                if field_value is None:
                    continue  # Skip null values
                elif isinstance(field_value, str):
                    value_str = field_value  # Already a string
                elif isinstance(field_value, bool):
                    # Convert booleans to lowercase strings
                    value_str = "true" if field_value else "false"
                elif isinstance(field_value, (dict, list)):
                    # Serialize objects and arrays as JSON
                    value_str = json.dumps(field_value, ensure_ascii=False, separators=(',', ':'))
                else:
                    # For numbers and other types - convert to string
                    value_str = str(field_value)
                
                # Create PatientMetadata effect
                metadata_payload = {
                    "patient_id": patient_id,
                    "namespace": "tellescope_custom_fields",
                    "key": field_name,
                    "value": value_str
                }
                
                effect = Effect(
                    type=EffectType.UPSERT_PATIENT_METADATA,
                    payload=json.dumps(metadata_payload)
                )
                effects.append(effect)
                
                log.debug(f"Created PatientMetadata effect for field '{field_name}' = '{value_str}'")
                
            except Exception as e:
                log.error(f"Error creating PatientMetadata effect for field '{field_name}': {str(e)}")
                continue
                
        return effects

    def _create_success_effect(self, message: str, tellescope_enduser_id: Optional[str], 
                             canvas_patient_id: str, operation_type: str = "unknown") -> Effect:
        """
        Create a success effect for logging
        
        Args:
            message: Success message
            tellescope_enduser_id: Tellescope enduser ID (if found)
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
            "protocol": "tellescope_enduser_to_canvas_metadata",
            "event_type": "PATIENT_UPDATED",
            "resource_id": canvas_patient_id,
            "target_system": "canvas",
            "source_system": "tellescope"
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
            "protocol": "tellescope_enduser_to_canvas_metadata",
            "event_type": "PATIENT_UPDATED",
            "target_system": "canvas",
            "source_system": "tellescope",
            "retry_recommended": error_category in ["sync_error"]
        }
        
        return Effect(type=EffectType.LOG, payload=json.dumps(payload))