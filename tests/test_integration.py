"""
Integration tests for Barrel Monitor API
Tests complex workflows and interactions between different endpoints
"""
import pytest
from tests.utils.test_data import TestDataFactory

class TestIntegration:
    """Integration tests for end-to-end workflows"""
    
    def test_complete_barrel_lifecycle(self, api_client):
        """
        Test: Complete barrel lifecycle
        1. Create barrel
        2. Add measurement
        3. Get data
        4. Delete barrel
        """
        # 1. Create barrel
        barrel_data = TestDataFactory.create_valid_barrel_data()
        barrel_response = api_client.create_barrel(barrel_data)
        assert barrel_response.status_code in [200, 201]
        
        barrel_id = barrel_response.json()['id']
        
        try:
            # 2. Add measurement to barrel
            measurement_data = TestDataFactory.create_valid_measurement_data(barrel_id)
            measurement_response = api_client.create_measurement(measurement_data)
            assert measurement_response.status_code in [200, 201]
            
            measurement_id = measurement_response.json()['id']
            
            # 3. Verify barrel exists in list
            barrels_response = api_client.get_barrels()
            assert barrels_response.status_code == 200
            
            barrels = barrels_response.json()
            barrel_ids = [b['id'] for b in barrels]
            assert barrel_id in barrel_ids, "Created barrel should be in barrels list"
            
            # 4. Verify measurement exists in list
            measurements_response = api_client.get_measurements()
            assert measurements_response.status_code == 200
            
            measurements = measurements_response.json()
            measurement_ids = [m['id'] for m in measurements]
            assert measurement_id in measurement_ids, "Created measurement should be in measurements list"
            
            # 5. Get measurement detail and verify link to barrel
            measurement_detail = api_client.get_measurement(measurement_id)
            assert measurement_detail.status_code == 200
            
            measurement = measurement_detail.json()
            assert measurement['barrelId'] == barrel_id, "Measurement should be linked to correct barrel"
            
        finally:
            # 6. Cleanup - delete barrel
            delete_response = api_client.delete_barrel(barrel_id)
            assert delete_response.status_code in [200, 204]
    
    def test_multiple_measurements_for_single_barrel(self, api_client, sample_barrel_id):
        """
        Test: Multiple measurements for single barrel
        """
        measurement_ids = []
        
        # Create 3 measurements for same barrel
        for i in range(3):
            measurement_data = TestDataFactory.create_valid_measurement_data(sample_barrel_id)
            # Modify values to be different
            measurement_data['dirtLevel'] = 80.0 + i * 5
            measurement_data['weight'] = 150.0 + i * 10
            
            response = api_client.create_measurement(measurement_data)
            assert response.status_code in [200, 201]
            
            measurement_ids.append(response.json()['id'])
        
        # Verify all measurements exist
        measurements_response = api_client.get_measurements()
        assert measurements_response.status_code == 200
        
        all_measurements = measurements_response.json()
        barrel_measurements = [m for m in all_measurements if m['barrelId'] == sample_barrel_id]
        
        # Should exist at least 3 measurements for our barrel
        assert len(barrel_measurements) >= 3, f"Expected at least 3 measurements for barrel {sample_barrel_id}"
        
        # Verify our measurements are in the list
        all_measurement_ids = [m['id'] for m in all_measurements]
        for measurement_id in measurement_ids:
            assert measurement_id in all_measurement_ids, f"Measurement {measurement_id} should exist"
    
    def test_barrel_deletion_impact_on_measurements(self, api_client):
        """
        Test: Impact of barrel deletion on related measurements
        Tests what happens to measurements when we delete a barrel
        """
        # Create barrel
        barrel_data = TestDataFactory.create_valid_barrel_data()
        barrel_response = api_client.create_barrel(barrel_data)
        assert barrel_response.status_code in [200, 201]
        
        barrel_id = barrel_response.json()['id']
        
        # Create measurement for barrel
        measurement_data = TestDataFactory.create_valid_measurement_data(barrel_id)
        measurement_response = api_client.create_measurement(measurement_data)
        assert measurement_response.status_code == 200
        
        measurement_id = measurement_response.json()['id']
        
        # Delete barrel
        delete_response = api_client.delete_barrel(barrel_id)
        assert delete_response.status_code in [200, 204]
        
        # Verify barrel no longer exists
        barrel_check = api_client.get_barrel(barrel_id)
        assert barrel_check.status_code == 404
        
        # Check what happened to measurement
        measurement_check = api_client.get_measurement(measurement_id)
        # Measurement may still exist (depends on API implementation)
        # Document behavior for future reference
        if measurement_check.status_code == 200:
            # Measurement still exists - soft delete or orphaned measurement
            print(f"Measurement {measurement_id} still exists after barrel deletion")
        elif measurement_check.status_code == 404:
            # Measurement was deleted with barrel - cascade delete
            print(f"Measurement {measurement_id} was deleted with barrel")
        else:
            # Unexpected status code
            pytest.fail(f"Unexpected status code {measurement_check.status_code} for measurement after barrel deletion")
    
    def test_data_consistency_after_operations(self, api_client):
        """
        Test: Data consistency after series of operations
        """
        created_barrels = []
        created_measurements = []
        
        try:
            # Create several barrels
            for i in range(2):
                barrel_data = TestDataFactory.create_valid_barrel_data()
                response = api_client.create_barrel(barrel_data)
                assert response.status_code in [200, 201]
                
                barrel_id = response.json()['id']
                created_barrels.append(barrel_id)
                
                # Create measurement for each barrel
                measurement_data = TestDataFactory.create_valid_measurement_data(barrel_id)
                measurement_response = api_client.create_measurement(measurement_data)
                assert measurement_response.status_code in [200, 201]
                
                created_measurements.append(measurement_response.json()['id'])
            
            # Verify data consistency
            barrels_response = api_client.get_barrels()
            assert barrels_response.status_code == 200
            
            measurements_response = api_client.get_measurements()
            assert measurements_response.status_code == 200
            
            all_barrels = barrels_response.json()
            all_measurements = measurements_response.json()
            
            # All our barrels should be in the list
            barrel_ids = [b['id'] for b in all_barrels]
            for barrel_id in created_barrels:
                assert barrel_id in barrel_ids, f"Barrel {barrel_id} should be in list"
            
            # All our measurements should be in the list
            measurement_ids = [m['id'] for m in all_measurements]
            for measurement_id in created_measurements:
                assert measurement_id in measurement_ids, f"Measurement {measurement_id} should be in list"
            
            # Check relationships between barrels and measurements
            for measurement in all_measurements:
                if measurement['id'] in created_measurements:
                    assert measurement['barrelId'] in created_barrels, f"Measurement should be linked to valid barrel"
                    
        finally:
            # Cleanup all created barrels
            for barrel_id in created_barrels:
                try:
                    api_client.delete_barrel(barrel_id)
                except Exception as e:
                    print(f"Failed to cleanup barrel {barrel_id}: {e}")