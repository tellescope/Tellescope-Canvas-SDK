"""
Test suite for Canvas Patient to Tellescope Enduser sync protocol

Tests the automatic creation of Tellescope endusers when Canvas patients are created.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from canvas_sdk.effects import EffectType
from canvas_sdk.events import EventType

from protocols.canvas_patient_to_tellescope_enduser import Protocol


class TestCanvasPatientToTellescopeEnduserProtocol:
    """Test suite for the Canvas to Tellescope patient sync protocol"""
    
    def test_error_categorization_validation_error(self, protocol_instance):
        """Test error categorization for validation errors"""
        # Mock API validation error
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.side_effect = ValueError("Invalid email format")

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify error effect with proper categorization
        assert len(effects) == 1
        effect = effects[0]
        payload = json.loads(effect.payload)
        assert payload["status"] == "error"
        assert payload["error_category"] == "validation_error"
        assert "Data validation failed" in payload["message"]
        assert payload["retry_recommended"] == False
    
    def test_error_categorization_authentication_error(self, protocol_instance):
        """Test error categorization for authentication errors"""
        # Mock API authentication error
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.side_effect = PermissionError("Invalid API key")

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify error effect with proper categorization
        assert len(effects) == 1
        effect = effects[0]
        payload = json.loads(effect.payload)
        assert payload["status"] == "error"
        assert payload["error_category"] == "authentication_error"
        assert "Authentication failed" in payload["message"]
        assert payload["retry_recommended"] == False
    
    def test_error_categorization_connection_error(self, protocol_instance):
        """Test error categorization for connection errors"""
        # Mock API connection error
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.side_effect = ConnectionError("Network timeout")

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify error effect with proper categorization
        assert len(effects) == 1
        effect = effects[0]
        payload = json.loads(effect.payload)
        assert payload["status"] == "error"
        assert payload["error_category"] == "connection_error"
        assert "Connection failed" in payload["message"]
        assert payload["retry_recommended"] == False

    @pytest.fixture
    def mock_canvas_patient(self):
        """Mock Canvas patient instance"""
        patient = Mock()
        patient.id = "canvas_patient_123"
        patient.first_name = "John"
        patient.last_name = "Doe"
        patient.email = "john.doe@example.com"
        patient.phone_number = "+1234567890"
        patient.date_of_birth = datetime(1990, 1, 15)
        patient.sex = "M"
        patient.address = "123 Main St, City, State"
        patient.date_created = datetime.now()
        return patient

    @pytest.fixture
    def mock_event(self, mock_canvas_patient):
        """Mock Canvas patient creation event"""
        event = Mock()
        event.target = Mock()
        event.target.id = mock_canvas_patient.id
        event.target.instance = mock_canvas_patient
        event.context = {}
        return event

    @pytest.fixture
    def protocol_instance(self, mock_event):
        """Create protocol instance with mocked dependencies"""
        with patch('protocols.canvas_patient_to_tellescope_enduser.TellescopeAPI') as mock_api_class:
            protocol = Protocol(mock_event)
            protocol.secrets = {}
            # Mock the TellescopeAPI instance
            protocol.tellescope_api = mock_api_class.return_value
            return protocol

    def test_protocol_responds_to_patient_created_event(self):
        """Test that protocol is configured to respond to patient creation events"""
        assert Protocol.RESPONDS_TO == EventType.Name(EventType.PATIENT_CREATED)

    def test_successful_enduser_creation(self, protocol_instance, mock_canvas_patient):
        """Test successful creation of Tellescope enduser from Canvas patient"""
        # Mock TellescopeAPI responses
        protocol_instance.tellescope_api.find_by.return_value = None  # No existing enduser
        
        created_enduser = {
            "id": "tellescope_enduser_456",
            "email": "john.doe@example.com",
            "fname": "John",
            "lname": "Doe",
            "externalId": "canvas_patient_123",
            "source": "Canvas"
        }
        protocol_instance.tellescope_api.create.return_value = created_enduser

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify TellescopeAPI calls
        protocol_instance.tellescope_api.find_by.assert_called_once_with(
            "endusers", 
            {"externalId": "canvas_patient_123"}
        )
        
        # Verify create was called with correct data
        create_call_args = protocol_instance.tellescope_api.create.call_args
        assert create_call_args[0][0] == "enduser"  # resource type
        enduser_data = create_call_args[0][1]  # data
        
        # Verify mapped data
        assert enduser_data["externalId"] == "canvas_patient_123"
        assert enduser_data["source"] == "Canvas"
        assert enduser_data["fname"] == "John"
        assert enduser_data["lname"] == "Doe"
        assert enduser_data["email"] == "john.doe@example.com"
        assert enduser_data["phone"] == "+1234567890"
        assert enduser_data["dateOfBirth"] == "01-15-1990"
        assert enduser_data["gender"] == "Male"
        assert "canvas-patient" in enduser_data["tags"]
        assert "auto-synced" in enduser_data["tags"]

        # Verify success effect
        assert len(effects) == 1
        effect = effects[0]
        assert effect.type == EffectType.LOG
        
        payload = json.loads(effect.payload)
        assert payload["status"] == "success"
        assert payload["tellescope_enduser_id"] == "tellescope_enduser_456"
        assert payload["canvas_patient_id"] == "canvas_patient_123"
        assert payload["operation_type"] == "enduser_creation"
        assert payload["event_type"] == "PATIENT_CREATED"
        assert payload["resource_id"] == "canvas_patient_123"
        assert payload["target_system"] == "tellescope"
        assert payload["source_system"] == "canvas"

    def test_existing_enduser_handling(self, protocol_instance):
        """Test handling when enduser already exists in Tellescope"""
        # Mock existing enduser
        existing_enduser = {
            "id": "existing_enduser_789",
            "externalId": "canvas_patient_123",
            "email": "john.doe@example.com"
        }
        protocol_instance.tellescope_api.find_by.return_value = existing_enduser

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify find_by was called but create was not
        protocol_instance.tellescope_api.find_by.assert_called_once()
        protocol_instance.tellescope_api.create.assert_not_called()

        # Verify success effect for existing enduser
        assert len(effects) == 1
        effect = effects[0]
        payload = json.loads(effect.payload)
        assert payload["status"] == "success"
        assert "already exists" in payload["message"]
        assert payload["tellescope_enduser_id"] == "existing_enduser_789"
        assert payload["operation_type"] == "duplicate_handling"

    def test_gender_mapping(self, protocol_instance, mock_canvas_patient):
        """Test gender mapping from Canvas to Tellescope"""
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.return_value = {"id": "test_id"}

        # Test different gender values
        test_cases = [
            ("M", "Male"),
            ("F", "Female"),
            ("O", "Other"),
            ("Other", "Other"),
            (None, "Unknown"),
            ("unknown_value", "Unknown")
        ]

        for canvas_sex, expected_gender in test_cases:
            mock_canvas_patient.sex = canvas_sex
            protocol_instance.compute()
            
            # Get the data passed to create
            create_call_args = protocol_instance.tellescope_api.create.call_args
            enduser_data = create_call_args[0][1]
            assert enduser_data["gender"] == expected_gender

    def test_email_fallback(self, protocol_instance, mock_canvas_patient):
        """Test email fallback when patient has no email"""
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.return_value = {"id": "test_id"}

        # Test with no email
        mock_canvas_patient.email = None
        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert enduser_data["email"] == "patientcanvas_patient_123@canvas.medical"

        # Test with empty email
        mock_canvas_patient.email = ""
        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert enduser_data["email"] == "patientcanvas_patient_123@canvas.medical"

    def test_date_of_birth_formatting(self, protocol_instance, mock_canvas_patient):
        """Test date of birth formatting"""
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.return_value = {"id": "test_id"}

        # Test with datetime object
        mock_canvas_patient.date_of_birth = datetime(1985, 12, 25)
        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert enduser_data["dateOfBirth"] == "12-25-1985"

        # Test with string date
        mock_canvas_patient.date_of_birth = "03-15-1992"
        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert enduser_data["dateOfBirth"] == "03-15-1992"

        # Test with None
        mock_canvas_patient.date_of_birth = None
        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert "dateOfBirth" not in enduser_data

    def test_error_handling_tellescope_api_failure(self, protocol_instance):
        """Test error handling when Tellescope API fails"""
        # Mock API failure
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.side_effect = Exception("API connection failed")

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify error effect
        assert len(effects) == 1
        effect = effects[0]
        assert effect.type == EffectType.LOG
        
        payload = json.loads(effect.payload)
        assert payload["status"] == "error"
        assert "Unexpected error" in payload["message"]
        assert "API connection failed" in payload["message"]
        assert payload["error_category"] == "unexpected_error"
        assert payload["retry_recommended"] == True

    def test_error_handling_missing_patient_instance(self, protocol_instance):
        """Test error handling when patient instance is missing"""
        # Mock missing patient instance
        protocol_instance.event.target.instance = None

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify error effect
        assert len(effects) == 1
        effect = effects[0]
        payload = json.loads(effect.payload)
        assert payload["status"] == "error"
        assert "Patient instance not available" in payload["message"]
        assert payload["error_category"] == "missing_patient_instance"
        assert payload["retry_recommended"] == False

    def test_custom_fields_mapping(self, protocol_instance, mock_canvas_patient):
        """Test that custom fields are properly mapped"""
        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.return_value = {"id": "test_id"}

        protocol_instance.compute()

        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        
        # Verify custom fields
        assert "fields" in enduser_data
        fields = enduser_data["fields"]
        assert fields["canvas_patient_id"] == "canvas_patient_123"
        assert "sync_timestamp" in fields
        assert fields["sync_source"] == "canvas_patient_creation_protocol"
        assert "canvas_address" in fields
        assert "canvas_created_date" in fields

    def test_minimal_patient_data(self, protocol_instance, mock_event):
        """Test protocol with minimal patient data"""
        # Create minimal patient with only required fields
        minimal_patient = Mock()
        minimal_patient.id = "minimal_patient_456"
        minimal_patient.first_name = None
        minimal_patient.last_name = None
        minimal_patient.email = None
        minimal_patient.phone_number = None
        minimal_patient.date_of_birth = None
        minimal_patient.sex = None

        mock_event.target.instance = minimal_patient
        protocol_instance.event = mock_event

        protocol_instance.tellescope_api.find_by.return_value = None
        protocol_instance.tellescope_api.create.return_value = {"id": "minimal_enduser"}

        # Execute protocol
        effects = protocol_instance.compute()

        # Verify it still works with minimal data
        assert len(effects) == 1
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "success"
        assert payload["operation_type"] == "enduser_creation"

        # Verify create was called with minimal but valid data
        create_call_args = protocol_instance.tellescope_api.create.call_args
        enduser_data = create_call_args[0][1]
        assert enduser_data["externalId"] == "minimal_patient_456"
        assert enduser_data["source"] == "Canvas"
        assert enduser_data["email"] == "patientminimal_patient_456@canvas.medical"
        assert enduser_data["gender"] == "Unknown"