#!/usr/bin/env python3
"""
Assumptions Workflow
====================

Workflow for tracking and reviewing implementation assumptions.

This module provides functions for:
1. Documenting assumptions when implementing features with skipped dependencies
2. Reviewing assumptions when skipped features are completed
3. Agent prompts for assumption tracking

Integration points:
- Call when implementing a feature that depends on a skipped feature
- Call when marking a previously skipped feature as passing
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from api.database import Feature, FeatureAssumption, FeatureDependency


# Agent prompt templates
ASSUMPTION_DOCUMENTATION_PROMPT = """
⚠️  IMPORTANT: Dependency on Skipped Feature

You are implementing Feature #{current_id}: "{current_name}"

This feature depends on Feature #{dependency_id}: "{dependency_name}" which was SKIPPED.

**YOU MUST document any assumptions you make about the skipped feature.**

When writing code for this feature:

1. **Add assumption comments** in your code where you make assumptions:
   ```
   // ASSUMPTION: Feature #{dependency_id} ({dependency_name}) will use [describe assumption]
   // If different approach is taken, this code may need updating
   // Location: [file path]:[line numbers]
   ```

2. **Document the assumption** using this format:
   - What you're assuming about the skipped feature
   - Where in the code you made this assumption
   - What impact it would have if the assumption is wrong

3. **Use placeholder implementations** where needed:
   - Mock functions/APIs that don't exist yet
   - Fake data that represents what you expect
   - Mark with TODO comments referencing the skipped feature

Example assumption documentation:
```javascript
// ASSUMPTION: OAuth feature #{dependency_id} will use Google OAuth
// If a different provider is chosen (GitHub, Facebook), this avatar URL
// parsing logic will need to be updated
// See: Feature #{current_id} assumption in features.db
async function getOAuthAvatar(userId) {{
  // TODO: Replace with real OAuth integration when Feature #{dependency_id} is implemented
  return '/default-avatar.png';
}}
```

After implementing, you should record the assumption details for review when Feature #{dependency_id} is completed.
"""

ASSUMPTION_REVIEW_PROMPT = """
✓ Feature #{feature_id}: "{feature_name}" marked as passing

⚠️  ASSUMPTION REVIEW REQUIRED

{count} features made assumptions about how this feature would be implemented:

{assumptions_list}

**YOU MUST review each assumption:**

For each assumption above:
1. **Read the actual implementation** of Feature #{feature_id}
2. **Compare with the assumption** - is it correct?
3. **If CORRECT**: No action needed
4. **If INCORRECT**: The dependent feature may need rework

If any assumptions are incorrect:
- Review the code at the specified location
- Determine if changes are needed
- Consider creating a fix feature
- Update the assumption status

