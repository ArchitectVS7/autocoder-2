"""
Checkpoint Configuration System
================================

Loads and manages checkpoint configuration from autocoder_config.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class CheckpointTrigger:
    """Represents a trigger condition for running checkpoints."""

    feature_count: Optional[int] = None
    milestone: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointTrigger':
        """Create trigger from dictionary."""
        return cls(
            feature_count=data.get('feature_count'),
            milestone=data.get('milestone')
        )

    def matches(self, features_completed: int, feature_name: str = "") -> bool:
        """Check if this trigger matches current state."""
        if self.feature_count is not None:
            return features_completed == self.feature_count

        if self.milestone and feature_name:
            # Check if feature name contains milestone keyword (case-insensitive)
            milestone_lower = self.milestone.lower()
            feature_lower = feature_name.lower()

            # Check for exact substring match
            if milestone_lower in feature_lower:
                return True

            # Also check for singular/plural variants
            # Remove trailing 's' for plural->singular check
            if milestone_lower.endswith('s'):
                singular = milestone_lower[:-1]
                if singular in feature_lower:
                    return True

            # Add trailing 's' for singular->plural check
            plural = milestone_lower + 's'
            if plural in feature_lower:
                return True

        return False


@dataclass
class CheckpointTypes:
    """Configuration for enabled checkpoint types."""

    code_review: bool = True
    security_audit: bool = True
    performance_check: bool = True
    accessibility_check: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointTypes':
        """Create from dictionary."""
        return cls(
            code_review=data.get('code_review', True),
            security_audit=data.get('security_audit', True),
            performance_check=data.get('performance_check', True),
            accessibility_check=data.get('accessibility_check', False)
        )

    def get_enabled(self) -> List[str]:
        """Get list of enabled checkpoint types."""
        enabled = []
        if self.code_review:
            enabled.append('code_review')
        if self.security_audit:
            enabled.append('security_audit')
        if self.performance_check:
            enabled.append('performance_check')
        if self.accessibility_check:
            enabled.append('accessibility_check')
        return enabled


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint system."""

    enabled: bool = True
    frequency: int = 10  # Every N features
    types: CheckpointTypes = field(default_factory=CheckpointTypes)
    auto_pause_on_critical: bool = True
    triggers: List[CheckpointTrigger] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointConfig':
        """Create configuration from dictionary."""
        types_data = data.get('types', {})
        triggers_data = data.get('triggers', [])

        return cls(
            enabled=data.get('enabled', True),
            frequency=data.get('frequency', 10),
            types=CheckpointTypes.from_dict(types_data),
            auto_pause_on_critical=data.get('auto_pause_on_critical', True),
            triggers=[CheckpointTrigger.from_dict(t) for t in triggers_data]
        )

    def should_run_checkpoint(
        self,
        features_completed: int,
        feature_name: str = ""
    ) -> bool:
        """
        Determine if checkpoint should run based on configuration.

        Args:
            features_completed: Number of features completed so far
            feature_name: Name of current/last completed feature

        Returns:
            True if checkpoint should run, False otherwise
        """
        if not self.enabled:
            return False

        # Check frequency-based trigger
        if features_completed > 0 and features_completed % self.frequency == 0:
            return True

        # Check custom triggers
        for trigger in self.triggers:
            if trigger.matches(features_completed, feature_name):
                return True

        return False


@dataclass
class AutocoderConfig:
    """Complete autocoder configuration."""

    checkpoints: CheckpointConfig = field(default_factory=CheckpointConfig)
    output_directory: str = "./autocoder_output"
    verbose_logging: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutocoderConfig':
        """Create configuration from dictionary."""
        checkpoint_data = data.get('checkpoints', {})

        return cls(
            checkpoints=CheckpointConfig.from_dict(checkpoint_data),
            output_directory=data.get('output_directory', './autocoder_output'),
            verbose_logging=data.get('verbose_logging', True)
        )

    @classmethod
    def load(cls, config_path: Path) -> 'AutocoderConfig':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to autocoder_config.yaml

        Returns:
            AutocoderConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if not config_path.exists():
            # Return default configuration if file doesn't exist
            return cls()

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        if data is None:
            # Empty file, return defaults
            return cls()

        return cls.from_dict(data)

    @classmethod
    def load_from_project(cls, project_dir: Path) -> 'AutocoderConfig':
        """
        Load configuration from project directory.

        Looks for autocoder_config.yaml in project root.

        Args:
            project_dir: Path to project directory

        Returns:
            AutocoderConfig instance (defaults if no config file)
        """
        config_path = project_dir / 'autocoder_config.yaml'
        return cls.load(config_path)

    def save(self, config_path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_path: Path where to save autocoder_config.yaml
        """
        data = {
            'checkpoints': {
                'enabled': self.checkpoints.enabled,
                'frequency': self.checkpoints.frequency,
                'types': {
                    'code_review': self.checkpoints.types.code_review,
                    'security_audit': self.checkpoints.types.security_audit,
                    'performance_check': self.checkpoints.types.performance_check,
                    'accessibility_check': self.checkpoints.types.accessibility_check,
                },
                'auto_pause_on_critical': self.checkpoints.auto_pause_on_critical,
                'triggers': [
                    {k: v for k, v in {'feature_count': t.feature_count, 'milestone': t.milestone}.items() if v is not None}
                    for t in self.checkpoints.triggers
                ]
            },
            'output_directory': self.output_directory,
            'verbose_logging': self.verbose_logging
        }

        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Singleton instance for easy access
_config_instance: Optional[AutocoderConfig] = None


def get_config(project_dir: Optional[Path] = None) -> AutocoderConfig:
    """
    Get current configuration instance.

    Args:
        project_dir: Optional project directory to load from

    Returns:
        AutocoderConfig instance
    """
    global _config_instance

    if _config_instance is None:
        if project_dir:
            _config_instance = AutocoderConfig.load_from_project(project_dir)
        else:
            _config_instance = AutocoderConfig()

    return _config_instance


def set_config(config: AutocoderConfig) -> None:
    """
    Set the configuration instance (useful for testing).

    Args:
        config: AutocoderConfig to use
    """
    global _config_instance
    _config_instance = config


def reset_config() -> None:
    """Reset configuration to None (useful for testing)."""
    global _config_instance
    _config_instance = None
