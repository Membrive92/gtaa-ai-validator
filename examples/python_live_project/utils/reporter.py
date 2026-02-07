"""
Custom report generator.
BAD PRACTICE: Reinventing the wheel instead of using pytest-html or allure properly.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Custom HTML report generator."""

    def __init__(self, report_dir: str = "reports"):
        self.report_dir = report_dir
        self.results = []
        self.start_time = None
        self.end_time = None
        os.makedirs(report_dir, exist_ok=True)

    def start_suite(self):
        self.start_time = datetime.now()
        self.results = []

    def add_result(self, test_name: str, status: str, duration: float,
                   error_msg: str = "", screenshot: str = ""):
        self.results.append({
            "test_name": test_name,
            "status": status,
            "duration": round(duration, 2),
            "error_msg": error_msg,
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat()
        })

    def end_suite(self):
        self.end_time = datetime.now()

    def generate_html_report(self) -> str:
        """Generate HTML report - BAD: Entire HTML template as string."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0

        # BAD PRACTICE: Massive inline HTML string
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: white; padding: 15px; border-radius: 8px; flex: 1; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .passed {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .skipped {{ color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        .status-passed {{ background: #d5f4e6; color: #27ae60; padding: 4px 8px; border-radius: 4px; }}
        .status-failed {{ background: #fde8e8; color: #e74c3c; padding: 4px 8px; border-radius: 4px; }}
        .status-skipped {{ background: #fff3cd; color: #f39c12; padding: 4px 8px; border-radius: 4px; }}
        .error-msg {{ color: #e74c3c; font-size: 0.9em; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Automation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Duration: {duration:.1f}s</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h2>{total}</h2>
            <p>Total Tests</p>
        </div>
        <div class="summary-card">
            <h2 class="passed">{passed}</h2>
            <p>Passed</p>
        </div>
        <div class="summary-card">
            <h2 class="failed">{failed}</h2>
            <p>Failed</p>
        </div>
        <div class="summary-card">
            <h2 class="skipped">{skipped}</h2>
            <p>Skipped</p>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration (s)</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
"""
        for i, result in enumerate(self.results, 1):
            status_class = f"status-{result['status'].lower()}"
            error_html = f'<div class="error-msg">{result["error_msg"]}</div>' if result["error_msg"] else ""
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{result['test_name']}{error_html}</td>
                <td><span class="{status_class}">{result['status']}</span></td>
                <td>{result['duration']}</td>
                <td>{result['error_msg'][:100] if result['error_msg'] else '-'}</td>
            </tr>
"""
        html += """
        </tbody>
    </table>
</body>
</html>"""

        report_path = os.path.join(self.report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(report_path, "w") as f:
            f.write(html)

        return report_path

    def generate_json_report(self) -> str:
        """Generate JSON report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": total - passed - failed,
                "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
            },
            "results": self.results
        }

        report_path = os.path.join(self.report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report_path
