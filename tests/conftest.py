"""
Pytest konfigurace a fixtures pro testy
"""
import pytest
import logging
import os
from typing import List
from tests.utils.api_client import BarrelAPIClient

# Konfigurace loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def api_client():
    """
    Session-wide API client fixture
    """
    return BarrelAPIClient()

@pytest.fixture(scope="function")
def cleanup_barrels():
    """
    Fixture for cleanup of created barrels after test
    Used to ensure clean state between tests
    """
    created_barrel_ids: List[str] = []
    
    def _add_barrel_for_cleanup(barrel_id: str):
        created_barrel_ids.append(barrel_id)
    
    # Return function to add barrel to cleanup list
    yield _add_barrel_for_cleanup
    
    # Cleanup po testu
    client = BarrelAPIClient()
    for barrel_id in created_barrel_ids:
        try:
            response = client.delete_barrel(barrel_id)
            if response.status_code == 200:
                logging.info(f"Cleaned up barrel {barrel_id}")
            else:
                logging.warning(f"Failed to cleanup barrel {barrel_id}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error during cleanup of barrel {barrel_id}: {str(e)}")

@pytest.fixture
def sample_barrel_id(api_client, cleanup_barrels):
    """
    Fixture that creates test barrel and returns its ID
    Automatically deletes it after test
    """
    from tests.utils.test_data import TestDataFactory
    
    barrel_data = TestDataFactory.create_valid_barrel_data()
    response = api_client.create_barrel(barrel_data)
    
    assert response.status_code in [200, 201], f"Failed to create test barrel: {response.status_code}"
    
    barrel_id = response.json()['id']
    cleanup_barrels(barrel_id)
    
    return barrel_id