**Report your findings:**
- List each assumption as VALID or INVALID
- For invalid assumptions, describe what needs to change
- Recommend whether dependent features need rework
"""


class AssumptionsWorkflow:
    """Workflow for managing implementation assumptions."""

    def __init__(self, db_session: Session):
        """Initialize workflow with database session.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def check_for_skipped_dependencies(self, feature_id: int) -> List[Dict]:
        """Check if a feature depends on any skipped features.

        Args:
            feature_id: ID of the feature being implemented

        Returns:
            List of skipped dependencies with details
        """
        # Get all dependencies for this feature
        dependencies = self.db.query(FeatureDependency).filter(
            FeatureDependency.feature_id == feature_id
        ).all()

        skipped_deps = []
        for dep in dependencies:
            depends_on_feature = self.db.query(Feature).filter(
                Feature.id == dep.depends_on_feature_id
            ).first()

            if depends_on_feature and depends_on_feature.was_skipped and not depends_on_feature.passes:
                skipped_deps.append({
                    'dependency_id': depends_on_feature.id,
                    'dependency_name': depends_on_feature.name,
                    'dependency_description': depends_on_feature.description,
                    'confidence': dep.confidence,
                    'detected_method': dep.detected_method,
                })

        return skipped_deps

    def get_assumption_prompt(self, current_feature_id: int, dependency_feature_id: int) -> str:
        """Get the agent prompt for documenting assumptions.

        Args:
            current_feature_id: ID of the feature being implemented
            dependency_feature_id: ID of the skipped dependency

        Returns:
            Formatted prompt for the agent
        """
        current_feature = self.db.query(Feature).filter(
            Feature.id == current_feature_id
        ).first()

        dependency_feature = self.db.query(Feature).filter(
            Feature.id == dependency_feature_id
        ).first()

        if not current_feature or not dependency_feature:
            return ""

        return ASSUMPTION_DOCUMENTATION_PROMPT.format(
            current_id=current_feature.id,
            current_name=current_feature.name,
            dependency_id=dependency_feature.id,
            dependency_name=dependency_feature.name,
        )

    def create_assumption(
        self,
        feature_id: int,
        depends_on_feature_id: int,
        assumption_text: str,
        code_location: Optional[str] = None,
        impact_description: Optional[str] = None
    ) -> FeatureAssumption:
        """Create a new assumption record.

        Args:
            feature_id: ID of the feature making the assumption
            depends_on_feature_id: ID of the skipped feature being assumed about
            assumption_text: Description of the assumption
            code_location: File path and line numbers where assumption is made
            impact_description: What happens if assumption is wrong

        Returns:
            Created FeatureAssumption object
        """
        assumption = FeatureAssumption(
            feature_id=feature_id,
            depends_on_feature_id=depends_on_feature_id,
            assumption_text=assumption_text,
            code_location=code_location,
            impact_description=impact_description,
            status="ACTIVE",
            created_at=datetime.utcnow()
        )

        self.db.add(assumption)
        self.db.commit()
        self.db.refresh(assumption)

        return assumption

    def get_assumptions_for_review(self, completed_feature_id: int) -> List[FeatureAssumption]:
        """Get all assumptions that need review when a feature is completed.

        Args:
            completed_feature_id: ID of the feature that was just completed

        Returns:
            List of assumptions to review
        """
        assumptions = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.depends_on_feature_id == completed_feature_id,
            FeatureAssumption.status == "ACTIVE"
        ).all()

        return assumptions

    def get_assumption_review_prompt(self, completed_feature_id: int) -> Optional[str]:
        """Get the agent prompt for reviewing assumptions.

        Args:
            completed_feature_id: ID of the feature that was just completed

        Returns:
            Formatted prompt for the agent, or None if no assumptions to review
        """
        feature = self.db.query(Feature).filter(
            Feature.id == completed_feature_id
        ).first()

        if not feature:
            return None

        assumptions = self.get_assumptions_for_review(completed_feature_id)

        if not assumptions:
            return None

        # Format assumptions list
        assumptions_list = []
        for i, assumption in enumerate(assumptions, 1):
            dependent_feature = self.db.query(Feature).filter(
                Feature.id == assumption.feature_id
            ).first()

            assumption_text = f"""
{i}. Feature #{dependent_feature.id}: {dependent_feature.name}
   Assumption: "{assumption.assumption_text}"
   Location: {assumption.code_location or 'Not specified'}
   Impact if wrong: {assumption.impact_description or 'Not specified'}
"""
            assumptions_list.append(assumption_text)

        return ASSUMPTION_REVIEW_PROMPT.format(
            feature_id=feature.id,
            feature_name=feature.name,
            count=len(assumptions),
            assumptions_list="\n".join(assumptions_list)
        )

    def mark_assumptions_for_review(self, completed_feature_id: int) -> int:
        """Mark all assumptions for a completed feature as needing review.

        Args:
            completed_feature_id: ID of the feature that was just completed

        Returns:
            Number of assumptions marked for review
        """
        assumptions = self.get_assumptions_for_review(completed_feature_id)

        count = 0
        for assumption in assumptions:
            assumption.status = "NEEDS_REVIEW"
            count += 1

        self.db.commit()

        return count

    def validate_assumption(self, assumption_id: int) -> bool:
        """Mark an assumption as validated (correct).

        Args:
            assumption_id: ID of the assumption

        Returns:
            True if successful, False if assumption not found
        """
        assumption = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption_id
        ).first()

        if not assumption:
            return False

        assumption.status = "VALIDATED"
        assumption.validated_at = datetime.utcnow()
        self.db.commit()

        return True

    def invalidate_assumption(self, assumption_id: int) -> Tuple[bool, Optional[int]]:
        """Mark an assumption as invalid (incorrect).

        Args:
            assumption_id: ID of the assumption

        Returns:
            Tuple of (success, feature_id_needing_rework)
        """
        assumption = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption_id
        ).first()

        if not assumption:
            return False, None

        assumption.status = "INVALID"
        assumption.validated_at = datetime.utcnow()
        self.db.commit()

        # Return the feature ID that may need rework
        return True, assumption.feature_id

    def get_assumption_statistics(self) -> Dict:
        """Get statistics about assumptions in the project.

        Returns:
            Dictionary with assumption counts by status
        """
        total = self.db.query(FeatureAssumption).count()
        active = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.status == "ACTIVE"
        ).count()
        needs_review = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.status == "NEEDS_REVIEW"
        ).count()
        validated = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.status == "VALIDATED"
        ).count()
        invalid = self.db.query(FeatureAssumption).filter(
            FeatureAssumption.status == "INVALID"
        ).count()

        return {
            'total': total,
            'active': active,
            'needs_review': needs_review,
            'validated': validated,
            'invalid': invalid,
            'accuracy_rate': (validated / (validated + invalid) * 100) if (validated + invalid) > 0 else 0
        }


