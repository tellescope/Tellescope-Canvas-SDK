"""
Test suite for Canvas Enduser Lookup Utility

Tests the utility functions for finding Tellescope endusers that originated from Canvas.
"""

import pytest
from unittest.mock import Mock, patch

from utilities.canvas_enduser_lookup import (
    CanvasEnduserLookup,
    find_tellescope_enduser_for_canvas_patient,
    find_tellescope_enduser_by_external_id,
    find_tellescope_enduser_by_reference,
    get_all_tellescope_endusers_for_canvas_patient,
    canvas_patient_has_tellescope_enduser
)


class TestCanvasEnduserLookupClass:
    """Test suite for the CanvasEnduserLookup class"""

    @pytest.fixture
    def mock_tellescope_api(self):
        """Mock TellescopeAPI instance"""
        return Mock()

    @pytest.fixture
    def lookup_instance(self, mock_tellescope_api):
        """Create CanvasEnduserLookup instance with mocked API"""
        return CanvasEnduserLookup(mock_tellescope_api)

    @pytest.fixture
    def sample_enduser_external_id(self):
        """Sample enduser found via externalId match"""
        return {
            "id": "tellescope_enduser_123",
            "email": "jane.smith@example.com",
            "fname": "Jane",
            "lname": "Smith",
            "source": "Canvas",
            "externalId": "canvas_patient_456",
            "references": []
        }

    @pytest.fixture
    def sample_enduser_references(self):
        """Sample enduser found via references match"""
        return {
            "id": "tellescope_enduser_789",
            "email": "jane.smith@example.com",
            "fname": "Jane",
            "lname": "Smith",
            "source": "Manual",
            "externalId": "different_id",
            "references": [
                {"type": "Canvas", "id": "canvas_patient_456"},
                {"type": "Other", "id": "some_other_id"}
            ]
        }

    def test_initialization_with_api(self, mock_tellescope_api):
        """Test initialization with provided TellescopeAPI instance"""
        lookup = CanvasEnduserLookup(mock_tellescope_api)
        assert lookup.tellescope_api == mock_tellescope_api

    @patch('utilities.canvas_enduser_lookup.TellescopeAPI')
    def test_initialization_without_api(self, mock_api_class):
        """Test initialization without provided TellescopeAPI instance"""
        lookup = CanvasEnduserLookup()
        mock_api_class.assert_called_once()
        assert lookup.tellescope_api == mock_api_class.return_value

    def test_find_enduser_for_canvas_patient_via_external_id(self, lookup_instance, sample_enduser_external_id):
        """Test successful lookup via source=Canvas and externalId match"""
        # Mock API response
        lookup_instance.tellescope_api.find_by.return_value = sample_enduser_external_id

        # Test the method
        result = lookup_instance.find_enduser_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert result == sample_enduser_external_id
        
        # Verify correct MongoDB filter was used
        expected_filter = {
            "$or": [
                {
                    "$and": [
                        {"source": "Canvas"},
                        {"externalId": "canvas_patient_456"}
                    ]
                },
                {
                    "references": {
                        "$elemMatch": {
                            "type": "Canvas",
                            "id": "canvas_patient_456"
                        }
                    }
                }
            ]
        }
        
        lookup_instance.tellescope_api.find_by.assert_called_once_with(
            "endusers", 
            expected_filter
        )

    def test_find_enduser_for_canvas_patient_via_references(self, lookup_instance, sample_enduser_references):
        """Test successful lookup via references field match"""
        # Mock API response
        lookup_instance.tellescope_api.find_by.return_value = sample_enduser_references

        # Test the method
        result = lookup_instance.find_enduser_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert result == sample_enduser_references
        assert result["source"] == "Manual"
        assert len(result["references"]) == 2

    def test_find_enduser_for_canvas_patient_not_found(self, lookup_instance):
        """Test when no enduser is found"""
        # Mock no enduser found
        lookup_instance.tellescope_api.find_by.return_value = None

        # Test the method
        result = lookup_instance.find_enduser_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert result is None

    def test_find_enduser_by_external_id(self, lookup_instance, sample_enduser_external_id):
        """Test the external ID specific lookup method"""
        lookup_instance.tellescope_api.find_by.return_value = sample_enduser_external_id

        # Test the method
        result = lookup_instance.find_enduser_by_external_id("canvas_patient_456")

        # Verify result
        assert result == sample_enduser_external_id
        
        # Verify correct filter for external ID only
        expected_filter = {
            "$and": [
                {"source": "Canvas"},
                {"externalId": "canvas_patient_456"}
            ]
        }
        lookup_instance.tellescope_api.find_by.assert_called_once_with("endusers", expected_filter)

    def test_find_enduser_by_reference(self, lookup_instance, sample_enduser_references):
        """Test the references specific lookup method"""
        lookup_instance.tellescope_api.find_by.return_value = sample_enduser_references

        # Test the method
        result = lookup_instance.find_enduser_by_reference("canvas_patient_456")

        # Verify result
        assert result == sample_enduser_references
        
        # Verify correct filter for references only
        expected_filter = {
            "references": {
                "$elemMatch": {
                    "type": "Canvas",
                    "id": "canvas_patient_456"
                }
            }
        }
        lookup_instance.tellescope_api.find_by.assert_called_once_with("endusers", expected_filter)

    def test_get_all_endusers_for_canvas_patient(self, lookup_instance):
        """Test getting all matching endusers (in case of duplicates)"""
        # Mock multiple endusers
        endusers_list = [
            {
                "id": "enduser_1",
                "source": "Canvas",
                "externalId": "canvas_patient_456"
            },
            {
                "id": "enduser_2", 
                "source": "Manual",
                "references": [{"type": "Canvas", "id": "canvas_patient_456"}]
            }
        ]
        lookup_instance.tellescope_api.list.return_value = endusers_list

        # Test the method
        result = lookup_instance.get_all_endusers_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "enduser_1"
        assert result[1]["id"] == "enduser_2"
        
        # Verify list was called with correct filter
        call_args = lookup_instance.tellescope_api.list.call_args
        assert call_args[1]["mongodb_filter"]["$or"] is not None

    def test_enduser_exists_for_canvas_patient_true(self, lookup_instance, sample_enduser_external_id):
        """Test enduser existence check when enduser exists"""
        lookup_instance.tellescope_api.find_by.return_value = sample_enduser_external_id

        # Test the method
        result = lookup_instance.enduser_exists_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert result is True

    def test_enduser_exists_for_canvas_patient_false(self, lookup_instance):
        """Test enduser existence check when no enduser exists"""
        lookup_instance.tellescope_api.find_by.return_value = None

        # Test the method
        result = lookup_instance.enduser_exists_for_canvas_patient("canvas_patient_456")

        # Verify result
        assert result is False

    def test_error_handling_api_failure(self, lookup_instance):
        """Test error handling when TellescopeAPI fails"""
        # Mock API failure
        lookup_instance.tellescope_api.find_by.side_effect = Exception("API connection failed")

        # Test that exception is raised
        with pytest.raises(Exception, match="API connection failed"):
            lookup_instance.find_enduser_for_canvas_patient("canvas_patient_456")

    def test_patient_id_string_conversion(self, lookup_instance):
        """Test that patient IDs are properly converted to strings"""
        lookup_instance.tellescope_api.find_by.return_value = None

        # Test with integer patient ID
        lookup_instance.find_enduser_for_canvas_patient(12345)

        # Verify patient ID was converted to string in the filter
        call_args = lookup_instance.tellescope_api.find_by.call_args
        filter_used = call_args[0][1]
        
        # Check that string conversion happened
        or_conditions = filter_used["$or"]
        external_id_condition = or_conditions[0]["$and"][1]
        assert external_id_condition["externalId"] == "12345"
        
        references_condition = or_conditions[1]["references"]["$elemMatch"]
        assert references_condition["id"] == "12345"


