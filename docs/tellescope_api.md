# Tellescope API Documentation

## Overview

Tellescope is a HIPAA-compliant healthcare patient CRM platform offering comprehensive patient management, communication tools, and workflow automation through a RESTful API.

### Key Features
- Patient (enduser) relationship management
- Multi-channel communication (secure email, chat, SMS)
- Care coordination and progress tracking
- Analytics and reporting
- AI-powered conversation generation

### API Characteristics
- RESTful architecture with JSON data format
- Comprehensive CRUD operations for all resources
- Built-in pagination and filtering
- Webhook support for real-time notifications
- HIPAA-compliant security

## Quick Reference

### Essential Setup
```python
import requests
import os

# Load credentials
TELLESCOPE_API_KEY = os.getenv("TELLESCOPE_API_KEY")
TELLESCOPE_API_URL = os.getenv("TELLESCOPE_API_URL")  # Default: https://api.tellescope.com/v1

# Standard headers
headers = {
    "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
    "Content-Type": "application/json"
}
```

### Common Request Patterns
```python
# GET request with error handling
def get_tellescope_data(endpoint, params=None):
    try:
        response = requests.get(
            f"{TELLESCOPE_API_URL}/{endpoint}",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Tellescope API error: {str(e)}")

# POST request for creating resources
def create_tellescope_resource(endpoint, data):
    try:
        response = requests.post(
            f"{TELLESCOPE_API_URL}/{endpoint}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Tellescope API error: {str(e)}")
```

## Authentication

### API Key Authentication
```python
# Method 1: Authorization header (recommended)
headers = {
    "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
    "Content-Type": "application/json"
}

# Method 2: Query parameter
params = {"apiKey": TELLESCOPE_API_KEY}
```

### Environment Configuration
```python
# Load from environment variables
TELLESCOPE_API_KEY = os.getenv("TELLESCOPE_API_KEY")
TELLESCOPE_API_URL = os.getenv("TELLESCOPE_API_URL", "https://api.tellescope.com/v1")

# Validation
if not TELLESCOPE_API_KEY:
    raise EnvironmentError("TELLESCOPE_API_KEY environment variable required")

## Core CRUD Patterns

### Base URLs
- **Production**: `https://api.tellescope.com/v1`
- **Staging**: `https://staging-api.tellescope.com/v1`

### Standard CRUD Operations
```python
# CREATE - POST /{resource}
def create_resource(resource_type, data):
    return create_tellescope_resource(resource_type, data)

# READ - GET /{resource} or GET /{resource}/{id}
def get_resources(resource_type, filters=None):
    return get_tellescope_data(resource_type, params=filters)

def get_resource_by_id(resource_type, resource_id):
    return get_tellescope_data(f"{resource_type}/{resource_id}")

# UPDATE - PATCH /{resource}/{id}
def update_resource(resource_type, resource_id, updates):
    response = requests.patch(
        f"{TELLESCOPE_API_URL}/{resource_type}/{resource_id}",
        headers=headers,
        json=updates
    )
    response.raise_for_status()
    return response.json()

# DELETE - DELETE /{resource}/{id}
def delete_resource(resource_type, resource_id):
    response = requests.delete(
        f"{TELLESCOPE_API_URL}/{resource_type}/{resource_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.status_code == 200
```

### Pagination
```python
def get_paginated_resources(resource_type, limit=100):
    all_resources = []
    last_id = None
    
    while True:
        params = {"limit": limit}
        if last_id:
            params["lastId"] = last_id
            
        response = get_tellescope_data(resource_type, params)
        resources = response.get("data", [])
        
        if not resources:
            break
            
        all_resources.extend(resources)
        last_id = resources[-1].get("id")
        
        if len(resources) < limit:
            break
    
    return all_resources
```

### Filtering and Searching
```python
# Time-based filtering
def get_recent_resources(resource_type, days_back=7):
    from datetime import datetime, timedelta
    
    from_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    params = {"fromUpdated": from_date}
    
    return get_tellescope_data(resource_type, params)

# Custom filters
def get_filtered_resources(resource_type, filters):
    """
    Common filter parameters:
    - fromUpdated, from, to: Date filtering
    - limit: Page size (max 100)
    - lastId: Pagination cursor
    """
    return get_tellescope_data(resource_type, params=filters)
```

