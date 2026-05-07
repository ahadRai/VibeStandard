

---

## **The Core Concept**

VibeStandard is a **static \+ dynamic analysis tool** that takes a codebase (or repo URL) and outputs a scored report across multiple production-readiness dimensions. Think of it as a linter, but instead of style, it checks whether the code is actually deployable.

---

## **Architecture Overview---**

## **The 5 Analyzers — What to Check**

### **1\. Dependency Analyzer (your H2 problem lives here)**

This is the most important one for catching vibe-coded naivety. It reads `pom.xml`, `build.gradle`, `package.json`, `requirements.txt`, `pyproject.toml`, etc.

**Rules to implement:**

| Flag | Severity | Example |
| ----- | ----- | ----- |
| In-memory / dev database in prod config | Critical | H2, SQLite, Derby |
| Pinned to `latest` or no version | High | `"express": "latest"` |
| Dev dependency in prod bundle | High | `nodemon` in `dependencies` |
| Known CVE in dependency | Critical | Via OSV / Snyk API |
| No lock file present | Medium | Missing `package-lock.json` |
| Deprecated package | Low | `request` npm package |

For database detection specifically, scan for H2, HSQLDB, Derby, SQLite, and `file:` JDBC URLs in any config file. Flag them as **"test-grade database"** with a critical severity.

---

### **2\. Config Analyzer**

Reads environment config files: `application.properties`, `application.yml`, `.env`, `config.py`, `appsettings.json`, Docker Compose files, etc.

**Rules:**

* `spring.datasource.url` pointing to `h2:mem` or `jdbc:h2`  
* `DEBUG=True` / `debug: true` without an environment guard  
* Hardcoded secrets (passwords, API keys, tokens) — use regex patterns like `password=`, `secret=`, `apiKey=`  
* `spring.jpa.ddl-auto=create-drop` (nukes the DB on restart)  
* `ALLOWED_HOSTS=*` in Django  
* CORS set to `*` unconditionally  
* No separate prod/dev config profiles — single flat config file

---

### **3\. Security Analyzer**

This goes beyond config and reads the actual code.

**Rules:**

* SQL concatenation (not parameterized queries): `"SELECT * FROM users WHERE id=" + userId`  
* Disabled CSRF protection  
* JWT with `alg: none` or hardcoded secret  
* `eval()` on user input  
* No input validation on API endpoints  
* Missing `helmet` (Node) or `SECURE_*` settings (Django)  
* Passwords stored without hashing (no bcrypt/argon2 import)  
* `ssl_verify=False` or `verify=False` in HTTP clients  
* Exposed stack traces in error handlers

---

### **4\. Infra Analyzer**

Reads `Dockerfile`, `docker-compose.yml`, Kubernetes YAML, Terraform, etc.

**Rules:**

* Running as root in Docker (`USER` instruction missing)  
* `docker-compose.yml` present but no production override file  
* No health checks defined  
* Database container has no volume mount (data is ephemeral)  
* `restart: unless-stopped` missing on critical services  
* No resource limits (CPU/memory)  
* Secrets passed as plain env vars in compose instead of Docker secrets  
* Using `:latest` image tag

---

### **5\. Observability Analyzer**

Checks whether the app can be monitored in production.

**Rules:**

* No structured logging library (just `console.log` or `print`)  
* No error tracking (Sentry, Rollbar, etc.)  
* No health/readiness endpoint (`/health`, `/ping`, `/ready`)  
* No metrics endpoint (Prometheus, Datadog)  
* Logs written to files with no rotation strategy  
* No request ID / correlation ID middleware

---

## **The Scoring Engine**

Give each finding a severity weight:

Critical  \= \-30 points  
High      \= \-15 points  
Medium    \=  \-7 points  
Low       \=  \-3 points

Start at 100\. Clamp at 0\. Map to a grade:

90–100 → A  (Production-ready)  
75–89  → B  (Minor issues)  
55–74  → C  (Needs work before deployment)  
30–54  → D  (Significant risks)  
0–29   → F  (Not production-grade)

Also produce a **"VibeScore"** label: `TEST_GRADE`, `STAGING_READY`, or `PRODUCTION_READY`.

---

## **Tech Stack to Build It**

**Option A — CLI tool (Python, fastest to build)**

