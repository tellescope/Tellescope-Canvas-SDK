"""
Test suite for TellescopeAPI utility

Tests CRUD operations for Enduser model:
1. Create an Enduser
2. Read the created Enduser  
3. Update the Enduser
4. Delete the Enduser
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from utilities.tellescope_api import TellescopeAPI


class TestTellescopeAPI:
    """Test suite for TellescopeAPI CRUD operations"""
    
    @pytest.fixture
    def api_client(self):
        """Create TellescopeAPI client using environment variables from .env file"""
        return TellescopeAPI()  # Uses TELLESCOPE_API_KEY and TELLESCOPE_API_URL from .env
    
    @pytest.fixture
    def sample_enduser_data(self):
        """Sample enduser data for testing"""
        return {
            "email": "test@example.com",
            "fname": "John",
            "lname": "Doe",
            "phone": "+1234567890",
            "dateOfBirth": "01-15-1990",
            "gender": "Male"
        }
    
    @pytest.fixture
    def sample_enduser_response(self, sample_enduser_data):
        """Sample API response for created enduser"""
        return {
            **sample_enduser_data,
            "id": "test_enduser_id_123",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
            "businessId": "test_business_id"
        }
    
    def test_initialization(self):
        """Test TellescopeAPI initialization"""
        import os
        
        # Test with explicit credentials
        api = TellescopeAPI(api_key="test_key", api_url="https://test.com")
        assert api.api_key == "test_key"
        assert api.api_url == "https://test.com"
        assert api.headers["Authorization"] == "API_KEY test_key"
        
        # Test with environment variables (default behavior)
        api_env = TellescopeAPI()
        assert api_env.api_key == os.getenv("TELLESCOPE_API_KEY")
        assert api_env.api_url == os.getenv("TELLESCOPE_API_URL")
        
        # Test missing API key by temporarily clearing env var
        original_key = os.environ.get("TELLESCOPE_API_KEY")
        os.environ.pop("TELLESCOPE_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="API key is required"):
                TellescopeAPI()
        finally:
            if original_key:
                os.environ["TELLESCOPE_API_KEY"] = original_key
    
    def test_get_singular_resource_name(self, api_client):
        """Test resource name conversion from plural to singular"""
        # Test standard cases
        assert api_client._get_singular_resource_name("endusers") == "enduser"
        assert api_client._get_singular_resource_name("emails") == "email"
        assert api_client._get_singular_resource_name("tickets") == "ticket"
        
        # Test special cases
        assert api_client._get_singular_resource_name("sms-messages") == "sms-message"
        assert api_client._get_singular_resource_name("calendar-events") == "calendar-event"
        assert api_client._get_singular_resource_name("form-responses") == "form-response"
        
        # Test already singular
        assert api_client._get_singular_resource_name("enduser") == "enduser"
    
    @patch('requests.request')
    def test_create_enduser(self, mock_request, api_client, sample_enduser_data, sample_enduser_response):
        """Test creating an enduser"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_enduser_response
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test create operation
        result = api_client.create("enduser", sample_enduser_data)
        
        # Verify request was made correctly
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/enduser"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        
        mock_request.assert_called_once_with(
            "POST",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            },
            json=sample_enduser_data
        )
        
        # Verify response
        assert result == sample_enduser_response
        assert result["id"] == "test_enduser_id_123"
        assert result["email"] == "test@example.com"
    
    @patch('requests.request')
    def test_read_enduser(self, mock_request, api_client, sample_enduser_response):
        """Test reading an enduser by ID"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_enduser_response
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test read operation
        enduser_id = "test_enduser_id_123"
        result = api_client.read("enduser", enduser_id)
        
        # Verify request was made correctly
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/enduser/{enduser_id}"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        
        mock_request.assert_called_once_with(
            "GET",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            }
        )
        
        # Verify response
        assert result == sample_enduser_response
        assert result["id"] == enduser_id
    
    @patch('requests.request')
    def test_update_enduser(self, mock_request, api_client, sample_enduser_response):
        """Test updating an enduser"""
        # Prepare update data and expected response
        update_data = {"fname": "Jane", "phone": "+9876543210"}
        updated_response = {**sample_enduser_response, **update_data}
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = updated_response
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test update operation
        enduser_id = "test_enduser_id_123"
        result = api_client.update("enduser", enduser_id, update_data)
        
        # Verify request was made correctly
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/enduser/{enduser_id}"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        
        mock_request.assert_called_once_with(
            "PATCH",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            },
            json=update_data
        )
        
        # Verify response
        assert result["fname"] == "Jane"
        assert result["phone"] == "+9876543210"
        assert result["id"] == enduser_id
    
    @patch('requests.request')
    def test_delete_enduser(self, mock_request, api_client):
        """Test deleting an enduser"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test delete operation
        enduser_id = "test_enduser_id_123"
        result = api_client.delete("enduser", enduser_id)
        
        # Verify request was made correctly
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/enduser/{enduser_id}"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        
        mock_request.assert_called_once_with(
            "DELETE",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            }
        )
        
        # Verify response
        assert result is True
    
    @patch('requests.request')
    def test_list_endusers(self, mock_request, api_client, sample_enduser_response):
        """Test listing endusers with and without filters"""
        # Mock successful response
        endusers_list = [sample_enduser_response, {**sample_enduser_response, "id": "another_id"}]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = endusers_list
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test list without filters
        result = api_client.list("endusers")
        
        # Verify request was made correctly
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/endusers"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        
        mock_request.assert_called_with(
            "GET",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            },
            params={}
        )
        
        # Verify response
        assert len(result) == 2
        assert result[0]["id"] == "test_enduser_id_123"
    
    @patch('requests.request')
    def test_list_endusers_with_mongodb_filter(self, mock_request, api_client, sample_enduser_response):
        """Test listing endusers with MongoDB filter"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [sample_enduser_response]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test list with MongoDB filter
        mongodb_filter = {"email": "test@example.com"}
        result = api_client.list("endusers", mongodb_filter=mongodb_filter)
        
        # Verify request was made correctly with mdbFilter
        import os
        expected_url = f"{os.getenv('TELLESCOPE_API_URL')}/endusers"
        expected_auth = f"API_KEY {os.getenv('TELLESCOPE_API_KEY')}"
        expected_params = {"mdbFilter": json.dumps(mongodb_filter)}
        
        mock_request.assert_called_with(
            "GET",
            expected_url,
            headers={
                "Authorization": expected_auth,
                "Content-Type": "application/json"
            },
            params=expected_params
        )
        
        # Verify response
        assert len(result) == 1
        assert result[0]["email"] == "test@example.com"
    
    @patch('requests.request')
    def test_find_by(self, mock_request, api_client, sample_enduser_response):
        """Test finding a single enduser by MongoDB filter"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [sample_enduser_response]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test find_by operation
        mongodb_filter = {"externalId": "canvas_123"}
        result = api_client.find_by("endusers", mongodb_filter)
        
        # Verify response
        assert result == sample_enduser_response
        assert result["id"] == "test_enduser_id_123"
        
        # Test when no results found
        mock_response.json.return_value = []
        result = api_client.find_by("endusers", mongodb_filter)
        assert result is None
    
    @patch('requests.request')
    def test_error_handling(self, mock_request, api_client):
        """Test error handling for various HTTP errors"""
        # Test 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Resource not found"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_request.return_value = mock_response
        
        with pytest.raises(ValueError, match="Resource not found"):
            api_client.read("enduser", "nonexistent_id")
        
        # Test 401 error
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with pytest.raises(PermissionError, match="Invalid API key or insufficient permissions"):
            api_client.read("enduser", "test_id")
        
        # Test 400 error
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with pytest.raises(ValueError, match="Invalid request data"):
            api_client.create("enduser", {"invalid": "data"})
        
        # Test rate limit error
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with pytest.raises(ConnectionError, match="Rate limit exceeded"):
            api_client.read("enduser", "test_id")


