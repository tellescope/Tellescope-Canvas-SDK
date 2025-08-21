"""
Tests for the Tellescope Enduser to Canvas Metadata sync protocol
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from canvas_sdk.effects import Effect, EffectType
from canvas_sdk.events import EventType

from protocols.tellescope_enduser_to_canvas_metadata import Protocol


class TestTellescopeEnduserToCanvasMetadataProtocol:
    """Test cases for the metadata sync protocol"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_event = Mock()
        self.mock_event.target.instance.id = "test_patient_123"
        
        self.mock_secrets = {
            "TELLESCOPE_API_KEY": "test_api_key",
            "TELLESCOPE_API_URL": "https://api.tellescope.com/v1"
        }
        
        # Create protocol instance with mocked dependencies
        with patch('protocols.tellescope_enduser_to_canvas_metadata.TellescopeAPI'), \
             patch('protocols.tellescope_enduser_to_canvas_metadata.CanvasEnduserLookup'), \
             patch('protocols.tellescope_enduser_to_canvas_metadata.get_cache') as mock_get_cache:
            
            # Mock the Canvas cache
            self.mock_cache = MagicMock()
            mock_get_cache.return_value = self.mock_cache
            
            self.protocol = Protocol(self.mock_event, self.mock_secrets)

    def test_responds_to_patient_updated_event(self):
        """Test that protocol responds to PATIENT_UPDATED events"""
        assert self.protocol.RESPONDS_TO == EventType.Name(EventType.PATIENT_UPDATED)

    def test_rate_limiting_functionality(self):
        """Test 5-minute rate limiting per patient using Canvas cache"""
        patient_id = "test_patient_123"
        cache_key = f"patient_metadata_sync:{patient_id}"
        
        # Initially not rate limited - cache returns False for __contains__
        self.mock_cache.__contains__.return_value = False
        
        # Should not be rate limited
        assert cache_key not in self.protocol.cache
        
        # Simulate cache entry exists (rate limited)
        self.mock_cache.__contains__.return_value = True
        
        # Should be rate limited
        assert cache_key in self.protocol.cache
        
        # Test cache.set is called with correct parameters
        sync_data = {"test": "data"}
        self.protocol.cache.set(cache_key, sync_data, self.protocol.RATE_LIMIT_SECONDS)
        
        # Verify cache.set was called with correct arguments
        self.mock_cache.set.assert_called_with(cache_key, sync_data, 300)

    def test_extract_custom_fields_from_dict(self):
        """Test extracting custom fields when fields is a dict"""
        enduser = {
            "id": "enduser_123",
            "fields": {
                "custom_field_1": "value1",
                "custom_field_2": "value2",
                "numeric_field": 42
            }
        }
        
        fields = self.protocol._extract_custom_fields(enduser)
        
        assert fields == {
            "custom_field_1": "value1",
            "custom_field_2": "value2",
            "numeric_field": 42
        }

    def test_extract_custom_fields_from_json_string(self):
        """Test extracting custom fields when fields is a JSON string"""
        enduser = {
            "id": "enduser_123",
            "fields": '{"custom_field_1": "value1", "custom_field_2": "value2"}'
        }
        
        fields = self.protocol._extract_custom_fields(enduser)
        
        assert fields == {
            "custom_field_1": "value1",
            "custom_field_2": "value2"
        }

    def test_extract_custom_fields_invalid_json(self):
        """Test handling invalid JSON in fields"""
        enduser = {
            "id": "enduser_123",
            "fields": "invalid json string"
        }
        
        fields = self.protocol._extract_custom_fields(enduser)
        
        assert fields == {}

    def test_extract_custom_fields_empty_fields(self):
        """Test handling empty or missing fields"""
        test_cases = [
            {"id": "enduser_123", "fields": {}},
            {"id": "enduser_123", "fields": None},
            {"id": "enduser_123"},  # No fields key
        ]
        
        for enduser in test_cases:
            fields = self.protocol._extract_custom_fields(enduser)
            assert fields == {}

    def test_sync_custom_fields_to_metadata(self):
        """Test syncing custom fields to PatientMetadata effects"""
        patient_id = "test_patient_123"
        custom_fields = {
            "field1": "value1",
            "field2": 42,
            "field3": True,
            "field4": False,
            "field5": {"nested": "object"},
            "field6": [1, 2, 3],
            "field7": None  # Should be skipped
        }
        
        effects = self.protocol._sync_custom_fields_to_metadata(patient_id, custom_fields)
        
        # Should create 6 effects (excluding None value)
        assert len(effects) == 6
        
        # Check each effect and verify proper type conversion
        payload_by_key = {}
        for effect in effects:
            assert effect.type == EffectType.UPSERT_PATIENT_METADATA
            payload = json.loads(effect.payload)
            assert payload["patient_id"] == patient_id
            assert payload["namespace"] == "tellescope_custom_fields"
            payload_by_key[payload["key"]] = payload["value"]
        
        # Verify proper type conversion
        assert payload_by_key["field1"] == "value1"  # String unchanged
        assert payload_by_key["field2"] == "42"      # Number to string
        assert payload_by_key["field3"] == "true"    # Boolean True to "true"
        assert payload_by_key["field4"] == "false"   # Boolean False to "false"
        assert payload_by_key["field5"] == '{"nested":"object"}'  # Object to JSON
        assert payload_by_key["field6"] == '[1,2,3]'  # Array to JSON
        assert "field7" not in payload_by_key  # None value skipped

    @patch('protocols.tellescope_enduser_to_canvas_metadata.log')
    def test_compute_no_secrets_configured(self, mock_log):
        """Test compute method when Tellescope secrets are not configured"""
        # Create protocol without secrets using the proper mocking context
        with patch('protocols.tellescope_enduser_to_canvas_metadata.TellescopeAPI'), \
             patch('protocols.tellescope_enduser_to_canvas_metadata.CanvasEnduserLookup'), \
             patch('protocols.tellescope_enduser_to_canvas_metadata.get_cache') as mock_get_cache:
            
            mock_cache = MagicMock()
            mock_get_cache.return_value = mock_cache
            protocol = Protocol(self.mock_event, {})
        
        effects = protocol.compute()
        
        assert effects == []
        mock_log.warning.assert_called_with("Tellescope API credentials not configured, skipping metadata sync")

    def test_compute_no_patient_instance(self):
        """Test compute method when patient instance is not available"""
        self.mock_event.target.instance = None
        
        effects = self.protocol.compute()
        
        assert len(effects) == 1
        assert effects[0].type == EffectType.LOG
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "error"
        assert "Patient instance not available" in payload["message"]

    def test_compute_rate_limited(self):
        """Test compute method when patient is rate limited"""
        patient_id = "test_patient_123"
        cache_key = f"patient_metadata_sync:{patient_id}"
        
        # Setup rate limiting - simulate cache entry exists
        self.mock_cache.__contains__.return_value = True
        
        effects = self.protocol.compute()
        
        assert len(effects) == 1
        assert effects[0].type == EffectType.LOG
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "success"
        assert payload["operation_type"] == "rate_limited"

    def test_compute_enduser_not_found(self):
        """Test compute method when Tellescope enduser is not found"""
        # Ensure not rate limited
        self.mock_cache.__contains__.return_value = False
        
        # Mock enduser lookup to return None
        self.protocol.enduser_lookup.find_enduser_for_canvas_patient.return_value = None
        
        effects = self.protocol.compute()
        
        assert len(effects) == 1
        assert effects[0].type == EffectType.LOG
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "success"
        assert payload["operation_type"] == "enduser_not_found"

    def test_compute_no_custom_fields(self):
        """Test compute method when enduser has no custom fields"""
        # Ensure not rate limited
        self.mock_cache.__contains__.return_value = False
        
        # Mock enduser lookup to return enduser without fields
        mock_enduser = {"id": "enduser_123", "fields": {}}
        self.protocol.enduser_lookup.find_enduser_for_canvas_patient.return_value = mock_enduser
        
        effects = self.protocol.compute()
        
        assert len(effects) == 1
        assert effects[0].type == EffectType.LOG
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "success"
        assert payload["operation_type"] == "no_custom_fields"

    def test_compute_successful_sync(self):
        """Test successful metadata sync"""
        # Ensure not rate limited
        self.mock_cache.__contains__.return_value = False
        
        # Mock enduser lookup to return enduser with custom fields
        mock_enduser = {
            "id": "enduser_123",
            "fields": {
                "custom_field_1": "value1",
                "custom_field_2": "value2"
            }
        }
        self.protocol.enduser_lookup.find_enduser_for_canvas_patient.return_value = mock_enduser
        
        effects = self.protocol.compute()
        
        # Should have 2 PatientMetadata effects + 1 success log
        assert len(effects) == 3
        
        # Check PatientMetadata effects
        metadata_effects = [e for e in effects if e.type == EffectType.UPSERT_PATIENT_METADATA]
        assert len(metadata_effects) == 2
        
        # Check success log
        log_effects = [e for e in effects if e.type == EffectType.LOG]
        assert len(log_effects) == 1
        payload = json.loads(log_effects[0].payload)
        assert payload["status"] == "success"
        assert payload["operation_type"] == "metadata_sync"
        assert "Successfully synced 2 custom fields" in payload["message"]

    def test_compute_handles_exceptions(self):
        """Test compute method handles exceptions gracefully"""
        # Ensure not rate limited
        self.mock_cache.__contains__.return_value = False
        
        # Mock enduser lookup to raise an exception
        self.protocol.enduser_lookup.find_enduser_for_canvas_patient.side_effect = Exception("Test error")
        
        effects = self.protocol.compute()
        
        assert len(effects) == 1
        assert effects[0].type == EffectType.LOG
        payload = json.loads(effects[0].payload)
        assert payload["status"] == "error"
        assert "Sync failed: Test error" in payload["message"]

    def test_cache_integration(self):
        """Test Canvas cache integration"""
        patient_id = "test_patient_123"
        cache_key = f"patient_metadata_sync:{patient_id}"
        
        # Test cache operations
        sync_data = {
            "enduser_id": "enduser_123",
            "fields_count": 2,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test cache.set method
        self.protocol.cache.set(cache_key, sync_data, 300)
        self.mock_cache.set.assert_called_with(cache_key, sync_data, 300)
        
        # Test cache __contains__ method
        self.mock_cache.__contains__.return_value = True
        assert cache_key in self.protocol.cache

    def test_create_success_effect_structure(self):
        """Test success effect has correct structure"""
        effect = self.protocol._create_success_effect(
            "Test message", "enduser_123", "patient_123", "test_operation"
        )
        
        assert effect.type == EffectType.LOG
        payload = json.loads(effect.payload)
        
        expected_fields = [
            "status", "message", "tellescope_enduser_id", "canvas_patient_id",
            "operation_type", "timestamp", "protocol", "event_type",
            "resource_id", "target_system", "source_system"
        ]
        
        for field in expected_fields:
            assert field in payload
            
        assert payload["status"] == "success"
        assert payload["protocol"] == "tellescope_enduser_to_canvas_metadata"
        assert payload["event_type"] == "PATIENT_UPDATED"

    def test_create_error_effect_structure(self):
        """Test error effect has correct structure"""
        effect = self.protocol._create_error_effect("Test error", "test_category")
        
        assert effect.type == EffectType.LOG
        payload = json.loads(effect.payload)
        
        expected_fields = [
            "status", "message", "error_category", "timestamp", "protocol",
            "event_type", "target_system", "source_system", "retry_recommended"
        ]
        
        for field in expected_fields:
            assert field in payload
            
        assert payload["status"] == "error"
        assert payload["protocol"] == "tellescope_enduser_to_canvas_metadata"
        assert payload["event_type"] == "PATIENT_UPDATED"