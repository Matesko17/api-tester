"""
Performance reporter for generating detailed reports
Creates HTML, JSON and text reports from performance metrics
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import asdict
import statistics

from tests.utils.performance_metrics import PerformanceReport

class PerformanceReporter:
    """Generator for performance reports"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize performance reporter
        
        Args:
            output_dir: Directory for saving reports
        """
        if output_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            output_dir = os.path.join(project_root, 'reports', 'performance')
            
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_json_report(self, report: PerformanceReport, 
                           filename: str = None) -> str:
        """
        Generate JSON report
        
        Args:
            report: PerformanceReport object
            filename: File name (auto-generated if None)
            
        Returns:
            Path to generated file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{report.test_name}_{timestamp}.json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert dataclass to dict
        report_dict = asdict(report)
        
        # Convert datetime objects to strings
        report_dict['start_time'] = report.start_time.isoformat()
        report_dict['end_time'] = report.end_time.isoformat()
        
        # Add calculated fields
        report_dict['test_duration'] = (report.end_time - report.start_time).total_seconds()
        report_dict['success_rate'] = (report.successful_requests / report.total_requests * 100) if report.total_requests > 0 else 0
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
        return filepath
    
    def generate_html_report(self, reports: List[PerformanceReport], 
                           filename: str = None) -> str:
        """
        Generate HTML report with graphs and tables
        
        Args:
            reports: List of PerformanceReport objects
            filename: File name
            
        Returns:
            Path to generated HTML file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_dashboard_{timestamp}.html"
            
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._generate_html_content(reports)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return filepath
    
    def generate_benchmark_report(self, reports: List[PerformanceReport]) -> str:
        """
        Generate benchmark report for comparing different tests
        
        Args:
            reports: List of reports to compare
            
        Returns:
            Path to benchmark file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_comparison_{timestamp}.json"
        filepath = os.path.join(self.output_dir.replace('performance', 'benchmarks'), filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        benchmark_data = {
            'generated_at': datetime.now().isoformat(),
            'tests_compared': len(reports),
            'summary': self._generate_benchmark_summary(reports),
            'detailed_results': []
        }
        
        for report in reports:
            benchmark_data['detailed_results'].append({
                'test_name': report.test_name,
                'requests_per_second': report.requests_per_second,
                'avg_response_time': report.avg_response_time,
                'error_rate': report.error_rate,
                'success_rate': (report.successful_requests / report.total_requests * 100) if report.total_requests > 0 else 0,
                'percentiles': report.percentiles
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(benchmark_data, f, indent=2)
            
        return filepath
    
    def _generate_html_content(self, reports: List[PerformanceReport]) -> str:
        """Generate HTML content for report"""
        
        # CSS styles
        css_styles = """
        <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-label { font-weight: bold; color: #7f8c8d; }
        .metric-value { font-size: 1.2em; color: #2c3e50; margin-left: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .success { color: #27ae60; font-weight: bold; }
        .warning { color: #f39c12; font-weight: bold; }
        .error { color: #e74c3c; font-weight: bold; }
        .chart { margin: 20px 0; padding: 20px; background: #fafafa; border-radius: 5px; }
        </style>
        """
        
        # JavaScript for simple graphs
        js_scripts = """
        <script>
        function createBarChart(containerId, data, title) {
            const container = document.getElementById(containerId);
            container.innerHTML = '<h3>' + title + '</h3>';
            
            const maxValue = Math.max(...data.map(d => d.value));
            
            data.forEach(item => {
                const bar = document.createElement('div');
                bar.style.cssText = 'margin: 5px 0; background: #3498db; height: 30px; position: relative; border-radius: 3px;';
                bar.style.width = (item.value / maxValue * 100) + '%';
                
                const label = document.createElement('span');
                label.textContent = item.name + ': ' + item.value.toFixed(2);
                label.style.cssText = 'position: absolute; left: 10px; top: 5px; color: white; font-weight: bold;';
                
                bar.appendChild(label);
                container.appendChild(bar);
            });
        }
        </script>
        """
        
        # Generate summary statistics
        total_requests = sum(r.total_requests for r in reports)
        avg_rps = statistics.mean([r.requests_per_second for r in reports]) if reports else 0
        avg_response_time = statistics.mean([r.avg_response_time for r in reports]) if reports else 0
        
        # HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Test Report</title>
            <meta charset="utf-8">
            {css_styles}
        </head>
        <body>
            <div class="container">
                <h1>Performance Test Report</h1>
                <div class="summary">
                    <h2>Overall Summary</h2>
                    <div class="metric">
                        <span class="metric-label">Tests Run:</span>
                        <span class="metric-value">{len(reports)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Requests:</span>
                        <span class="metric-value">{total_requests:,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg RPS:</span>
                        <span class="metric-value">{avg_rps:.2f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Response Time:</span>
                        <span class="metric-value">{avg_response_time:.3f}s</span>
                    </div>
                </div>
                
                <h2>Detailed Results</h2>
                <table>
                    <tr>
                        <th>Test Name</th>
                        <th>Total Requests</th>
                        <th>Success Rate</th>
                        <th>Error Rate</th>
                        <th>Avg Response Time</th>
                        <th>RPS</th>
                        <th>95th Percentile</th>
                    </tr>
        """
        
        for report in reports:
            success_rate = (report.successful_requests / report.total_requests * 100) if report.total_requests > 0 else 0
            success_class = "success" if success_rate >= 90 else "warning" if success_rate >= 70 else "error"
            error_class = "success" if report.error_rate <= 5 else "warning" if report.error_rate <= 20 else "error"
            
            html += f"""
                    <tr>
                        <td><strong>{report.test_name}</strong></td>
                        <td>{report.total_requests:,}</td>
                        <td class="{success_class}">{success_rate:.1f}%</td>
                        <td class="{error_class}">{report.error_rate:.1f}%</td>
                        <td>{report.avg_response_time:.3f}s</td>
                        <td>{report.requests_per_second:.2f}</td>
                        <td>{report.percentiles.get(95, 0):.3f}s</td>
                    </tr>
            """
        
        html += """
                </table>
                
                <div id="rpsChart" class="chart"></div>
                <div id="responseTimeChart" class="chart"></div>
                
                <h2>Error Analysis</h2>
        """
        
        # Error analysis
        all_errors = {}
        for report in reports:
            for error, count in report.errors.items():
                all_errors[error] = all_errors.get(error, 0) + count
        
        if all_errors:
            html += "<table><tr><th>Error Type</th><th>Count</th><th>Tests Affected</th></tr>"
            for error, count in sorted(all_errors.items(), key=lambda x: x[1], reverse=True):
                tests_affected = sum(1 for r in reports if error in r.errors)
                html += f"<tr><td>{error}</td><td>{count}</td><td>{tests_affected}</td></tr>"
            html += "</table>"
        else:
            html += "<p class='success'>No errors detected across all tests!</p>"
        
        html += f"""
                <div class="summary">
                    <h2>Report Generated</h2>
                    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Report includes {len(reports)} performance test(s)</p>
                </div>
            </div>
            
            {js_scripts}
            
            <script>
                // Create charts
                const rpsData = [
        """
        
        for report in reports:
            html += f'{{"name": "{report.test_name}", "value": {report.requests_per_second}}},'
        
        html += """
                ];
                
                const responseTimeData = [
        """
        
        for report in reports:
            html += f'{{"name": "{report.test_name}", "value": {report.avg_response_time}}},'
        
        html += """
                ];
                
                createBarChart('rpsChart', rpsData, 'Requests Per Second Comparison');
                createBarChart('responseTimeChart', responseTimeData, 'Average Response Time Comparison');
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _generate_benchmark_summary(self, reports: List[PerformanceReport]) -> Dict[str, Any]:
        """Generate summary for benchmark"""
        if not reports:
            return {}
        
        rps_values = [r.requests_per_second for r in reports]
        response_times = [r.avg_response_time for r in reports]
        error_rates = [r.error_rate for r in reports]
        
        return {
            'best_rps': {
                'value': max(rps_values),
                'test': reports[rps_values.index(max(rps_values))].test_name
            },
            'worst_rps': {
                'value': min(rps_values),
                'test': reports[rps_values.index(min(rps_values))].test_name
            },
            'best_response_time': {
                'value': min(response_times),
                'test': reports[response_times.index(min(response_times))].test_name
            },
            'worst_response_time': {
                'value': max(response_times),
                'test': reports[response_times.index(max(response_times))].test_name
            },
            'lowest_error_rate': {
                'value': min(error_rates),
                'test': reports[error_rates.index(min(error_rates))].test_name
            },
            'highest_error_rate': {
                'value': max(error_rates),
                'test': reports[error_rates.index(max(error_rates))].test_name
            }
        }