class TestEndToEndEnduserCRUD:
    """End-to-end test simulating complete CRUD lifecycle for an Enduser"""
    
    @pytest.fixture
    def api_client(self):
        """Create TellescopeAPI client for end-to-end testing"""
        return TellescopeAPI()  # Uses environment variables from .env
    
    @patch('requests.request')
    def test_complete_enduser_crud_lifecycle(self, mock_request, api_client):
        """Test complete CRUD lifecycle: Create -> Read -> Update -> Delete"""
        
        # Step 1: CREATE
        create_data = {
            "email": "lifecycle@example.com",
            "fname": "Lifecycle",
            "lname": "Test",
            "phone": "+1111111111"
        }
        
        created_enduser = {
            **create_data,
            "id": "lifecycle_test_id",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
        
        # Mock CREATE response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = created_enduser
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Execute CREATE
        result = api_client.create("enduser", create_data)
        assert result["id"] == "lifecycle_test_id"
        assert result["email"] == "lifecycle@example.com"
        enduser_id = result["id"]
        
        # Step 2: READ
        # Mock READ response
        mock_response.json.return_value = created_enduser
        
        # Execute READ
        result = api_client.read("enduser", enduser_id)
        assert result["id"] == enduser_id
        assert result["fname"] == "Lifecycle"
        
        # Step 3: UPDATE
        update_data = {"fname": "Updated", "lname": "Name"}
        updated_enduser = {**created_enduser, **update_data}
        
        # Mock UPDATE response
        mock_response.json.return_value = updated_enduser
        
        # Execute UPDATE
        result = api_client.update("enduser", enduser_id, update_data)
        assert result["fname"] == "Updated"
        assert result["lname"] == "Name"
        assert result["email"] == "lifecycle@example.com"  # Unchanged
        
        # Step 4: DELETE
        # Mock DELETE response
        mock_response.status_code = 200
        mock_response.json.return_value = None
        
        # Execute DELETE
        result = api_client.delete("enduser", enduser_id)
        assert result is True
        
        # Verify all operations were called with correct endpoints
        calls = mock_request.call_args_list
        assert len(calls) == 4
        
        # Verify all operations were called with correct endpoints
        import os
        base_url = os.getenv('TELLESCOPE_API_URL')
        
        # Verify CREATE used singular endpoint
        assert calls[0][0][1] == f"{base_url}/enduser"
        assert calls[0][0][0] == "POST"
        
        # Verify READ used singular endpoint with ID
        assert calls[1][0][1] == f"{base_url}/enduser/{enduser_id}"
        assert calls[1][0][0] == "GET"
        
        # Verify UPDATE used singular endpoint with ID
        assert calls[2][0][1] == f"{base_url}/enduser/{enduser_id}"
        assert calls[2][0][0] == "PATCH"
        
        # Verify DELETE used singular endpoint with ID
        assert calls[3][0][1] == f"{base_url}/enduser/{enduser_id}"
        assert calls[3][0][0] == "DELETE"