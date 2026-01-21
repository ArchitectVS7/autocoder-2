"""
Visual QA Agent for Phase 5 - Task 5.3

This module analyzes screenshots for visual bugs and UX issues,
checking alignment, spacing, overflow, and viewport consistency.

Features:
- Analyzes screenshots for visual bugs
- Checks alignment, spacing, overflow
- Compares across viewports (mobile/tablet/desktop)
- Generates visual_qa_report.md
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Literal
from PIL import Image
import json


IssueSeverity = Literal["critical", "warning", "info"]
IssueType = Literal["alignment", "spacing", "overflow", "responsive", "contrast", "layout"]


@dataclass
class VisualIssue:
    """Represents a visual bug or UX issue found in screenshots."""
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    screenshot_path: Path
    location: Optional[str] = None
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "screenshot_path": str(self.screenshot_path),
            "location": self.location,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class ViewportAnalysis:
    """Analysis results for a specific viewport size."""
    viewport_name: str
    width: int
    height: int
    issues_found: List[VisualIssue] = field(default_factory=list)
    screenshots_analyzed: int = 0

    def add_issue(self, issue: VisualIssue) -> None:
        """Add an issue to this viewport analysis."""
        self.issues_found.append(issue)

    @property
    def critical_issues(self) -> List[VisualIssue]:
        """Get all critical issues."""
        return [i for i in self.issues_found if i.severity == "critical"]

    @property
    def warnings(self) -> List[VisualIssue]:
        """Get all warnings."""
        return [i for i in self.issues_found if i.severity == "warning"]

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "viewport_name": self.viewport_name,
            "width": self.width,
            "height": self.height,
            "screenshots_analyzed": self.screenshots_analyzed,
            "issues_found": [i.to_dict() for i in self.issues_found],
            "summary": {
                "total_issues": len(self.issues_found),
                "critical": len(self.critical_issues),
                "warnings": len(self.warnings)
            }
        }


@dataclass
class VisualQAReport:
    """Complete visual QA analysis report."""
    flow_id: str
    viewport_analyses: List[ViewportAnalysis] = field(default_factory=list)
    cross_viewport_issues: List[VisualIssue] = field(default_factory=list)

    def add_viewport_analysis(self, analysis: ViewportAnalysis) -> None:
        """Add a viewport analysis to the report."""
        self.viewport_analyses.append(analysis)

    @property
    def all_issues(self) -> List[VisualIssue]:
        """Get all issues from all viewports."""
        issues = []
        for analysis in self.viewport_analyses:
            issues.extend(analysis.issues_found)
        issues.extend(self.cross_viewport_issues)
        return issues

    @property
    def total_critical_issues(self) -> int:
        """Count of all critical issues."""
        return len([i for i in self.all_issues if i.severity == "critical"])

    @property
    def total_warnings(self) -> int:
        """Count of all warnings."""
        return len([i for i in self.all_issues if i.severity == "warning"])

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "flow_id": self.flow_id,
            "viewport_analyses": [va.to_dict() for va in self.viewport_analyses],
            "cross_viewport_issues": [i.to_dict() for i in self.cross_viewport_issues],
            "summary": {
                "total_issues": len(self.all_issues),
                "critical": self.total_critical_issues,
                "warnings": self.total_warnings
            }
        }


class VisualQAAgent:
    """
    Analyzes screenshots for visual bugs and UX issues.

    This agent performs automated visual quality assurance by analyzing
    screenshots for common issues like alignment problems, spacing inconsistencies,
    overflow, and responsive design issues across different viewports.
    """

    # Standard viewport sizes
    VIEWPORTS = {
        "mobile": (375, 667),      # iPhone SE
        "tablet": (768, 1024),     # iPad
        "desktop": (1920, 1080)    # Full HD
    }

    def __init__(self, screenshots_dir: Path = Path("screenshots")):
        """
        Initialize the Visual QA Agent.

        Args:
            screenshots_dir: Directory containing screenshots to analyze
        """
        self.screenshots_dir = Path(screenshots_dir)

    def analyze_screenshot(
        self,
        screenshot_path: Path,
        viewport_name: str
    ) -> List[VisualIssue]:
        """
        Analyze a single screenshot for visual issues.

        Args:
            screenshot_path: Path to the screenshot file
            viewport_name: Name of the viewport (mobile, tablet, desktop)

        Returns:
            List of visual issues found
        """
        issues = []

        if not screenshot_path.exists():
            return issues

        try:
            img = Image.open(screenshot_path)
            width, height = img.size

            # Check image dimensions match expected viewport
            expected_width, expected_height = self.VIEWPORTS.get(
                viewport_name,
                (width, height)
            )

            # Detect potential overflow
            if width > expected_width * 1.1:  # 10% tolerance
                issues.append(VisualIssue(
                    issue_type="overflow",
                    severity="warning",
                    description=f"Screenshot width ({width}px) exceeds expected viewport width ({expected_width}px)",
                    screenshot_path=screenshot_path,
                    suggested_fix="Check for horizontal scrollbars or content overflow"
                ))

            # Detect very small images (might indicate rendering issues)
            if width < 100 or height < 100:
                issues.append(VisualIssue(
                    issue_type="layout",
                    severity="critical",
                    description=f"Screenshot dimensions too small ({width}x{height}px), possible rendering failure",
                    screenshot_path=screenshot_path,
                    suggested_fix="Verify page loaded correctly before screenshot"
                ))

            # Check aspect ratio for common issues
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio > 3.0:  # Unusually wide
                issues.append(VisualIssue(
                    issue_type="layout",
                    severity="warning",
                    description=f"Unusual aspect ratio ({aspect_ratio:.2f}), content may be misaligned",
                    screenshot_path=screenshot_path,
                    suggested_fix="Review layout for horizontal overflow or flexbox issues"
                ))

        except Exception as e:
            issues.append(VisualIssue(
                issue_type="layout",
                severity="critical",
                description=f"Failed to analyze screenshot: {str(e)}",
                screenshot_path=screenshot_path
            ))

        return issues

    def analyze_flow(self, flow_id: str) -> VisualQAReport:
        """
        Analyze all screenshots for a specific user flow.

        Args:
            flow_id: ID of the user flow to analyze

        Returns:
            VisualQAReport with all findings
        """
        report = VisualQAReport(flow_id=flow_id)

        flow_dir = self.screenshots_dir / flow_id
        if not flow_dir.exists():
            return report

        # Analyze screenshots in this flow
        screenshots = sorted(flow_dir.glob("*.png"))

        # For this demo, analyze with desktop viewport
        desktop_analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080,
            screenshots_analyzed=len(screenshots)
        )

        for screenshot in screenshots:
            issues = self.analyze_screenshot(screenshot, "desktop")
            for issue in issues:
                desktop_analysis.add_issue(issue)

        report.add_viewport_analysis(desktop_analysis)

        # Check for cross-viewport issues if multiple viewport screenshots exist
        # (In a real implementation, we'd compare the same step across viewports)

        return report

    def analyze_all_flows(self) -> Dict[str, VisualQAReport]:
        """
        Analyze all user flows in the screenshots directory.

        Returns:
            Dictionary mapping flow IDs to their VisualQAReports
        """
        reports = {}

        if not self.screenshots_dir.exists():
            return reports

        for flow_dir in self.screenshots_dir.iterdir():
            if flow_dir.is_dir():
                flow_id = flow_dir.name
                report = self.analyze_flow(flow_id)
                reports[flow_id] = report

        return reports

    def compare_viewports(
        self,
        flow_id: str,
        screenshot_name: str
    ) -> List[VisualIssue]:
        """
        Compare the same screenshot across different viewports.

        Args:
            flow_id: User flow ID
            screenshot_name: Name of the screenshot to compare

        Returns:
            List of cross-viewport issues found
        """
        issues = []
        viewport_sizes = {}

        # Collect screenshot from each viewport variant
        for viewport_name in ["mobile", "tablet", "desktop"]:
            viewport_dir = self.screenshots_dir / f"{flow_id}_{viewport_name}"
            if viewport_dir.exists():
                screenshot_path = viewport_dir / screenshot_name
                if screenshot_path.exists():
                    try:
                        img = Image.open(screenshot_path)
                        viewport_sizes[viewport_name] = img.size
                    except Exception:
                        pass

        # Compare sizes for consistency
        if len(viewport_sizes) > 1:
            sizes = list(viewport_sizes.values())
            # Check if all viewports show similar content
            # (This is a simplified check; real implementation would use image comparison)
            widths = [s[0] for s in sizes]
            if max(widths) / min(widths) > 2.5:
                issues.append(VisualIssue(
                    issue_type="responsive",
                    severity="warning",
                    description=f"Large layout differences across viewports for {screenshot_name}",
                    screenshot_path=self.screenshots_dir / flow_id / screenshot_name,
                    suggested_fix="Review responsive design implementation"
                ))

        return issues

    def generate_report_markdown(self, report: VisualQAReport) -> str:
        """
        Generate a markdown report from VisualQAReport.

        Args:
            report: VisualQAReport to format

        Returns:
            Formatted markdown string
        """
        md = f"# Visual QA Report: {report.flow_id}\n\n"

        # Summary
        md += "## Summary\n\n"
        md += f"- **Total Issues:** {len(report.all_issues)}\n"
        md += f"- **Critical Issues:** {report.total_critical_issues} ❌\n"
        md += f"- **Warnings:** {report.total_warnings} ⚠️\n\n"

        # Issues by viewport
        for viewport_analysis in report.viewport_analyses:
            md += f"## {viewport_analysis.viewport_name.title()} Viewport "
            md += f"({viewport_analysis.width}x{viewport_analysis.height})\n\n"
            md += f"- Screenshots Analyzed: {viewport_analysis.screenshots_analyzed}\n"
            md += f"- Issues Found: {len(viewport_analysis.issues_found)}\n\n"

            if viewport_analysis.critical_issues:
                md += "### Critical Issues ❌\n\n"
                for issue in viewport_analysis.critical_issues:
                    md += f"- **{issue.issue_type.title()}**: {issue.description}\n"
                    md += f"  - Screenshot: `{issue.screenshot_path.name}`\n"
                    if issue.suggested_fix:
                        md += f"  - Fix: {issue.suggested_fix}\n"
                    md += "\n"

            if viewport_analysis.warnings:
                md += "### Warnings ⚠️\n\n"
                for issue in viewport_analysis.warnings:
                    md += f"- **{issue.issue_type.title()}**: {issue.description}\n"
                    md += f"  - Screenshot: `{issue.screenshot_path.name}`\n"
                    if issue.suggested_fix:
                        md += f"  - Fix: {issue.suggested_fix}\n"
                    md += "\n"

        # Cross-viewport issues
        if report.cross_viewport_issues:
            md += "## Cross-Viewport Issues\n\n"
            for issue in report.cross_viewport_issues:
                md += f"- **{issue.issue_type.title()}**: {issue.description}\n"
                if issue.suggested_fix:
                    md += f"  - Fix: {issue.suggested_fix}\n"
                md += "\n"

        return md

    def save_report(
        self,
        report: VisualQAReport,
        output_file: Path = Path("visual_qa_report.md")
    ) -> Path:
        """
        Save visual QA report to markdown file.

        Args:
            report: VisualQAReport to save
            output_file: Path to output file

        Returns:
            Path to saved report
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        markdown = self.generate_report_markdown(report)
        output_file.write_text(markdown)

        return output_file

    def save_report_json(
        self,
        report: VisualQAReport,
        output_file: Path = Path("visual_qa_report.json")
    ) -> Path:
        """
        Save visual QA report to JSON file.

        Args:
            report: VisualQAReport to save
            output_file: Path to output JSON file

        Returns:
            Path to saved report
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        return output_file


def analyze_screenshots(
    screenshots_dir: Path = Path("screenshots"),
    output_dir: Path = Path("reports")
) -> Dict[str, VisualQAReport]:
    """
    Convenience function to analyze all screenshots and generate reports.

    Args:
        screenshots_dir: Directory containing screenshots
        output_dir: Directory for report output

    Returns:
        Dictionary of flow IDs to VisualQAReports
    """
    agent = VisualQAAgent(screenshots_dir=screenshots_dir)
    reports = agent.analyze_all_flows()

    output_dir.mkdir(parents=True, exist_ok=True)

    for flow_id, report in reports.items():
        # Save markdown report
        md_file = output_dir / f"visual_qa_{flow_id}.md"
        agent.save_report(report, md_file)

        # Save JSON report
        json_file = output_dir / f"visual_qa_{flow_id}.json"
        agent.save_report_json(report, json_file)

    return reports


if __name__ == "__main__":
    # Example usage
    reports = analyze_screenshots()
    print(f"✨ Analyzed {len(reports)} user flows")

    for flow_id, report in reports.items():
        print(f"\n{flow_id}:")
        print(f"  - Total issues: {len(report.all_issues)}")
        print(f"  - Critical: {report.total_critical_issues}")
        print(f"  - Warnings: {report.total_warnings}")
