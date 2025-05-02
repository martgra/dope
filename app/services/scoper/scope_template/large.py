from app.models.domain.scope_template import (
    DocSectionTemplate,
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)

TIERS = [ProjectTier.large, ProjectTier.massive]

deployment_guide = DocTemplate(
    description="Procedures for manual and automated deployments, including rollback steps.",
    tiers=TIERS,
    sections={
        "environment_matrix": DocSectionTemplate(
            description="List of target environments (dev, staging, prod) and their configurations",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
        ),
        "manual_deployment_steps": DocSectionTemplate(
            description="Step-by-step instructions for performing a manual rollout",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "automated_deployment": DocSectionTemplate(
            description="How CI/CD pipelines or scripts deploy to each environment",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "rollback_and_recovery": DocSectionTemplate(
            description="Procedures to revert or recover from a failed release",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "post_deploy_validation": DocSectionTemplate(
            description="Checks and smoke-tests to verify a successful deployment",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering],
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
        ),
        "health_checks_and_alerts": DocSectionTemplate(
            description="How to interpret health endpoints, dashboards, and set alerts",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "scaling_procedures": DocSectionTemplate(
            description="Steps to scale components horizontally or vertically",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "backup_and_restore": DocSectionTemplate(
            description="Backup locations, retention policies, and restore instructions",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "incident_response": DocSectionTemplate(
            description="Troubleshooting flowcharts, common failure resolutions, "
            "and escalation paths",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
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
        ),
        "encryption_and_secrets": DocSectionTemplate(
            description="Encryption at rest/in transit and secret-management best practices",
            themes=[SectionTheme.governance, SectionTheme.technical],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
        ),
        "vulnerability_scanning": DocSectionTemplate(
            description="Tools, schedules, and processes for scanning code and containers",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
        ),
        "compliance_requirements": DocSectionTemplate(
            description="Regulatory controls (GDPR, PCI, HIPAA) and how they're enforced",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance],
        ),
        "audit_and_logging": DocSectionTemplate(
            description="Audit-log locations, retention, and how to review for compliance",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance, SectionAudience.engineering],
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
        ),
        "caching_strategies": DocSectionTemplate(
            description="Approaches for in-memory, CDN, and DB caching to reduce latency",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "database_optimization": DocSectionTemplate(
            description="Indexing, query tuning, and connection-pool best practices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "resource_allocation": DocSectionTemplate(
            description="Guidance on CPU, memory, and network resource quotas",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "tuning_guidelines": DocSectionTemplate(
            description="General tips for improving throughput and reducing contention",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
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
        ),
        "dashboards_and_visualizations": DocSectionTemplate(
            description="Pre-built dashboards and instructions for customizing views",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "alerting_and_slo": DocSectionTemplate(
            description="Defining SLOs/SLAs and configuring alerts on key metrics",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "log_aggregation": DocSectionTemplate(
            description="Centralized logging architecture and query examples",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "metric_collection": DocSectionTemplate(
            description="List of key metrics (latency, error rates, capacity) "
            "and how they're gathered",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
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
