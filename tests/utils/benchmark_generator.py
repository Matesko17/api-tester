"""
Benchmark generator for comparing multiple test runs
Generates comprehensive benchmark comparison reports
"""
import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any
from tests.utils.performance_reporter import PerformanceReporter
from tests.utils.performance_metrics import PerformanceReport

class BenchmarkGenerator:
    """Generator for benchmark comparison reports"""
    
    def __init__(self, reports_dir: str = None):
        """
        Initialize benchmark generator
        
        Args:
            reports_dir: Directory containing performance reports
        """
        if reports_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            reports_dir = os.path.join(project_root, 'reports', 'performance')
            
        self.reports_dir = reports_dir
        self.benchmarks_dir = os.path.join(os.path.dirname(reports_dir), 'benchmarks')
        os.makedirs(self.benchmarks_dir, exist_ok=True)
    
    def collect_json_reports(self) -> List[Dict[str, Any]]:
        """
        Collect all JSON performance reports
        
        Returns:
            List of report data dictionaries
        """
        if not os.path.exists(self.reports_dir):
            return []
            
        json_files = glob.glob(os.path.join(self.reports_dir, '*.json'))
        reports = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    report_data['source_file'] = os.path.basename(json_file)
                    reports.append(report_data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                
        return reports
    
    def generate_benchmark_comparison(self, test_filter: str = None) -> str:
        """
        Generate benchmark comparison report
        
        Args:
            test_filter: Optional filter for test names
            
        Returns:
            Path to generated benchmark report
        """
        reports = self.collect_json_reports()
        
        if not reports:
            print("No performance reports found to compare")
            return None
            
        # Filter reports if specified
        if test_filter:
            reports = [r for r in reports if test_filter in r.get('test_name', '')]
        
        # Group reports by test name
        grouped_reports = {}
        for report in reports:
            test_name = report.get('test_name', 'unknown')
            if test_name not in grouped_reports:
                grouped_reports[test_name] = []
            grouped_reports[test_name].append(report)
        
        # Generate comparison data
        comparison_data = {
            'generated_at': datetime.now().isoformat(),
            'total_reports': len(reports),
            'test_groups': len(grouped_reports),
            'tests': {}
        }
        
        for test_name, test_reports in grouped_reports.items():
            # Sort by timestamp
            test_reports.sort(key=lambda x: x.get('start_time', ''))
            
            # Calculate statistics
            rps_values = [r.get('requests_per_second', 0) for r in test_reports]
            response_times = [r.get('avg_response_time', 0) for r in test_reports]
            error_rates = [r.get('error_rate', 0) for r in test_reports]
            
            comparison_data['tests'][test_name] = {
                'runs': len(test_reports),
                'latest_run': test_reports[-1].get('start_time', ''),
                'metrics': {
                    'rps': {
                        'min': min(rps_values) if rps_values else 0,
                        'max': max(rps_values) if rps_values else 0,
                        'avg': sum(rps_values) / len(rps_values) if rps_values else 0,
                        'trend': self._calculate_trend(rps_values)
                    },
                    'response_time': {
                        'min': min(response_times) if response_times else 0,
                        'max': max(response_times) if response_times else 0,
                        'avg': sum(response_times) / len(response_times) if response_times else 0,
                        'trend': self._calculate_trend(response_times, reverse=True)
                    },
                    'error_rate': {
                        'min': min(error_rates) if error_rates else 0,
                        'max': max(error_rates) if error_rates else 0,
                        'avg': sum(error_rates) / len(error_rates) if error_rates else 0,
                        'trend': self._calculate_trend(error_rates, reverse=True)
                    }
                },
                'history': [
                    {
                        'timestamp': r.get('start_time', ''),
                        'rps': r.get('requests_per_second', 0),
                        'response_time': r.get('avg_response_time', 0),
                        'error_rate': r.get('error_rate', 0),
                        'total_requests': r.get('total_requests', 0)
                    }
                    for r in test_reports[-10:]  # Last 10 runs
                ]
            }
        
        # Generate best/worst performers
        if comparison_data['tests']:
            all_tests = comparison_data['tests']
            
            # Best RPS
            best_rps_test = max(all_tests.items(), 
                              key=lambda x: x[1]['metrics']['rps']['max'])
            comparison_data['best_performers'] = {
                'highest_rps': {
                    'test': best_rps_test[0],
                    'value': best_rps_test[1]['metrics']['rps']['max']
                }
            }
            
            # Lowest error rate
            lowest_error_test = min(all_tests.items(),
                                   key=lambda x: x[1]['metrics']['error_rate']['min'])
            comparison_data['best_performers']['lowest_error_rate'] = {
                'test': lowest_error_test[0],
                'value': lowest_error_test[1]['metrics']['error_rate']['min']
            }
            
            # Fastest response time
            fastest_test = min(all_tests.items(),
                             key=lambda x: x[1]['metrics']['response_time']['min'])
            comparison_data['best_performers']['fastest_response'] = {
                'test': fastest_test[0],
                'value': fastest_test[1]['metrics']['response_time']['min']
            }
        
        # Save benchmark report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_comparison_{timestamp}.json"
        filepath = os.path.join(self.benchmarks_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"Benchmark comparison report generated: {filepath}")
        
        # Also generate HTML summary
        self._generate_html_summary(comparison_data, timestamp)
        
        return filepath
    
    def _calculate_trend(self, values: List[float], reverse: bool = False) -> str:
        """
        Calculate trend from values
        
        Args:
            values: List of values
            reverse: True if lower is better
            
        Returns:
            Trend indicator (improving/stable/degrading)
        """
        if len(values) < 2:
            return "stable"
            
        # Compare last quarter with previous
        quarter_size = max(1, len(values) // 4)
        recent = values[-quarter_size:]
        previous = values[-2*quarter_size:-quarter_size] if len(values) > quarter_size else values[:-quarter_size]
        
        if not previous:
            return "stable"
            
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        change_percent = ((recent_avg - previous_avg) / previous_avg) * 100 if previous_avg else 0
        
        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "degrading" if reverse else "improving"
        else:
            return "improving" if reverse else "degrading"
    
    def _generate_html_summary(self, comparison_data: Dict[str, Any], timestamp: str):
        """Generate HTML summary of benchmark comparison"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Benchmark Comparison Report</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-label {{ font-weight: bold; color: #7f8c8d; }}
                .metric-value {{ font-size: 1.2em; color: #2c3e50; margin-left: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .improving {{ color: #27ae60; font-weight: bold; }}
                .stable {{ color: #f39c12; }}
                .degrading {{ color: #e74c3c; font-weight: bold; }}
                .best {{ background-color: #d4edda; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Benchmark Comparison Report</h1>
                <div class="summary">
                    <h2>Summary</h2>
                    <div class="metric">
                        <span class="metric-label">Generated:</span>
                        <span class="metric-value">{comparison_data['generated_at']}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Reports:</span>
                        <span class="metric-value">{comparison_data['total_reports']}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Test Groups:</span>
                        <span class="metric-value">{comparison_data['test_groups']}</span>
                    </div>
                </div>
                
                <h2>Performance Trends</h2>
                <table>
                    <tr>
                        <th>Test Name</th>
                        <th>Runs</th>
                        <th>RPS (avg/max)</th>
                        <th>Response Time (avg/min)</th>
                        <th>Error Rate (avg/min)</th>
                        <th>Trends</th>
                    </tr>
        """
        
        for test_name, test_data in comparison_data.get('tests', {}).items():
            metrics = test_data['metrics']
            
            rps_trend_class = metrics['rps']['trend']
            response_trend_class = metrics['response_time']['trend']
            error_trend_class = metrics['error_rate']['trend']
            
            html_content += f"""
                    <tr>
                        <td><strong>{test_name}</strong></td>
                        <td>{test_data['runs']}</td>
                        <td>{metrics['rps']['avg']:.2f} / {metrics['rps']['max']:.2f}</td>
                        <td>{metrics['response_time']['avg']:.3f}s / {metrics['response_time']['min']:.3f}s</td>
                        <td>{metrics['error_rate']['avg']:.1f}% / {metrics['error_rate']['min']:.1f}%</td>
                        <td>
                            RPS: <span class="{rps_trend_class}">{rps_trend_class}</span><br>
                            Response: <span class="{response_trend_class}">{response_trend_class}</span><br>
                            Errors: <span class="{error_trend_class}">{error_trend_class}</span>
                        </td>
                    </tr>
            """
        
        html_content += """
                </table>
        """
        
        # Best performers section
        if 'best_performers' in comparison_data:
            html_content += """
                <h2>Best Performers</h2>
                <div class="summary">
            """
            
            best = comparison_data['best_performers']
            if 'highest_rps' in best:
                html_content += f"""
                    <div class="metric">
                        <span class="metric-label">Highest RPS:</span>
                        <span class="metric-value">{best['highest_rps']['test']} ({best['highest_rps']['value']:.2f})</span>
                    </div>
                """
            
            if 'lowest_error_rate' in best:
                html_content += f"""
                    <div class="metric">
                        <span class="metric-label">Lowest Error Rate:</span>
                        <span class="metric-value">{best['lowest_error_rate']['test']} ({best['lowest_error_rate']['value']:.1f}%)</span>
                    </div>
                """
            
            if 'fastest_response' in best:
                html_content += f"""
                    <div class="metric">
                        <span class="metric-label">Fastest Response:</span>
                        <span class="metric-value">{best['fastest_response']['test']} ({best['fastest_response']['value']:.3f}s)</span>
                    </div>
                """
            
            html_content += """
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Save HTML report
        html_filename = f"benchmark_comparison_{timestamp}.html"
        html_filepath = os.path.join(self.benchmarks_dir, html_filename)
        
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Benchmark HTML report generated: {html_filepath}")

# Helper function for pytest integration
def generate_benchmark_after_tests():
    """Generate benchmark report after test run"""
    generator = BenchmarkGenerator()
    return generator.generate_benchmark_comparison()