## Core Data Models

### Endusers (Patients)
The primary patient/client record in Tellescope.

**Key Fields:**
- `id`: Unique identifier
- `email`: Email address (required)
- `fname`: First name (required)
- `lname`: Last name (required)
- `phone`: Phone number
- `dateOfBirth`: Date of birth (YYYY-MM-DD format)
- `sex`: Gender ('M' or 'F')
- `externalId`: External system identifier (useful for Canvas integration)
- `tags`: Array of string tags for categorization
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### Users
Represents team members and staff accounts.

**Key Fields:**
- `id`: Unique identifier
- `email`: Email address
- `fname`: First name
- `lname`: Last name
- `role`: User role/permissions level
- `organizationId`: Associated organization

### Common Resource Patterns
Most Tellescope resources follow similar patterns:

**Standard Fields:**
- `id`: Unique identifier (string)
- `createdAt`: ISO timestamp of creation
- `updatedAt`: ISO timestamp of last update
- `organizationId`: Associated organization ID

**Relationship Fields:**
- `enduseruId`: References an enduser (patient)
- `userId`: References a user (staff member)

## Enduser (Patient) Management

### Basic Operations
```python
# Create a new patient (minimal required fields)
def create_enduser(email, fname, lname, **optional_fields):
    patient_data = {
        "email": email,
        "fname": fname,
        "lname": lname,
        **optional_fields
    }
    return create_resource("endusers", patient_data)

# Search patients by various criteria
def search_endusers(search_params):
    """
    Common search parameters:
    - email: Exact email match
    - phone: Phone number search
    - fname, lname: Name search
    - externalId: External system ID
    - tags: Filter by tags
    """
    return get_resources("endusers", search_params)

# Update patient information
def update_enduser(enduser_id, updates):
    return update_resource("endusers", enduser_id, updates)
```

### Canvas Integration Patterns
```python
def sync_canvas_patient_to_tellescope(canvas_patient):
    """
    Sync Canvas patient data to Tellescope enduser
    """
    # Map Canvas patient to Tellescope enduser format
    tellescope_data = {
        "email": canvas_patient.email or f"patient{canvas_patient.id}@canvas.medical",
        "fname": canvas_patient.first_name,
        "lname": canvas_patient.last_name,
        "phone": canvas_patient.phone_number,
        "dateOfBirth": canvas_patient.date_of_birth.strftime("%Y-%m-%d") if canvas_patient.date_of_birth else None,
        "sex": canvas_patient.sex,
        "externalId": str(canvas_patient.id),  # Store Canvas patient ID for lookup
        "tags": ["canvas-patient"]
    }
    
    # Check if enduser already exists by Canvas ID
    existing = search_endusers({"externalId": str(canvas_patient.id)})
    
    if existing.get("data"):
        # Update existing enduser
        enduser_id = existing["data"][0]["id"]
        return update_enduser(enduser_id, tellescope_data)
    else:
        # Create new enduser
        return create_enduser(**tellescope_data)

def find_tellescope_patient_by_canvas_id(canvas_patient_id):
    """
    Find Tellescope enduser by Canvas patient ID
    """
    result = search_endusers({"externalId": str(canvas_patient_id)})
    return result.get("data", [{}])[0] if result.get("data") else None
```

## Communication and Workflow

### Common Communication Resources
- **Messages**: Secure messaging between staff and patients
- **SMSMessages**: SMS communication records
- **Emails**: Email communication records
- **ChatRooms**: Group chat functionality
- **Calls**: Phone call records

### Basic Communication Patterns
```python
# Send a message to a patient
def send_message_to_enduser(enduser_id, message_text, user_id):
    message_data = {
        "enduserId": enduser_id,
        "userId": user_id,
        "message": message_text,
        "channel": "secure_message"  # or other channel types
    }
    return create_resource("messages", message_data)

# Get conversation history
def get_enduser_messages(enduser_id, limit=50):
    params = {
        "enduserId": enduser_id,
        "limit": limit
    }
    return get_resources("messages", params)

# Send SMS (if SMS integration is configured)
def send_sms_to_enduser(enduser_id, sms_text):
    sms_data = {
        "enduserId": enduser_id,
        "message": sms_text
    }
    return create_resource("sms-messages", sms_data)
```