class TestConvenienceFunctions:
    """Test suite for the convenience functions"""

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_find_tellescope_enduser_for_canvas_patient(self, mock_lookup_class):
        """Test the convenience function for main lookup"""
        # Mock the class and its method
        mock_instance = mock_lookup_class.return_value
        expected_result = {"id": "test_enduser"}
        mock_instance.find_enduser_for_canvas_patient.return_value = expected_result

        # Test the function
        result = find_tellescope_enduser_for_canvas_patient("test_patient")

        # Verify
        mock_lookup_class.assert_called_once()
        mock_instance.find_enduser_for_canvas_patient.assert_called_once_with("test_patient")
        assert result == expected_result

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_find_tellescope_enduser_by_external_id(self, mock_lookup_class):
        """Test the convenience function for external ID lookup"""
        mock_instance = mock_lookup_class.return_value
        expected_result = {"id": "test_enduser"}
        mock_instance.find_enduser_by_external_id.return_value = expected_result

        result = find_tellescope_enduser_by_external_id("test_patient")

        mock_instance.find_enduser_by_external_id.assert_called_once_with("test_patient")
        assert result == expected_result

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_find_tellescope_enduser_by_reference(self, mock_lookup_class):
        """Test the convenience function for reference lookup"""
        mock_instance = mock_lookup_class.return_value
        expected_result = {"id": "test_enduser"}
        mock_instance.find_enduser_by_reference.return_value = expected_result

        result = find_tellescope_enduser_by_reference("test_patient")

        mock_instance.find_enduser_by_reference.assert_called_once_with("test_patient")
        assert result == expected_result

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_get_all_tellescope_endusers_for_canvas_patient(self, mock_lookup_class):
        """Test the convenience function for getting all endusers"""
        mock_instance = mock_lookup_class.return_value
        expected_result = [{"id": "enduser1"}, {"id": "enduser2"}]
        mock_instance.get_all_endusers_for_canvas_patient.return_value = expected_result

        result = get_all_tellescope_endusers_for_canvas_patient("test_patient")

        mock_instance.get_all_endusers_for_canvas_patient.assert_called_once_with("test_patient")
        assert result == expected_result

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_canvas_patient_has_tellescope_enduser(self, mock_lookup_class):
        """Test the convenience function for existence check"""
        mock_instance = mock_lookup_class.return_value
        mock_instance.enduser_exists_for_canvas_patient.return_value = True

        result = canvas_patient_has_tellescope_enduser("test_patient")

        mock_instance.enduser_exists_for_canvas_patient.assert_called_once_with("test_patient")
        assert result is True

    @patch('utilities.canvas_enduser_lookup.CanvasEnduserLookup')
    def test_convenience_functions_error_propagation(self, mock_lookup_class):
        """Test that convenience functions properly propagate errors"""
        mock_instance = mock_lookup_class.return_value
        mock_instance.find_enduser_for_canvas_patient.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            find_tellescope_enduser_for_canvas_patient("test_patient")


