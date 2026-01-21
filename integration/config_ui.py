"""
Configuration UI for Phase 6: Integration & Polish.

Provides CLI interface for enabling/disabling features and setting thresholds.
"""

import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from integration.workflow_orchestrator import WorkflowConfig


class ConfigurationUI:
    """
    CLI interface for managing autocoder workflow configuration.

    Allows users to:
    - View current configuration
    - Enable/disable features
    - Set thresholds and parameters
    - Save/load configuration from files
    """

    def __init__(self, project_dir: Path):
        """
        Initialize configuration UI.

        Args:
            project_dir: Path to project directory
        """
        self.project_dir = Path(project_dir)
        self.config_file = self.project_dir / "autocoder_config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> WorkflowConfig:
        """Load configuration from file or use defaults."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f)
                return WorkflowConfig.from_dict(data)
        return WorkflowConfig()

    def save_config(self):
        """Save current configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w') as f:
            yaml.dump(self.config.to_dict(), f, default_flow_style=False, sort_keys=False)

        print(f"✓ Configuration saved to: {self.config_file}")

    def show_config(self):
        """Display current configuration."""
        print("\n📋 Current Autocoder Configuration")
        print("=" * 60)

        # Phase toggles
        print("\n🎯 Phase Toggles:")
        print(f"  Design Iteration:    {'✓ Enabled' if self.config.enable_design_iteration else '✗ Disabled'}")
        print(f"  Checkpoints:         {'✓ Enabled' if self.config.enable_checkpoints else '✗ Disabled'}")
        print(f"  UX Evaluation:       {'✓ Enabled' if self.config.enable_ux_evaluation else '✗ Disabled'}")
        print(f"  Metrics:             {'✓ Enabled' if self.config.enable_metrics else '✗ Disabled'}")

        # Design iteration settings
        print("\n🎨 Design Iteration Settings:")
        print(f"  Max Iterations:      {self.config.max_design_iterations}")
        print(f"  Convergence:         {self.config.design_convergence_threshold}")

        # Checkpoint settings
        print("\n🚧 Checkpoint Settings:")
        print(f"  Frequency:           Every {self.config.checkpoint_frequency} features")
        print(f"  Auto-pause critical: {'✓ Yes' if self.config.auto_pause_on_critical else '✗ No'}")

        # UX evaluation settings
        print("\n📊 UX Evaluation Settings:")
        print(f"  Run after complete:  {'✓ Yes' if self.config.run_ux_after_completion else '✗ No'}")
        print(f"  Flows:               {', '.join(self.config.ux_flows)}")
        print(f"  Min UX Score:        {self.config.min_ux_score}/10")

        # Metrics settings
        print("\n📈 Metrics Settings:")
        print(f"  Track performance:   {'✓ Yes' if self.config.track_performance else '✗ No'}")
        print(f"  Generate comparison: {'✓ Yes' if self.config.generate_comparison else '✗ No'}")

        # Output settings
        print("\n📁 Output Settings:")
        print(f"  Output directory:    {self.config.output_directory}")
        print(f"  Verbose logging:     {'✓ Yes' if self.config.verbose_logging else '✗ No'}")

        print("\n" + "=" * 60)
        print(f"Config file: {self.config_file}")
        print()

    def enable_feature(self, feature: str):
        """
        Enable a feature.

        Args:
            feature: Feature name (design, checkpoints, ux, metrics)
        """
        feature_map = {
            'design': 'enable_design_iteration',
            'checkpoints': 'enable_checkpoints',
            'ux': 'enable_ux_evaluation',
            'metrics': 'enable_metrics'
        }

        if feature not in feature_map:
            print(f"❌ Unknown feature: {feature}")
            print(f"   Available: {', '.join(feature_map.keys())}")
            return

        attr_name = feature_map[feature]
        setattr(self.config, attr_name, True)
        self.save_config()
        print(f"✓ Enabled: {feature}")

    def disable_feature(self, feature: str):
        """
        Disable a feature.

        Args:
            feature: Feature name (design, checkpoints, ux, metrics)
        """
        feature_map = {
            'design': 'enable_design_iteration',
            'checkpoints': 'enable_checkpoints',
            'ux': 'enable_ux_evaluation',
            'metrics': 'enable_metrics'
        }

        if feature not in feature_map:
            print(f"❌ Unknown feature: {feature}")
            print(f"   Available: {', '.join(feature_map.keys())}")
            return

        attr_name = feature_map[feature]
        setattr(self.config, attr_name, False)
        self.save_config()
        print(f"✓ Disabled: {feature}")

    def set_threshold(self, name: str, value: Any):
        """
        Set a threshold value.

        Args:
            name: Threshold name
            value: New value
        """
        threshold_map = {
            'checkpoint_frequency': (int, 'Checkpoint frequency'),
            'max_design_iterations': (int, 'Max design iterations'),
            'min_ux_score': (float, 'Minimum UX score'),
            'design_convergence_threshold': (float, 'Design convergence threshold')
        }

        if name not in threshold_map:
            print(f"❌ Unknown threshold: {name}")
            print(f"   Available: {', '.join(threshold_map.keys())}")
            return

        value_type, display_name = threshold_map[name]

        try:
            typed_value = value_type(value)
            setattr(self.config, name, typed_value)
            self.save_config()
            print(f"✓ Set {display_name}: {typed_value}")
        except ValueError:
            print(f"❌ Invalid value for {name}: {value} (expected {value_type.__name__})")

    def reset_config(self):
        """Reset configuration to defaults."""
        self.config = WorkflowConfig()
        self.save_config()
        print("✓ Configuration reset to defaults")

    def export_json(self, output_path: Path):
        """
        Export configuration to JSON.

        Args:
            output_path: Path to JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        print(f"✓ Configuration exported to: {output_path}")

    def import_json(self, input_path: Path):
        """
        Import configuration from JSON.

        Args:
            input_path: Path to JSON file
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
        self.config = WorkflowConfig.from_dict(data)
        self.save_config()
        print(f"✓ Configuration imported from: {input_path}")

    def interactive_setup(self):
        """Interactive configuration setup wizard."""
        print("\n🚀 Autocoder Configuration Wizard")
        print("=" * 60)
        print("\nAnswer the following questions to configure your workflow.")
        print("Press Enter to keep the default value shown in brackets.\n")

        # Phase toggles
        print("📋 Phase Toggles:")

        self.config.enable_design_iteration = self._ask_bool(
            "Enable design iteration? (Pre-development validation)",
            self.config.enable_design_iteration
        )

        self.config.enable_checkpoints = self._ask_bool(
            "Enable checkpoints? (Code quality gates during development)",
            self.config.enable_checkpoints
        )

        self.config.enable_ux_evaluation = self._ask_bool(
            "Enable UX evaluation? (Post-development UX testing)",
            self.config.enable_ux_evaluation
        )

        self.config.enable_metrics = self._ask_bool(
            "Enable metrics tracking? (Performance and cost tracking)",
            self.config.enable_metrics
        )

        # Thresholds
        print("\n⚙️  Thresholds:")

        if self.config.enable_checkpoints:
            self.config.checkpoint_frequency = self._ask_int(
                "Checkpoint frequency (features)",
                self.config.checkpoint_frequency
            )

        if self.config.enable_design_iteration:
            self.config.max_design_iterations = self._ask_int(
                "Max design iterations",
                self.config.max_design_iterations
            )

        if self.config.enable_ux_evaluation:
            self.config.min_ux_score = self._ask_float(
                "Minimum UX score (1-10)",
                self.config.min_ux_score
            )

        # Save
        self.save_config()
        print("\n✓ Configuration saved!")
        print(f"   Location: {self.config_file}")

    def _ask_bool(self, question: str, default: bool) -> bool:
        """Ask yes/no question."""
        default_str = "Y/n" if default else "y/N"
        response = input(f"  {question} [{default_str}]: ").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes', 'true', '1']

    def _ask_int(self, question: str, default: int) -> int:
        """Ask integer question."""
        response = input(f"  {question} [{default}]: ").strip()

        if not response:
            return default

        try:
            return int(response)
        except ValueError:
            print(f"  ⚠️  Invalid number, using default: {default}")
            return default

    def _ask_float(self, question: str, default: float) -> float:
        """Ask float question."""
        response = input(f"  {question} [{default}]: ").strip()

        if not response:
            return default

        try:
            return float(response)
        except ValueError:
            print(f"  ⚠️  Invalid number, using default: {default}")
            return default


