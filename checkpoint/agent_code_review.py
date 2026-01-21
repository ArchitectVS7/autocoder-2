"""
Code Review Checkpoint Agent
=============================

Analyzes recently changed files for code quality issues, anti-patterns,
naming conventions, refactoring opportunities, and duplication.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from checkpoint.orchestrator import CheckpointResult, CheckpointIssue, IssueSeverity


class CodeReviewAgent:
    """Performs automated code review on recently changed files."""

    def __init__(self, project_dir: Path):
        """
        Initialize the code review agent.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir

        # Patterns for code smells and anti-patterns
        self.CODE_SMELLS = {
            'console_log': {
                'pattern': r'console\.(log|debug|info|warn|error)',
                'severity': IssueSeverity.WARNING,
                'title': 'Console statement found',
                'description': 'Console statements should be removed before production',
                'suggestion': 'Use a proper logging library or remove debug statements'
            },
            'todo_comment': {
                'pattern': r'(TODO|FIXME|XXX|HACK)',
                'severity': IssueSeverity.INFO,
                'title': 'TODO comment found',
                'description': 'Code contains TODO/FIXME comment',
                'suggestion': 'Consider creating a feature or issue to track this work'
            },
            'large_function': {
                'pattern': None,  # Detected by line count
                'severity': IssueSeverity.WARNING,
                'title': 'Large function detected',
                'description': 'Function exceeds 50 lines',
                'suggestion': 'Consider breaking down into smaller, focused functions'
            },
            'hardcoded_credentials': {
                'pattern': r'(password|api[_-]?key|secret|token)\s*=\s*["\'][^"\']+["\']',
                'severity': IssueSeverity.CRITICAL,
                'title': 'Hardcoded credentials detected',
                'description': 'Potential hardcoded password/API key found',
                'suggestion': 'Use environment variables or a secrets manager'
            },
            'multiple_return_statements': {
                'pattern': None,  # Detected by counting returns
                'severity': IssueSeverity.INFO,
                'title': 'Multiple return statements',
                'description': 'Function has many return statements',
                'suggestion': 'Consider simplifying control flow'
            }
        }

        # Naming convention patterns
        self.NAMING_CONVENTIONS = {
            'python': {
                'function': r'^[a-z_][a-z0-9_]*$',
                'class': r'^[A-Z][a-zA-Z0-9]*$',
                'constant': r'^[A-Z][A-Z0-9_]*$',
            },
            'javascript': {
                'function': r'^[a-z][a-zA-Z0-9]*$',
                'class': r'^[A-Z][a-zA-Z0-9]*$',
                'constant': r'^[A-Z][A-Z0-9_]*$',
            },
            'typescript': {
                'function': r'^[a-z][a-zA-Z0-9]*$',
                'class': r'^[A-Z][a-zA-Z0-9]*$',
                'interface': r'^I?[A-Z][a-zA-Z0-9]*$',
                'constant': r'^[A-Z][A-Z0-9_]*$',
            }
        }

    def analyze(self, commits: int = 1) -> CheckpointResult:
        """
        Analyze recently changed files.

        Args:
            commits: Number of recent commits to analyze

        Returns:
            CheckpointResult with issues found
        """
        issues = []

        # Get recently changed files
        changed_files = self._get_changed_files(commits)

        if not changed_files:
            return CheckpointResult(
                checkpoint_type='code_review',
                status='PASS',
                issues=[],
                metadata={'files_analyzed': 0}
            )

        # Analyze each file
        for file_path in changed_files:
            file_issues = self._analyze_file(file_path)
            issues.extend(file_issues)

        # Check for code duplication across files
        duplication_issues = self._check_duplication(changed_files)
        issues.extend(duplication_issues)

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
            checkpoint_type='code_review',
            status=status,
            issues=issues,
            metadata={
                'files_analyzed': len(changed_files),
                'files': [str(f) for f in changed_files]
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
                    # Only analyze source code files
                    if file_path.exists() and self._is_source_file(file_path):
                        files.append(file_path)

            return files

        except subprocess.CalledProcessError:
            # If git diff fails (e.g., not enough commits), fall back to staged files
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
                        if file_path.exists() and self._is_source_file(file_path):
                            files.append(file_path)

                return files

            except subprocess.CalledProcessError:
                return []

    def _is_source_file(self, file_path: Path) -> bool:
        """
        Check if file is a source code file that should be analyzed.

        Args:
            file_path: Path to file

        Returns:
            True if file should be analyzed
        """
        source_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs'}
        return file_path.suffix in source_extensions

    def _analyze_file(self, file_path: Path) -> List[CheckpointIssue]:
        """
        Analyze a single file for issues.

        Args:
            file_path: Path to file

        Returns:
            List of issues found
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Check for code smells with patterns
            for smell_name, smell_config in self.CODE_SMELLS.items():
                if smell_config['pattern']:
                    smell_issues = self._check_pattern(
                        file_path, content, lines, smell_name, smell_config
                    )
                    issues.extend(smell_issues)

            # Check for large functions
            large_function_issues = self._check_large_functions(file_path, lines)
            issues.extend(large_function_issues)

            # Check naming conventions
            naming_issues = self._check_naming_conventions(file_path, content)
            issues.extend(naming_issues)

            # Check for multiple return statements
            return_issues = self._check_multiple_returns(file_path, lines)
            issues.extend(return_issues)

        except Exception as e:
            # If we can't read the file, create an info issue
            issues.append(CheckpointIssue(
                severity=IssueSeverity.INFO,
                checkpoint_type='code_review',
                title='Could not analyze file',
                description=f'Error reading file: {e}',
                location=str(file_path.relative_to(self.project_dir))
            ))

        return issues

    def _check_pattern(
        self,
        file_path: Path,
        content: str,
        lines: List[str],
        smell_name: str,
        smell_config: Dict
    ) -> List[CheckpointIssue]:
        """
        Check for a specific pattern in file content.

        Args:
            file_path: Path to file
            content: File content
            lines: File lines
            smell_name: Name of code smell
            smell_config: Configuration for this smell

        Returns:
            List of issues found
        """
        issues = []
        pattern = re.compile(smell_config['pattern'], re.IGNORECASE)

        for line_num, line in enumerate(lines, start=1):
            matches = pattern.findall(line)
            if matches:
                issues.append(CheckpointIssue(
                    severity=smell_config['severity'],
                    checkpoint_type='code_review',
                    title=smell_config['title'],
                    description=smell_config['description'],
                    location=str(file_path.relative_to(self.project_dir)),
                    line_number=line_num,
                    suggestion=smell_config['suggestion']
                ))

        return issues

    def _check_large_functions(
        self,
        file_path: Path,
        lines: List[str]
    ) -> List[CheckpointIssue]:
        """
        Check for functions that are too large.

        Args:
            file_path: Path to file
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []
        extension = file_path.suffix

        # Function start patterns by language
        function_patterns = {
            '.py': r'^\s*def\s+(\w+)',
            '.js': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()',
            '.ts': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()',
            '.jsx': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()',
            '.tsx': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()',
        }

        pattern_str = function_patterns.get(extension)
        if not pattern_str:
            return issues

        pattern = re.compile(pattern_str)
        function_starts = []

        # Find function starts
        for line_num, line in enumerate(lines, start=1):
            match = pattern.search(line)
            if match:
                function_name = match.group(1) or match.group(2) if match.lastindex >= 2 else match.group(1)
                function_starts.append((line_num, function_name))

        # Estimate function lengths (simplified - doesn't handle nested functions perfectly)
        for i, (start_line, func_name) in enumerate(function_starts):
            end_line = function_starts[i + 1][0] - 1 if i + 1 < len(function_starts) else len(lines)
            func_length = end_line - start_line + 1

            if func_length > 50:
                issues.append(CheckpointIssue(
                    severity=IssueSeverity.WARNING,
                    checkpoint_type='code_review',
                    title='Large function detected',
                    description=f'Function "{func_name}" is {func_length} lines long',
                    location=str(file_path.relative_to(self.project_dir)),
                    line_number=start_line,
                    suggestion='Consider breaking down into smaller, focused functions'
                ))

        return issues

    def _check_naming_conventions(
        self,
        file_path: Path,
        content: str
    ) -> List[CheckpointIssue]:
        """
        Check naming conventions for functions, classes, etc.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of issues found
        """
        issues = []
        extension = file_path.suffix

        # Map extensions to language conventions
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }

        language = language_map.get(extension)
        if not language:
            return issues

        conventions = self.NAMING_CONVENTIONS.get(language, {})

        # Check class names (Python and JS/TS)
        if 'class' in conventions:
            class_pattern = r'class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                if not re.match(conventions['class'], class_name):
                    issues.append(CheckpointIssue(
                        severity=IssueSeverity.WARNING,
                        checkpoint_type='code_review',
                        title='Naming convention violation',
                        description=f'Class name "{class_name}" should use PascalCase',
                        location=str(file_path.relative_to(self.project_dir)),
                        suggestion='Rename class to follow PascalCase convention'
                    ))

        return issues

    def _check_multiple_returns(
        self,
        file_path: Path,
        lines: List[str]
    ) -> List[CheckpointIssue]:
        """
        Check for functions with many return statements.

        Args:
            file_path: Path to file
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []
        extension = file_path.suffix

        # Function start patterns by language
        function_patterns = {
            '.py': r'^\s*def\s+(\w+)',
            '.js': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)',
            '.ts': r'^\s*(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)',
        }

        pattern_str = function_patterns.get(extension)
        if not pattern_str:
            return issues

        pattern = re.compile(pattern_str)
        return_pattern = re.compile(r'^\s*return\s+')

        current_function = None
        return_count = 0

        for line_num, line in enumerate(lines, start=1):
            # Check if starting a new function
            match = pattern.search(line)
            if match:
                # Report on previous function if needed
                if current_function and return_count > 4:
                    func_name, func_line = current_function
                    issues.append(CheckpointIssue(
                        severity=IssueSeverity.INFO,
                        checkpoint_type='code_review',
                        title='Multiple return statements',
                        description=f'Function "{func_name}" has {return_count} return statements',
                        location=str(file_path.relative_to(self.project_dir)),
                        line_number=func_line,
                        suggestion='Consider simplifying control flow'
                    ))

                # Start tracking new function
                function_name = match.group(1) or (match.group(2) if match.lastindex >= 2 else None)
                current_function = (function_name, line_num)
                return_count = 0

            # Count returns in current function
            if current_function and return_pattern.search(line):
                return_count += 1

        # Check last function
        if current_function and return_count > 4:
            func_name, func_line = current_function
            issues.append(CheckpointIssue(
                severity=IssueSeverity.INFO,
                checkpoint_type='code_review',
                title='Multiple return statements',
                description=f'Function "{func_name}" has {return_count} return statements',
                location=str(file_path.relative_to(self.project_dir)),
                line_number=func_line,
                suggestion='Consider simplifying control flow'
            ))

        return issues

    def _check_duplication(self, files: List[Path]) -> List[CheckpointIssue]:
        """
        Check for code duplication across files.

        This is a simplified implementation that looks for duplicate
        function signatures and similar code blocks.

        Args:
            files: List of files to check

        Returns:
            List of duplication issues found
        """
        issues = []

        # Extract function signatures from all files
        function_bodies: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Look for function definitions and collect their bodies
                in_function = False
                function_start = 0
                function_lines = []

                for line_num, line in enumerate(lines, start=1):
                    # Simple heuristic: function starts with 'def' or 'function'
                    if re.match(r'^\s*(def|function|const\s+\w+\s*=\s*\()', line):
                        if in_function and len(function_lines) > 5:
                            # Hash the function body
                            body_hash = self._normalize_code('\n'.join(function_lines))
                            function_bodies[body_hash].append((file_path, function_start))

                        in_function = True
                        function_start = line_num
                        function_lines = [line]
                    elif in_function:
                        function_lines.append(line)

                # Check last function
                if in_function and len(function_lines) > 5:
                    body_hash = self._normalize_code('\n'.join(function_lines))
                    function_bodies[body_hash].append((file_path, function_start))

            except Exception:
                continue

        # Report duplicates
        for body_hash, locations in function_bodies.items():
            if len(locations) > 1:
                # Found duplication
                location_strs = [
                    f"{fp.relative_to(self.project_dir)}:{ln}"
                    for fp, ln in locations
                ]

                issues.append(CheckpointIssue(
                    severity=IssueSeverity.WARNING,
                    checkpoint_type='code_review',
                    title='Duplicated code detected',
                    description=f'Similar code found in {len(locations)} locations',
                    location=', '.join(location_strs[:3]),  # Limit to 3 locations
                    suggestion='Consider extracting common logic into a shared function'
                ))

        return issues

    def _normalize_code(self, code: str) -> str:
        """
        Normalize code for comparison by removing whitespace and comments.

        Args:
            code: Source code

        Returns:
            Normalized code string
        """
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)

        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)

        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)

        return code.strip()
