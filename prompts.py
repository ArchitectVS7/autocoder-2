"""
Prompt Loading Utilities
========================

Functions for loading prompt templates with project-specific support.

Fallback chain:
1. Project-specific: {project_dir}/prompts/{name}.md
2. Base template: .claude/templates/{name}.template.md
"""

import shutil
from pathlib import Path

# Base templates location (generic templates)
TEMPLATES_DIR = Path(__file__).parent / ".claude" / "templates"


def get_project_prompts_dir(project_dir: Path) -> Path:
    """Get the prompts directory for a specific project."""
    return project_dir / "prompts"


def load_prompt(name: str, project_dir: Path | None = None) -> str:
    """
    Load a prompt template with fallback chain.

    Fallback order:
    1. Project-specific: {project_dir}/prompts/{name}.md
    2. Base template: .claude/templates/{name}.template.md

    Args:
        name: The prompt name (without extension), e.g., "initializer_prompt"
        project_dir: Optional project directory for project-specific prompts

    Returns:
        The prompt content as a string

    Raises:
        FileNotFoundError: If prompt not found in any location
    """
    # 1. Try project-specific first
    if project_dir:
        project_prompts = get_project_prompts_dir(project_dir)
        project_path = project_prompts / f"{name}.md"
        if project_path.exists():
            try:
                return project_path.read_text(encoding="utf-8")
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not read {project_path}: {e}")

    # 2. Try base template
    template_path = TEMPLATES_DIR / f"{name}.template.md"
    if template_path.exists():
        try:
            return template_path.read_text(encoding="utf-8")
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not read {template_path}: {e}")

    raise FileNotFoundError(
        f"Prompt '{name}' not found in:\n"
        f"  - Project: {project_dir / 'prompts' if project_dir else 'N/A'}\n"
        f"  - Templates: {TEMPLATES_DIR}"
    )


def get_initializer_prompt(project_dir: Path | None = None) -> str:
    """Load the initializer prompt (project-specific if available)."""
    return load_prompt("initializer_prompt", project_dir)


def get_coding_prompt(project_dir: Path | None = None) -> str:
    """Load the coding agent prompt (project-specific if available)."""
    return load_prompt("coding_prompt", project_dir)


def get_testing_prompt(project_dir: Path | None = None) -> str:
    """Load the testing agent prompt (project-specific if available)."""
    return load_prompt("testing_prompt", project_dir)


def get_single_feature_prompt(feature_id: int, project_dir: Path | None = None, yolo_mode: bool = False) -> str:
    """
    Load the coding prompt with single-feature focus instructions prepended.

    When the orchestrator assigns a specific feature to a coding agent,
    this prompt ensures the agent works ONLY on that feature.

    Args:
        feature_id: The specific feature ID to work on
        project_dir: Optional project directory for project-specific prompts
        yolo_mode: Ignored (kept for backward compatibility). Testing is now
                   handled by separate testing agents, not YOLO prompts.

    Returns:
        The prompt with single-feature instructions prepended
    """
    # Always use the standard coding prompt
    # (Testing/regression is handled by separate testing agents)
    base_prompt = get_coding_prompt(project_dir)

    # Prepend single-feature instructions
    single_feature_header = f"""## SINGLE FEATURE MODE

**CRITICAL: You are assigned to work on Feature #{feature_id} ONLY.**

This session is part of a parallel execution where multiple agents work on different features simultaneously. You MUST:

1. **Skip the `feature_get_next` step** - Your feature is already assigned: #{feature_id}
2. **Immediately mark feature #{feature_id} as in-progress** using `feature_mark_in_progress`
3. **Focus ONLY on implementing and testing feature #{feature_id}**
4. **Do NOT work on any other features** - other agents are handling them

When you complete feature #{feature_id}:
- Mark it as passing with `feature_mark_passing`
- Commit your changes
- End the session

If you cannot complete feature #{feature_id} due to a blocker:
- Use `feature_skip` to move it to the end of the queue
- Document the blocker in claude-progress.txt
- End the session

---

"""

    return single_feature_header + base_prompt


