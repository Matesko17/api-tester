"""
Barrel API endpoint tests
Tests all CRUD operations for barrels including edge cases
"""
import pytest
import uuid
from tests.utils.test_data import TestDataFactory

class TestBarrels:
    """Test class for barrel endpoints"""
    
    def test_create_barrel_success(self, api_client, cleanup_barrels):
        """Test: Successful barrel creation with valid data"""
        # Prepare test data
        barrel_data = TestDataFactory.create_valid_barrel_data()
        
        # Execute request
        response = api_client.create_barrel(barrel_data)
        
        # Verify response
        assert response.status_code in [200, 201], f"Expected 200 or 201, got {response.status_code}"
        
        response_data = response.json()
        assert 'id' in response_data, "Response should contain 'id' field"
        assert response_data['qr'] == barrel_data['qr']
        assert response_data['rfid'] == barrel_data['rfid'] 
        assert response_data['nfc'] == barrel_data['nfc']
        
        # Verify UUID format
        barrel_id = response_data['id']
        uuid.UUID(barrel_id)  # Throws exception if invalid UUID
        
        # Cleanup
        cleanup_barrels(barrel_id)
    
    def test_create_barrel_missing_required_field(self, api_client):
        """Test: Creating barrel with missing required field (qr)"""
        barrel_data = TestDataFactory.create_invalid_barrel_data_missing_qr()
        
        response = api_client.create_barrel(barrel_data)
        
        # API should return error for missing required field
        assert response.status_code == 400, f"Expected 400 for missing required field, got {response.status_code}"
    
    def test_create_barrel_empty_strings(self, api_client):
        """Test: Creating barrel with empty strings"""
        barrel_data = TestDataFactory.create_invalid_barrel_data_empty_strings()
        
        response = api_client.create_barrel(barrel_data)
        
        # API should return error for empty strings (minLength: 1)
        assert response.status_code == 400, f"Expected 400 for empty strings, got {response.status_code}"
    
    def test_create_barrel_empty_body(self, api_client):
        """Test: Creating barrel with empty request body"""
        response = api_client.create_barrel({})
        
        assert response.status_code == 400, f"Expected 400 for empty body, got {response.status_code}"
    
    def test_get_barrels_list(self, api_client):
        """Test: Getting list of all barrels"""
        response = api_client.get_barrels()
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        barrels = response.json()
        assert isinstance(barrels, list), "Response should be a list"
        
        # If there are any barrels, check structure
        if barrels:
            first_barrel = barrels[0]
            assert 'id' in first_barrel
            assert 'qr' in first_barrel
            assert 'rfid' in first_barrel
            assert 'nfc' in first_barrel
    
    def test_get_barrel_by_id_success(self, api_client, sample_barrel_id):
        """Test: Getting detail of existing barrel by ID"""
        response = api_client.get_barrel(sample_barrel_id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        barrel = response.json()
        assert barrel['id'] == sample_barrel_id
        assert 'qr' in barrel
        assert 'rfid' in barrel
        assert 'nfc' in barrel
    
    def test_get_barrel_by_id_not_found(self, api_client):
        """Test: Getting detail of non-existent barrel"""
        non_existent_id = TestDataFactory.generate_non_existent_uuid()
        
        response = api_client.get_barrel(non_existent_id)
        
        # API may return 404 or 500 for non-existent barrel  
        assert response.status_code in [404, 500], f"Expected 404 or 500 for non-existent barrel, got {response.status_code}"
    
    def test_get_barrel_invalid_uuid(self, api_client):
        """Test: Getting barrel with invalid UUID format"""
        invalid_id = TestDataFactory.generate_invalid_uuid()
        
        response = api_client.get_barrel(invalid_id)
        
        # API may return various error codes for invalid UUID
        assert response.status_code in [400, 404, 500], f"Expected 400, 404 or 500 for invalid UUID, got {response.status_code}"
    
    def test_delete_barrel_success(self, api_client, sample_barrel_id):
        """Test: Successful deletion of existing barrel"""
        response = api_client.delete_barrel(sample_barrel_id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify that barrel was actually deleted
        get_response = api_client.get_barrel(sample_barrel_id)
        assert get_response.status_code == 404, "Barrel should not exist after deletion"
    
    def test_delete_barrel_not_found(self, api_client):
        """Test: Deleting non-existent barrel"""
        non_existent_id = TestDataFactory.generate_non_existent_uuid()
        
        response = api_client.delete_barrel(non_existent_id)
        
        # API may return 404 or 500 for non-existent barrel  
        assert response.status_code in [404, 500], f"Expected 404 or 500 for non-existent barrel, got {response.status_code}"