"""
Security Analyzer — scans source code for dangerous coding patterns and security vulnerabilities.

Implements 10 security rules plus Semgrep integration for comprehensive static analysis.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from rich.console import Console

from vibestandard.analyzers.base import BaseAnalyzer
from vibestandard.models import Finding

console = Console(stderr=True)

# Files and directories to always skip
_SKIP_DIRS = {"tests", "test", "__pycache__", ".git", "node_modules", "venv", ".venv"}
_SKIP_FILE_PATTERNS = {"test_", "_test.py", "spec.", ".spec."}
_MAX_FILE_SIZE = 500 * 1024  # 500KB

# Source file extensions to scan
_SOURCE_EXTENSIONS = {".py", ".java", ".js", ".ts"}

# Import patterns for password hashing libraries
_PASSWORD_HASH_IMPORTS = {
    "bcrypt", "argon2", "passlib", "werkzeug.security",
    "hashpw", "make_password", "django.contrib.auth.hashers",
    "check_password_hash", "generate_password_hash"
}


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes source code for security vulnerabilities."""
    
    name = "security"
    ecosystem = "generic"
    
    # Hardcoded rule definitions for security checks
    SECURITY_RULES = {
        "sql-injection-concat": {
            "name": "SQL injection via string concatenation",
            "severity": "critical",
            "message": "SQL query is built using string concatenation or f-string interpolation. This allows attackers to manipulate the query and access or destroy data.",
            "fix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,)). Never concatenate variables directly into SQL strings."
        },
        "eval-on-input": {
            "name": "eval() called on user input",
            "severity": "critical",
            "message": "eval() or exec() is called with user-controlled input. This allows attackers to execute arbitrary Python code on your server.",
            "fix": "Remove eval() and exec() entirely. Use a safe expression parser (like simpleeval) if you need to evaluate user expressions, or rethink the design to avoid dynamic code execution."
        },
        "ssl-verify-disabled": {
            "name": "SSL verification disabled",
            "severity": "high",
            "message": "SSL/TLS certificate verification is disabled. This allows attackers to intercept encrypted traffic using a man-in-the-middle attack.",
            "fix": "Remove verify=False. If you are using a self-signed certificate, configure a custom CA bundle instead: requests.get(url, verify='/path/to/ca-bundle.crt')"
        },
        "csrf-disabled": {
            "name": "CSRF protection disabled",
            "severity": "high",
            "message": "CSRF protection is disabled. This allows attackers to trick authenticated users into performing unintended actions on your application.",
            "fix": "Remove @csrf_exempt from non-API views. If building a REST API consumed by a separate frontend, use token-based authentication (JWT) instead of session cookies, which eliminates the need for CSRF tokens."
        },
        "password-not-hashed": {
            "name": "Password stored without hashing",
            "severity": "high",
            "message": "Passwords appear to be stored without hashing. Storing raw passwords means a database breach exposes every user's password immediately.",
            "fix": "Use bcrypt or argon2 to hash passwords before storing them. Example with bcrypt: hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()). Never store or log raw passwords."
        },
        "jwt-hardcoded-secret": {
            "name": "JWT secret hardcoded",
            "severity": "critical",
            "message": "JWT secret is hardcoded as a string literal. Anyone who reads your source code (including in a public repo) can forge authentication tokens for any user.",
            "fix": "Move the JWT secret to an environment variable: jwt.encode(payload, os.environ.get('JWT_SECRET'), algorithm='HS256'). Generate a strong random secret: python -c \"import secrets; print(secrets.token_hex(64))\""
        },
        "pickle-untrusted-data": {
            "name": "Pickle deserialization of untrusted data",
            "severity": "critical",
            "message": "pickle.loads() is called on data from an external source. Pickle can execute arbitrary code during deserialization — passing attacker-controlled data to pickle.loads() is remote code execution.",
            "fix": "Never deserialize pickle data from untrusted sources. Use JSON for data interchange. If you need to cache Python objects, use a safe serialization format like MessagePack or marshal only within a trusted boundary."
        },
        "open-redirect": {
            "name": "Open redirect vulnerability",
            "severity": "medium",
            "message": "Application redirects to a URL from user input without validation. Attackers use open redirects to build convincing phishing URLs that appear to come from your domain.",
            "fix": "Validate the redirect URL before using it. Only allow redirects to relative URLs or a whitelist of known safe domains. Use url_has_allowed_host_and_scheme() in Django or implement your own allowlist check."
        },
        "unrestricted-file-upload": {
            "name": "Unrestricted file upload",
            "severity": "high",
            "message": "File upload does not validate file type or extension. Attackers can upload executable files (PHP, Python scripts) and potentially execute them on your server.",
            "fix": "Validate the file extension against an allowlist before saving: ALLOWED = {'png', 'jpg', 'pdf'}. Use werkzeug's secure_filename() to sanitize the filename. Consider also validating MIME type using the python-magic library."
        },
        "missing-auth-on-sensitive-route": {
            "name": "Missing authentication on sensitive route",
            "severity": "medium",
            "message": "A sensitive route is accessible without authentication. Any user — including unauthenticated attackers — can access this endpoint.",
            "fix": "Add an authentication decorator to this route. In Django use @login_required, in Flask-Login use @login_required, in FastAPI use Depends(get_current_user), in Flask-JWT-Extended use @jwt_required()."
        }
    }
    
    def analyze(self) -> list[Finding]:
        """Run all security checks across source files."""
        # 1. Filter to source files only
        source_files = self._get_source_files()
        
        if not source_files:
            return []
        
        # 2. Run all 10 regex-based checks
        self._check_sql_injection(source_files)
        self._check_eval_on_input(source_files)
        self._check_ssl_verify_disabled(source_files)
        self._check_csrf_disabled(source_files)
        self._check_password_not_hashed(source_files)
        self._check_jwt_hardcoded_secret(source_files)
        self._check_pickle_untrusted_data(source_files)
        self._check_open_redirect(source_files)
        self._check_unrestricted_file_upload(source_files)
        self._check_missing_auth_on_sensitive_route(source_files)
        
        # 3. Run Semgrep if enabled
        if self.options.get("use_semgrep", True):
            semgrep_findings = self._run_semgrep()
            self.findings.extend(semgrep_findings)
        
        # 4. Deduplicate findings
        self.findings = self._deduplicate(self.findings)
        
        return self.findings
    
    def add_security_finding(self, rule_id: str, file: str, line: int | None = None) -> None:
        """Add a security finding using hardcoded rule definitions."""
        rule = self.SECURITY_RULES.get(rule_id)
        if not rule:
            return
        
        finding = Finding(
            rule_id=rule_id,
            name=rule["name"],
            severity=rule["severity"],
            message=rule["message"],
            fix=rule["fix"],
            file=file,
            line=line,
            analyzer=self.name,
            ecosystem=self.ecosystem,
        )
        self.findings.append(finding)
    
    def _get_source_files(self) -> list[Path]:
        """Get list of source files, filtering out tests, binaries, and large files."""
        source_files = []
        
        for rel_path in self.file_tree:
            # Skip if in excluded directory
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            
            # Skip test files
            filename = rel_path.name
            if any(filename.startswith(p) or filename.endswith(p) 
                   for p in _SKIP_FILE_PATTERNS):
                continue
            
            # Only scan source extensions
            if rel_path.suffix.lower() not in _SOURCE_EXTENSIONS:
                continue
            
            # Skip files larger than 500KB
            abs_path = self.root / rel_path
            try:
                if abs_path.stat().st_size > _MAX_FILE_SIZE:
                    console.print(
                        f"[dim]Skipping large file (>500KB): {rel_path}[/]"
                    )
                    continue
            except OSError:
                continue
            
            source_files.append(rel_path)
        
        return source_files
    
    def _is_comment_line(self, line: str, file_ext: str) -> bool:
        """Check if a line is a comment."""
        stripped = line.strip()
        if file_ext == ".py":
            return stripped.startswith("#")
        elif file_ext in {".js", ".ts", ".java"}:
            return stripped.startswith("//")
        return False
    
    def _has_ignore_directive(self, line: str) -> bool:
        """Check if line contains # noqa or # vibestandard: ignore."""
        return "# noqa" in line or "# vibestandard: ignore" in line
    
    def _read_file_lines(self, rel_path: Path) -> tuple[list[str] | None, str]:
        """Read file and return lines and file extension."""
        abs_path = self.root / rel_path
        content = self.read_file_safe(abs_path)
        if not content:
            return None, ""
        return content.splitlines(), rel_path.suffix.lower()
    
    def _check_sql_injection(self, files: list[Path]) -> None:
        """Rule 1: Detect SQL queries built with string concatenation or f-strings."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                # Skip comments and ignore directives
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Pattern 1: execute("SELECT... with + operator
                if re.search(r'execute\(["\'](?:SELECT|INSERT|UPDATE|DELETE).*["\'].*\+', line, re.IGNORECASE):
                    self.add_security_finding(
                        "sql-injection-concat",
                        str(rel_path),
                        line=i + 1
                    )
                    continue
                
                # Pattern 2: execute(f"SELECT... with {variable}
                if re.search(r'execute\(f["\'](?:SELECT|INSERT|UPDATE|DELETE).*\{.*\}', line, re.IGNORECASE):
                    self.add_security_finding(
                        "sql-injection-concat",
                        str(rel_path),
                        line=i + 1
                    )
                    continue
                
                # Pattern 3: execute with % formatting
                if re.search(r'execute\(.*%\s*\(', line):
                    self.add_security_finding(
                        "sql-injection-concat",
                        str(rel_path),
                        line=i + 1
                    )
    
    def _check_eval_on_input(self, files: list[Path]) -> None:
        """Rule 2: Detect eval() or exec() with user-controlled input."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Flag eval/exec with user input patterns
                if re.search(r'\b(eval|exec)\s*\(\s*(request\.|input\(|data|user|form)', line):
                    # Don't flag eval(repr(...))
                    if "repr(" not in line:
                        self.add_security_finding(
                            "eval-on-input",
                            str(rel_path),
                            line=i + 1
                        )
    
    def _check_ssl_verify_disabled(self, files: list[Path]) -> None:
        """Rule 3: Detect SSL verification being disabled."""
        for rel_path in files:
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                patterns = [
                    r'verify\s*=\s*False',
                    r'ssl_verify\s*=\s*False',
                    r'urllib3\.disable_warnings\(\)',
                    r'VERIFY_SSL\s*=\s*False',
                    r'check_hostname\s*=\s*False'
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line):
                        self.add_security_finding(
                            "ssl-verify-disabled",
                            str(rel_path),
                            line=i + 1
                        )
                        break
    
    def _check_csrf_disabled(self, files: list[Path]) -> None:
        """Rule 4: Detect CSRF protection being disabled."""
        for rel_path in files:
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                patterns = [
                    r'@csrf_exempt',
                    r'WTF_CSRF_ENABLED\s*=\s*False',
                    r'csrf_protection\s*=\s*False'
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line):
                        self.add_security_finding(
                            "csrf-disabled",
                            str(rel_path),
                            line=i + 1
                        )
                        break
    
    def _check_password_not_hashed(self, files: list[Path]) -> None:
        """Rule 5: Detect passwords stored without hashing."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            # Check if file has password hashing imports - scan ENTIRE file
            content = "\n".join(lines)
            has_hash_import = False
            for imp in _PASSWORD_HASH_IMPORTS:
                # Check for import statements
                if re.search(rf'\b(import|from)\s+{re.escape(imp)}\b', content):
                    has_hash_import = True
                    break
            
            # Skip file if it has proper hashing imports
            if has_hash_import:
                continue
            
            # Look for password assignment from request
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Pattern: password = request.form[...] or similar
                if re.search(r'\b\w*password\w*\s*=.*request\.(form|data|POST|json|args)', line, re.IGNORECASE):
                    self.add_security_finding(
                        "password-not-hashed",
                        str(rel_path),
                        line=i + 1
                    )
    
    def _check_jwt_hardcoded_secret(self, files: list[Path]) -> None:
        """Rule 6: Detect JWT tokens signed with hardcoded secrets."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Match jwt.encode/decode with string literal as second arg
                if re.search(r'jwt\.(encode|decode)\s*\([^,\)]+,\s*["\']', line):
                    # Don't flag if it's using os.environ or settings
                    if not re.search(r'(os\.environ|os\.getenv|settings\.|config\.)', line):
                        self.add_security_finding(
                            "jwt-hardcoded-secret",
                            str(rel_path),
                            line=i + 1
                        )
    
    def _check_pickle_untrusted_data(self, files: list[Path]) -> None:
        """Rule 7: Detect pickle.loads() on untrusted data."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Match pickle.loads() with untrusted sources
                if re.search(r'pickle\.loads\s*\(', line):
                    # Skip if loading from local file
                    if re.search(r'open\s*\(["\']', line):
                        continue
                    
                    # Flag if argument contains untrusted sources
                    if re.search(r'(request\.|redis|cache|receive|socket|input\()', line):
                        self.add_security_finding(
                            "pickle-untrusted-data",
                            str(rel_path),
                            line=i + 1
                        )
    
    def _check_open_redirect(self, files: list[Path]) -> None:
        """Rule 8: Detect unvalidated redirects to user-supplied URLs."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                patterns = [
                    r'redirect\s*\(\s*request\.(args|GET|form)\.get\(',
                    r'HttpResponseRedirect\s*\(\s*request\.GET\.get\('
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line):
                        self.add_security_finding(
                            "open-redirect",
                            str(rel_path),
                            line=i + 1
                        )
                        break
    
    def _check_unrestricted_file_upload(self, files: list[Path]) -> None:
        """Rule 9: Detect file upload without validation."""
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            # Look for functions with request.files and file.save()
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                if "request.files" in line:
                    # Check next 20 lines for file.save() without validation
                    has_save = False
                    has_validation = False
                    
                    for j in range(i, min(i + 20, len(lines))):
                        check_line = lines[j]
                        if re.search(r'\.save\(|\.write\(', check_line):
                            has_save = True
                        if re.search(r'(\.split\(["\']\.["\']|os\.path\.splitext|mimetypes|imghdr|ALLOWED_EXTENSIONS)', check_line):
                            has_validation = True
                    
                    if has_save and not has_validation:
                        self.add_security_finding(
                            "unrestricted-file-upload",
                            str(rel_path),
                            line=i + 1
                        )
    
    def _check_missing_auth_on_sensitive_route(self, files: list[Path]) -> None:
        """Rule 10: Detect sensitive routes without authentication."""
        sensitive_paths = ["/admin", "/delete", "/users", "/settings", "/dashboard", "/config", "/manage", "/internal"]
        auth_decorators = [
            "@login_required", "@jwt_required", "@requires_auth",
            "@permission_required", "@staff_member_required", "@token_required",
            "Depends(get_current_user)"
        ]
        route_decorators = ["@app.route", "@router.get", "@router.post", "@router.put", "@router.delete", "@api_view"]
        
        for rel_path in files:
            if rel_path.suffix.lower() != ".py":
                continue
            
            lines, ext = self._read_file_lines(rel_path)
            if not lines:
                continue
            
            for i, line in enumerate(lines):
                if self._is_comment_line(line, ext) or self._has_ignore_directive(line):
                    continue
                
                # Check for route decorators with sensitive paths
                is_route = any(route in line for route in route_decorators)
                if not is_route:
                    continue
                
                has_sensitive_path = any(path in line for path in sensitive_paths)
                if not has_sensitive_path:
                    continue
                
                # Check lines AFTER route decorator (between route and function def)
                # Look for auth decorators in the next 5 lines
                has_auth = False
                for j in range(i + 1, min(i + 6, len(lines))):
                    check_line = lines[j].strip()
                    # Stop if we hit the function definition
                    if check_line.startswith("def ") or check_line.startswith("async def "):
                        break
                    # Check for auth decorators
                    if any(auth in lines[j] for auth in auth_decorators):
                        has_auth = True
                        break
                
                if not has_auth:
                    self.add_security_finding(
                        "missing-auth-on-sensitive-route",
                        str(rel_path),
                        line=i + 1
                    )
    
    def _run_semgrep(self) -> list[Finding]:
        """Run Semgrep and parse results."""
        try:
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", "--quiet", str(self.root)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if not result.stdout:
                return []
            
            try:
                semgrep_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                console.print("[yellow]Warning:[/] Semgrep output was not valid JSON — skipping")
                return []
            
            findings = []
            results = semgrep_data.get("results", [])
            
            # Severity mapping
            severity_map = {
                "ERROR": "critical",
                "WARNING": "high",
                "INFO": "medium"
            }
            
            for finding in results:
                rule_id = finding.get("check_id", "unknown")
                path = finding.get("path", "")
                start_line = finding.get("start", {}).get("line")
                extra = finding.get("extra", {})
                message = extra.get("message", "")
                semgrep_severity = extra.get("severity", "INFO")
                
                vs_severity = severity_map.get(semgrep_severity, "medium")
                
                # Create relative path
                try:
                    rel_path = str(Path(path).relative_to(self.root))
                except ValueError:
                    rel_path = path
                
                finding_obj = Finding(
                    rule_id=f"semgrep:{rule_id}",
                    name=f"Semgrep: {rule_id}",
                    severity=vs_severity,
                    message=message,
                    fix="Review and fix the security issue identified by Semgrep.",
                    file=rel_path,
                    line=start_line,
                    analyzer="security",
                    ecosystem="generic"
                )
                findings.append(finding_obj)
            
            return findings
            
        except FileNotFoundError:
            console.print(
                "[yellow]Warning:[/] Semgrep not installed — skipping deep security scan. "
                "Install with: pip install semgrep"
            )
            return []
        except subprocess.TimeoutExpired:
            console.print("[yellow]Warning:[/] Semgrep scan timed out (120s) — skipping")
            return []
        except Exception as e:
            console.print(f"[yellow]Warning:[/] Semgrep scan failed: {e}")
            return []
    
    def _deduplicate(self, findings: list[Finding]) -> list[Finding]:
        """Deduplicate findings, keeping the most detailed message."""
        if not findings:
            return []
        
        # Group by (file, line)
        from collections import defaultdict
        grouped: dict[tuple[str, int | None], list[Finding]] = defaultdict(list)
        
        for finding in findings:
            key = (finding.file, finding.line)
            grouped[key].append(finding)
        
        # For each group, keep the most detailed finding
        deduped = []
        for key, group in grouped.items():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                # Keep finding with longest message (most detailed)
                # Or prefer non-semgrep findings (our custom rules)
                custom_findings = [f for f in group if not f.rule_id.startswith("semgrep:")]
                if custom_findings:
                    deduped.append(max(custom_findings, key=lambda f: len(f.message)))
                else:
                    deduped.append(max(group, key=lambda f: len(f.message)))
        
        return deduped