vibecheck/  
├── cli.py              \# Entry point (click or typer)  
├── ingestion/  
│   ├── loader.py       \# Git clone, ZIP, or local path  
│   └── file\_tree.py    \# Walk \+ classify files  
├── analyzers/  
│   ├── base.py         \# Abstract Analyzer class  
│   ├── dependency.py  
│   ├── config.py  
│   ├── security.py  
│   ├── infra.py  
│   └── observability.py  
├── engine/  
│   ├── scorer.py       \# Aggregate findings → score  
│   └── rules.py        \# Rule definitions (YAML-driven)  
├── reporters/  
│   ├── cli\_reporter.py \# Rich terminal output  
│   ├── json\_reporter.py  
│   └── html\_reporter.py  
└── rules/  
    ├── java.yaml  
    ├── node.yaml  
    ├── python.yaml  
    └── docker.yaml

Use **`rich`** for beautiful CLI output, **`PyYAML`** for rules, **`gitpython`** for repo cloning, and **`semgrep`** (open source) as the AST-level code scanner underneath your security analyzer.

**Option B — Web app (Next.js \+ API routes)**

Lets people paste a GitHub URL and get a badge. Add GitHub Actions integration later so it runs on every push.

**Option C — GitHub App**

The most powerful — runs automatically on PRs and posts a comment with the VibeCheck report. Use Probot or Octokit.

---

## **Rules-as-YAML Design**

The key architectural decision is making rules declarative, not hardcoded. This way you can add new rules without touching code:

\# rules/java.yaml  
\- id: h2-database  
  name: H2 in-memory database detected  
  severity: critical  
  message: \>  
    H2 is a development/test database and is not suitable for production.  
    Replace with PostgreSQL, MySQL, or another production-grade database.  
  fix: "Change spring.datasource.url to a PostgreSQL connection string"  
  match:  
    files: \["\*.properties", "\*.yml", "\*.yaml"\]  
    pattern: "h2:mem|jdbc:h2|com.h2database"

\- id: ddl-create-drop  
  name: JPA DDL auto set to create-drop  
  severity: critical  
  match:  
    files: \["\*.properties", "\*.yml"\]  
    pattern: "ddl-auto=create-drop|ddl-auto: create-drop"

---

## **Build Order (Recommended)**

1. **Week 1:** CLI skeleton \+ file ingestion \+ dependency analyzer (catches the H2 problem). This alone is already useful.  
2. **Week 2:** Config analyzer \+ basic scoring \+ `rich` terminal report.  
3. **Week 3:** Security analyzer (integrate Semgrep for the heavy lifting).  
4. **Week 4:** Infra \+ observability analyzers.  
5. **Week 5:** HTML report output \+ GitHub Action integration.  
6. **Week 6:** Web UI with drag-and-drop ZIP upload.

---

## **Making it Smarter with AI**

Since you're building a tool *for* vibe-coded software, you can use an LLM as one of your analyzers. After the static rules run, pass the top findings \+ relevant code snippets to Claude/GPT and ask it to:

* Explain *why* this is a problem in plain English  
* Suggest a concrete fix with a code snippet  
* Rate whether the overall codebase structure suggests a junior/vibe-coder or experienced developer

This gives you **context-aware explanations** rather than just rule IDs.

---

## **Quick Win — Start Here**

Your first working version can be just 3 files:

\# vibecheck.py  
import re, sys  
from pathlib import Path

CRITICAL\_PATTERNS \= {  
    "H2 database (test-grade)": r"h2:mem|jdbc:h2|com\\.h2database",  
    "Hardcoded password":        r"password\\s\*=\\s\*\['\\"\]\[^'\\"\]{4,}",  
    "debug=True in config":      r"(?i)debug\\s\*=\\s\*true",  
    "create-drop DDL":           r"ddl-auto\\s\*\[=:\]\\s\*create-drop",  
    "CORS allow all":            r"ALLOWED\_ORIGINS\\s\*=\\s\*\\\*|cors\\(.\*\\\*.\*\\)",  
    "SSL verify disabled":       r"verify\\s\*=\\s\*False|ssl\_verify\\s\*=\\s\*False",  
}

path \= Path(sys.argv\[1\])  
findings \= \[\]  
for f in path.rglob("\*"):  
    if f.is\_file() and f.suffix in \['.py','.java','.properties','.yml','.yaml','.env','.json','.xml'\]:  
        text \= f.read\_text(errors='ignore')  
        for name, pattern in CRITICAL\_PATTERNS.items():  
            if re.search(pattern, text):  
                findings.append((name, str(f)))

if findings:  
    print("🚨 CRITICAL ISSUES FOUND:")  
    for name, file in findings:  
        print(f"  \[{name}\] in {file}")  
else:  
    print("✅ No critical issues detected")

Run it: `python vibestandard.py ./my-vibecoded-project`

This catches your exact H2 problem on day one. Then layer everything else on top.

---

The key insight that makes this valuable is the **rules-as-YAML** design — every new bad pattern you encounter in vibe-coded software becomes a new rule, and the tool gets smarter over time. You could even open-source the rules and let the community contribute.