def get_app_spec(project_dir: Path) -> str:
    """
    Load the app spec from the project.

    Checks in order:
    1. Project prompts directory: {project_dir}/prompts/app_spec.txt
    2. Project root (legacy): {project_dir}/app_spec.txt

    Args:
        project_dir: The project directory

    Returns:
        The app spec content

    Raises:
        FileNotFoundError: If no app_spec.txt found
    """
    # Try project prompts directory first
    project_prompts = get_project_prompts_dir(project_dir)
    spec_path = project_prompts / "app_spec.txt"
    if spec_path.exists():
        try:
            return spec_path.read_text(encoding="utf-8")
        except (OSError, PermissionError) as e:
            raise FileNotFoundError(f"Could not read {spec_path}: {e}") from e

    # Fallback to legacy location in project root
    legacy_spec = project_dir / "app_spec.txt"
    if legacy_spec.exists():
        try:
            return legacy_spec.read_text(encoding="utf-8")
        except (OSError, PermissionError) as e:
            raise FileNotFoundError(f"Could not read {legacy_spec}: {e}") from e

    raise FileNotFoundError(f"No app_spec.txt found for project: {project_dir}")


def scaffold_project_prompts(project_dir: Path) -> Path:
    """
    Create the project prompts directory and copy base templates.

    This sets up a new project with template files that can be customized.

    Args:
        project_dir: The absolute path to the project directory

    Returns:
        The path to the project prompts directory
    """
    project_prompts = get_project_prompts_dir(project_dir)
    project_prompts.mkdir(parents=True, exist_ok=True)

    # Define template mappings: (source_template, destination_name)
    templates = [
        ("app_spec.template.txt", "app_spec.txt"),
        ("coding_prompt.template.md", "coding_prompt.md"),
        ("initializer_prompt.template.md", "initializer_prompt.md"),
        ("testing_prompt.template.md", "testing_prompt.md"),
    ]

    copied_files = []
    for template_name, dest_name in templates:
        template_path = TEMPLATES_DIR / template_name
        dest_path = project_prompts / dest_name

        # Only copy if template exists and destination doesn't
        if template_path.exists() and not dest_path.exists():
            try:
                shutil.copy(template_path, dest_path)
                copied_files.append(dest_name)
            except (OSError, PermissionError) as e:
                print(f"  Warning: Could not copy {dest_name}: {e}")

    if copied_files:
        print(f"  Created prompt files: {', '.join(copied_files)}")

    return project_prompts


def has_project_prompts(project_dir: Path) -> bool:
    """
    Check if a project has valid prompts set up.

    A project has valid prompts if:
    1. The prompts directory exists, AND
    2. app_spec.txt exists within it, AND
    3. app_spec.txt contains the <project_specification> tag

    Args:
        project_dir: The project directory to check

    Returns:
        True if valid project prompts exist, False otherwise
    """
    project_prompts = get_project_prompts_dir(project_dir)
    app_spec = project_prompts / "app_spec.txt"

    if not app_spec.exists():
        # Also check legacy location in project root
        legacy_spec = project_dir / "app_spec.txt"
        if legacy_spec.exists():
            try:
                content = legacy_spec.read_text(encoding="utf-8")
                return "<project_specification>" in content
            except (OSError, PermissionError):
                return False
        return False

    # Check for valid spec content
    try:
        content = app_spec.read_text(encoding="utf-8")
        return "<project_specification>" in content
    except (OSError, PermissionError):
        return False


