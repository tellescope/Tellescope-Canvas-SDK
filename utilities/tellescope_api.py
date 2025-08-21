"""
Tellescope API CRUD Utility

A universal utility for Create, Read, Update, Delete operations on all Tellescope model types.
Follows the API conventions where:
- CREATE: POST /{resource} (singular)
- READ single: GET /{resource}/{id} (singular) 
- READ list: GET /{resources} (plural)
- UPDATE: PATCH /{resource}/{id} (singular)
- DELETE: DELETE /{resource}/{id} (singular)
"""

import requests
import json
from typing import Optional
from typing import Dict, Any, Optional, List, Union


class TellescopeAPI:
    """Universal CRUD utility for all Tellescope model types"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize Tellescope API utility
        
        Args:
            api_key: Tellescope API key (must be provided)
            api_url: Tellescope API URL (defaults to https://api.tellescope.com/v1)
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.tellescope.com/v1"
        if not self.api_key:
            raise ValueError("API key is required. Pass api_key parameter explicitly.")
        self.headers = {
            "Authorization": f"API_KEY {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_singular_resource_name(self, resource_type: str) -> str:
        """Convert plural resource name to singular for API endpoints"""
        # Handle special cases and common plural forms
        special_cases = {
            "sms-messages": "sms-message",
            "chat-rooms": "chat-room", 
            "calendar-events": "calendar-event",
            "calendar-event-templates": "calendar-event-template",
            "automation-steps": "automation-step",
            "automated-actions": "automated-action",
            "automation-triggers": "automation-trigger",
            "form-fields": "form-field",
            "form-responses": "form-response",
            "phone-calls": "phone-call",
            "enduser-medications": "enduser-medication",
            "enduser-observations": "enduser-observation",
            "managed-content-records": "managed-content-record"
        }
        
        if resource_type in special_cases:
            return special_cases[resource_type]
        
        # Default: remove 's' from end if present
        return resource_type.rstrip('s') if resource_type.endswith('s') else resource_type
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid request data: {e.response.text}")
            elif e.response.status_code == 401:
                raise PermissionError("Invalid API key or insufficient permissions")
            elif e.response.status_code == 404:
                raise ValueError("Resource not found")
            elif e.response.status_code == 429:
                raise ConnectionError("Rate limit exceeded - retry after delay")
            else:
                raise Exception(f"Tellescope API error: {e.response.status_code} {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Network error connecting to Tellescope: {str(e)}")
    
    def create(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record
        
        Args:
            resource_type: Type of resource (e.g., "enduser", "email", "ticket")
            data: Record data as dictionary
            
        Returns:
            Created record with ID and timestamps
        """
        singular_resource = self._get_singular_resource_name(resource_type)
        url = f"{self.api_url}/{singular_resource}"
        
        response = self._make_request("POST", url, json=data)
        return response.json()
    
    def read(self, resource_type: str, record_id: str) -> Dict[str, Any]:
        """
        Read a single record by ID
        
        Args:
            resource_type: Type of resource (e.g., "enduser", "email", "ticket")  
            record_id: ID of the record to retrieve
            
        Returns:
            Record data as dictionary
        """
        singular_resource = self._get_singular_resource_name(resource_type)
        url = f"{self.api_url}/{singular_resource}/{record_id}"
        
        response = self._make_request("GET", url)
        return response.json()
    
    def update(self, resource_type: str, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing record
        
        Args:
            resource_type: Type of resource (e.g., "enduser", "email", "ticket")
            record_id: ID of the record to update
            updates: Partial data to update
            
        Returns:
            Updated record data
        """
        singular_resource = self._get_singular_resource_name(resource_type)
        url = f"{self.api_url}/{singular_resource}/{record_id}"
        
        response = self._make_request("PATCH", url, json=updates)
        return response.json()
    
    def delete(self, resource_type: str, record_id: str) -> bool:
        """
        Delete a record
        
        Args:
            resource_type: Type of resource (e.g., "enduser", "email", "ticket")
            record_id: ID of the record to delete
            
        Returns:
            True if deletion successful
        """
        singular_resource = self._get_singular_resource_name(resource_type)
        url = f"{self.api_url}/{singular_resource}/{record_id}"
        
        response = self._make_request("DELETE", url)
        return response.status_code == 200
    
    def list(self, resource_type: str, filters: Optional[Dict[str, Any]] = None, 
             mongodb_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List records with optional filtering
        
        Args:
            resource_type: Type of resource (e.g., "endusers", "emails", "tickets") - use plural
            filters: Traditional filter parameters
            mongodb_filter: MongoDB query for flexible filtering (recommended)
            
        Returns:
            List of records
        """
        # Use resource_type as-is for list operations (should be plural)
        url = f"{self.api_url}/{resource_type}"
        
        params = filters or {}
        if mongodb_filter:
            params["mdbFilter"] = json.dumps(mongodb_filter)
        
        response = self._make_request("GET", url, params=params)
        result = response.json()
        
        # Handle both list and paginated response formats
        return result if isinstance(result, list) else result.get("data", [])
    
    def find_by(self, resource_type: str, mongodb_filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single record using MongoDB filtering
        
        Args:
            resource_type: Type of resource (e.g., "endusers", "emails") - use plural
            mongodb_filter: MongoDB query to find the record
            
        Returns:
            First matching record or None if not found
        """
        results = self.list(resource_type, mongodb_filter=mongodb_filter)
        return results[0] if results else None