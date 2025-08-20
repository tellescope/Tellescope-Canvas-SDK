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
import time
from datetime import datetime, timedelta

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

### Common Endpoints
*Note: GET requests for lists use plural endpoints (e.g., `/endusers`). POST, PATCH, DELETE, and single GET requests use singular endpoints (e.g., `/enduser`, `/enduser/{id}`).*

| Resource | List Endpoint (GET) | Single/Modify Endpoints | Description |
|----------|---------------------|-------------------------|-------------|
| Endusers | `/endusers` | `/enduser`, `/enduser/{id}` | Patient/client records |
| Users | `/users` | `/user`, `/user/{id}` | Staff/team member accounts |
| Emails | `/emails` | `/email`, `/email/{id}` | Email communication records |
| SMS Messages | `/sms-messages` | `/sms-message`, `/sms-message/{id}` | SMS communication records |
| Chat Rooms | `/chat-rooms` | `/chat-room`, `/chat-room/{id}` | Group chat functionality |
| Chat Messages | `/chats` | `/chat`, `/chat/{id}` | Individual chat messages |
| Message Templates | `/templates` | `/template`, `/template/{id}` | Email/SMS template library |
| Files | `/files` | `/file`, `/file/{id}` | File attachments and documents |
| Tickets | `/tickets` | `/ticket`, `/ticket/{id}` | Task/issue tracking |
| Notes | `/notes` | `/note`, `/note/{id}` | Patient notes and annotations |
| Forms | `/forms` | `/form`, `/form/{id}` | Data collection forms |
| Form Fields | `/form-fields` | `/form-field`, `/form-field/{id}` | Individual form field definitions |
| Form Responses | `/form-responses` | `/form-response`, `/form-response/{id}` | Submitted form data |
| Calendar Events | `/calendar-events` | `/calendar-event`, `/calendar-event/{id}` | Appointments and meetings |

### Standard CRUD Operations
```python
# CREATE - POST /{resource} (singular)
def create_resource(resource_type, data):
    try:
        response = requests.post(
            f"{TELLESCOPE_API_URL}/{resource_type}",
            headers={
                "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Tellescope API error: {str(e)}")

# READ - GET /{resources} (plural) for lists or GET /{resource}/{id} (singular) for single
def get_resources(resource_type, filters=None):
    try:
        response = requests.get(
            f"{TELLESCOPE_API_URL}/{resource_type}",
            headers={
                "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
                "Content-Type": "application/json"
            },
            params=filters
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Tellescope API error: {str(e)}")

def get_resource_by_id(resource_type, resource_id):
    try:
        # Use singular form for single resource retrieval
        singular_resource = resource_type.rstrip('s') if resource_type.endswith('s') else resource_type
        response = requests.get(
            f"{TELLESCOPE_API_URL}/{singular_resource}/{resource_id}",
            headers={
                "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Tellescope API error: {str(e)}")

# UPDATE - PATCH /{resource}/{id} (singular)
def update_resource(resource_type, resource_id, updates):
    # Use singular form for updates
    singular_resource = resource_type.rstrip('s') if resource_type.endswith('s') else resource_type
    response = requests.patch(
        f"{TELLESCOPE_API_URL}/{singular_resource}/{resource_id}",
        headers={
            "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
            "Content-Type": "application/json"
        },
        json=updates
    )
    response.raise_for_status()
    return response.json()

# DELETE - DELETE /{resource}/{id} (singular)
def delete_resource(resource_type, resource_id):
    # Use singular form for deletion
    singular_resource = resource_type.rstrip('s') if resource_type.endswith('s') else resource_type
    response = requests.delete(
        f"{TELLESCOPE_API_URL}/{singular_resource}/{resource_id}",
        headers={
            "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
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
            
        response = get_resources(resource_type, params)
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

#### mdbFilter - MongoDB Query Filtering (Most Flexible)
**IMPORTANT**: Both singular and plural GET endpoints accept an `mdbFilter` parameter that accepts JSON-encoded MongoDB query syntax. This is the **most flexible way** to filter data and should be the preferred method for complex queries.

```python
import json

# MongoDB-style filtering with mdbFilter (RECOMMENDED)
def get_resources_with_mongodb_filter(resource_type, mongodb_query):
    """
    Use MongoDB query syntax for maximum flexibility
    
    MongoDB query examples:
    - {"email": "john@example.com"} - Exact email match
    - {"age": {"$gte": 18, "$lt": 65}} - Age between 18 and 64
    - {"tags": {"$in": ["vip", "priority"]}} - Has any of these tags
    - {"$and": [{"status": "active"}, {"lastLogin": {"$exists": true}}]} - Multiple conditions
    - {"createdAt": {"$gte": "2024-01-01T00:00:00Z"}} - Created after date
    - {"fname": {"$exists": true}} - Has first name field
    """
    params = {
        "mdbFilter": json.dumps(mongodb_query)
    }
    return get_resources(resource_type, params)

