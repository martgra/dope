from dope.models.domain.scope import (
    DocSectionTemplate,
    DocTemplate,
    FreshnessLevel,
    UpdateTriggers,
)
from dope.models.enums import DocTemplateKey, ProjectTier, SectionAudience, SectionTheme

TIERS = [ProjectTier.large, ProjectTier.massive]

deployment_guide = DocTemplate(
    description="Procedures for manual and automated deployments, including rollback steps.",
    tiers=TIERS,
    sections={
        "environment_matrix": DocSectionTemplate(
            description="List of target environments (dev, staging, prod) and their configurations",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", ".github/**/*", "Dockerfile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"environment", "staging", "production", "dev"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "manual_deployment_steps": DocSectionTemplate(
            description="Step-by-step instructions for performing a manual rollout",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["Makefile", "scripts/**/*", "*.yaml"],
                change_types={"deployment"},
                min_magnitude=0.4,
                relevant_terms={"deploy", "manual", "rollout", "procedure"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "automated_deployment": DocSectionTemplate(
            description="How CI/CD pipelines or scripts deploy to each environment",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "scripts/**/*", "Makefile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"automated", "ci", "cd", "pipeline"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "rollback_and_recovery": DocSectionTemplate(
            description="Procedures to revert or recover from a failed release",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "scripts/**/*"],
                change_types={"deployment"},
                min_magnitude=0.3,
                relevant_terms={"rollback", "recovery", "revert", "failure"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "post_deploy_validation": DocSectionTemplate(
            description="Checks and smoke-tests to verify a successful deployment",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["tests/**/*.py", "scripts/**/*"],
                change_types={"testing", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"validation", "smoke test", "verify", "check"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
    },
)

operations_runbooks = DocTemplate(
    description="Operational procedures for service management, monitoring, and incident response.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.support],
    sections={
        "service_controls": DocSectionTemplate(
            description="Commands or API calls to start, stop, and restart services",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/cli/*.py", "scripts/**/*", "Makefile"],
                change_types={"cli", "api"},
                min_magnitude=0.4,
                relevant_terms={"service", "start", "stop", "restart", "control"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "health_checks_and_alerts": DocSectionTemplate(
            description="How to interpret health endpoints, dashboards, and set alerts",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "*.yaml"],
                change_types={"feature", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"health", "alert", "monitoring", "dashboard"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "scaling_procedures": DocSectionTemplate(
            description="Steps to scale components horizontally or vertically",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", "Dockerfile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"scale", "scaling", "horizontal", "vertical"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "backup_and_restore": DocSectionTemplate(
            description="Backup locations, retention policies, and restore instructions",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["scripts/**/*", "*.yaml"],
                change_types={"configuration"},
                min_magnitude=0.3,
                relevant_terms={"backup", "restore", "retention", "recovery"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "incident_response": DocSectionTemplate(
            description="Troubleshooting flowcharts, common failure resolutions, "
            "and escalation paths",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py"],
                change_types={"bugfix", "feature"},
                min_magnitude=0.3,
                relevant_terms={"incident", "troubleshoot", "failure", "escalation"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
    },
)

security_compliance = DocTemplate(
    description="Security policies, authentication/authorization flows, "
    "and compliance requirements.",
    tiers=TIERS,
    roles=[SectionAudience.compliance, SectionAudience.engineering],
    sections={
        "authn_authz_flows": DocSectionTemplate(
            description="Overview of authentication and authorization mechanisms",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "dope/core/*.py"],
                change_types={"security", "api"},
                min_magnitude=0.5,
                relevant_terms={"authentication", "authorization", "auth", "security"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "encryption_and_secrets": DocSectionTemplate(
            description="Encryption at rest/in transit and secret-management best practices",
            themes=[SectionTheme.governance, SectionTheme.technical],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml", ".env*"],
                change_types={"security", "configuration"},
                min_magnitude=0.5,
                relevant_terms={"encryption", "secret", "security", "credentials"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "vulnerability_scanning": DocSectionTemplate(
            description="Tools, schedules, and processes for scanning code and containers",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "pyproject.toml", "Dockerfile"],
                change_types={"security", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"vulnerability", "scan", "security", "cve"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "compliance_requirements": DocSectionTemplate(
            description="Regulatory controls (GDPR, PCI, HIPAA) and how they're enforced",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml"],
                change_types={"security", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"compliance", "gdpr", "regulatory", "policy"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "audit_and_logging": DocSectionTemplate(
            description="Audit-log locations, retention, and how to review for compliance",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml"],
                change_types={"security", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"audit", "log", "compliance", "retention"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
    },
)

performance_tuning = DocTemplate(
    description="Guidance on profiling, caching, and resource optimization for performance.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "profiling_and_benchmarking": DocSectionTemplate(
            description="How to profile services and interpret benchmark results",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "tests/**/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"profile", "benchmark", "performance", "optimize"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "caching_strategies": DocSectionTemplate(
            description="Approaches for in-memory, CDN, and DB caching to reduce latency",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "dope/core/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"cache", "caching", "performance", "latency"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "database_optimization": DocSectionTemplate(
            description="Indexing, query tuning, and connection-pool best practices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/repositories/**/*.py", "dope/models/**/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"database", "query", "optimization", "index"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "resource_allocation": DocSectionTemplate(
            description="Guidance on CPU, memory, and network resource quotas",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", "Dockerfile"],
                change_types={"configuration", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"resource", "cpu", "memory", "quota"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "tuning_guidelines": DocSectionTemplate(
            description="General tips for improving throughput and reducing contention",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"tuning", "performance", "throughput", "optimization"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
    },
)

monitoring_metrics = DocTemplate(
    description="Setup and interpretation of monitoring dashboards, alerts, and SLO definitions.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "monitoring_setup": DocSectionTemplate(
            description="How to configure metric collectors and exporters",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", "dope/services/**/*.py"],
                change_types={"configuration", "feature"},
                min_magnitude=0.3,
                relevant_terms={"monitoring", "metrics", "collector", "exporter"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "dashboards_and_visualizations": DocSectionTemplate(
            description="Pre-built dashboards and instructions for customizing views",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.json"],
                change_types={"configuration", "feature"},
                min_magnitude=0.2,
                relevant_terms={"dashboard", "visualization", "monitoring", "metrics"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "alerting_and_slo": DocSectionTemplate(
            description="Defining SLOs/SLAs and configuring alerts on key metrics",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"alert", "slo", "sla", "monitoring"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "log_aggregation": DocSectionTemplate(
            description="Centralized logging architecture and query examples",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "dope/**/*.py"],
                change_types={"configuration", "feature"},
                min_magnitude=0.3,
                relevant_terms={"log", "logging", "aggregation", "centralized"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "metric_collection": DocSectionTemplate(
            description="List of key metrics (latency, error rates, capacity) "
            "and how they're gathered",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "*.yaml"],
                change_types={"feature", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"metric", "collection", "monitoring", "observability"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
    },
)

large = {
    DocTemplateKey.deployment_guide: deployment_guide,
    DocTemplateKey.monitoring_metrics: monitoring_metrics,
    DocTemplateKey.operations_runbooks: operations_runbooks,
    DocTemplateKey.performance_tuning: performance_tuning,
    DocTemplateKey.security_compliance: security_compliance,
}
