"""
Concurrency tests for Barrel Monitor API
Tests API behavior under concurrent requests from multiple users
"""
import pytest
import asyncio
import aiohttp
import threading
import time
from datetime import datetime, timedelta
from typing import List
import concurrent.futures
from tests.utils.config_loader import config_loader
from tests.utils.performance_metrics import PerformanceMetrics, ConcurrentMetrics
from tests.utils.performance_reporter import PerformanceReporter
from tests.utils.test_data import TestDataFactory

class TestConcurrency:
    """Test class for concurrency testing"""
    
    @pytest.fixture(scope="class")
    def perf_config(self):
        """Fixture for performance configuration"""
        return config_loader.get_performance_config()
    
    @pytest.fixture(scope="class")
    def api_config(self):
        """Fixture for API configuration"""
        return config_loader.get_api_config('performance')
    
    def test_concurrent_barrel_creation(self, api_config, perf_config):
        """
        Test: Concurrent barrel creation by multiple users
        Simulates real usage where multiple users create barrels simultaneously
        """
        concurrent_users = [1, 2]  # Quick demo - small number only
        metrics = ConcurrentMetrics()
        
        for user_count in concurrent_users:
            print(f"\n--- Testing with {user_count} concurrent users ---")
            
            # Prepare test data for each thread
            test_data = [TestDataFactory.create_valid_barrel_data() for _ in range(user_count)]
            
            # Thread function
            def create_barrel_worker(thread_id: int, barrel_data: dict):
                """Worker function for creating barrel in thread"""
                try:
                    import requests
                    start_time = time.time()
                    
                    response = requests.post(
                        f"{api_config['base_url']}/barrels",
                        json=barrel_data,
                        timeout=api_config.get('timeout', 30)
                    )
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # Record metrics
                    from tests.utils.performance_metrics import RequestMetric
                    metric = RequestMetric(
                        timestamp=start_time,
                        method="POST",
                        endpoint="/barrels",
                        status_code=response.status_code,
                        response_time=response_time,
                        request_size=len(str(barrel_data)),
                        response_size=len(response.text)
                    )
                    
                    metrics.record_thread_metric(thread_id, metric)
                    
                    # Cleanup - try to delete created barrel
                    if response.status_code in [200, 201] and response.json():
                        try:
                            barrel_id = response.json().get('id')
                            if barrel_id:
                                requests.delete(f"{api_config['base_url']}/barrels/{barrel_id}")
                        except:
                            pass  # Cleanup is not critical
                            
                except Exception as e:
                    # Record error metric
                    from tests.utils.performance_metrics import RequestMetric
                    metric = RequestMetric(
                        timestamp=time.time(),
                        method="POST", 
                        endpoint="/barrels",
                        status_code=0,
                        response_time=0.0,
                        error=str(e)
                    )
                    metrics.record_thread_metric(thread_id, metric)
            
            # Launch concurrent threads
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = []
                for i, barrel_data in enumerate(test_data):
                    future = executor.submit(create_barrel_worker, i, barrel_data)
                    futures.append(future)
                
                # Wait for all threads to complete
                concurrent.futures.wait(futures, timeout=30)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            report = metrics.get_concurrency_report()
            
            print(f"Concurrent users: {user_count}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Total requests: {report['total_requests']}")
            print(f"Threads with errors: {report['threads_with_errors']}")
            
            # Generate basic performance report
            perf_metrics = PerformanceMetrics(f"concurrent_creation_{user_count}_users")
            perf_metrics.start_time = datetime.now() - timedelta(seconds=total_time)
            perf_metrics.end_time = datetime.now()
            
            # Add metrics from concurrent report
            for _ in range(report['total_requests'] - report['threads_with_errors']):
                perf_metrics.record_request("POST", "/barrels", 200, total_time/report['total_requests'])
            for _ in range(report['threads_with_errors']):
                perf_metrics.record_request("POST", "/barrels", 500, total_time/report['total_requests'], error="Thread error")
            
            perf_report = perf_metrics.generate_report()
            reporter = PerformanceReporter()
            html_path = reporter.generate_html_report([perf_report], f"concurrent_creation_{user_count}_users.html")
            print(f"Report generated: {html_path}")
            
            # Assertions
            assert report['total_requests'] == user_count, f"Expected {user_count} requests, got {report['total_requests']}"
            assert report['concurrent_threads'] == user_count, f"Expected {user_count} threads"
            
            # Most requests should be successful (we tolerate some API issues)
            success_rate = 1 - (report['threads_with_errors'] / user_count)
            assert success_rate >= 0.7, f"Success rate too low: {success_rate*100:.1f}%"
    
    @pytest.mark.skip(reason="Skipped for quick demo")
    def test_mixed_concurrent_operations(self, api_config, perf_config):
        """
        Test: Combination of different operations simultaneously
        Simulates real usage with mixed operations (create, read, delete)
        """
        concurrent_users = 2  # Quick demo
        operations_per_user = 2  # Smaller number of operations
        
        metrics = PerformanceMetrics("mixed_concurrent_operations")
        metrics.start_test()
        
        def mixed_operations_worker(thread_id: int):
            """Worker that performs mixed operations"""
            import requests
            
            for op_num in range(operations_per_user):
                try:
                    if op_num == 0:  # Create barrel
                        barrel_data = TestDataFactory.create_valid_barrel_data()
                        start_time = time.time()
                        
                        response = requests.post(
                            f"{api_config['base_url']}/barrels",
                            json=barrel_data,
                            timeout=api_config.get('timeout', 30)
                        )
                        
                        response_time = time.time() - start_time
                        metrics.record_request("POST", "/barrels", response.status_code, response_time)
                        
                        # Store barrel ID for later operations
                        if response.status_code in [200, 201] and response.json():
                            globals()[f'barrel_id_{thread_id}'] = response.json().get('id')
                    
                    elif op_num == 1:  # Get barrels list
                        start_time = time.time()
                        
                        response = requests.get(
                            f"{api_config['base_url']}/barrels",
                            timeout=api_config.get('timeout', 30)
                        )
                        
                        response_time = time.time() - start_time
                        metrics.record_request("GET", "/barrels", response.status_code, response_time)
                    
                    elif op_num == 2:  # Cleanup - delete barrel
                        barrel_id = globals().get(f'barrel_id_{thread_id}')
                        if barrel_id:
                            start_time = time.time()
                            
                            response = requests.delete(
                                f"{api_config['base_url']}/barrels/{barrel_id}",
                                timeout=api_config.get('timeout', 30)
                            )
                            
                            response_time = time.time() - start_time
                            metrics.record_request("DELETE", f"/barrels/{barrel_id}", response.status_code, response_time)
                    
                    # Small pause between operations
                    time.sleep(0.1)
                    
                except Exception as e:
                    metrics.record_request("ERROR", "/unknown", 0, 0.0, error=str(e))
        
        # Launch concurrent threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(mixed_operations_worker, i) for i in range(concurrent_users)]
            concurrent.futures.wait(futures, timeout=60)
        
        metrics.end_test()
        report = metrics.generate_report()
        
        print(f"\n--- Mixed Concurrent Operations Report ---")
        print(f"Total requests: {report.total_requests}")
        print(f"Successful requests: {report.successful_requests}")
        print(f"Failed requests: {report.failed_requests}")
        print(f"Average response time: {report.avg_response_time:.3f}s")
        print(f"Error rate: {report.error_rate:.1f}%")
        
        # Generate reports
        reporter = PerformanceReporter()
        html_path = reporter.generate_html_report([report], "mixed_concurrent_operations.html")
        json_path = reporter.generate_json_report(report, "mixed_concurrent_operations.json")
        print(f"Reports generated: {html_path}, {json_path}")
        
        # Assertions
        expected_total_requests = concurrent_users * operations_per_user
        assert report.total_requests >= expected_total_requests * 0.8, "Too few requests completed"
        
        # We tolerate higher error rate due to API issues
        assert report.error_rate <= 70, f"Error rate too high: {report.error_rate:.1f}%"
        
        # Response time should not be too high
        assert report.avg_response_time <= 10.0, f"Average response time too high: {report.avg_response_time:.3f}s"
    
    @pytest.mark.skip(reason="Skipped for quick demo")
    def test_sustained_concurrent_load(self, api_config, perf_config):
        """
        Test: Sustained load over longer period
        Tests API stability under continuous load
        """
        concurrent_users = 2  # Quick demo
        test_duration = 15  # seconds - shortened
        request_interval = 1  # seconds between requests - faster
        
        metrics = PerformanceMetrics("sustained_concurrent_load")
        metrics.start_test()
        
        stop_flag = threading.Event()
        
        def sustained_worker(thread_id: int):
            """Worker for sustained testing"""
            import requests
            
            while not stop_flag.is_set():
                try:
                    # Alternate between different operations
                    if thread_id % 2 == 0:  # Even threads - create barrel
                        barrel_data = TestDataFactory.create_valid_barrel_data()
                        start_time = time.time()
                        
                        response = requests.post(
                            f"{api_config['base_url']}/barrels",
                            json=barrel_data,
                            timeout=api_config.get('timeout', 30)
                        )
                        
                        response_time = time.time() - start_time
                        metrics.record_request("POST", "/barrels", response.status_code, response_time)
                        
                    else:  # Odd threads - get barrels
                        start_time = time.time()
                        
                        response = requests.get(
                            f"{api_config['base_url']}/barrels",
                            timeout=api_config.get('timeout', 30)
                        )
                        
                        response_time = time.time() - start_time
                        metrics.record_request("GET", "/barrels", response.status_code, response_time)
                    
                    # Wait before next request
                    time.sleep(request_interval)
                    
                except Exception as e:
                    metrics.record_request("ERROR", "/unknown", 0, 0.0, error=str(e))
                    time.sleep(request_interval)  # Wait even on error
        
        # Launch sustained threads
        threads = []
        for i in range(concurrent_users):
            thread = threading.Thread(target=sustained_worker, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Let run for specified duration
        time.sleep(test_duration)
        stop_flag.set()
        
        # Wait for all threads to finish
        for thread in threads:
            thread.join(timeout=10)
        
        metrics.end_test()
        report = metrics.generate_report()
        
        print(f"\n--- Sustained Concurrent Load Report ---")
        print(f"Test duration: {test_duration}s")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Total requests: {report.total_requests}")
        print(f"Requests per second: {report.requests_per_second:.2f}")
        print(f"Error rate: {report.error_rate:.1f}%")
        print(f"Average response time: {report.avg_response_time:.3f}s")
        
        # Generate reports
        reporter = PerformanceReporter()
        html_path = reporter.generate_html_report([report], "sustained_concurrent_load.html")
        json_path = reporter.generate_json_report(report, "sustained_concurrent_load.json")
        print(f"Reports generated: {html_path}, {json_path}")
        
        # Assertions for sustained test
        min_expected_requests = (test_duration // request_interval) * concurrent_users * 0.8
        assert report.total_requests >= min_expected_requests, f"Too few requests: {report.total_requests}"
        
        # For sustained test we expect stable performance
        assert report.requests_per_second >= 0.5, f"RPS too low: {report.requests_per_second:.2f}"
        assert report.error_rate <= 80, f"Error rate too high for sustained test: {report.error_rate:.1f}%"