def should_document_assumptions(db_session: Session, feature_id: int) -> bool:
    """Check if a feature should document assumptions.

    Args:
        db_session: SQLAlchemy database session
        feature_id: ID of the feature being implemented

    Returns:
        True if the feature depends on skipped features
    """
    workflow = AssumptionsWorkflow(db_session)
    skipped_deps = workflow.check_for_skipped_dependencies(feature_id)
    return len(skipped_deps) > 0


def should_review_assumptions(db_session: Session, feature_id: int) -> bool:
    """Check if assumptions should be reviewed for a completed feature.

    Args:
        db_session: SQLAlchemy database session
        feature_id: ID of the feature that was just completed

    Returns:
        True if there are assumptions to review
    """
    workflow = AssumptionsWorkflow(db_session)
    assumptions = workflow.get_assumptions_for_review(feature_id)
    return len(assumptions) > 0


# Integration example for agent.py
def integrate_with_agent_example():
    """
    Example integration with agent workflow.

    This is pseudocode showing how to integrate assumptions tracking.
    """
    # In agent.py, when starting to implement a feature:
    """
    feature = get_next_feature()

    # Check for skipped dependencies
    if should_document_assumptions(db_session, feature.id):
        workflow = AssumptionsWorkflow(db_session)
        skipped_deps = workflow.check_for_skipped_dependencies(feature.id)

        for dep in skipped_deps:
            # Add assumption prompt to agent context
            prompt = workflow.get_assumption_prompt(
                feature.id,
                dep['dependency_id']
            )
            # Include prompt in agent instructions

    # After implementing the feature, agent should call:
    # workflow.create_assumption(
    #     feature_id=feature.id,
    #     depends_on_feature_id=dependency_id,
    #     assumption_text="OAuth will use Google OAuth provider",
    #     code_location="src/api/users.js:145-152",
    #     impact_description="If different provider chosen, avatar URL parsing needs update"
    # )
    """

    # In agent.py, when marking a feature as passing:
    """
    feature = mark_feature_passing(feature_id)

    # Check if this was a previously skipped feature
    if feature.was_skipped and should_review_assumptions(db_session, feature.id):
        workflow = AssumptionsWorkflow(db_session)

        # Get review prompt for agent
        review_prompt = workflow.get_assumption_review_prompt(feature.id)

        # Agent reviews assumptions and reports findings
        # Then mark assumptions as validated or invalid

        # Mark assumptions as needing review
        count = workflow.mark_assumptions_for_review(feature.id)

        # Agent can use CLI to validate/invalidate:
        # assumptions_cli.py --project-dir . --validate-assumption 3
        # assumptions_cli.py --project-dir . --invalidate-assumption 4
    """