class TestMongoDBFilterStructure:
    """Test suite for MongoDB filter structure validation"""

    @pytest.fixture
    def lookup_instance(self):
        """Create lookup instance with mock API"""
        mock_api = Mock()
        return CanvasEnduserLookup(mock_api)

    def test_main_filter_structure(self, lookup_instance):
        """Test that the main MongoDB filter structure is correct"""
        lookup_instance.tellescope_api.find_by.return_value = None

        # Execute the lookup
        lookup_instance.find_enduser_for_canvas_patient("test_patient_123")

        # Get the filter that was used
        call_args = lookup_instance.tellescope_api.find_by.call_args
        filter_used = call_args[0][1]

        # Verify filter structure
        assert "$or" in filter_used
        or_conditions = filter_used["$or"]
        assert len(or_conditions) == 2

        # Check first condition (source + externalId)
        first_condition = or_conditions[0]
        assert "$and" in first_condition
        and_conditions = first_condition["$and"]
        assert {"source": "Canvas"} in and_conditions
        assert {"externalId": "test_patient_123"} in and_conditions

        # Check second condition (references)
        second_condition = or_conditions[1]
        assert "references" in second_condition
        elem_match = second_condition["references"]["$elemMatch"]
        assert elem_match["type"] == "Canvas"
        assert elem_match["id"] == "test_patient_123"

    def test_external_id_filter_structure(self, lookup_instance):
        """Test external ID filter structure"""
        lookup_instance.tellescope_api.find_by.return_value = None

        lookup_instance.find_enduser_by_external_id("test_patient_123")

        call_args = lookup_instance.tellescope_api.find_by.call_args
        filter_used = call_args[0][1]

        expected_filter = {
            "$and": [
                {"source": "Canvas"},
                {"externalId": "test_patient_123"}
            ]
        }
        assert filter_used == expected_filter

    def test_reference_filter_structure(self, lookup_instance):
        """Test reference filter structure"""
        lookup_instance.tellescope_api.find_by.return_value = None

        lookup_instance.find_enduser_by_reference("test_patient_123")

        call_args = lookup_instance.tellescope_api.find_by.call_args
        filter_used = call_args[0][1]

        expected_filter = {
            "references": {
                "$elemMatch": {
                    "type": "Canvas",
                    "id": "test_patient_123"
                }
            }
        }
        assert filter_used == expected_filter