# Examples of MongoDB filtering for common scenarios
def get_endusers_by_email(email):
    """Find enduser by exact email match"""
    mongodb_query = {"email": email}
    return get_resources_with_mongodb_filter("endusers", mongodb_query)

def get_active_endusers_with_tags(tags_list):
    """Find active endusers with specific tags"""
    mongodb_query = {
        "$and": [
            {"tags": {"$in": tags_list}},
            {"$or": [
                {"status": {"$ne": "inactive"}},
                {"status": {"$exists": False}}
            ]}
        ]
    }
    return get_resources_with_mongodb_filter("endusers", mongodb_query)

def get_endusers_by_age_range(min_age, max_age):
    """Find endusers within an age range"""
    mongodb_query = {
        "age": {
            "$gte": min_age,
            "$lte": max_age
        }
    }
    return get_resources_with_mongodb_filter("endusers", mongodb_query)

def get_recent_communications(resource_type, days_back=7):
    """Get communications from the last N days using MongoDB date filtering"""
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    mongodb_query = {
        "createdAt": {"$gte": cutoff_date}
    }
    return get_resources_with_mongodb_filter(resource_type, mongodb_query)

# Traditional parameter-based filtering (less flexible)
def get_recent_resources(resource_type, days_back=7):
    from datetime import datetime, timedelta
    
    from_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    params = {"fromUpdated": from_date}
    
    return get_resources(resource_type, params)

# Custom filters
def get_filtered_resources(resource_type, filters):
    """
    Common filter parameters (less flexible than mdbFilter):
    - fromUpdated, from, to: Date filtering
    - limit: Page size (max 100)
    - lastId: Pagination cursor
    - mdbFilter: JSON-encoded MongoDB query (MOST FLEXIBLE)
    """
    return get_resources(resource_type, filters)
```

### API Response Format
```python
# Typical list response format (GET /{resource})
[
    { "id": "12345", "fname": "John", "lname": "Doe", ... },
    { "id": "67890", "fname": "Jane", "lname": "Smith", ... }
]

# Single resource response (GET /{resource}/{id} or POST /{resource})
{ 
    "id": "12345", 
    "fname": "John", 
    "lname": "Doe",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    ...
}

# Error response format
{
    "error": "Resource not found",
    "code": 404
}

# Accessing data in responses
def handle_list_response(response):
    if isinstance(response, list):
        return response  # List of records
    return []

def handle_single_response(response):
    if isinstance(response, dict) and "id" in response:
        return response  # Single record
    return None
