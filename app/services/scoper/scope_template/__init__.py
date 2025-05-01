from app.models.domain.scope_template import DocTemplate, ProjectTier, StructureTemplate
from app.services.scoper.scope_template.large import large
from app.services.scoper.scope_template.massive import massive
from app.services.scoper.scope_template.medium import medium
from app.services.scoper.scope_template.small import small
from app.services.scoper.scope_template.trivial import trivial

DOC_SCOPE = StructureTemplate(docs={**trivial, **small, **medium, **large, **massive})


def get_scope(size: ProjectTier = "small") -> dict[str, DocTemplate]:
    """Return relevant docs based on project Tier."""
    return {key: item for key, item in DOC_SCOPE.docs.items() if size in item.tiers}
