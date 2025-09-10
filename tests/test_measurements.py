"""
Measurement API endpoint tests
Tests all operations for measurements including edge cases and data validation
"""
import pytest
import uuid
from tests.utils.test_data import TestDataFactory

class TestMeasurements:
    """Test class for measurement endpoints"""
    
    def test_create_measurement_success(self, api_client, sample_barrel_id):
        """Test: Successful measurement creation with valid data"""
        # Prepare test data
        measurement_data = TestDataFactory.create_valid_measurement_data(sample_barrel_id)
        
        # Execute request
        response = api_client.create_measurement(measurement_data)
        
        # Verify response
        assert response.status_code in [200, 201], f"Expected 200 or 201, got {response.status_code}"
        
        response_data = response.json()
        assert 'id' in response_data, "Response should contain 'id' field"
        assert response_data['barrelId'] == measurement_data['barrelId']
        assert response_data['dirtLevel'] == measurement_data['dirtLevel']
        assert response_data['weight'] == measurement_data['weight']
        
        # Verify UUID format
        measurement_id = response_data['id']
        uuid.UUID(measurement_id)  # Throws exception if invalid UUID
    
    def test_create_measurement_missing_barrel_id(self, api_client):
        """Test: Creating measurement without barrelId"""
        measurement_data = TestDataFactory.create_invalid_measurement_data_missing_barrel_id()
        
        response = api_client.create_measurement(measurement_data)
        
        # API should return error for missing required field
        assert response.status_code == 400, f"Expected 400 for missing barrelId, got {response.status_code}"
    
    def test_create_measurement_invalid_data_types(self, api_client):
        """Test: Creating measurement with invalid data types"""
        measurement_data = TestDataFactory.create_invalid_measurement_data_wrong_types()
        
        response = api_client.create_measurement(measurement_data)
        
        # API should return error for wrong data types
        assert response.status_code == 400, f"Expected 400 for invalid data types, got {response.status_code}"
    
    def test_create_measurement_non_existent_barrel(self, api_client):
        """Test: Creating measurement for non-existent barrel"""
        non_existent_barrel_id = TestDataFactory.generate_non_existent_uuid()
        measurement_data = TestDataFactory.create_valid_measurement_data(non_existent_barrel_id)
        
        response = api_client.create_measurement(measurement_data)
        
        # API should return error for non-existent barrel
        # May return 400 (bad request) or 404 (not found) depending on implementation
        assert response.status_code in [400, 404], f"Expected 400 or 404 for non-existent barrel, got {response.status_code}"
    
    def test_create_measurement_empty_body(self, api_client):
        """Test: Creating measurement with empty request body"""
        response = api_client.create_measurement({})
        
        assert response.status_code == 400, f"Expected 400 for empty body, got {response.status_code}"
    
    def test_get_measurements_list(self, api_client):
        """Test: Getting list of all measurements"""
        response = api_client.get_measurements()
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        measurements = response.json()
        assert isinstance(measurements, list), "Response should be a list"
        
        # If there are any measurements, check structure
        if measurements:
            first_measurement = measurements[0]
            assert 'id' in first_measurement
            assert 'barrelId' in first_measurement
            assert 'dirtLevel' in first_measurement
            assert 'weight' in first_measurement
            
            # Check data types
            assert isinstance(first_measurement['dirtLevel'], (int, float))
            assert isinstance(first_measurement['weight'], (int, float))
    
    def test_get_measurement_by_id_success(self, api_client, sample_barrel_id):
        """Test: Getting detail of existing measurement by ID"""
        # First create measurement
        measurement_data = TestDataFactory.create_valid_measurement_data(sample_barrel_id)
        create_response = api_client.create_measurement(measurement_data)
        assert create_response.status_code in [200, 201]
        
        measurement_id = create_response.json()['id']
        
        # Get measurement detail
        response = api_client.get_measurement(measurement_id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        measurement = response.json()
        assert measurement['id'] == measurement_id
        assert measurement['barrelId'] == sample_barrel_id
        assert 'dirtLevel' in measurement
        assert 'weight' in measurement
    
    def test_get_measurement_by_id_not_found(self, api_client):
        """Test: Getting detail of non-existent measurement"""
        non_existent_id = TestDataFactory.generate_non_existent_uuid()
        
        response = api_client.get_measurement(non_existent_id)
        
        # API may return 404 or 500 for non-existent measurement
        assert response.status_code in [404, 500], f"Expected 404 or 500 for non-existent measurement, got {response.status_code}"
    
    def test_get_measurement_invalid_uuid(self, api_client):
        """Test: Getting measurement with invalid UUID format"""
        invalid_id = TestDataFactory.generate_invalid_uuid()
        
        response = api_client.get_measurement(invalid_id)
        
        # API may return various error codes for invalid UUID
        assert response.status_code in [400, 404, 500], f"Expected 400, 404 or 500 for invalid UUID, got {response.status_code}"