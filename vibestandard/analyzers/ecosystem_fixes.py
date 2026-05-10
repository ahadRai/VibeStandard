"""
Ecosystem-aware fix messages for observability rules.

Provides language-specific fix suggestions based on detected ecosystems.
"""

# Ecosystem-specific fix messages for each observability rule

STRUCTURED_LOGGING_FIXES = {
    "python": (
        "Add a structured logging library. Use loguru (pip install loguru) or the built-in logging module "
        "with a JSON formatter. Replace print() calls with logger.info(), logger.error() etc. "
        "Configure log level from an environment variable: LOG_LEVEL=INFO."
    ),
    "node": (
        "Add a structured logging library. Use winston (npm install winston) or pino (npm install pino). "
        "Replace console.log() calls with logger.info(), logger.error() etc. "
        "Configure log level from an environment variable: LOG_LEVEL=info."
    ),
    "java": (
        "Add a structured logging library. Use SLF4J with Logback or Log4j2. "
        "Replace System.out.println() calls with logger.info(), logger.error() etc. "
        "Configure log level from environment or application properties: logging.level.root=INFO."
    ),
    "go": (
        "Add a structured logging library. Use uber-go/zap (go get go.uber.org/zap) or "
        "sirupsen/logrus (go get github.com/sirupsen/logrus). "
        "Replace fmt.Println() calls with logger.Info(), logger.Error() etc. "
        "Configure log level from an environment variable: LOG_LEVEL=info."
    ),
}

ERROR_TRACKING_FIXES = {
    "python": (
        "Integrate Sentry — it has a generous free tier. Install with: pip install sentry-sdk. "
        "Then add to your app initialization: import sentry_sdk; "
        "sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN')). "
        "Alternatives: Rollbar, Bugsnag, Datadog APM."
    ),
    "node": (
        "Integrate Sentry — it has a generous free tier. Install with: npm install @sentry/node. "
        "Then add to your app initialization: const Sentry = require('@sentry/node'); "
        "Sentry.init({ dsn: process.env.SENTRY_DSN }). "
        "Alternatives: Rollbar, Bugsnag, Datadog APM."
    ),
    "java": (
        "Integrate Sentry — it has a generous free tier. Add to Maven: "
        "<dependency><groupId>io.sentry</groupId><artifactId>sentry</artifactId></dependency>. "
        "Then initialize: Sentry.init(options -> options.setDsn(System.getenv(\"SENTRY_DSN\"))). "
        "Alternatives: Rollbar, Bugsnag, Datadog APM."
    ),
    "go": (
        "Integrate Sentry — it has a generous free tier. Install with: go get github.com/getsentry/sentry-go. "
        "Then initialize: sentry.Init(sentry.ClientOptions{Dsn: os.Getenv(\"SENTRY_DSN\")}). "
        "Alternatives: Rollbar, Bugsnag, Datadog APM."
    ),
}

METRICS_FIXES = {
    "python": (
        "Add prometheus_client (pip install prometheus-client). Expose a /metrics endpoint and track "
        "at minimum: request count, request duration, and error rate. Connect to Grafana for dashboards. "
        "Alternatives: statsd, Datadog, OpenTelemetry."
    ),
    "node": (
        "Add prom-client (npm install prom-client). Expose a /metrics endpoint and track "
        "at minimum: request count, request duration, and error rate. Connect to Grafana for dashboards. "
        "Alternatives: statsd, Datadog, OpenTelemetry."
    ),
    "java": (
        "Add Micrometer (spring-boot-starter-actuator includes it). Expose a /actuator/prometheus endpoint "
        "and track at minimum: request count, request duration, and error rate. "
        "Connect to Grafana for dashboards. Alternatives: Dropwizard Metrics, Datadog, OpenTelemetry."
    ),
    "go": (
        "Add prometheus/client_golang (go get github.com/prometheus/client_golang). "
        "Expose a /metrics endpoint and track at minimum: request count, request duration, and error rate. "
        "Connect to Grafana for dashboards. Alternatives: statsd, Datadog, OpenTelemetry."
    ),
}

# Generic fallbacks if ecosystem not detected
GENERIC_FIXES = {
    "structured_logging": (
        "Add a structured logging library appropriate for your language stack. "
        "Replace print/console.log/System.out statements with proper logging calls. "
        "Configure log level from an environment variable."
    ),
    "error_tracking": (
        "Integrate an error tracking service like Sentry, Rollbar, or Bugsnag. "
        "These services have generous free tiers and take minutes to set up. "
        "They provide real-time error notifications with stack traces and context."
    ),
    "metrics": (
        "Add metrics instrumentation using Prometheus, Datadog, or similar. "
        "Expose a /metrics endpoint and track at minimum: request count, "
        "request duration, and error rate. Connect to Grafana for dashboards."
    ),
}


def get_ecosystem_fix(rule_id: str, ecosystems: list[str] | None = None) -> str:
    """
    Get ecosystem-aware fix message for a rule.
    
    Args:
        rule_id: The observability rule ID
        ecosystems: List of detected ecosystems (python, node, java, go, docker, generic)
    
    Returns:
        Ecosystem-specific fix message, or generic fallback
    """
    if not ecosystems:
        ecosystems = ["generic"]
    
    fix_map = {
        "no-structured-logging": STRUCTURED_LOGGING_FIXES,
        "no-error-tracking": ERROR_TRACKING_FIXES,
        "no-metrics-endpoint": METRICS_FIXES,
    }
    
    generic_map = {
        "no-structured-logging": GENERIC_FIXES["structured_logging"],
        "no-error-tracking": GENERIC_FIXES["error_tracking"],
        "no-metrics-endpoint": GENERIC_FIXES["metrics"],
    }
    
    fixes = fix_map.get(rule_id)
    if not fixes:
        return generic_map.get(rule_id, "")
    
    # Try to find a match for detected ecosystems
    for eco in ecosystems:
        eco_lower = eco.lower()
        if eco_lower in fixes:
            return fixes[eco_lower]
    
    # Return generic fallback
    return generic_map.get(rule_id, "")
