"""
Infra Analyzer — scans containerization and deployment configs for production-readiness issues.

Implements 12 rules covering Docker, Docker Compose, Kubernetes, and CI/CD pipelines.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from rich.console import Console

from vibestandard.analyzers.base import BaseAnalyzer
from vibestandard.models import Finding

console = Console(stderr=True)

# Files and directories to skip
_SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__"}
_MAX_FILE_SIZE = 200 * 1024  # 200KB

# Database images that need volumes
_DB_IMAGES = {"postgres", "mysql", "mariadb", "mongodb", "mongo", "redis", "elasticsearch"}

# Dev tooling services that don't need restart policy
_DEV_SERVICES = {"adminer", "phpmyadmin", "mailhog"}

# Secret variable patterns
_SECRET_PATTERNS = {"PASSWORD", "SECRET", "API_KEY", "TOKEN", "PRIVATE_KEY", "DATABASE_URL"}

# Hardcoded rule definitions
INFRA_RULES = {
    "docker-run-as-root": {
        "name": "Docker container runs as root",
        "severity": "high",
        "message": "Dockerfile has no USER instruction — container runs as root. If the container is compromised, the attacker has root-level access to the host system.",
        "fix": "Add a non-root user before the final CMD or ENTRYPOINT: RUN addgroup --system app && adduser --system --ingroup app app then USER app"
    },
    "no-healthcheck": {
        "name": "No HEALTHCHECK in Dockerfile",
        "severity": "medium",
        "message": "Dockerfile has no HEALTHCHECK instruction. Docker and orchestrators cannot detect if your application has crashed inside the container.",
        "fix": "Add a HEALTHCHECK instruction: HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8080/health || exit 1"
    },
    "latest-image-tag": {
        "name": "Image uses :latest tag or no tag",
        "severity": "high",
        "message": "Image uses the :latest tag or no tag. The :latest tag is mutable — upstream can push a breaking change at any time and your next deployment will silently use a different image.",
        "fix": "Pin to a specific immutable version tag: FROM python:3.13.1-slim instead of FROM python:latest. Check Docker Hub for available version tags."
    },
    "db-no-volume": {
        "name": "Database service has no volume",
        "severity": "critical",
        "message": "Database service '{service_name}' has no volume mapping. All data will be permanently lost every time the container restarts or is recreated.",
        "fix": "Add a named volume to the service:\n  volumes:\n    - postgres_data:/var/lib/postgresql/data\nAnd declare the volume at the top level:\nvolumes:\n  postgres_data:"
    },
    "no-restart-policy": {
        "name": "Service has no restart policy",
        "severity": "medium",
        "message": "Service '{service_name}' has no restart policy. If it crashes in production it will stay down until manually restarted.",
        "fix": "Add restart: unless-stopped to the service. For critical services consider restart: always."
    },
    "no-resource-limits": {
        "name": "Service has no resource limits",
        "severity": "medium",
        "message": "Service '{service_name}' has no memory or CPU resource limits. A memory leak or traffic spike can take down the entire host.",
        "fix": "Add resource limits under deploy:\n  deploy:\n    resources:\n      limits:\n        memory: 512M\n        cpus: '0.5'"
    },
    "secrets-as-env-vars": {
        "name": "Secrets hardcoded as env vars",
        "severity": "high",
        "message": "Service '{service_name}' has secret '{var_name}' hardcoded as a plain environment variable in docker-compose.yml. Anyone with access to this file has the secret.",
        "fix": "Use variable substitution instead: POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}. Store the actual value in a .env file that is listed in .gitignore and never committed."
    },
    "missing-dockerignore": {
        "name": "Missing .dockerignore file",
        "severity": "low",
        "message": "No .dockerignore file found. The entire project directory is sent to the Docker build daemon, including node_modules, .git, and any local secrets.",
        "fix": "Create a .dockerignore file alongside your Dockerfile. At minimum include: .git, node_modules, venv, .env, __pycache__, *.pyc, .pytest_cache"
    },
    "no-multi-stage-build": {
        "name": "No multi-stage Docker build",
        "severity": "low",
        "message": "Dockerfile uses a single build stage. The final image likely contains build tools, compilers, and dev dependencies that are not needed at runtime.",
        "fix": "Use a multi-stage build: use one stage to build/compile and a second minimal stage to run. This can reduce image size by 70-90%."
    },
    "compose-only-no-k8s": {
        "name": "Only Docker Compose, no cloud deployment config",
        "severity": "low",
        "message": "Only a docker-compose.yml is present with no cloud or Kubernetes deployment configuration. Docker Compose is not suitable for production-scale or highly available deployments.",
        "fix": "For production, consider deploying to a managed platform (Railway, Render, Fly.io) with a config file, or write Kubernetes manifests or a Helm chart for more control."
    },
    "no-ci-pipeline": {
        "name": "No CI/CD pipeline configured",
        "severity": "medium",
        "message": "No CI/CD pipeline configuration found. Code is being deployed without automated testing, building, or validation.",
        "fix": "Add a GitHub Actions workflow at .github/workflows/ci.yml that runs your tests on every push and pull request before allowing deployment."
    },
    "port-bound-to-all-interfaces": {
        "name": "Database port exposed to host",
        "severity": "medium",
        "message": "Database service '{service_name}' exposes port {port} to the host. Database ports should never be publicly accessible.",
        "fix": "Remove the ports: mapping from database services entirely. Application services on the same Docker network can reach the database by service name without exposing the port to the host."
    }
}


class InfraAnalyzer(BaseAnalyzer):
    """Analyzes infrastructure configuration for production-readiness issues."""
    
    name = "infra"
    ecosystem = "docker"
    
    def analyze(self) -> list[Finding]:
        """Run all infrastructure checks."""
        # Get files to scan
        dockerfiles = self._get_dockerfiles()
        compose_files = self._get_compose_files()
        
        # Run Dockerfile checks
        self._check_docker_run_as_root(dockerfiles)
        self._check_no_healthcheck(dockerfiles)
        self._check_latest_image_tag(dockerfiles, compose_files)
        self._check_missing_dockerignore(dockerfiles)
        self._check_no_multi_stage_build(dockerfiles)
        
        # Run Compose checks
        self._check_db_no_volume(compose_files)
        self._check_no_restart_policy(compose_files)
        self._check_no_resource_limits(compose_files)
        self._check_secrets_as_env_vars(compose_files)
        self._check_port_bound_to_all_interfaces(compose_files)
        
        # Run project-level checks
        self._check_compose_only_no_k8s(compose_files)
        self._check_no_ci_pipeline()
        
        return self.findings
    
    def _add_infra_finding(self, rule_id: str, file: str, line: int | None = None, **kwargs) -> None:
        """Add an infra finding with optional message formatting."""
        rule = INFRA_RULES.get(rule_id)
        if not rule:
            return
        
        message = rule["message"].format(**kwargs) if kwargs else rule["message"]
        fix = rule["fix"].format(**kwargs) if kwargs else rule["fix"]
        
        finding = Finding(
            rule_id=rule_id,
            name=rule["name"],
            severity=rule["severity"],
            message=message,
            fix=fix,
            file=file,
            line=line,
            analyzer=self.name,
            ecosystem=self.ecosystem,
        )
        self.findings.append(finding)
    
    # ---- File Discovery ----
    
    def _get_dockerfiles(self) -> list[Path]:
        """Find all Dockerfile variants."""
        dockerfiles = []
        for rel_path in self.file_tree:
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            if rel_path.name.startswith("Dockerfile") or rel_path.name.endswith(".dockerfile"):
                # Skip files larger than 200KB
                abs_path = self.root / rel_path
                try:
                    if abs_path.stat().st_size <= _MAX_FILE_SIZE:
                        dockerfiles.append(rel_path)
                except OSError:
                    continue
        return dockerfiles
    
    def _get_compose_files(self) -> list[Path]:
        """Find all Docker Compose files."""
        compose_files = []
        for rel_path in self.file_tree:
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            if rel_path.name.startswith("docker-compose"):
                # Skip files larger than 200KB
                abs_path = self.root / rel_path
                try:
                    if abs_path.stat().st_size <= _MAX_FILE_SIZE:
                        compose_files.append(rel_path)
                except OSError:
                    continue
        return compose_files
    
    def _get_k8s_files(self) -> list[Path]:
        """Find Kubernetes manifests."""
        k8s_files = []
        for rel_path in self.file_tree:
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            if (rel_path.name.endswith(".k8s.yml") or rel_path.name.endswith(".k8s.yaml") or
                "kubernetes" in rel_path.parts or "k8s" in rel_path.parts):
                k8s_files.append(rel_path)
        return k8s_files
    
    def _get_ci_files(self) -> list[Path]:
        """Find CI/CD configuration files."""
        ci_patterns = {
            ".gitlab-ci.yml", "Jenkinsfile", "bitbucket-pipelines.yml",
            ".travis.yml", "azure-pipelines.yml"
        }
        ci_files = []
        for rel_path in self.file_tree:
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            # GitHub Actions
            if rel_path.parts[0] == ".github" and len(rel_path.parts) > 1 and rel_path.parts[1] == "workflows":
                if rel_path.suffix in {".yml", ".yaml"}:
                    ci_files.append(rel_path)
            # Other CI files
            elif rel_path.name in ci_patterns:
                ci_files.append(rel_path)
            # CircleCI
            elif rel_path.parts[0] == ".circleci" and rel_path.name == "config.yml":
                ci_files.append(rel_path)
            # Makefile with deploy/ci targets
            elif rel_path.name == "Makefile":
                content = self.read_file_safe(self.root / rel_path)
                if content and re.search(r'^(deploy|ci)\s*:', content, re.MULTILINE):
                    ci_files.append(rel_path)
        return ci_files
    
    # ---- Parsers ----
    
    def _parse_dockerfile_instructions(self, content: str) -> list[tuple[str, str]]:
        """Parse Dockerfile into list of (INSTRUCTION, arguments) tuples."""
        instructions = []
        lines = content.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Handle line continuations
            while line.endswith("\\") and i < len(lines):
                line = line[:-1] + " " + lines[i].strip()
                i += 1
            
            # Split instruction from arguments
            parts = line.split(None, 1)
            if len(parts) == 2:
                instructions.append((parts[0].upper(), parts[1]))
            elif len(parts) == 1:
                instructions.append((parts[0].upper(), ""))
        
        return instructions
    
    def _parse_yaml_safe(self, path: Path) -> dict | None:
        """Safely parse a YAML file."""
        try:
            content = self.read_file_safe(path)
            if content is None:
                return None
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            console.print(f"[yellow]Warning:[/] Malformed YAML in {path}: {e}")
            return None
    
    # ---- Rule Checks ----
    
    def _check_docker_run_as_root(self, dockerfiles: list[Path]) -> None:
        """Rule 1: Flag Dockerfiles without USER instruction."""
        for rel_path in dockerfiles:
            content = self.read_file_safe(self.root / rel_path)
            if not content:
                continue
            
            instructions = self._parse_dockerfile_instructions(content)
            
            # Find last FROM instruction
            last_from_idx = -1
            for i, (instr, _) in enumerate(instructions):
                if instr == "FROM":
                    last_from_idx = i
            
            # Check if USER exists after last FROM
            has_user = False
            for i in range(last_from_idx + 1, len(instructions)):
                if instructions[i][0] == "USER":
                    user_value = instructions[i][1].strip()
                    # Check if it's a non-root user
                    if user_value and user_value not in {"root", "0"}:
                        has_user = True
                        break
            
            if not has_user:
                self._add_infra_finding("docker-run-as-root", str(rel_path))
    
    def _check_no_healthcheck(self, dockerfiles: list[Path]) -> None:
        """Rule 2: Flag Dockerfiles without HEALTHCHECK instruction."""
        for rel_path in dockerfiles:
            content = self.read_file_safe(self.root / rel_path)
            if not content:
                continue
            
            instructions = self._parse_dockerfile_instructions(content)
            has_healthcheck = any(instr == "HEALTHCHECK" for instr, _ in instructions)
            
            if not has_healthcheck:
                self._add_infra_finding("no-healthcheck", str(rel_path))
    
    def _check_latest_image_tag(self, dockerfiles: list[Path], compose_files: list[Path]) -> None:
        """Rule 3: Flag :latest or untagged images."""
        # Check Dockerfiles
        for rel_path in dockerfiles:
            content = self.read_file_safe(self.root / rel_path)
            if not content:
                continue
            
            instructions = self._parse_dockerfile_instructions(content)
            for instr, args in instructions:
                if instr == "FROM":
                    image = args.split()[0] if args else ""
                    # Skip scratch (special keyword)
                    if image == "scratch":
                        continue
                    # Flag if :latest or no tag
                    if image.endswith(":latest") or (":" not in image and "@" not in image):
                        self._add_infra_finding("latest-image-tag", str(rel_path))
                        break
        
        # Check Compose files
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                image = service_config.get("image", "")
                if image and (image.endswith(":latest") or (":" not in image and "@" not in image)):
                    self._add_infra_finding("latest-image-tag", str(rel_path))
                    break
    
    def _check_db_no_volume(self, compose_files: list[Path]) -> None:
        """Rule 4: Flag database services without volumes."""
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                
                image = service_config.get("image", "").lower()
                is_db = any(db in image for db in _DB_IMAGES)
                
                if is_db and "volumes" not in service_config:
                    self._add_infra_finding(
                        "db-no-volume",
                        str(rel_path),
                        service_name=service_name
                    )
    
    def _check_no_restart_policy(self, compose_files: list[Path]) -> None:
        """Rule 5: Flag services without restart policy."""
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                
                # Skip dev tooling
                image = service_config.get("image", "").lower()
                if any(dev in image for dev in _DEV_SERVICES):
                    continue
                
                if "restart" not in service_config:
                    self._add_infra_finding(
                        "no-restart-policy",
                        str(rel_path),
                        service_name=service_name
                    )
    
    def _check_no_resource_limits(self, compose_files: list[Path]) -> None:
        """Rule 6: Flag services without resource limits."""
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                
                # Check for mem_limit (legacy) or deploy.resources.limits
                has_limits = "mem_limit" in service_config
                
                if not has_limits:
                    deploy = service_config.get("deploy", {})
                    if isinstance(deploy, dict):
                        resources = deploy.get("resources", {})
                        if isinstance(resources, dict) and "limits" in resources:
                            has_limits = True
                
                if not has_limits:
                    self._add_infra_finding(
                        "no-resource-limits",
                        str(rel_path),
                        service_name=service_name
                    )
    
    def _check_secrets_as_env_vars(self, compose_files: list[Path]) -> None:
        """Rule 7: Flag hardcoded secrets in environment variables."""
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                
                env = service_config.get("environment", {})
                if not isinstance(env, (dict, list)):
                    continue
                
                # Handle list format: ["KEY=value", ...]
                if isinstance(env, list):
                    env_dict = {}
                    for item in env:
                        if "=" in str(item):
                            key, value = str(item).split("=", 1)
                            env_dict[key] = value
                    env = env_dict
                
                for var_name, var_value in env.items():
                    # Check if variable name contains secret patterns
                    if any(pattern in var_name.upper() for pattern in _SECRET_PATTERNS):
                        # Skip if using ${VAR} syntax
                        if isinstance(var_value, str) and var_value.startswith("${") and var_value.endswith("}"):
                            continue
                        # Flag hardcoded secrets
                        if var_value and isinstance(var_value, str) and len(var_value) > 0:
                            self._add_infra_finding(
                                "secrets-as-env-vars",
                                str(rel_path),
                                service_name=service_name,
                                var_name=var_name
                            )
    
    def _check_missing_dockerignore(self, dockerfiles: list[Path]) -> None:
        """Rule 8: Flag missing .dockerignore file."""
        if not dockerfiles:
            return
        
        # Check if .dockerignore exists at root level
        has_dockerignore = any(f.name == ".dockerignore" for f in self.file_tree)
        
        if not has_dockerignore:
            # Report on the first Dockerfile
            self._add_infra_finding("missing-dockerignore", str(dockerfiles[0]))
    
    def _check_no_multi_stage_build(self, dockerfiles: list[Path]) -> None:
        """Rule 9: Flag single-stage builds for compiled languages."""
        # Check if project has build tools
        has_build_tools = any(
            f.name in {"package.json", "pom.xml", "build.gradle", "build.gradle.kts", "go.mod"}
            for f in self.file_tree
        )
        
        if not has_build_tools:
            return
        
        for rel_path in dockerfiles:
            content = self.read_file_safe(self.root / rel_path)
            if not content:
                continue
            
            instructions = self._parse_dockerfile_instructions(content)
            from_count = sum(1 for instr, _ in instructions if instr == "FROM")
            
            # Only one FROM instruction
            if from_count != 1:
                continue
            
            # Check if base image is alpine or slim
            for instr, args in instructions:
                if instr == "FROM":
                    image = args.split()[0] if args else ""
                    if "alpine" in image or "slim" in image:
                        return  # Python slim/alpine is already minimal
            
            self._add_infra_finding("no-multi-stage-build", str(rel_path))
    
    def _check_compose_only_no_k8s(self, compose_files: list[Path]) -> None:
        """Rule 10: Flag projects with only docker-compose."""
        if not compose_files:
            return
        
        # Check for deployment configs
        k8s_files = self._get_k8s_files()
        
        deployment_patterns = {
            "*.tf", "fly.toml", "railway.toml", "render.yaml",
            "app.yaml", "Procfile"
        }
        
        has_deployment_config = bool(k8s_files)
        
        for rel_path in self.file_tree:
            if any(rel_path.match(pattern) for pattern in deployment_patterns):
                has_deployment_config = True
                break
        
        if not has_deployment_config:
            self._add_infra_finding("compose-only-no-k8s", str(compose_files[0]))
    
    def _check_no_ci_pipeline(self) -> None:
        """Rule 11: Flag missing CI/CD configuration."""
        ci_files = self._get_ci_files()
        
        if not ci_files:
            # Use root as the "file" for this finding
            self._add_infra_finding("no-ci-pipeline", str(self.root / "README.md"))
    
    def _check_port_bound_to_all_interfaces(self, compose_files: list[Path]) -> None:
        """Rule 12: Flag database services with exposed ports."""
        for rel_path in compose_files:
            compose_data = self._parse_yaml_safe(self.root / rel_path)
            if not compose_data:
                continue
            
            services = compose_data.get("services", {})
            if not isinstance(services, dict):
                continue
            
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    continue
                
                image = service_config.get("image", "").lower()
                is_db = any(db in image for db in _DB_IMAGES)
                
                if not is_db:
                    continue
                
                ports = service_config.get("ports", [])
                if not isinstance(ports, list):
                    continue
                
                for port_mapping in ports:
                    port_str = str(port_mapping)
                    
                    # Flag if format is "0.0.0.0:PORT:PORT" or "PORT:PORT"
                    # Do NOT flag "127.0.0.1:PORT:PORT" (localhost only)
                    if port_str.startswith("0.0.0.0:"):
                        # Explicit all-interfaces binding
                        parts = port_str.split(":")
                        if len(parts) >= 2:
                            self._add_infra_finding(
                                "port-bound-to-all-interfaces",
                                str(rel_path),
                                service_name=service_name,
                                port=parts[-1]
                            )
                            break
                    elif port_str.count(":") == 1 and not port_str.startswith("127.0.0.1"):
                        # Format "PORT:PORT" without explicit IP - binds to all interfaces
                        parts = port_str.split(":")
                        self._add_infra_finding(
                            "port-bound-to-all-interfaces",
                            str(rel_path),
                            service_name=service_name,
                            port=parts[-1]
                        )
                        break
