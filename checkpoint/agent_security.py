"""
Security Audit Checkpoint Agent
================================

Scans for OWASP Top 10 vulnerabilities, authentication/authorization issues,
input sanitization problems, and API endpoint security.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

from checkpoint_orchestrator import CheckpointResult, CheckpointIssue, IssueSeverity


class SecurityAuditAgent:
    """Performs automated security audit on recently changed files."""

    def __init__(self, project_dir: Path):
        """
        Initialize the security audit agent.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir

        # OWASP Top 10 detection patterns
        self.VULNERABILITY_PATTERNS = {
            # A01:2021 - Broken Access Control
            'missing_authorization': {
                'patterns': [
                    r'@app\.route.*POST.*\n(?!.*@login_required)(?!.*@requires_auth)(?!.*check.*auth)',
                    r'router\.(post|put|delete)\([^)]+\).*\n(?!.*auth)',
                    r'app\.(post|put|delete)\([^)]+,\s*(?!.*auth)',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Missing authorization check',
                'description': 'Endpoint accepts mutations without authorization',
                'suggestion': 'Add @login_required, @requires_auth, or equivalent authorization check'
            },

            # A02:2021 - Cryptographic Failures
            'weak_crypto': {
                'patterns': [
                    r'MD5\(',
                    r'SHA1\(',
                    r'\.md5\(',
                    r'hashlib\.md5',
                    r'hashlib\.sha1',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Weak cryptographic algorithm',
                'description': 'Using MD5 or SHA1 (weak hash functions)',
                'suggestion': 'Use SHA-256 or better (hashlib.sha256, bcrypt, argon2)'
            },

            # A03:2021 - Injection
            'sql_injection': {
                'patterns': [
                    r'\.execute\([^)]*["\'].*%s.*["\'][^)]*\)',
                    r'\.execute\([^)]*f["\'].*\{.*\}.*["\'][^)]*\)',
                    r'query\s*=\s*["\']SELECT.*["\'].*\+',
                    r'\.raw\([^)]*f["\']',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'SQL injection vulnerability',
                'description': 'SQL query with string concatenation or formatting',
                'suggestion': 'Use parameterized queries or ORM methods'
            },

            'xss_vulnerability': {
                'patterns': [
                    r'\.innerHTML\s*=',
                    r'dangerouslySetInnerHTML',
                    r'document\.write\(',
                    r'\.html\([^)]*\+',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'XSS vulnerability',
                'description': 'Unsafe HTML rendering without sanitization',
                'suggestion': 'Use textContent, sanitize HTML, or use framework safety features'
            },

            'command_injection': {
                'patterns': [
                    r'os\.system\([^)]*\+',
                    r'subprocess\.(call|run|Popen)\([^)]*f["\']',
                    r'exec\([^)]*\+',
                    r'eval\([^)]*\+',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Command injection vulnerability',
                'description': 'Shell command with unsanitized input',
                'suggestion': 'Use subprocess with shell=False and array arguments'
            },

            # A04:2021 - Insecure Design
            'jwt_in_localstorage': {
                'patterns': [
                    r'localStorage\.setItem\([^)]*token',
                    r'localStorage\.setItem\([^)]*jwt',
                    r'localStorage\.setItem\([^)]*auth',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'JWT stored in localStorage',
                'description': 'Tokens in localStorage are vulnerable to XSS',
                'suggestion': 'Use httpOnly cookies for authentication tokens'
            },

            # A05:2021 - Security Misconfiguration
            'debug_mode_enabled': {
                'patterns': [
                    r'DEBUG\s*=\s*True',
                    r'app\.debug\s*=\s*True',
                    r'DEBUG:\s*true',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Debug mode enabled',
                'description': 'Debug mode should be disabled in production',
                'suggestion': 'Set DEBUG=False and use environment variables'
            },

            'missing_rate_limiting': {
                'patterns': [
                    r'@app\.route.*login.*\n(?!.*@limiter)',
                    r'@app\.route.*auth.*\n(?!.*@limiter)',
                    r'router\.post.*auth.*\n(?!.*rateLimit)',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Missing rate limiting on auth endpoint',
                'description': 'Authentication endpoints should have rate limiting',
                'suggestion': 'Add rate limiting with @limiter.limit or rateLimit middleware'
            },

            # A07:2021 - Identification and Authentication Failures
            'weak_password_validation': {
                'patterns': [
                    r'len\(.*password.*\)\s*[<>=]+\s*[1-7](?!\d)',
                    r'password.*\.length\s*[<>=]+\s*[1-7](?!\d)',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Weak password requirements',
                'description': 'Password minimum length should be at least 8 characters',
                'suggestion': 'Enforce strong password policy (min 8 chars, complexity)'
            },

            # A08:2021 - Software and Data Integrity Failures
            'missing_csrf_protection': {
                'patterns': [
                    r'<form[^>]*method=["\']post["\'][^>]*>(?!.*csrf)',
                    r'@app\.route.*POST.*\n(?!.*csrf)',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Missing CSRF protection',
                'description': 'POST endpoint without CSRF token',
                'suggestion': 'Add CSRF protection (Flask-WTF, Django CSRF, etc.)'
            },

            # A09:2021 - Security Logging and Monitoring Failures
            'sensitive_data_in_logs': {
                'patterns': [
                    r'log.*password',
                    r'log.*token',
                    r'log.*secret',
                    r'console\.log.*password',
                    r'print.*password',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Sensitive data in logs',
                'description': 'Logging passwords, tokens, or secrets',
                'suggestion': 'Never log sensitive data; use [REDACTED] placeholders'
            },

            # A10:2021 - Server-Side Request Forgery
            'ssrf_vulnerability': {
                'patterns': [
                    r'requests\.get\([^)]*input',
                    r'requests\.get\([^)]*request\.',
                    r'urllib\.request\.urlopen\([^)]*input',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Potential SSRF vulnerability',
                'description': 'HTTP request with user-provided URL',
                'suggestion': 'Validate and whitelist URLs before making requests'
            },
        }

        # Authentication/Authorization patterns
        self.AUTH_PATTERNS = {
            'hardcoded_secret_key': {
                'patterns': [
                    r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',
                    r'JWT_SECRET\s*=\s*["\'][^"\']+["\']',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Hardcoded secret key',
                'description': 'Secret key hardcoded in source code',
                'suggestion': 'Use environment variables for secrets'
            },

            'insecure_comparison': {
                'patterns': [
                    r'password\s*==',
                    r'token\s*==',
                    r'if.*password.*==',
                ],
                'severity': IssueSeverity.WARNING,
                'title': 'Insecure comparison',
                'description': 'Using == for password/token comparison (timing attack)',
                'suggestion': 'Use hmac.compare_digest() or secrets.compare_digest()'
            },
        }

        # Input sanitization patterns
        self.SANITIZATION_PATTERNS = {
            'unsanitized_file_path': {
                'patterns': [
                    r'open\([^)]*request\.',
                    r'open\([^)]*input',
                    r'Path\([^)]*request\.',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Path traversal vulnerability',
                'description': 'File path from user input without validation',
                'suggestion': 'Validate and sanitize file paths; use secure_filename()'
            },

            'unsafe_deserialization': {
                'patterns': [
                    r'pickle\.loads?\(',
                    r'yaml\.load\([^)]*(?!Loader)',
                    r'eval\(',
                ],
                'severity': IssueSeverity.CRITICAL,
                'title': 'Unsafe deserialization',
                'description': 'Deserializing untrusted data',
                'suggestion': 'Use json.loads() or yaml.safe_load() instead'
            },
        }

    def analyze(self, commits: int = 1) -> CheckpointResult:
        """
        Analyze recently changed files for security vulnerabilities.

        Args:
            commits: Number of recent commits to analyze

        Returns:
            CheckpointResult with security issues found
        """
        issues = []

        # Get recently changed files
        changed_files = self._get_changed_files(commits)

        if not changed_files:
            return CheckpointResult(
                checkpoint_type='security_audit',
                status='PASS',
                issues=[],
                metadata={'files_analyzed': 0}
            )

        # Analyze each file
        for file_path in changed_files:
            file_issues = self._analyze_file(file_path)
            issues.extend(file_issues)

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
            checkpoint_type='security_audit',
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
        Check if file should be analyzed for security issues.

        Args:
            file_path: Path to file

        Returns:
            True if file should be analyzed
        """
        # Analyze source code files
        source_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.php', '.rb'}
        # Also analyze config files
        config_extensions = {'.yml', '.yaml', '.json', '.env', '.config'}
        # And HTML templates
        template_extensions = {'.html', '.htm', '.jinja', '.jinja2', '.ejs', '.hbs'}

        all_extensions = source_extensions | config_extensions | template_extensions
        return file_path.suffix in all_extensions

    def _analyze_file(self, file_path: Path) -> List[CheckpointIssue]:
        """
        Analyze a single file for security issues.

        Args:
            file_path: Path to file

        Returns:
            List of security issues found
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Check OWASP Top 10 vulnerabilities
            for vuln_name, vuln_config in self.VULNERABILITY_PATTERNS.items():
                vuln_issues = self._check_patterns(
                    file_path, content, lines, vuln_name, vuln_config
                )
                issues.extend(vuln_issues)

            # Check authentication/authorization
            for auth_name, auth_config in self.AUTH_PATTERNS.items():
                auth_issues = self._check_patterns(
                    file_path, content, lines, auth_name, auth_config
                )
                issues.extend(auth_issues)

            # Check input sanitization
            for sanit_name, sanit_config in self.SANITIZATION_PATTERNS.items():
                sanit_issues = self._check_patterns(
                    file_path, content, lines, sanit_name, sanit_config
                )
                issues.extend(sanit_issues)

        except Exception as e:
            # If we can't read the file, create an info issue
            issues.append(CheckpointIssue(
                severity=IssueSeverity.INFO,
                checkpoint_type='security_audit',
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
        Check for specific security patterns in file.

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
                            checkpoint_type='security_audit',
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
                            checkpoint_type='security_audit',
                            title=pattern_config['title'],
                            description=pattern_config['description'],
                            location=str(file_path.relative_to(self.project_dir)),
                            line_number=line_num,
                            suggestion=pattern_config['suggestion']
                        ))
                        # Only report once per pattern per file
                        break

        return issues
