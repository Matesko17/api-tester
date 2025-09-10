"""
API Client for Barrel Monitor API
Provides wrapper for HTTP requests with error handling and logging
"""
import os
import requests
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class BarrelAPIClient:
    """API client for communication with Barrel Monitor API"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialize API client
        
        Args:
            base_url: Base URL for API (default from ENV)
            timeout: Timeout for HTTP requests in seconds
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', 'https://to-barrel-monitor.azurewebsites.net')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                     params: Dict[str, Any] = None) -> requests.Response:
        """
        Provede HTTP request s loggingem a error handlingem
        
        Args:
            method: HTTP metoda (GET, POST, DELETE)
            endpoint: API endpoint (e.g. '/barrels')
            data: Data pro request body
            params: Query parametry
            
        Returns:
            requests.Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        # Log request
        logger.info(f"Making {method} request to {url}")
        if data:
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        if params:
            logger.debug(f"Request params: {params}")
            
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Log response
            logger.info(f"Response status: {response.status_code}")
            if response.text:
                logger.debug(f"Response body: {response.text}")
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    # Barrel endpoints
    def create_barrel(self, barrel_data: Dict[str, str]) -> requests.Response:
        """Creates new barrel"""
        return self._make_request('POST', '/barrels', data=barrel_data)
    
    def get_barrels(self) -> requests.Response:
        """Gets list of all barrels"""
        return self._make_request('GET', '/barrels')
    
    def get_barrel(self, barrel_id: str) -> requests.Response:
        """Gets detail of specific barrel"""
        return self._make_request('GET', f'/barrels/{barrel_id}')
    
    def delete_barrel(self, barrel_id: str) -> requests.Response:
        """Deletes barrel"""
        return self._make_request('DELETE', f'/barrels/{barrel_id}')
    
    # Measurement endpoints
    def create_measurement(self, measurement_data: Dict[str, Any]) -> requests.Response:
        """Creates new measurement"""
        return self._make_request('POST', '/measurements', data=measurement_data)
    
    def get_measurements(self) -> requests.Response:
        """Gets list of all measurements"""
        return self._make_request('GET', '/measurements')
    
    def get_measurement(self, measurement_id: str) -> requests.Response:
        """Gets detail of specific measurement"""
        return self._make_request('GET', f'/measurements/{measurement_id}')