def create_cli():
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Autocoder Workflow Configuration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current configuration
  python -m integration.config_ui --show

  # Enable/disable features
  python -m integration.config_ui --enable design
  python -m integration.config_ui --disable ux

  # Set thresholds
  python -m integration.config_ui --set checkpoint_frequency 5
  python -m integration.config_ui --set min_ux_score 8.5

  # Interactive setup
  python -m integration.config_ui --setup

  # Reset to defaults
  python -m integration.config_ui --reset

  # Export/import
  python -m integration.config_ui --export my_config.json
  python -m integration.config_ui --import my_config.json
        """
    )

    parser.add_argument(
        '--project-dir',
        type=Path,
        default=Path.cwd(),
        help='Project directory (default: current directory)'
    )

    parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration'
    )

    parser.add_argument(
        '--enable',
        type=str,
        metavar='FEATURE',
        help='Enable feature (design, checkpoints, ux, metrics)'
    )

    parser.add_argument(
        '--disable',
        type=str,
        metavar='FEATURE',
        help='Disable feature (design, checkpoints, ux, metrics)'
    )

    parser.add_argument(
        '--set',
        nargs=2,
        metavar=('NAME', 'VALUE'),
        help='Set threshold value'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset configuration to defaults'
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run interactive configuration wizard'
    )

    parser.add_argument(
        '--export',
        type=Path,
        metavar='FILE',
        help='Export configuration to JSON file'
    )

    parser.add_argument(
        '--import',
        dest='import_file',
        type=Path,
        metavar='FILE',
        help='Import configuration from JSON file'
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = create_cli()
    args = parser.parse_args()

    ui = ConfigurationUI(args.project_dir)

    # Execute command
    if args.show:
        ui.show_config()

    elif args.enable:
        ui.enable_feature(args.enable)

    elif args.disable:
        ui.disable_feature(args.disable)

    elif args.set:
        name, value = args.set
        ui.set_threshold(name, value)

    elif args.reset:
        ui.reset_config()

    elif args.setup:
        ui.interactive_setup()

    elif args.export:
        ui.export_json(args.export)

    elif args.import_file:
        ui.import_json(args.import_file)

    else:
        # Default: show current configuration
        ui.show_config()


if __name__ == '__main__':
    main()
