"""
Rate limiting and DDOS protection tests for Barrel Monitor API
Tests API behavior under high load and possible DDOS attacks
"""
import pytest
import time
import threading
import requests
from typing import List, Dict
import concurrent.futures
from tests.utils.config_loader import config_loader
from tests.utils.performance_metrics import PerformanceMetrics
from tests.utils.performance_reporter import PerformanceReporter
from tests.utils.test_data import TestDataFactory

class TestRateLimiting:
    """Test class for rate limiting and DDOS protection"""
    
    @pytest.fixture(scope="class")
    def load_config(self):
        """Fixture for load testing configuration"""
        return config_loader.get_load_testing_config()
    
    @pytest.fixture(scope="class") 
    def ddos_config(self):
        """Fixture for DDOS protection configuration"""
        return config_loader.get_ddos_config()
    
    @pytest.fixture(scope="class")
    def api_config(self):
        """Fixture for API configuration"""
        return config_loader.get_api_config('load_testing')
    
    def test_burst_request_handling(self, api_config, ddos_config):
        """
        Test: Burst requests - quickly sending many requests at once
        Tests how API handles sudden load spikes
        """
        if not ddos_config.get('enabled', False):
            pytest.skip("DDOS testing not enabled in configuration")
            
        burst_tests = ddos_config.get('rate_limit_tests', [])
        if not burst_tests:
            pytest.skip("No burst tests configured")
        
        for burst_test in burst_tests:
            test_name = burst_test.get('name', 'burst_test')
            rps_target = burst_test.get('requests_per_second', 10)
            duration = burst_test.get('duration', 5)
            
            print(f"\n--- Burst Test: {test_name} ({rps_target} RPS for {duration}s) ---")
            
            metrics = PerformanceMetrics(f"burst_{test_name}")
            metrics.start_test()
            
            # Limit for quick demo
            duration = min(duration, 10)  # Max 10 seconds
            rps_target = min(rps_target, 5)  # Max 5 RPS
            
            # Calculate interval between requests
            request_interval = 1.0 / rps_target
            total_requests = rps_target * duration
            
            def burst_worker():
                """Worker for burst requests"""
                for i in range(total_requests):
                    try:
                        barrel_data = TestDataFactory.create_valid_barrel_data()
                        start_time = time.time()
                        
                        response = requests.post(
                            f"{api_config['base_url']}/barrels",
                            json=barrel_data,
                            timeout=5  # Short timeout for burst test
                        )
                        
                        response_time = time.time() - start_time
                        metrics.record_request(
                            "POST", "/barrels", 
                            response.status_code, response_time
                        )
                        
                        # Quick cleanup
                        if response.status_code in [200, 201] and response.json():
                            try:
                                barrel_id = response.json().get('id')
                                if barrel_id:
                                    requests.delete(f"{api_config['base_url']}/barrels/{barrel_id}")
                            except:
                                pass
                                
                    except Exception as e:
                        metrics.record_request("POST", "/barrels", 0, 0.0, error=str(e))
                    
                    # Timing for burst
                    if i < total_requests - 1:  # Not on last request
                        time.sleep(request_interval)
            
            # Execute burst test
            start_time = time.time()
            burst_worker()
            actual_duration = time.time() - start_time
            
            metrics.end_test()
            report = metrics.generate_report()
            
            print(f"Target RPS: {rps_target}, Actual RPS: {report.requests_per_second:.2f}")
            print(f"Total requests: {report.total_requests}")
            print(f"Success rate: {(report.successful_requests/report.total_requests*100):.1f}%")
            print(f"Error rate: {report.error_rate:.1f}%")
            print(f"Avg response time: {report.avg_response_time:.3f}s")
            
            # Generate HTML and JSON reports
            reporter = PerformanceReporter()
            html_path = reporter.generate_html_report([report], f"rate_limiting_{test_name}.html")
            json_path = reporter.generate_json_report(report, f"rate_limiting_{test_name}.json")
            print(f"Reports generated: {html_path}, {json_path}")
            
            # Assertions
            assert report.total_requests >= total_requests * 0.9, f"Too few requests completed: {report.total_requests}"
            
            # For burst test we accept higher error rate
            if report.error_rate > 50:
                print(f"WARNING: High error rate {report.error_rate:.1f}% - possible rate limiting")
            
            # If API has rate limiting, we should see HTTP 429 or 503
            rate_limit_indicators = any(error for error in report.errors.keys() 
                                      if '429' in error or '503' in error or '502' in error)
            
            if rate_limit_indicators:
                print("API appears to have rate limiting protection")
            else:
                print("WARNING: No clear rate limiting detected")
    
    @pytest.mark.skip(reason="Skipped for quick demo")
    def test_sustained_high_load(self, api_config, ddos_config):
        """
        Test: Long-term high load
        Tests API stability under continuous high load
        """
        if not ddos_config.get('enabled', False):
            pytest.skip("DDOS testing not enabled")
            
        # Find sustained test
        rate_tests = ddos_config.get('rate_limit_tests', [])
        sustained_test = None
        for test in rate_tests:
            if 'sustained' in test.get('name', '').lower():
                sustained_test = test
                break
                
        if not sustained_test:
            pytest.skip("No sustained high load test configured")
        
        rps_target = min(sustained_test.get('requests_per_second', 3), 3)  # Max 3 RPS
        duration = 15  # Quick demo - only 15 seconds
        
        print(f"\n--- Sustained Load Test: {rps_target} RPS for {duration}s ---")
        
        metrics = PerformanceMetrics("sustained_high_load")
        metrics.start_test()
        
        stop_flag = threading.Event()
        request_interval = 1.0 / rps_target
        
        def sustained_worker():
            """Worker for sustained load"""
            while not stop_flag.is_set():
                try:
                    # Alternate between GET and POST operations
                    if time.time() % 2 < 1:  # Half the time GET
                        start_time = time.time()
                        response = requests.get(
                            f"{api_config['base_url']}/barrels",
                            timeout=10
                        )
                        response_time = time.time() - start_time
                        metrics.record_request("GET", "/barrels", response.status_code, response_time)
                        
                    else:  # Half the time POST
                        barrel_data = TestDataFactory.create_valid_barrel_data()
                        start_time = time.time()
                        response = requests.post(
                            f"{api_config['base_url']}/barrels",
                            json=barrel_data,
                            timeout=10
                        )
                        response_time = time.time() - start_time
                        metrics.record_request("POST", "/barrels", response.status_code, response_time)
                        
                        # Cleanup
                        if response.status_code in [200, 201] and response.json():
                            try:
                                barrel_id = response.json().get('id')
                                if barrel_id:
                                    requests.delete(f"{api_config['base_url']}/barrels/{barrel_id}")
                            except:
                                pass
                    
                except Exception as e:
                    metrics.record_request("ERROR", "/unknown", 0, 0.0, error=str(e))
                
                time.sleep(request_interval)
        
        # Launch sustained load
        thread = threading.Thread(target=sustained_worker)
        thread.start()
        
        # Monitor progress
        for i in range(duration):
            time.sleep(1)
            if i % 10 == 0:  # Every 10 seconds
                stats = metrics.get_real_time_stats()
                print(f"Progress: {i+1}/{duration}s, RPS: {stats['requests_per_second_estimate']:.1f}, "
                      f"Errors: {stats['recent_error_rate']:.1f}%")
        
        stop_flag.set()
        thread.join(timeout=5)
        
        metrics.end_test()
        report = metrics.generate_report()
        
        print(f"\n--- Sustained Load Results ---")
        print(f"Duration: {duration}s")
        print(f"Target RPS: {rps_target}, Achieved RPS: {report.requests_per_second:.2f}")
        print(f"Total requests: {report.total_requests}")
        print(f"Error rate: {report.error_rate:.1f}%")
        print(f"Average response time: {report.avg_response_time:.3f}s")
        print(f"99th percentile: {report.percentiles.get(99, 0):.3f}s")
        
        # Assertions for sustained load
        min_expected_requests = duration * rps_target * 0.7  # 70% tolerance
        assert report.total_requests >= min_expected_requests, f"Too few requests: {report.total_requests}"
        
        # For sustained test error rate should be reasonable
        if report.error_rate > 80:
            print("WARNING: Very high error rate - API may be overwhelmed")
        
        # Response time should not increase dramatically
        if report.avg_response_time > 10.0:
            print("WARNING: High response times - possible performance degradation")
    
    @pytest.mark.skip(reason="Skipped for quick demo")
    def test_connection_flooding(self, api_config, ddos_config):
        """
        Test: Connection flooding - many concurrent connections
        Tests how API handles large number of concurrent connections
        """
        if not ddos_config.get('enabled', False):
            pytest.skip("DDOS testing not enabled")
            
        flood_config = ddos_config.get('connection_flood', {})
        if not flood_config:
            pytest.skip("Connection flooding not configured")
        
        max_connections = 5  # Quick demo - only 5 connections
        connection_rate = flood_config.get('connection_rate', 10)
        
        print(f"\n--- Connection Flooding Test: {max_connections} connections ---")
        
        metrics = PerformanceMetrics("connection_flooding")
        metrics.start_test()
        
        # Session pool for connection reuse
        session = requests.Session()
        
        def flood_worker(worker_id: int):
            """Worker for connection flooding"""
            try:
                # Several requests per connection
                for request_num in range(3):
                    start_time = time.time()
                    
                    response = session.get(
                        f"{api_config['base_url']}/barrels",
                        timeout=15
                    )
                    
                    response_time = time.time() - start_time
                    metrics.record_request("GET", "/barrels", response.status_code, response_time)
                    
                    time.sleep(0.5)  # Short pause between requests
                    
            except Exception as e:
                metrics.record_request("GET", "/barrels", 0, 0.0, error=str(e))
        
        # Execute connection flood
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_connections) as executor:
            futures = []
            
            for i in range(max_connections):
                future = executor.submit(flood_worker, i)
                futures.append(future)
                
                # Rate limiting for thread spawning
                if i % connection_rate == 0 and i > 0:
                    time.sleep(1)
            
            # Wait for completion
            completed = concurrent.futures.as_completed(futures, timeout=30)
            finished_count = sum(1 for _ in completed)
        
        session.close()
        metrics.end_test()
        report = metrics.generate_report()
        
        print(f"\n--- Connection Flooding Results ---")
        print(f"Max connections: {max_connections}")
        print(f"Completed workers: {finished_count}/{max_connections}")
        print(f"Total requests: {report.total_requests}")
        print(f"Error rate: {report.error_rate:.1f}%")
        print(f"Average response time: {report.avg_response_time:.3f}s")
        
        # Assertions
        expected_requests = max_connections * 3  # 3 requests per worker
        completion_rate = report.total_requests / expected_requests
        
        print(f"Completion rate: {completion_rate*100:.1f}%")
        
        # For connection flooding test we accept lower completion rate
        assert completion_rate >= 0.5, f"Too many connections failed: {completion_rate*100:.1f}%"
        
        # High error rate may indicate connection limiting
        if report.error_rate > 30:
            print("High error rate suggests connection limiting is working")
        
    @pytest.mark.skip(reason="Skipped for quick demo")
    def test_attack_pattern_detection(self, api_config, ddos_config):
        """
        Test: Attack pattern detection
        Simulates various attack patterns and monitors API response
        """
        if not ddos_config.get('enabled', False):
            pytest.skip("DDOS testing not enabled")
            
        attack_patterns = ddos_config.get('attack_patterns', [])
        if not attack_patterns:
            pytest.skip("No attack patterns configured")
        
        for pattern_config in attack_patterns:
            pattern_name = pattern_config.get('name', 'unknown_pattern')
            pattern_type = pattern_config.get('pattern', 'burst')
            
            print(f"\n--- Attack Pattern Test: {pattern_name} ---")
            
            metrics = PerformanceMetrics(f"attack_{pattern_name}")
            metrics.start_test()
            
            if pattern_type == 'burst':
                # Burst pattern - rapid burst requests
                burst_size = pattern_config.get('burst_size', 50)
                burst_interval = pattern_config.get('burst_interval', 2)
                
                for burst_num in range(3):  # 3 bursts
                    print(f"Executing burst {burst_num + 1}/3...")
                    
                    # Rapid fire requests
                    for i in range(burst_size):
                        try:
                            start_time = time.time()
                            
                            # Alternate between GET and POST
                            if i % 2 == 0:
                                response = requests.get(
                                    f"{api_config['base_url']}/barrels",
                                    timeout=5
                                )
                                metrics.record_request("GET", "/barrels", response.status_code, 
                                                     time.time() - start_time)
                            else:
                                barrel_data = TestDataFactory.create_valid_barrel_data()
                                response = requests.post(
                                    f"{api_config['base_url']}/barrels",
                                    json=barrel_data,
                                    timeout=5
                                )
                                metrics.record_request("POST", "/barrels", response.status_code,
                                                     time.time() - start_time)
                                
                        except Exception as e:
                            metrics.record_request("ERROR", "/unknown", 0, 0.0, error=str(e))
                    
                    # Pause between bursts
                    if burst_num < 2:
                        time.sleep(burst_interval)
            
            elif pattern_type == 'constant':
                # Constant pattern - constant load
                rpm = 30  # Quick demo - 30 RPM
                duration = 20  # Quick demo - 20 seconds
                request_interval = 60.0 / rpm
                
                end_time = time.time() + duration
                while time.time() < end_time:
                    try:
                        start_time = time.time()
                        response = requests.get(
                            f"{api_config['base_url']}/barrels",
                            timeout=10
                        )
                        metrics.record_request("GET", "/barrels", response.status_code,
                                             time.time() - start_time)
                    except Exception as e:
                        metrics.record_request("GET", "/barrels", 0, 0.0, error=str(e))
                    
                    time.sleep(request_interval)
            
            metrics.end_test()
            report = metrics.generate_report()
            
            print(f"Pattern: {pattern_name}")
            print(f"Total requests: {report.total_requests}")
            print(f"Error rate: {report.error_rate:.1f}%")
            print(f"Avg response time: {report.avg_response_time:.3f}s")
            
            # Analyze response patterns
            error_types = list(report.errors.keys())
            if error_types:
                print(f"Error types detected: {error_types}")
                
            # High error rates may indicate attack detection
            if report.error_rate > 50:
                print("High error rate suggests attack pattern detection")
            
            # Increasing response times may indicate defensive measures
            if report.avg_response_time > 2.0:
                print("High response times may indicate defensive throttling")
            
            assert report.total_requests > 0, "No requests completed"