```

## Core Data Models

**Standard Fields (shared across all models):**
- `id`: Unique identifier (string)
- `createdAt`: ISO timestamp of creation
- `updatedAt`: ISO timestamp of last update
- `businessId`: Associated tenant within Tellescope
- `creator`: ID of user who created the record

### Endusers (Patients)
Primary patient/client records in Tellescope.

**Required Fields:**
- No required fields (email, fname, lname are common but not technically required)

**Key Fields:**
- `email`: Email address
- `fname`: First name
- `lname`: Last name
- `phone`: Primary phone number
- `alternatePhones`: Array of alternate phone numbers
- `landline`: Landline phone number
- `dateOfBirth`: Date of birth (MM-DD-YYYY format)
- `gender`: Gender ('Male', 'Female', 'Other', 'Unknown')
- `genderIdentity`: Gender identity (separate from biological gender)
- `externalId`: External system identifier (useful for Canvas integration)
- `source`: Data source (e.g., "Canvas")
- `tags`: Array of string tags for categorization
- `fields`: Custom fields (key-value pairs)
- `assignedTo`: Array of user IDs assigned to this patient
- `primaryAssignee`: Primary assigned user ID
- `timezone`: Patient's timezone
- `preference`: Communication preference ('email', 'sms', 'call', 'chat')
- `emailConsent`: Boolean for email communication consent
- `phoneConsent`: Boolean for phone/SMS communication consent
- `journeys`: Object mapping journey IDs to current state
- `relationships`: Array of patient relationships
- `insurance`: Primary insurance information
- `insuranceSecondary`: Secondary insurance information
- `accessTags`: Array of access control tags

### Users (Staff)
Team member and staff accounts.

**Required Fields:**
- `email`: Email address (required)
- `verifiedEmail`: Boolean indicating email verification status

**Key Fields:**
- `fname`: First name
- `lname`: Last name
- `displayName`: Public display name
- `internalDisplayName`: Internal display name
- `phone`: Phone number
- `roles`: Array of user roles
- `timezone`: User's timezone
- `avatar`: Avatar image URL
- `emailSignature`: Email signature
- `twilioNumber`: Assigned phone number
- `fromEmail`: Default from email address
- `specialties`: Array of medical specialties
- `bio`: User biography
- `NPI`: National Provider Identifier
- `DEA`: DEA number
- `externalId`: External system identifier

### Emails
Email communication records.

**Required Fields:**
- `enduserId`: Associated patient ID (can be null)
- `subject`: Email subject line
- `textContent`: Plain text email content

**Key Fields:**
- `userId`: Sending user ID
- `HTMLContent`: HTML email content
- `inbound`: Boolean indicating inbound vs outbound
- `delivered`: Boolean delivery status
- `threadId`: Email thread identifier
- `source`: Source email address
- `timestamp`: Email timestamp
- `readBy`: Object tracking read status by user
- `ticketIds`: Associated ticket IDs
- `tags`: Email tags
- `attachments`: File attachments

### SMS Messages
SMS communication records.

**Required Fields:**
- `enduserId`: Associated patient ID
- `message`: SMS message text

**Key Fields:**
- `inbound`: Boolean indicating direction
- `delivered`: Boolean delivery status
- `userId`: Sending user ID
- `phoneNumber`: The Tellescope phone number used
- `enduserPhoneNumber`: The phone number of the Enduser
- `timestamp`: Message timestamp
- `readBy`: Object tracking read status
- `ticketIds`: Associated ticket IDs
- `tags`: Message tags

### Tickets
Task and issue tracking records.

**Required Fields:**
- `title`: Ticket title

**Key Fields:**
- `enduserId`: Associated patient ID
- `message`: Ticket description
- `closedAt`: Closure timestamp
- `closedBy`: User who closed the ticket
- `closedForReason`: Reason for closure
- `dueDateInMS`: Due date in milliseconds since Unix epoch
- `owner`: Assigned owner user ID
- `priority`: Priority level (number)
- `type`: Ticket type
- `stage`: Current stage
- `actions`: Array of ticket actions
- `tags`: Ticket tags

### Forms
Data collection form definitions.

**Required Fields:**
- `title`: Form title

**Key Fields:**
- `description`: Form description
- `allowPublicURL`: Boolean for public access
- `type`: Form type ('note' or 'enduserFacing')
- `scoring`: Array of scoring configurations
- `customGreeting`: Custom greeting message
- `thanksMessage`: Thank you message after submission
- `tags`: Form tags

### Form Responses
Submitted form data.

**Required Fields:**
- `formId`: Associated form ID
- `enduserId`: Patient who submitted
- `formTitle`: Title of the form

**Key Fields:**
- `responses`: Array of answers
- `submittedAt`: Submission timestamp
- `submittedBy`: User who submitted
- `publicSubmit`: Boolean for public submissions
- `scores`: Calculated scores
- `tags`: Response tags

### Calendar Events
Appointments and scheduled events.

**Required Fields:**
- `title`: Event title
- `startTimeInMS`: Start time in milliseconds since Unix epoch
- `durationInMinutes`: Duration in minutes

**Key Fields:**
- `attendees`: Array of attendee objects
- `type`: Event type
- `description`: Event description
- `enableVideoCall`: Boolean for video call integration
- `templateId`: Associated template ID
- `locationId`: Location ID
- `cancelledAt`: Cancellation timestamp
- `completedAt`: Completion timestamp
- `tags`: Event tags

### Common Resource Patterns
Most Tellescope resources follow similar patterns:

**Relationship Fields:**
- `enduserId`: References an enduser (patient)
- `userId`: References a user (staff member)

## Enduser (Patient) Management

### Basic Operations
```python
# Create a new patient (no fields are technically required)
def create_enduser(**patient_data):
    """
    Create a new enduser (patient) record
    
    Common fields:
    - email: Patient email address
    - fname: First name
    - lname: Last name
    - phone: Primary phone number
    - dateOfBirth: Date of birth (MM-DD-YYYY format)
    - gender: Gender ('Male', 'Female', 'Other', 'Unknown')
    - externalId: External system identifier
    - source: Data source (e.g., "Canvas")
    - tags: Array of tags
    """
    return create_resource("enduser", patient_data)

# Search patients by various criteria
def search_endusers(search_params=None, mongodb_filter=None):
    """
    Search endusers using traditional parameters or MongoDB filtering
    
    For simple searches, use search_params:
    - email: Exact email match
    - phone: Phone number search
    - fname, lname: Name search
    - externalId: External system ID
    - tags: Filter by tags
    - assignedTo: Filter by assigned user IDs
    
    For complex searches, use mongodb_filter (RECOMMENDED):
    - mongodb_filter: Dict with MongoDB query syntax
    """
    if mongodb_filter:
        return get_resources_with_mongodb_filter("endusers", mongodb_filter)
    return get_resources("endusers", search_params or {})

# Update patient information
def update_enduser(enduser_id, updates):
    return update_resource("enduser", enduser_id, updates)