### Workflow and Task Management
```python
# Common workflow resources
# - Tasks: Action items and to-dos
# - Appointments: Scheduled meetings/calls
# - Forms: Data collection forms
# - Automations: Workflow triggers

# Create a task for follow-up
def create_follow_up_task(enduser_id, title, description, assigned_user_id):
    task_data = {
        "enduserId": enduser_id,
        "userId": assigned_user_id,
        "title": title,
        "description": description,
        "status": "pending"
    }
    return create_resource("tasks", task_data)

# Get patient's tasks
def get_enduser_tasks(enduser_id):
    params = {"enduserId": enduser_id}
    return get_resources("tasks", params)
```

## Error Handling and Best Practices

### Common Error Patterns
```python
def safe_tellescope_request(func, *args, **kwargs):
    """
    Wrapper for safe Tellescope API requests with proper error handling
    """
    try:
        return func(*args, **kwargs)
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

# Usage with error handling
def get_enduser_safely(enduser_id):
    try:
        return safe_tellescope_request(get_enduser, enduser_id)
    except ValueError as e:
        if "not found" in str(e):
            return None  # Patient doesn't exist
        raise  # Re-raise other validation errors
    except PermissionError:
        raise Exception("Invalid Tellescope API credentials")
    except ConnectionError as e:
        if "Rate limit" in str(e):
            time.sleep(1)  # Simple retry after rate limit
            return safe_tellescope_request(get_enduser, enduser_id)
        raise
```

### Validation Helpers
```python
def validate_tellescope_credentials():
    """
    Validate that Tellescope API credentials are properly configured
    """
    if not TELLESCOPE_API_KEY:
        raise EnvironmentError("TELLESCOPE_API_KEY environment variable required")
    
    if not TELLESCOPE_API_URL:
        raise EnvironmentError("TELLESCOPE_API_URL environment variable required")
    
    # Test API connection
    try:
        response = requests.get(
            f"{TELLESCOPE_API_URL}/users",
            headers=headers,
            params={"limit": 1}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        raise ConnectionError("Unable to connect to Tellescope API - check credentials and URL")

def validate_enduser_data(enduser_data):
    """
    Validate enduser data before API calls
    """
    required_fields = ["email", "fname", "lname"]
    
    for field in required_fields:
        if not enduser_data.get(field):
            raise ValueError(f"Required field missing: {field}")
    
    # Email validation
    email = enduser_data.get("email")
    if "@" not in email or "." not in email:
        raise ValueError(f"Invalid email format: {email}")
    
    return True
```

### Best Practices for AI Assistants

1. **Always validate credentials first** - Call `validate_tellescope_credentials()` at the start of protocols
2. **Use externalId for integration** - Store Canvas patient IDs in Tellescope's `externalId` field
3. **Handle rate limits gracefully** - Implement retry logic with delays
4. **Validate data before API calls** - Check required fields and formats
5. **Use pagination for large datasets** - Don't attempt to fetch all records at once
6. **Implement proper error handling** - Return user-friendly Canvas effects for errors
7. **Test with staging environment** - Use staging API URL for development and testing

### Canvas Integration Checklist
```python
def canvas_tellescope_integration_checklist():
    """
    Pre-flight checklist for Canvas-Tellescope integration
    """
    checks = {
        "credentials": False,
        "patient_mapping": False,
        "error_handling": False
    }
    
    try:
        # 1. Verify Tellescope credentials
        validate_tellescope_credentials()
        checks["credentials"] = True
        
        # 2. Test patient mapping
        test_canvas_patient = type('Patient', (), {
            'id': 'test123',
            'first_name': 'Test',
            'last_name': 'Patient',
            'email': 'test@example.com'
        })()
        
        mapped_data = {
            "email": test_canvas_patient.email,
            "fname": test_canvas_patient.first_name,
            "lname": test_canvas_patient.last_name,
            "externalId": str(test_canvas_patient.id)
        }
        validate_enduser_data(mapped_data)
        checks["patient_mapping"] = True
        
        # 3. Test error handling
        try:
            get_enduser_safely("nonexistent_id")
        except:
            pass  # Expected to fail
        checks["error_handling"] = True
        
        return checks
        
    except Exception as e:
        return {"error": str(e), **checks}
```