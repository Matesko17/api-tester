"""
Configuration loader for test scenarios
Loads YAML configurations and provides them to tests
"""
import os
import yaml
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Utility class for loading test configurations"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize config loader
        
        Args:
            config_dir: Path to configuration directory
        """
        if config_dir is None:
            # Find config directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            config_dir = os.path.join(project_root, 'config')
            
        self.config_dir = config_dir
        self._configs = {}
        
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Args:
            config_name: Configuration name (without .yaml)
            
        Returns:
            Dictionary with configuration
        """
        if config_name in self._configs:
            return self._configs[config_name]
            
        config_file = os.path.join(self.config_dir, f"{config_name}.yaml")
        
        if not os.path.exists(config_file):
            logger.warning(f"Config file not found: {config_file}")
            return {}
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Cache config
            self._configs[config_name] = config
            
            logger.info(f"Loaded config: {config_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {str(e)}")
            return {}
    
    def get_api_config(self, config_name: str = "default") -> Dict[str, Any]:
        """Get API configuration"""
        config = self.load_config(config_name)
        return config.get('api', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance testing configuration"""
        config = self.load_config('performance')
        return config.get('performance', {})
    
    def get_load_testing_config(self) -> Dict[str, Any]:
        """Get load testing configuration"""
        config = self.load_config('load_testing')
        return config.get('load_testing', {})
        
    def get_ddos_config(self) -> Dict[str, Any]:
        """Get DDOS protection testing configuration"""
        config = self.load_config('load_testing')
        return config.get('ddos_protection', {})
    
    def get_batch_sizes(self) -> list:
        """Get configured batch sizes for testing"""
        perf_config = self.get_performance_config()
        return perf_config.get('batch_sizes', [1, 5, 10])
    
    def get_concurrent_users(self) -> list:
        """Get configured concurrent users for testing"""
        perf_config = self.get_performance_config()
        return perf_config.get('concurrent_users', [1, 3, 5])
    
    def get_test_data_config(self, config_name: str = "default") -> Dict[str, Any]:
        """Get configuration for test data generation"""
        config = self.load_config(config_name)
        return config.get('test_data', {})
    
    def merge_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge configuration with environment variables
        ENV vars have priority over YAML config
        """
        # API URL override
        if os.getenv('API_BASE_URL'):
            if 'api' not in config:
                config['api'] = {}
            config['api']['base_url'] = os.getenv('API_BASE_URL')
            
        # Timeout override
        if os.getenv('API_TIMEOUT'):
            if 'api' not in config:
                config['api'] = {}
            config['api']['timeout'] = int(os.getenv('API_TIMEOUT'))
            
        return config

# Global instance
config_loader = ConfigLoader()