```

### Canvas Integration Patterns
```python
def sync_canvas_patient_to_tellescope(canvas_patient):
    """
    Sync Canvas patient data to Tellescope enduser
    """
    # Map Canvas sex field to Tellescope gender field
    def map_canvas_sex_to_tellescope_gender(sex):
        if sex == 'M':
            return 'Male'
        elif sex == 'F':
            return 'Female'
        elif sex in ['O', 'Other']:
            return 'Other'
        else:
            return 'Unknown'
    
    # Map Canvas patient to Tellescope enduser format
    tellescope_data = {
        "email": canvas_patient.email or f"patient{canvas_patient.id}@canvas.medical",
        "fname": canvas_patient.first_name,
        "lname": canvas_patient.last_name,
        "phone": canvas_patient.phone_number,
        "dateOfBirth": canvas_patient.date_of_birth.strftime("%m-%d-%Y") if canvas_patient.date_of_birth else None,
        "gender": map_canvas_sex_to_tellescope_gender(canvas_patient.sex) if canvas_patient.sex else "Unknown",
        "externalId": str(canvas_patient.id),  # Store Canvas patient ID for lookup
        "source": "Canvas",
        "tags": ["canvas-patient"]
    }
    
    # Check if enduser already exists by Canvas ID (using mdbFilter for exact match)
    existing = search_endusers(mongodb_filter={"externalId": str(canvas_patient.id)})
    
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
    result = search_endusers(mongodb_filter={"externalId": str(canvas_patient_id)})
    return result.get("data", [{}])[0] if result.get("data") else None
```

## Communication and Workflow

### Common Communication Operations
```python
# Send an email to a patient
def send_email_to_enduser(enduser_id, subject, text_content, html_content=None, user_id=None):
    email_data = {
        "enduserId": enduser_id,
        "userId": user_id,  # Will use authenticated user if not specified
        "subject": subject,
        "textContent": text_content,
        "HTMLContent": html_content,
        "inbound": False
    }
    return create_resource("email", email_data)

# Send an SMS to a patient
def send_sms_to_enduser(enduser_id, message, user_id=None):
    sms_data = {
        "enduserId": enduser_id,
        "userId": user_id,
        "message": message,
        "inbound": False,
        "newThread": True
    }
    return create_resource("sms-message", sms_data)

# Create a ticket for follow-up
def create_ticket_for_enduser(enduser_id, title, message=None, user_id=None):
    ticket_data = {
        "enduserId": enduser_id,
        "title": title,
        "message": message,
        "owner": user_id
    }
    return create_resource("ticket", ticket_data)

# Get patient's communication history
def get_enduser_communications(enduser_id, limit=50):
    """
    Get recent communications for an enduser across multiple channels
    """
    # Get recent emails
    emails = get_resources("emails", {
        "enduserId": enduser_id,
        "limit": limit
    })
    
    # Get recent SMS messages
    sms_messages = get_resources("sms-messages", {
        "enduserId": enduser_id,
        "limit": limit
    })
    
    return {
        "emails": emails.get("data", []),
        "sms_messages": sms_messages.get("data", [])
    }
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
def get_enduser(enduser_id):
    """Get a single enduser by ID"""
    return get_resource_by_id("enduser", enduser_id)

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
            headers={
                "Authorization": f"API_KEY {TELLESCOPE_API_KEY}",
                "Content-Type": "application/json"
            },
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
2. **Use mdbFilter for complex queries** - When filtering data, prefer `mdbFilter` with MongoDB query syntax over traditional parameters for maximum flexibility
3. **Use externalId for integration** - Store Canvas patient IDs in Tellescope's `externalId` field and set the source to "Canvas" when creating new patients
4. **Handle rate limits gracefully** - Implement retry logic with delays
5. **Validate data before API calls** - Check required fields and formats
6. **Use pagination for large datasets** - Don't attempt to fetch all records at once
7. **Implement proper error handling** - Return user-friendly Canvas effects for errors
8. **Test with staging environment** - Use staging API URL for development and testing

#### MongoDB Query Reference for AI Assistants
When using `mdbFilter`, these MongoDB operators are commonly useful:
- `{"field": "value"}` - Exact match
- `{"field": {"$in": ["val1", "val2"]}}` - Field matches any value in array
- `{"field": {"$ne": "value"}}` - Not equal
- `{"field": {"$exists": true}}` - Field exists
- `{"field": {"$gte": value}}` - Greater than or equal
- `{"field": {"$lte": value}}` - Less than or equal
- `{"$and": [condition1, condition2]}` - Multiple conditions must be true
- `{"$or": [condition1, condition2]}` - At least one condition must be true

**IMPORTANT**: Always use `mdbFilter` with `json.dumps()` to properly encode the MongoDB query as JSON.

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