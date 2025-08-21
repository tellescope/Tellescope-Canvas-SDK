"""
Canvas Enduser Lookup Utility

Utility functions for finding Tellescope endusers that originated from Canvas patients.
Provides flexible lookup methods using different matching criteria.
"""

import json
from typing import Optional, Dict, Any, List
from logger import log

from tellescope.utilities.tellescope_api import TellescopeAPI


class CanvasEnduserLookup:
    """
    Utility class for finding Tellescope endusers that originated from Canvas patients
    
    Search criteria:
    1. Primary: source="Canvas" AND externalId=patient_id
    2. Secondary: references field contains { "type": "Canvas", "id": patient_id }
    """

    def __init__(self, tellescope_api: Optional[TellescopeAPI] = None):
        """
        Initialize the lookup utility
        
        Args:
            tellescope_api: Optional TellescopeAPI instance, creates new one if not provided
        """
        self.tellescope_api = tellescope_api or TellescopeAPI()

    def find_enduser_for_canvas_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Find Tellescope enduser that originated from Canvas for the given patient_id
        
        Args:
            patient_id: Canvas patient identifier
            
        Returns:
            Enduser record if found, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            # Search using MongoDB $or operator to check both conditions
            mongodb_filter = {
                "$or": [
                    # Primary match: source="Canvas" AND externalId=patient_id
                    {
                        "$and": [
                            {"source": "Canvas"},
                            {"externalId": str(patient_id)}
                        ]
                    },
                    # Secondary match: references contains Canvas reference
                    {
                        "references": {
                            "$elemMatch": {
                                "type": "Canvas",
                                "id": str(patient_id)
                            }
                        }
                    }
                ]
            }
            
            log.debug(f"Searching for enduser with filter: {json.dumps(mongodb_filter)}")
            
            # Use find_by to get the first matching enduser
            enduser = self.tellescope_api.find_by("endusers", mongodb_filter)
            
            if enduser:
                # Log which condition matched for debugging
                if (enduser.get("source") == "Canvas" and 
                    enduser.get("externalId") == str(patient_id)):
                    log.debug(f"Enduser {enduser['id']} matched via source+externalId")
                else:
                    log.debug(f"Enduser {enduser['id']} matched via references field")
            
            return enduser
            
        except Exception as e:
            log.error(f"Error searching for Canvas enduser: {str(e)}")
            raise

    def find_enduser_by_external_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Find enduser using only the primary match (source + externalId)
        
        Args:
            patient_id: Canvas patient identifier
            
        Returns:
            Enduser record if found, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            mongodb_filter = {
                "$and": [
                    {"source": "Canvas"},
                    {"externalId": str(patient_id)}
                ]
            }
            
            return self.tellescope_api.find_by("endusers", mongodb_filter)
            
        except Exception as e:
            log.error(f"Error searching for Canvas enduser by external ID: {str(e)}")
            raise

    def find_enduser_by_reference(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Find enduser using only the secondary match (references field)
        
        Args:
            patient_id: Canvas patient identifier
            
        Returns:
            Enduser record if found, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            mongodb_filter = {
                "references": {
                    "$elemMatch": {
                        "type": "Canvas",
                        "id": str(patient_id)
                    }
                }
            }
            
            return self.tellescope_api.find_by("endusers", mongodb_filter)
            
        except Exception as e:
            log.error(f"Error searching for Canvas enduser by reference: {str(e)}")
            raise

    def get_all_endusers_for_canvas_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all endusers that match the Canvas patient (in case of duplicates)
        
        Args:
            patient_id: Canvas patient identifier
            
        Returns:
            List of enduser records
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            mongodb_filter = {
                "$or": [
                    {
                        "$and": [
                            {"source": "Canvas"},
                            {"externalId": str(patient_id)}
                        ]
                    },
                    {
                        "references": {
                            "$elemMatch": {
                                "type": "Canvas",
                                "id": str(patient_id)
                            }
                        }
                    }
                ]
            }
            
            return self.tellescope_api.list("endusers", mongodb_filter=mongodb_filter)
            
        except Exception as e:
            log.error(f"Error searching for all Canvas endusers: {str(e)}")
            raise

    def enduser_exists_for_canvas_patient(self, patient_id: str) -> bool:
        """
        Check if any enduser exists for the given Canvas patient ID
        
        Args:
            patient_id: Canvas patient identifier
            
        Returns:
            True if at least one enduser exists, False otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        enduser = self.find_enduser_for_canvas_patient(patient_id)
        return enduser is not None


# Convenience functions for direct usage without instantiating the class
def find_tellescope_enduser_for_canvas_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find Tellescope enduser for Canvas patient
    
    Args:
        patient_id: Canvas patient identifier
        
    Returns:
        Enduser record if found, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasEnduserLookup()
    return lookup.find_enduser_for_canvas_patient(patient_id)


def find_tellescope_enduser_by_external_id(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find enduser by Canvas external ID only
    
    Args:
        patient_id: Canvas patient identifier
        
    Returns:
        Enduser record if found, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasEnduserLookup()
    return lookup.find_enduser_by_external_id(patient_id)


def find_tellescope_enduser_by_reference(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find enduser by Canvas reference only
    
    Args:
        patient_id: Canvas patient identifier
        
    Returns:
        Enduser record if found, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasEnduserLookup()
    return lookup.find_enduser_by_reference(patient_id)


def get_all_tellescope_endusers_for_canvas_patient(patient_id: str) -> List[Dict[str, Any]]:
    """
    Convenience function to get all endusers for Canvas patient
    
    Args:
        patient_id: Canvas patient identifier
        
    Returns:
        List of enduser records
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasEnduserLookup()
    return lookup.get_all_endusers_for_canvas_patient(patient_id)


def canvas_patient_has_tellescope_enduser(patient_id: str) -> bool:
    """
    Convenience function to check if Canvas patient has any Tellescope enduser
    
    Args:
        patient_id: Canvas patient identifier
        
    Returns:
        True if at least one enduser exists, False otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasEnduserLookup()
    return lookup.enduser_exists_for_canvas_patient(patient_id)