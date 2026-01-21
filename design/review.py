#!/usr/bin/env python3
"""
Design Review CLI - Task 4.6

Command-line tool for running persona-based design iteration.

Usage:
    python design_review.py --spec initial_spec.md
    python design_review.py --spec initial_spec.md --interactive
    python design_review.py --spec initial_spec.md --auto
    python design_review.py --continue 2  # Continue from iteration 2

Based on IMPLEMENTATION_PLAN.md Phase 4, Task 4.6: Design Review CLI
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from design.iteration import (
    DesignIterationAgent,
    PersonaReviewPanel,
    DesignSynthesisAgent,
    ConvergenceDetector,
    DesignDocument,
    DesignIterationResult
)
from design.persona_system import PersonaLoader


class DesignReviewCLI:
    """Command-line interface for design review process."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        interactive: bool = False,
        auto: bool = False
    ):
        """
        Initialize Design Review CLI.

        Args:
            output_dir: Directory for output files (default: ./design_review_output)
            interactive: Interactive mode - pause after each iteration
            auto: Auto mode - run until convergence without user input
        """
        if output_dir is None:
            output_dir = Path("./design_review_output")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.interactive = interactive
        self.auto = auto

        # Initialize components
        self.design_agent = DesignIterationAgent(self.output_dir / "designs")
        self.review_panel = PersonaReviewPanel()
        self.synthesis_agent = DesignSynthesisAgent()
        self.convergence_detector = ConvergenceDetector()

    def run_design_review(self, spec_file: Path, start_iteration: int = 1) -> DesignDocument:
        """
        Run the complete design review process.

        Args:
            spec_file: Path to initial specification file
            start_iteration: Iteration to start from (default: 1)

        Returns:
            Final DesignDocument after convergence
        """
        # Load specification
        if not spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {spec_file}")

        with open(spec_file, 'r', encoding='utf-8') as f:
            rough_spec = f.read()

        print("=" * 70)
        print("DESIGN REVIEW - Persona-Based Design Iteration")
        print("=" * 70)
        print(f"\nSpecification: {spec_file}")
        print(f"Output directory: {self.output_dir}")
        print(f"Mode: {'Interactive' if self.interactive else 'Auto' if self.auto else 'Standard'}")
        print()

        current_design = None
        iteration = start_iteration

        while True:
            print(f"\n{'=' * 70}")
            print(f"ITERATION {iteration}")
            print(f"{'=' * 70}\n")

            # Create design
            if iteration == 1:
                print("📝 Creating initial design from specification...")
                current_design = self.design_agent.create_initial_design(rough_spec, iteration)
            else:
                print("📝 Creating next iteration based on feedback...")
                current_design = self.design_agent.create_next_iteration(
                    previous_design,
                    synthesized_feedback
                )

            # Save design
            design_path = self.design_agent.save_design(current_design)
            print(f"✅ Design saved to: {design_path}")

            # Display design summary
            self._display_design_summary(current_design)

            # Collect persona feedback
            print("\n👥 Collecting feedback from personas...")
            feedback_list = self.review_panel.collect_feedback(current_design)

            # Save feedback
            feedback_path = self.review_panel.save_feedback(
                feedback_list,
                iteration,
                self.output_dir / "feedback"
            )
            print(f"✅ Feedback saved to: {feedback_path}")

            # Display feedback summary
            self._display_feedback_summary(feedback_list)

            # Synthesize feedback
            print("\n🔄 Synthesizing feedback from all personas...")
            synthesized_feedback = self.synthesis_agent.synthesize_feedback(
                feedback_list,
                iteration
            )

            # Display synthesis
            self._display_synthesis(synthesized_feedback)

            # Check convergence
            has_converged, reason = self.convergence_detector.has_converged(
                synthesized_feedback,
                iteration
            )

            print(f"\n🎯 Convergence check: {reason}")

            if has_converged:
                print("\n" + "=" * 70)
                print("✨ DESIGN HAS CONVERGED ✨")
                print("=" * 70)
                next_steps = self.convergence_detector.suggest_next_steps(has_converged, reason)
                for step in next_steps:
                    print(f"  {step}")
                print()

                # Save final design to prompts directory
                final_design_path = self._save_final_design(current_design)
                print(f"📄 Final design saved to: {final_design_path}")

                return current_design

            # Interactive mode - pause for user input
            if self.interactive:
                response = input("\nContinue to next iteration? (y/n): ").strip().lower()
                if response != 'y':
                    print("Design review stopped by user.")
                    return current_design

            # Auto mode - continue automatically
            elif self.auto:
                print("\n⏩ Auto mode - continuing to next iteration...")

            # Prepare for next iteration
            previous_design = current_design
            iteration += 1

    def continue_from_iteration(self, iteration: int) -> DesignDocument:
        """
        Continue design review from a specific iteration.

        Args:
            iteration: Iteration number to continue from

        Returns:
            Final DesignDocument after convergence
        """
        print(f"📂 Loading design from iteration {iteration}...")

        try:
            current_design = self.design_agent.load_design(iteration)
            print(f"✅ Loaded design iteration {iteration}")
            print()

            # Continue from this iteration
            # (In real implementation, would also load previous feedback)
            return self.run_design_review(
                Path("dummy_spec.txt"),  # Not used when continuing
                start_iteration=iteration + 1
            )

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def _display_design_summary(self, design: DesignDocument):
        """Display a summary of the design document."""
        print(f"\nDesign Summary:")
        print(f"  Title: {design.title}")
        print(f"  Mockups: {len(design.mockups)}")
        print(f"  User Flows: {len(design.user_flows)}")
        print(f"  Design Principles: {len(design.design_principles)}")

        if design.mockups:
            print(f"\n  Mockup screens: {', '.join(m.screen_name for m in design.mockups)}")

    def _display_feedback_summary(self, feedback_list):
        """Display a summary of persona feedback."""
        print(f"\nFeedback from {len(feedback_list)} personas:")

        for feedback in feedback_list:
            sentiment_emoji = {
                "positive": "😊",
                "neutral": "😐",
                "negative": "😟"
            }[feedback.sentiment.value]

            avg_score = sum(feedback.scores.values()) / len(feedback.scores) if feedback.scores else 0

            print(f"  {sentiment_emoji} {feedback.persona_name}: {avg_score:.1f}/10")
            print(f"     Likes: {len(feedback.likes)}, Concerns: {len(feedback.concerns)}, Suggestions: {len(feedback.suggestions)}")

    def _display_synthesis(self, synthesis):
        """Display synthesized feedback."""
        print(f"\nSynthesis:")
        print(f"  Consensus Level: {synthesis.consensus_level:.1%}")
        print(f"  Priority Changes: {len(synthesis.priority_changes)}")

        if synthesis.priority_changes:
            print("\n  Top priority changes:")
            for i, change in enumerate(synthesis.priority_changes[:3], 1):
                print(f"    {i}. {change}")

        if synthesis.conflicting_feedback:
            print(f"\n  ⚠️  Conflicting feedback detected: {len(synthesis.conflicting_feedback)} conflicts")

    def _save_final_design(self, design: DesignDocument) -> Path:
        """
        Save final design to prompts directory for use in development.

        Args:
            design: Final DesignDocument

        Returns:
            Path to saved final design file
        """
        prompts_dir = Path("./prompts")
        prompts_dir.mkdir(parents=True, exist_ok=True)

        final_design_path = prompts_dir / "final_design_spec.json"

        # Save as JSON
        import json
        with open(final_design_path, 'w', encoding='utf-8') as f:
            json.dump(design.to_dict(), f, indent=2, ensure_ascii=False)

        # Also save as Markdown for readability
        markdown_path = prompts_dir / "final_design_spec.md"
        self._save_design_as_markdown(design, markdown_path)

        return final_design_path

    def _save_design_as_markdown(self, design: DesignDocument, output_path: Path):
        """Save design document as Markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {design.title}\n\n")
            f.write(f"{design.description}\n\n")

            f.write("## Design Principles\n\n")
            for principle in design.design_principles:
                f.write(f"- {principle}\n")

            f.write("\n## Accessibility Considerations\n\n")
            for consideration in design.accessibility_considerations:
                f.write(f"- {consideration}\n")

            f.write("\n## Mockups\n\n")
            for mockup in design.mockups:
                f.write(f"### {mockup.screen_name}\n\n")
                f.write(f"{mockup.description}\n\n")
                f.write(f"**Layout:** {mockup.layout}\n\n")
                f.write(f"**Components:** {', '.join(mockup.components)}\n\n")

            f.write("\n## User Flows\n\n")
            for flow in design.user_flows:
                f.write(f"### {flow.name}\n\n")
                f.write(f"{flow.description}\n\n")
                f.write("**Steps:**\n\n")
                for step in flow.steps:
                    f.write(f"{step}\n")
                f.write("\n")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Persona-based design review and iteration system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start new design review
  python design_review.py --spec my_app_spec.md

  # Interactive mode (pause after each iteration)
  python design_review.py --spec my_app_spec.md --interactive

  # Auto mode (run until convergence)
  python design_review.py --spec my_app_spec.md --auto

  # Continue from specific iteration
  python design_review.py --continue 2

  # Custom output directory
  python design_review.py --spec my_app_spec.md --output ./my_design_review
        """
    )

    parser.add_argument(
        '--spec',
        type=Path,
        help="Path to initial specification file"
    )

    parser.add_argument(
        '--continue',
        dest='continue_iteration',
        type=int,
        metavar='ITERATION',
        help="Continue from specific iteration number"
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path("./design_review_output"),
        help="Output directory for design review files (default: ./design_review_output)"
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help="Interactive mode - pause after each iteration for user confirmation"
    )

    parser.add_argument(
        '--auto',
        action='store_true',
        help="Auto mode - run until convergence without pausing"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.spec and not args.continue_iteration:
        parser.error("Either --spec or --continue must be specified")

    if args.spec and args.continue_iteration:
        parser.error("Cannot specify both --spec and --continue")

    if args.interactive and args.auto:
        parser.error("Cannot use both --interactive and --auto modes")

    # Create CLI instance
    cli = DesignReviewCLI(
        output_dir=args.output,
        interactive=args.interactive,
        auto=args.auto
    )

    try:
        # Run design review
        if args.continue_iteration:
            final_design = cli.continue_from_iteration(args.continue_iteration)
        else:
            final_design = cli.run_design_review(args.spec)

        print("\n✅ Design review complete!")
        print(f"Final iteration: {final_design.iteration}")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Design review interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
