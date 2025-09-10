"""
Test data and factory methods for generating test objects
"""
import uuid
from typing import Dict, Any

class TestDataFactory:
    """Factory class for generating test data"""
    
    @staticmethod
    def create_valid_barrel_data() -> Dict[str, str]:
        """Create valid data for barrel"""
        unique_id = str(uuid.uuid4())[:8]  # Short unique identifier
        return {
            "qr": f"QR-{unique_id}",
            "rfid": f"RFID-{unique_id}", 
            "nfc": f"NFC-{unique_id}"
        }
    
    @staticmethod
    def create_valid_measurement_data(barrel_id: str) -> Dict[str, Any]:
        """Create valid data for measurement"""
        return {
            "barrelId": barrel_id,
            "dirtLevel": 85.5,
            "weight": 150.75
        }
    
    @staticmethod
    def create_invalid_barrel_data_missing_qr() -> Dict[str, str]:
        """Create invalid data for barrel - missing QR"""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "rfid": f"RFID-{unique_id}",
            "nfc": f"NFC-{unique_id}"
        }
    
    @staticmethod
    def create_invalid_barrel_data_empty_strings() -> Dict[str, str]:
        """Create invalid data for barrel - empty strings"""
        return {
            "qr": "",
            "rfid": "",
            "nfc": ""
        }
    
    @staticmethod
    def create_invalid_measurement_data_missing_barrel_id() -> Dict[str, Any]:
        """Create invalid data for measurement - missing barrel ID"""
        return {
            "dirtLevel": 85.5,
            "weight": 150.75
        }
    
    @staticmethod
    def create_invalid_measurement_data_wrong_types() -> Dict[str, Any]:
        """Create invalid data for measurement - wrong data types"""
        return {
            "barrelId": str(uuid.uuid4()),
            "dirtLevel": "not_a_number",
            "weight": "also_not_a_number"
        }
    
    @staticmethod
    def generate_invalid_uuid() -> str:
        """Generate invalid UUID"""
        return "not-a-valid-uuid"
    
    @staticmethod
    def generate_non_existent_uuid() -> str:
        """Generate UUID that doesn't exist in the system"""
        return str(uuid.uuid4())