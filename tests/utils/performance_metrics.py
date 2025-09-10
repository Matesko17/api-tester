"""
Performance metrics collector for API testing
Collects and analyzes performance data
"""
import time
import statistics
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class RequestMetric:
    """Individual HTTP request metric"""
    timestamp: float
    method: str
    endpoint: str
    status_code: int
    response_time: float  # sekundy
    request_size: int = 0
    response_size: int = 0
    error: Optional[str] = None

@dataclass 
class PerformanceReport:
    """Performance report for test suite"""
    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    percentiles: Dict[int, float] = field(default_factory=dict)
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    errors: Dict[str, int] = field(default_factory=dict)

class PerformanceMetrics:
    """Collector pro performance metriky"""
    
    def __init__(self, test_name: str):
        """
        Initialize performance metrics collector
        
        Args:
            test_name: Name of test scenario
        """
        self.test_name = test_name
        self.metrics: List[RequestMetric] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.lock = threading.Lock()
        
    def start_test(self):
        """Start performance test measurement"""
        self.start_time = datetime.now()
        self.metrics.clear()
        logger.info(f"Started performance monitoring for: {self.test_name}")
        
    def end_test(self):
        """End performance test measurement"""
        self.end_time = datetime.now()
        logger.info(f"Ended performance monitoring for: {self.test_name}")
        
    def record_request(self, method: str, endpoint: str, status_code: int, 
                      response_time: float, request_size: int = 0,
                      response_size: int = 0, error: str = None):
        """
        Record metric for HTTP request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            status_code: HTTP status code
            response_time: Response time in seconds
            request_size: Request size in bytes
            response_size: Response size in bytes
            error: Error message if error occurred
        """
        metric = RequestMetric(
            timestamp=time.time(),
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            error=error
        )
        
        with self.lock:
            self.metrics.append(metric)
            
    def generate_report(self) -> PerformanceReport:
        """
        Generate performance report from collected metrics
        
        Returns:
            PerformanceReport with analyzed data
        """
        if not self.metrics or not self.start_time or not self.end_time:
            logger.warning("Insufficient data for performance report")
            return PerformanceReport(
                test_name=self.test_name,
                start_time=self.start_time or datetime.now(),
                end_time=self.end_time or datetime.now(),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0
            )
            
        # Basic statistics
        response_times = [m.response_time for m in self.metrics]
        successful_requests = len([m for m in self.metrics if 200 <= m.status_code < 300])
        failed_requests = len(self.metrics) - successful_requests
        
        # Time calculations
        duration = (self.end_time - self.start_time).total_seconds()
        rps = len(self.metrics) / duration if duration > 0 else 0
        
        # Percentiles
        percentiles = {}
        if response_times:
            percentiles = {
                50: statistics.quantiles(response_times, n=2)[0],  # median
                90: statistics.quantiles(response_times, n=10)[8],  # 90th percentile
                95: statistics.quantiles(response_times, n=20)[18], # 95th percentile
                99: statistics.quantiles(response_times, n=100)[98] # 99th percentile
            }
            
        # Error analysis
        errors = {}
        for metric in self.metrics:
            if metric.error:
                errors[metric.error] = errors.get(metric.error, 0) + 1
            elif metric.status_code >= 400:
                error_key = f"HTTP_{metric.status_code}"
                errors[error_key] = errors.get(error_key, 0) + 1
                
        return PerformanceReport(
            test_name=self.test_name,
            start_time=self.start_time,
            end_time=self.end_time,
            total_requests=len(self.metrics),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            percentiles=percentiles,
            requests_per_second=rps,
            error_rate=(failed_requests / len(self.metrics) * 100) if self.metrics else 0,
            errors=errors
        )
        
    def get_real_time_stats(self) -> Dict[str, Any]:
        """
        Return real-time statistics during test execution
        
        Returns:
            Dictionary with current statistics
        """
        with self.lock:
            if not self.metrics:
                return {"total_requests": 0, "avg_response_time": 0, "error_rate": 0}
                
            recent_metrics = self.metrics[-100:]  # Last 100 requests
            response_times = [m.response_time for m in recent_metrics]
            successful = len([m for m in recent_metrics if 200 <= m.status_code < 300])
            
            return {
                "total_requests": len(self.metrics),
                "recent_avg_response_time": statistics.mean(response_times) if response_times else 0,
                "recent_error_rate": ((len(recent_metrics) - successful) / len(recent_metrics) * 100) if recent_metrics else 0,
                "requests_per_second_estimate": self._calculate_current_rps()
            }
            
    def _calculate_current_rps(self) -> float:
        """Calculate current RPS based on recent requests"""
        if len(self.metrics) < 2:
            return 0.0
            
        # Take last 10 requests to estimate RPS
        recent = self.metrics[-10:]
        if len(recent) < 2:
            return 0.0
            
        time_span = recent[-1].timestamp - recent[0].timestamp
        if time_span <= 0:
            return 0.0
            
        return (len(recent) - 1) / time_span

class ConcurrentMetrics:
    """Metrics collector for concurrent testing"""
    
    def __init__(self):
        self.thread_metrics: Dict[int, List[RequestMetric]] = {}
        self.lock = threading.Lock()
        
    def record_thread_metric(self, thread_id: int, metric: RequestMetric):
        """Record metric for specific thread"""
        with self.lock:
            if thread_id not in self.thread_metrics:
                self.thread_metrics[thread_id] = []
            self.thread_metrics[thread_id].append(metric)
            
    def get_concurrency_report(self) -> Dict[str, Any]:
        """Generate report for concurrency testing"""
        with self.lock:
            total_threads = len(self.thread_metrics)
            total_requests = sum(len(metrics) for metrics in self.thread_metrics.values())
            
            # Per-thread statistics
            thread_stats = {}
            for thread_id, metrics in self.thread_metrics.items():
                if metrics:
                    response_times = [m.response_time for m in metrics]
                    successful = len([m for m in metrics if 200 <= m.status_code < 300])
                    
                    thread_stats[thread_id] = {
                        "requests": len(metrics),
                        "successful": successful,
                        "failed": len(metrics) - successful,
                        "avg_response_time": statistics.mean(response_times),
                        "max_response_time": max(response_times)
                    }
                    
            return {
                "concurrent_threads": total_threads,
                "total_requests": total_requests,
                "thread_statistics": thread_stats,
                "threads_with_errors": len([tid for tid, stats in thread_stats.items() if stats["failed"] > 0])
            }