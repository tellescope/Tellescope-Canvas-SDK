"""
Canvas User Lookup Utility

Utility functions for finding Tellescope Users that correspond to Canvas Staff/Practitioners.
Provides flexible lookup methods using different matching criteria.
"""

import json
from typing import Optional, Dict, Any, List

from tellescope.utilities.tellescope_api import TellescopeAPI


class CanvasUserLookup:
    """
    Utility class for finding Tellescope Users that correspond to Canvas Staff/Practitioners
    
    Search criteria (in order of preference):
    1. Primary: externalId matches Canvas Staff ID (canvasId)
    2. Fallback: fname and lname match Canvas Staff first_name and last_name
    3. Optional: return any non-matching User when a valid User is needed
    """

    def __init__(self, tellescope_api: Optional[TellescopeAPI] = None):
        """
        Initialize the lookup utility
        
        Args:
            tellescope_api: Optional TellescopeAPI instance, creates new one if not provided
        """
        self.tellescope_api = tellescope_api or TellescopeAPI()

    def find_user_for_canvas_practitioner(self, canvas_staff_id: str, first_name: Optional[str] = None, 
                                        last_name: Optional[str] = None, 
                                        return_any_if_no_match: bool = False) -> Optional[Dict[str, Any]]:
        """
        Find Tellescope User that corresponds to Canvas Staff/Practitioner
        
        Args:
            canvas_staff_id: Canvas Staff identifier (UUID or ID)
            first_name: Canvas Staff first_name (for fallback matching)
            last_name: Canvas Staff last_name (for fallback matching)
            return_any_if_no_match: If True, return any User when no match is found
            
        Returns:
            User record if found, None otherwise (or any User if return_any_if_no_match=True)
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            # 1. Primary lookup by canvasId (canvasId)
            user = self.find_user_by_canvas_id(canvas_staff_id)
            if user:
                return user
            
            # 2. Fallback lookup by name if provided
            if first_name and last_name:
                user = self.find_user_by_name(first_name, last_name)
                if user:
                    return user
            
            # 3. Optional: return any User if requested
            if return_any_if_no_match:
                user = self.get_any_user()
                if user:
                    return user
            
            return None
            
        except Exception as e:
            raise Exception(f"Error searching for Canvas User: {str(e)}")

    def find_user_by_canvas_id(self, canvas_staff_id: str) -> Optional[Dict[str, Any]]:
        """
        Find User using Canvas Staff ID stored in canvasId field
        
        Args:
            canvas_staff_id: Canvas Staff identifier
            
        Returns:
            User record if found, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            mongodb_filter = {"canvasId": str(canvas_staff_id)}
            return self.tellescope_api.find_by("users", mongodb_filter)
            
        except Exception as e:
            raise Exception(f"Error searching for Canvas User by ID: {str(e)}")

    def find_user_by_name(self, first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
        """
        Find User using first and last name match
        
        Args:
            first_name: First name to match
            last_name: Last name to match
            
        Returns:
            User record if found, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            mongodb_filter = {
                "$and": [
                    {"fname": first_name.strip()},
                    {"lname": last_name.strip()}
                ]
            }
            
            return self.tellescope_api.find_by("users", mongodb_filter)
            
        except Exception as e:
            raise Exception(f"Error searching for Canvas User by name: {str(e)}")

    def get_any_user(self) -> Optional[Dict[str, Any]]:
        """
        Get any available User (fallback when specific match is not found but a valid User is needed)
        
        Returns:
            Any User record if available, None otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            users = self.tellescope_api.list("users", mongodb_filter={}, limit=1)
            return users[0] if users else None
            
        except Exception as e:
            raise Exception(f"Error getting any User: {str(e)}")

    def get_all_users_for_canvas_practitioner(self, canvas_staff_id: str, first_name: Optional[str] = None, 
                                            last_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all Users that match the Canvas Staff (in case of duplicates)
        
        Args:
            canvas_staff_id: Canvas Staff identifier
            first_name: Canvas Staff first_name (optional)
            last_name: Canvas Staff last_name (optional)
            
        Returns:
            List of User records
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        try:
            conditions = []
            
            # Add Canvas ID condition
            conditions.append({"externalId": str(canvas_staff_id)})
            
            # Add name condition if both names provided
            if first_name and last_name:
                conditions.append({
                    "$and": [
                        {"fname": first_name.strip()},
                        {"lname": last_name.strip()}
                    ]
                })
            
            mongodb_filter = {"$or": conditions} if len(conditions) > 1 else conditions[0]
            
            return self.tellescope_api.list("users", mongodb_filter=mongodb_filter)
            
        except Exception as e:
            raise Exception(f"Error searching for all Canvas Users: {str(e)}")

    def user_exists_for_canvas_practitioner(self, canvas_staff_id: str, first_name: Optional[str] = None, 
                                          last_name: Optional[str] = None) -> bool:
        """
        Check if any User exists for the given Canvas Staff
        
        Args:
            canvas_staff_id: Canvas Staff identifier
            first_name: Canvas Staff first_name (optional)
            last_name: Canvas Staff last_name (optional)
            
        Returns:
            True if at least one User exists, False otherwise
            
        Raises:
            Exception: If there's an error communicating with the Tellescope API
        """
        user = self.find_user_for_canvas_practitioner(canvas_staff_id, first_name, last_name)
        return user is not None


# Convenience functions for direct usage without instantiating the class
def find_tellescope_user_for_canvas_practitioner(canvas_staff_id: str, first_name: Optional[str] = None, 
                                                last_name: Optional[str] = None, 
                                                return_any_if_no_match: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find Tellescope User for Canvas Staff/Practitioner
    
    Args:
        canvas_staff_id: Canvas Staff identifier
        first_name: Canvas Staff first_name (for fallback matching)
        last_name: Canvas Staff last_name (for fallback matching)
        return_any_if_no_match: If True, return any User when no match is found
        
    Returns:
        User record if found, None otherwise (or any User if return_any_if_no_match=True)
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.find_user_for_canvas_practitioner(canvas_staff_id, first_name, last_name, return_any_if_no_match)


def find_tellescope_user_by_canvas_id(canvas_staff_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find User by Canvas Staff ID only
    
    Args:
        canvas_staff_id: Canvas Staff identifier
        
    Returns:
        User record if found, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.find_user_by_canvas_id(canvas_staff_id)


def find_tellescope_user_by_name(first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find User by name only
    
    Args:
        first_name: First name to match
        last_name: Last name to match
        
    Returns:
        User record if found, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.find_user_by_name(first_name, last_name)


def get_any_tellescope_user() -> Optional[Dict[str, Any]]:
    """
    Convenience function to get any available User
    
    Returns:
        Any User record if available, None otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.get_any_user()


def get_all_tellescope_users_for_canvas_practitioner(canvas_staff_id: str, first_name: Optional[str] = None, 
                                                   last_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to get all Users for Canvas Staff
    
    Args:
        canvas_staff_id: Canvas Staff identifier
        first_name: Canvas Staff first_name (optional)
        last_name: Canvas Staff last_name (optional)
        
    Returns:
        List of User records
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.get_all_users_for_canvas_practitioner(canvas_staff_id, first_name, last_name)


def canvas_practitioner_has_tellescope_user(canvas_staff_id: str, first_name: Optional[str] = None, 
                                          last_name: Optional[str] = None) -> bool:
    """
    Convenience function to check if Canvas Staff has any Tellescope User
    
    Args:
        canvas_staff_id: Canvas Staff identifier
        first_name: Canvas Staff first_name (optional)
        last_name: Canvas Staff last_name (optional)
        
    Returns:
        True if at least one User exists, False otherwise
        
    Raises:
        Exception: If there's an error communicating with the Tellescope API
    """
    lookup = CanvasUserLookup()
    return lookup.user_exists_for_canvas_practitioner(canvas_staff_id, first_name, last_name)