def copy_spec_to_project(project_dir: Path) -> None:
    """
    Copy the app spec file into the project root directory for the agent to read.

    This maintains backwards compatibility - the agent expects app_spec.txt
    in the project root directory.

    The spec is sourced from: {project_dir}/prompts/app_spec.txt

    Args:
        project_dir: The project directory
    """
    spec_dest = project_dir / "app_spec.txt"

    # Don't overwrite if already exists
    if spec_dest.exists():
        return

    # Copy from project prompts directory
    project_prompts = get_project_prompts_dir(project_dir)
    project_spec = project_prompts / "app_spec.txt"
    if project_spec.exists():
        try:
            shutil.copy(project_spec, spec_dest)
            print("Copied app_spec.txt to project directory")
            return
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not copy app_spec.txt: {e}")
            return

    print("Warning: No app_spec.txt found to copy to project directory")


# =============================================================================
# PHASE 0: PERSONA SWITCHING - Context-Aware Prompt Enhancement
# =============================================================================

def detect_feature_type(feature: dict) -> str:
    """
    Detect feature type from category, name, and description keywords.

    This enables context-appropriate persona selection without requiring
    explicit feature type annotation. The detection uses keyword matching
    across multiple feature fields.

    Args:
        feature: Feature dict with keys: 'category', 'name', 'description'
                 At minimum, 'name' and 'description' should be present.

    Returns:
        One of: "security", "ui_ux", "api", "data", "performance", "standard"

    Classification Strategy:
        - security: Authentication, authorization, encryption, tokens, payments
        - ui_ux: User interface, accessibility, design, responsive layouts
        - api: Backend endpoints, database operations, server logic
        - data: Import/export, validation, transformation, processing
        - performance: Optimization, caching, speed, efficiency
        - standard: Default (no special persona needed)

    Examples:
        >>> detect_feature_type({
        ...     'category': 'Authentication',
        ...     'name': 'User login with OAuth',
        ...     'description': 'Implement OAuth authentication flow'
        ... })
        'security'

        >>> detect_feature_type({
        ...     'category': 'UI',
        ...     'name': 'Responsive navigation menu',
        ...     'description': 'Build accessible navigation with keyboard support'
        ... })
        'ui_ux'
    """
    # Combine all text fields for analysis (lowercase for case-insensitive matching)
    text_parts = [
        feature.get('category', ''),
        feature.get('name', ''),
        feature.get('description', ''),
    ]
    text = ' '.join(str(part) for part in text_parts if part).lower()

    # Split into words for whole-word matching (avoid substring false positives)
    # e.g., "form" should not match "transformation"
    words = set(text.lower().replace(',', ' ').replace('.', ' ').split())

    # Security-sensitive features (highest priority - security is critical)
    security_keywords = {
        'auth', 'login', 'password', 'token', 'security', 'oauth',
        'jwt', 'session', 'permission', 'role', 'encrypt', 'payment',
        'credential', 'secret', 'authorization', 'authentication',
        'stripe', 'paypal', 'billing', '2fa', 'mfa',
        'hash', 'salt', 'https', 'ssl', 'tls', 'certificate',
    }
    # Also check multi-word phrases in original text
    if 'api key' in text or 'credit card' in text:
        return "security"
    if words & security_keywords:  # Set intersection for word matching
        return "security"

    # UI/UX focused features
    ui_ux_keywords = {
        'ui', 'ux', 'design', 'layout', 'accessibility', 'responsive',
        'button', 'form', 'modal', 'component', 'style', 'theme',
        'navigation', 'menu', 'dashboard', 'display', 'interface',
        'frontend', 'react', 'vue', 'angular', 'tailwind', 'css',
        'wcag', 'aria', 'keyboard', 'mobile',
        'tablet', 'desktop', 'breakpoint', 'animation', 'transition',
    }
    # Also check multi-word phrases
    if 'screen reader' in text:
        return "ui_ux"
    if words & ui_ux_keywords:
        return "ui_ux"

    # API/Backend features
    api_keywords = {
        'api', 'endpoint', 'route', 'controller', 'service',
        'database', 'query', 'migration', 'schema', 'model',
        'backend', 'server', 'rest', 'graphql', 'http',
        'post', 'get', 'put', 'delete', 'patch',
        'crud', 'orm', 'sql', 'postgresql', 'mysql',
        'mongodb', 'redis', 'cache', 'queue',
    }
    if words & api_keywords:
        return "api"

    # Data processing features
    data_keywords = {
        'data', 'export', 'import', 'csv', 'json', 'parse',
        'transform', 'validate', 'format', 'report', 'analytics',
        'etl', 'pipeline', 'batch', 'process', 'aggregate',
        'xml', 'yaml', 'excel', 'spreadsheet', 'file',
    }
    if words & data_keywords:
        return "data"

    # Performance features
    performance_keywords = {
        'performance', 'optimize', 'speed', 'efficient', 'fast', 'slow',
        'memory', 'cpu', 'latency', 'throughput', 'tuning',
    }
    # Multi-word phrases for performance
    if 'lazy load' in text:
        return "performance"
    if words & performance_keywords:
        return "performance"

    # Default: standard (no special persona)
    return "standard"


