from dope.models.domain.scope import (
    DocTemplate,
    StructureTemplate,
)
from dope.models.enums import DocTemplateKey, ProjectTier
from dope.services.scoper.scope_template.large import large
from dope.services.scoper.scope_template.massive import massive
from dope.services.scoper.scope_template.medium import medium
from dope.services.scoper.scope_template.small import small
from dope.services.scoper.scope_template.trivial import trivial

DOC_SCOPE = StructureTemplate(docs={**trivial, **small, **medium, **large, **massive})


def get_scope(size: ProjectTier = ProjectTier.small) -> dict[DocTemplateKey, DocTemplate]:
    """Return relevant docs based on project Tier."""
    return {key: item for key, item in DOC_SCOPE.docs.items() if item.tiers and size in item.tiers}
