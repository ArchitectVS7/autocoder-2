"""
Performance Checkpoint Agent
=============================

Analyzes bundle sizes, database query efficiency, N+1 queries,
and heavy dependencies.
"""

import re
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

from checkpoint_orchestrator import CheckpointResult, CheckpointIssue, IssueSeverity


class PerformanceAgent:
    """Performs automated performance analysis on recently changed files."""

    def __init__(self, project_dir: Path):
        """
        Initialize the performance agent.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir

        # Heavy dependency patterns
        self.HEAVY_DEPENDENCIES = {
            'moment': {
                'patterns': [
                    r'import.*moment',
                    r'require\(["\']moment["\']',
                    r'from ["\']moment["\']',
                ],
                'severity': IssueSeverity.INFO,
                'title': 'Heavy dependency: moment.js',
                'description': 'moment.js is 67KB minified (consider date-fns or dayjs)',
                'suggestion': 'Use lighter alternatives: date-fns (11KB) or dayjs (2KB)'
            },
            'lodash': {
                'patterns': [
                    r'import\s+_\s+from\s+["\']lodash["\']',
                    r'require\(["\']lodash["\']',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Heavy dependency: full lodash',
                'description': 'Full lodash import is 71KB (use per-method imports)',
                'suggestion': 'Import specific methods: import debounce from "lodash/debounce"'
            },
            'axios': {
                'patterns': [
                    r'import.*axios',
                    r'require\(["\']axios["\']',
                ],
                'severity': IssueSeverity.INFO,
                'title': 'Consider native fetch',
                'description': 'axios is 13KB (native fetch is built-in)',
                'suggestion': 'Consider using native fetch API for simple HTTP requests'
            },
        }

        # N+1 query patterns
        self.N_PLUS_ONE_PATTERNS = {
            'loop_with_query': {
                'patterns': [
                    r'for\s+\w+\s+in\s+[^:]+:\s*\n\s+[^\n]*\.query\.',
                    r'for\s+\w+\s+in\s+[^:]+:\s*\n\s+[^\n]*\.filter\(',
                    r'for\s+\w+\s+in\s+[^:]+:\s*\n\s+[^\n]*\.get\(',
                    r'for\s+\w+\s+in\s+[^:]+:\s*\n\s+[^\n]*\.filter_by\(',
                    r'forEach\([^)]+\)\s*\{[^\}]*\.find\(',
                    r'map\([^)]+\)\s*\{[^\}]*\.query\(',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Potential N+1 query',
                'description': 'Query inside loop may cause N+1 performance issue',
                'suggestion': 'Use join, prefetch_related, select_related, or batch queries'
            },
            'sequential_queries': {
                'patterns': [
                    r'\.all\(\)[^\n]*\n[^\n]*for\s+\w+\s+in[^\n]+:\s*\n\s+[^\n]*\.get\(',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Sequential database queries',
                'description': 'Multiple sequential queries detected',
                'suggestion': 'Combine queries or use eager loading'
            },
        }

        # Inefficient query patterns
        self.INEFFICIENT_QUERIES = {
            'select_all': {
                'patterns': [
                    r'SELECT\s+\*\s+FROM',
                    r'\.all\(\)\.count\(\)',
                ],
                'severity': IssueSeverity.INFO,
                'title': 'Inefficient query pattern',
                'description': 'SELECT * or .all().count() loads unnecessary data',
                'suggestion': 'Select specific columns or use .count() directly'
            },
            'missing_index': {
                'patterns': [
                    r'\.filter\([^)]*\)\.filter\(',
                    r'WHERE.*AND.*AND.*AND',
                ],
                'severity': IssueSeverity.INFO,
                'title': 'Consider database index',
                'description': 'Multiple filters may benefit from database index',
                'suggestion': 'Add database index on frequently queried columns'
            },
        }

        # Bundle size thresholds (in KB)
        self.BUNDLE_SIZE_THRESHOLDS = {
            'critical': 500,  # > 500KB
            'warning': 300,   # > 300KB
            'info': 200,      # > 200KB
        }

    def analyze(self, commits: int = 1) -> CheckpointResult:
        """
        Analyze recently changed files for performance issues.

        Args:
            commits: Number of recent commits to analyze

        Returns:
            CheckpointResult with performance issues found
        """
        issues = []

        # Get recently changed files
        changed_files = self._get_changed_files(commits)

        if not changed_files:
            return CheckpointResult(
                checkpoint_type='performance',
                status='PASS',
                issues=[],
                metadata={'files_analyzed': 0}
            )

        # Analyze each file
        for file_path in changed_files:
            file_issues = self._analyze_file(file_path)
            issues.extend(file_issues)

        # Check bundle sizes if package.json exists
        bundle_issues = self._check_bundle_sizes()
        issues.extend(bundle_issues)

        # Determine status
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        if critical_count > 0:
            status = 'FAIL'
        elif warning_count > 0:
            status = 'PASS_WITH_WARNINGS'
        else:
            status = 'PASS'

        return CheckpointResult(
            checkpoint_type='performance',
            status=status,
            issues=issues,
            metadata={
                'files_analyzed': len(changed_files),
                'files': [str(f.relative_to(self.project_dir)) for f in changed_files],
                'critical_issues': critical_count,
                'warnings': warning_count
            }
        )

    def _get_changed_files(self, commits: int = 1) -> List[Path]:
        """
        Get list of files changed in recent commits.

        Args:
            commits: Number of recent commits to analyze

        Returns:
            List of changed file paths
        """
        try:
            # Get changed files from recent commits
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'HEAD~{commits}', 'HEAD'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )

            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = self.project_dir / line
                    # Analyze source code and config files
                    if file_path.exists() and self._should_analyze(file_path):
                        files.append(file_path)

            return files

        except subprocess.CalledProcessError:
            # Fallback to staged files
            try:
                result = subprocess.run(
                    ['git', 'diff', '--name-only', '--cached'],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )

                files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        file_path = self.project_dir / line
                        if file_path.exists() and self._should_analyze(file_path):
                            files.append(file_path)

                return files

            except subprocess.CalledProcessError:
                return []

    def _should_analyze(self, file_path: Path) -> bool:
        """
        Check if file should be analyzed for performance issues.

        Args:
            file_path: Path to file

        Returns:
            True if file should be analyzed
        """
        # Analyze source code files
        source_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.sql'}
        # Also analyze config files
        config_extensions = {'.json'}

        all_extensions = source_extensions | config_extensions
        return file_path.suffix in all_extensions or file_path.name == 'package.json'

    def _analyze_file(self, file_path: Path) -> List[CheckpointIssue]:
        """
        Analyze a single file for performance issues.

        Args:
            file_path: Path to file

        Returns:
            List of performance issues found
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Check for heavy dependencies
            for dep_name, dep_config in self.HEAVY_DEPENDENCIES.items():
                dep_issues = self._check_patterns(
                    file_path, content, lines, dep_name, dep_config
                )
                issues.extend(dep_issues)

            # Check for N+1 queries
            for pattern_name, pattern_config in self.N_PLUS_ONE_PATTERNS.items():
                n_plus_one_issues = self._check_patterns(
                    file_path, content, lines, pattern_name, pattern_config
                )
                issues.extend(n_plus_one_issues)

            # Check for inefficient queries
            for query_name, query_config in self.INEFFICIENT_QUERIES.items():
                query_issues = self._check_patterns(
                    file_path, content, lines, query_name, query_config
                )
                issues.extend(query_issues)

        except Exception as e:
            # If we can't read the file, create an info issue
            issues.append(CheckpointIssue(
                severity=IssueSeverity.INFO,
                checkpoint_type='performance',
                title='Could not analyze file',
                description=f'Error reading file: {e}',
                location=str(file_path.relative_to(self.project_dir))
            ))

        return issues

    def _check_patterns(
        self,
        file_path: Path,
        content: str,
        lines: List[str],
        pattern_name: str,
        pattern_config: Dict
    ) -> List[CheckpointIssue]:
        """
        Check for specific performance patterns in file.

        Args:
            file_path: Path to file
            content: File content
            lines: File lines
            pattern_name: Name of pattern
            pattern_config: Configuration for this pattern

        Returns:
            List of issues found
        """
        issues = []

        for pattern_str in pattern_config['patterns']:
            pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

            # Check entire content for multiline patterns
            if '\n' in pattern_str or '.*' in pattern_str:
                matches = pattern.findall(content)
                if matches:
                    # Find approximate line number
                    match_obj = pattern.search(content)
                    if match_obj:
                        line_num = content[:match_obj.start()].count('\n') + 1
                        issues.append(CheckpointIssue(
                            severity=pattern_config['severity'],
                            checkpoint_type='performance',
                            title=pattern_config['title'],
                            description=pattern_config['description'],
                            location=str(file_path.relative_to(self.project_dir)),
                            line_number=line_num,
                            suggestion=pattern_config['suggestion']
                        ))
            else:
                # Check line by line for single-line patterns
                for line_num, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        issues.append(CheckpointIssue(
                            severity=pattern_config['severity'],
                            checkpoint_type='performance',
                            title=pattern_config['title'],
                            description=pattern_config['description'],
                            location=str(file_path.relative_to(self.project_dir)),
                            line_number=line_num,
                            suggestion=pattern_config['suggestion']
                        ))
                        # Only report once per pattern per file
                        break

        return issues

    def _check_bundle_sizes(self) -> List[CheckpointIssue]:
        """
        Check JavaScript bundle sizes.

        Returns:
            List of bundle size issues
        """
        issues = []

        # Check if package.json exists
        package_json = self.project_dir / 'package.json'
        if not package_json.exists():
            return issues

        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)

            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})

            # Estimate bundle size based on dependencies
            # This is a simplified heuristic
            total_deps = len(dependencies)

            # Rough estimate: each dependency averages 50KB
            estimated_size = total_deps * 50

            if estimated_size > self.BUNDLE_SIZE_THRESHOLDS['critical']:
                issues.append(CheckpointIssue(
                    severity=IssueSeverity.CRITICAL,
                    checkpoint_type='performance',
                    title='Large bundle size estimate',
                    description=f'Estimated bundle size: {estimated_size}KB ({total_deps} dependencies)',
                    location='package.json',
                    suggestion='Consider code splitting, tree shaking, or reducing dependencies'
                ))
            elif estimated_size > self.BUNDLE_SIZE_THRESHOLDS['warning']:
                issues.append(CheckpointIssue(
                    severity=IssueSeverity.WARNING,
                    checkpoint_type='performance',
                    title='Moderate bundle size',
                    description=f'Estimated bundle size: {estimated_size}KB ({total_deps} dependencies)',
                    location='package.json',
                    suggestion='Monitor bundle size and consider code splitting'
                ))

            # Check for actual build output if it exists
            dist_dir = self.project_dir / 'dist'
            build_dir = self.project_dir / 'build'

            for output_dir in [dist_dir, build_dir]:
                if output_dir.exists():
                    bundle_issues = self._check_build_output(output_dir)
                    issues.extend(bundle_issues)

        except Exception as e:
            # Silently ignore if we can't parse package.json
            pass

        return issues

    def _check_build_output(self, output_dir: Path) -> List[CheckpointIssue]:
        """
        Check actual build output sizes.

        Args:
            output_dir: Path to build output directory

        Returns:
            List of bundle size issues
        """
        issues = []

        try:
            # Find JavaScript bundles
            js_files = list(output_dir.glob('**/*.js'))

            for js_file in js_files:
                # Skip source maps and minified versions
                if '.map' in js_file.name or '.min.js' in js_file.name:
                    continue

                size_kb = js_file.stat().st_size / 1024

                if size_kb > self.BUNDLE_SIZE_THRESHOLDS['critical']:
                    issues.append(CheckpointIssue(
                        severity=IssueSeverity.CRITICAL,
                        checkpoint_type='performance',
                        title='Large JavaScript bundle',
                        description=f'Bundle {js_file.name} is {size_kb:.1f}KB',
                        location=str(js_file.relative_to(self.project_dir)),
                        suggestion='Use code splitting to reduce bundle size'
                    ))
                elif size_kb > self.BUNDLE_SIZE_THRESHOLDS['warning']:
                    issues.append(CheckpointIssue(
                        severity=IssueSeverity.WARNING,
                        checkpoint_type='performance',
                        title='Moderate bundle size',
                        description=f'Bundle {js_file.name} is {size_kb:.1f}KB',
                        location=str(js_file.relative_to(self.project_dir)),
                        suggestion='Consider optimizing bundle size'
                    ))

        except Exception:
            # Ignore errors reading build output
            pass

        return issues