def get_coding_prompt_with_persona(feature: dict, project_dir: Path | None = None) -> str:
    """
    Get coding prompt enhanced with appropriate persona based on feature type.

    This is the Phase 0 enhancement that brings context-appropriate expertise
    to the coding agent without requiring multi-agent orchestration.

    The function:
    1. Loads the base coding prompt (project-specific or template)
    2. Detects the feature type from keywords
    3. Appends the appropriate persona instructions
    4. Always appends the craftsmanship mindset

    Args:
        feature: Feature dict with at least 'name' and 'description' keys
        project_dir: Optional project directory for project-specific prompts

    Returns:
        Enhanced prompt with persona add-on(s) appended

    Persona Selection:
        - security features → SECURITY_PERSONA (paranoid, OWASP-focused)
        - ui_ux features → UX_PERSONA (accessibility, WCAG, responsive)
        - api features → API_PERSONA (performance, error handling, validation)
        - data features → DATA_PERSONA (validation, encoding, large datasets)
        - performance features → (no special persona yet, just craftsmanship)
        - standard features → (no special persona, just craftsmanship)

    Note:
        CRAFTSMANSHIP_MINDSET is ALWAYS appended to encourage initiative
        and quality beyond minimum requirements.

    Examples:
        >>> feature = {
        ...     'id': 5,
        ...     'name': 'User login with JWT tokens',
        ...     'description': 'Implement secure authentication'
        ... }
        >>> prompt = get_coding_prompt_with_persona(feature)
        # Returns base prompt + SECURITY_PERSONA + CRAFTSMANSHIP_MINDSET
    """
    from persona_prompts import (
        SECURITY_PERSONA,
        UX_PERSONA,
        API_PERSONA,
        DATA_PERSONA,
        CRAFTSMANSHIP_MINDSET,
    )

    # Load base coding prompt (project-specific if available)
    base_prompt = get_coding_prompt(project_dir)

    # Detect feature type
    feature_type = detect_feature_type(feature)

    # Select appropriate persona add-on
    persona_addon = ""
    if feature_type == "security":
        persona_addon = SECURITY_PERSONA
    elif feature_type == "ui_ux":
        persona_addon = UX_PERSONA
    elif feature_type == "api":
        persona_addon = API_PERSONA
    elif feature_type == "data":
        persona_addon = DATA_PERSONA
    # performance and standard get no special persona (craftsmanship only)

    # Build enhanced prompt
    enhanced_prompt = base_prompt

    # Add persona-specific expertise if applicable
    if persona_addon:
        enhanced_prompt = enhanced_prompt + "\n" + persona_addon

    # ALWAYS add craftsmanship mindset (applies to all features)
    enhanced_prompt = enhanced_prompt + "\n" + CRAFTSMANSHIP_MINDSET

    return enhanced_prompt
