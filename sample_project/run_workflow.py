"""
Workflow runner for sample Todo List App.

This script demonstrates running the complete autocoder workflow.

Usage:
    python run_workflow.py                  # Full workflow
    python run_workflow.py --dev-only       # Development only
    python run_workflow.py --interactive    # Pause after each phase
"""

import asyncio
import argparse
from pathlib import Path
import sys

# Add parent directory to path to import autocoder modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from integration.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowConfig,
    run_complete_workflow
)


async def run_full_workflow(interactive: bool = False):
    """
    Run the complete workflow from design to UX evaluation.

    Args:
        interactive: If True, pause after each phase for user confirmation
    """
    print("=" * 70)
    print("SAMPLE PROJECT: Todo List App")
    print("=" * 70)
    print()

    # Load initial specification
    spec_path = Path(__file__).parent / "initial_spec.md"
    with open(spec_path, 'r') as f:
        initial_spec = f.read()

    print(f"📝 Loaded specification: {spec_path}")
    print()

    # Load configuration
    config_path = Path(__file__).parent / "autocoder_config.yaml"

    import yaml
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    config = WorkflowConfig.from_dict(config_data)
    print(f"⚙️  Loaded configuration: {config_path}")
    print()

    # Create orchestrator
    project_dir = Path(__file__).parent
    orchestrator = WorkflowOrchestrator(project_dir, config)

    print("🚀 Starting workflow...")
    print()

    try:
        # Phase 1: Design Iteration
        if config.enable_design_iteration:
            print("=" * 70)
            print("PHASE 1: DESIGN ITERATION")
            print("=" * 70)
            print()

            design_spec = await orchestrator.run_design_iteration(initial_spec)

            if design_spec:
                print(f"✅ Design complete: {design_spec}")
            else:
                print("⚠️  Design iteration failed or skipped")

            if interactive:
                input("\nPress Enter to continue to development phase...")
                print()

        # Phase 2: Development with Checkpoints
        print("=" * 70)
        print("PHASE 2: DEVELOPMENT WITH CHECKPOINTS")
        print("=" * 70)
        print()
        print("⚠️  Note: Actual development happens via autonomous_agent_demo.py")
        print("   This is a simulation for the sample project.")
        print()

        # Simulate development
        success = await orchestrator.run_development_with_checkpoints(
            features_total=15  # Expected features for todo app
        )

        if success:
            print("✅ Development setup complete")
        else:
            print("❌ Development setup failed")
            return

        # Simulate progress updates
        for i in range(5, 16, 5):
            orchestrator.update_development_progress(i)
            if i % 5 == 0 and config.enable_checkpoints:
                # Simulate checkpoint
                orchestrator.record_checkpoint(critical_issues=0)

        if interactive:
            input("\nPress Enter to continue to UX evaluation phase...")
            print()

        # Phase 3: UX Evaluation
        if config.enable_ux_evaluation:
            print("=" * 70)
            print("PHASE 3: UX EVALUATION")
            print("=" * 70)
            print()
            print("⚠️  Note: This requires the app to be running.")
            print("   For sample project, this is simulated.")
            print()

            # In real usage, user would start their app:
            # cd src && npm start

            # Then evaluate:
            # ux_score = await orchestrator.run_ux_evaluation("http://localhost:3000")

            # For sample, we simulate:
            print("📊 Simulating UX evaluation...")
            orchestrator.result.ux_evaluation_complete = True
            orchestrator.result.ux_score = 8.2

            print(f"✅ UX evaluation complete: {orchestrator.result.ux_score}/10")

        # Finalize result
        orchestrator.result.success = True
        orchestrator.result.current_phase = orchestrator.result.current_phase.COMPLETE

        # Print summary
        print()
        print("=" * 70)
        print("✅ WORKFLOW COMPLETE")
        print("=" * 70)
        print()
        print_workflow_summary(orchestrator.result)

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ WORKFLOW FAILED")
        print("=" * 70)
        print(f"Error: {e}")


async def run_dev_only():
    """Run development phase only (skip design & UX)."""
    print("=" * 70)
    print("SAMPLE PROJECT: Todo List App (Development Only)")
    print("=" * 70)
    print()

    config = WorkflowConfig(
        enable_design_iteration=False,
        enable_checkpoints=True,
        enable_ux_evaluation=False,
        checkpoint_frequency=5
    )

    project_dir = Path(__file__).parent
    orchestrator = WorkflowOrchestrator(project_dir, config)

    print("🚀 Starting development...")
    print()

    success = await orchestrator.run_development_with_checkpoints(features_total=15)

    if success:
        print("✅ Development setup complete")

        # Simulate progress
        for i in range(5, 16, 5):
            orchestrator.update_development_progress(i)
            orchestrator.record_checkpoint(critical_issues=0)

        print()
        print("=" * 70)
        print("✅ DEVELOPMENT COMPLETE")
        print("=" * 70)
        print()
        print(f"Features completed: {orchestrator.result.features_completed}/15")
        print(f"Checkpoints run: {orchestrator.result.checkpoints_run}")


def print_workflow_summary(result):
    """Print workflow summary."""
    print(f"📊 Project: {result.project_name}")
    print()

    if result.design_spec_path:
        print("🎨 Design Iteration:")
        print(f"   Iterations: {result.design_iterations}")
        print(f"   Final spec: {result.design_spec_path}")
        print()

    if result.features_total > 0:
        print("💻 Development:")
        print(f"   Features: {result.features_completed}/{result.features_total}")
        print(f"   Checkpoints: {result.checkpoints_run}")
        print(f"   Critical issues: {result.critical_issues_found}")
        print()

    if result.ux_score:
        print("📱 UX Evaluation:")
        print(f"   Score: {result.ux_score}/10")
        if result.ux_report_path:
            print(f"   Report: {result.ux_report_path}")
        print()

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run autocoder workflow for sample Todo List App",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--dev-only',
        action='store_true',
        help='Run development only (skip design & UX)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Pause after each phase for user confirmation'
    )

    args = parser.parse_args()

    if args.dev_only:
        asyncio.run(run_dev_only())
    else:
        asyncio.run(run_full_workflow(interactive=args.interactive))


if __name__ == '__main__':
    main()
