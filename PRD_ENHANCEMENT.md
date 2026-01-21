# Autocoder Enhancement: Multi-Agent UX Evaluation & Design Iteration

**Version:** 1.0
**Status:** Proposed
**Created:** 2026-01-20

---

## Executive Summary

Extend autocoder from a pure coding agent to a **full product development system** that includes:
- **Pre-development:** Multi-persona design iteration and validation
- **During development:** Checkpoint code reviews and quality gates
- **Post-development:** Automated UX evaluation via Playwright + AI analysis
- **Continuous:** Simulated user testing from diverse perspectives

This transforms autocoder from "write code" to "build products users love."

---

## Vision Statement

*"What if your coding agent could also simulate a design team, QA team, and focus group - iterating on user experience from concept to completion?"*

---

## Problem Statement

Current autocoder limitations:
1. **No design validation** - Jumps straight to coding without design iteration
2. **No quality gates** - Code runs continuously without checkpoints
3. **No UX evaluation** - Can't judge if the final product is actually usable
4. **No user perspective** - Doesn't simulate real users with different needs/biases
5. **No visual feedback** - Can't see screenshots or evaluate UI aesthetics

**Business impact:**
- Products may be functionally complete but poorly designed
- No early detection of UX issues (expensive to fix later)
- Missing diverse user perspectives (accessibility, novice vs power users)
- No automated "would users like this?" validation

---

## Target Use Cases

| Use Case | Current State | With Enhancement |
|----------|---------------|------------------|
| **Building a SaaS dashboard** | Code works but UI is confusing | 5 personas review design first, UX validated with screenshots |
| **E-commerce checkout** | Functional but high drop-off rate | Novice persona identifies friction points before launch |
| **Accessibility compliance** | Manual audit required post-launch | Accessibility advocate persona reviews throughout |
| **Mobile app design** | Desktop-first, mobile broken | Mobile-first persona flags issues early |
| **Feature prioritization** | Developer-driven | User personas suggest features they actually want |

---

## Core Concepts

### 1. Persona System

**Definition:** AI agents with distinct perspectives, biases, and expertise areas.

**Example Personas:**

| Persona | Role | Biases | Key Concerns |
|---------|------|--------|--------------|
| **Sarah** | Accessibility Advocate | WCAG compliance, inclusive design | Color contrast, keyboard nav, screen readers, ARIA labels |
| **Marcus** | Power User | Efficiency, customization | Keyboard shortcuts, bulk operations, data export, API access |
| **Elena** | Novice User | Simplicity, guidance | Clear onboarding, helpful errors, tooltips, undo functionality |
| **David** | Mobile-First User | Touch-friendly, responsive | Thumb zones, loading speed, offline mode, gesture support |
| **Aisha** | Brand/Aesthetics | Visual appeal, consistency | Color harmony, typography, whitespace, visual hierarchy |
| **Raj** | Security Conscious | Privacy, data protection | Encryption, permissions, audit logs, GDPR compliance |
| **Lisa** | Performance Optimizer | Speed, efficiency | Load times, bundle size, caching, lazy loading |

**Persona Template:**
```json
{
  "id": "accessibility_advocate",
  "name": "Sarah Chen",
  "background": "Blind user who relies on screen readers daily",
  "expertise": "WCAG 2.1, ARIA, assistive technology",
  "bias": "Prioritizes accessibility over aesthetics",
  "typical_feedback": [
    "Missing alt text on decorative images",
    "Color contrast ratio only 3:1 (needs 4.5:1)",
    "Form inputs lack associated labels"
  ],
  "evaluation_criteria": [
    "Keyboard navigation completeness",
    "Screen reader compatibility",
    "Color contrast ratios",
    "Semantic HTML usage",
    "Focus indicators",
    "Error message clarity"
  ]
}
```

### 2. Design Iteration Loop

```
┌─────────────────────────────────────────────────────┐
│            DESIGN ITERATION CYCLE                   │
│                                                     │
│  Initial Spec (User Input)                         │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────┐                              │
│  │ Design Agent     │ Creates detailed mockup      │
│  │ - UI wireframes  │ description or spec          │
│  │ - User flows     │                              │
│  │ - Feature specs  │                              │
│  └────────┬─────────┘                              │
│           │                                         │
│           ▼                                         │
│  ┌─────────────────────────────────────────┐       │
│  │      PERSONA REVIEW PANEL               │       │
│  │                                         │       │
│  │  Sarah:  ⚠️  No keyboard shortcuts      │       │
│  │  Marcus: ✅  Love the efficiency        │       │
│  │  Elena:  ⚠️  Onboarding unclear         │       │
│  │  David:  ❌  Buttons too small for touch │       │
│  │  Aisha:  ⚠️  Color contrast issues      │       │
│  └────────┬────────────────────────────────┘       │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────┐                          │
│  │ Synthesis Agent      │ Aggregates feedback,     │
│  │ - Identifies patterns│ resolves conflicts,      │
│  │ - Prioritizes issues │ creates next iteration   │
│  │ - Creates v2 spec    │                          │
│  └────────┬─────────────┘                          │
│           │                                         │
│           ▼                                         │
│  Iteration 2 → [Persona Review] → Iteration 3      │
│                                                     │
│  (Repeat 2-4 times until consensus)                │
│           │                                         │
│           ▼                                         │
│  ✅ Final Design Spec → Pass to Coding Agent       │
└─────────────────────────────────────────────────────┘
```

### 3. Quality Gates (Checkpoints)

**Checkpoint Triggers:**
- Every N features completed (configurable, default: 10)
- Before major milestones (e.g., authentication, payments)
- On-demand via user command

**Checkpoint Activities:**

| Gate Type | Agent | What It Checks | Output |
|-----------|-------|----------------|--------|
| **Code Review** | Review Specialist | Code quality, patterns, maintainability | Pass/Fail + refactoring suggestions |
| **Security Audit** | Security Specialist | OWASP Top 10, input validation, auth | Vulnerability report + fixes |
| **Performance** | Performance Specialist | Bundle size, render time, queries | Metrics + optimization suggestions |
| **Accessibility** | A11y Specialist | WCAG compliance so far | Compliance report + fixes |
| **Test Coverage** | QA Specialist | Unit/integration test gaps | Coverage report + test suggestions |

**Checkpoint Flow:**
```python
# Pseudocode
async def checkpoint(project_dir: Path, features_completed: int):
    print(f"\n🚧 CHECKPOINT: {features_completed} features complete")

    results = []

    # Run all checkpoint agents in parallel
    results.append(await code_review_agent(project_dir))
    results.append(await security_audit_agent(project_dir))
    results.append(await performance_check_agent(project_dir))

    # Aggregate results
    issues = aggregate_checkpoint_results(results)

    if issues.critical:
        print("❌ CRITICAL ISSUES - Pausing development")
        return "PAUSE"
    elif issues.warnings:
        print(f"⚠️  {len(issues.warnings)} warnings - Continuing")
        return "CONTINUE_WITH_WARNINGS"
    else:
        print("✅ All checks passed")
        return "CONTINUE"
```

### 4. Playwright Integration + Visual UX Analysis

**Flow:**

```
Development Complete
    │
    ▼
┌────────────────────────────────┐
│ Playwright Test Runner         │
│ - Runs user flow simulations   │
│ - Captures screenshots         │
│ - Records videos               │
│ - Measures performance         │
└────────┬───────────────────────┘
         │
         ▼
    Screenshots Captured
    ├─ onboarding/step1.png
    ├─ onboarding/step2.png
    ├─ dashboard/main.png
    ├─ settings/preferences.png
    └─ checkout/payment.png
         │
         ▼
┌────────────────────────────────┐
│ Visual QA Agent                │
│ - Analyzes each screenshot     │
│ - Checks alignment, spacing    │
│ - Verifies responsive design   │
│ - Detects visual bugs          │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ UX Evaluation Agents           │
│                                │
│ For each screenshot:           │
│ • Accessibility Auditor        │
│ • Brand Consistency Checker    │
│ • Mobile UX Specialist         │
│ • Onboarding Flow Analyst      │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Persona User Testing           │
│                                │
│ Each persona "uses" the app:   │
│ - Sarah: Can I navigate it?    │
│ - Marcus: Is it efficient?     │
│ - Elena: Is it intuitive?      │
│ - David: Does it work mobile?  │
│ - Aisha: Is it beautiful?      │
└────────┬───────────────────────┘
         │
         ▼
    UX Report Generated
    ├─ Strengths
    ├─ Weaknesses
    ├─ Bugs to fix
    ├─ Suggested improvements
    └─ Feature ideas
```

**Claude's Vision Capabilities:**

Claude can analyze screenshots for:
- ✅ **Visual hierarchy** - Is important content prominent?
- ✅ **Color schemes** - Aesthetically pleasing? Accessible contrast?
- ✅ **Spacing/alignment** - Professional polish?
- ✅ **Typography** - Readable font sizes and hierarchy?
- ✅ **Responsive design** - Does layout adapt properly?
- ✅ **Consistency** - Same patterns throughout?
- ✅ **Accessibility** - WCAG compliance from visual inspection
- ✅ **Onboarding clarity** - Clear what to do next?
- ✅ **Error states** - Helpful error messages visible?

---

## Feature Specifications

### PHASE 1: Checkpoint System

**F1.1 - Checkpoint Configuration**
- User can set checkpoint frequency (every N features)
- User can enable/disable specific checkpoint types
- User can manually trigger checkpoints via command
- Checkpoints save results to `checkpoints/` directory

**F1.2 - Code Review Checkpoint**
- Analyzes recently changed files
- Checks for code smells, anti-patterns
- Validates naming conventions
- Suggests refactoring opportunities
- Outputs: `checkpoint_N_code_review.md`

**F1.3 - Security Audit Checkpoint**
- Scans for OWASP Top 10 vulnerabilities
- Checks authentication/authorization logic
- Validates input sanitization
- Reviews API endpoint security
- Outputs: `checkpoint_N_security.md`

**F1.4 - Performance Checkpoint**
- Analyzes bundle sizes
- Reviews database query efficiency
- Checks for N+1 queries
- Identifies heavy dependencies
- Outputs: `checkpoint_N_performance.md`

**F1.5 - Checkpoint Aggregation**
- Combines results from all checkpoint agents
- Categorizes issues (critical, warning, info)
- Decides: PAUSE, CONTINUE_WITH_WARNINGS, or CONTINUE
- Creates summary report

---

### PHASE 2: Persona-Based Design Iteration

**F2.1 - Persona Definition System**
- JSON-based persona definitions in `personas/` directory
- Built-in persona library (7 default personas)
- User can create custom personas
- Personas have: name, background, bias, concerns, evaluation criteria

**F2.2 - Design Iteration Agent**
- Takes initial spec/wireframe as input
- Creates detailed design document
- Outputs mockup descriptions (or integrates with design tools)

**F2.3 - Persona Review Panel**
- Each persona reviews current design iteration
- Provides feedback from their unique perspective
- Feedback includes: likes, concerns, suggestions
- Outputs: `design_iteration_N_feedback.json`

**F2.4 - Design Synthesis Agent**
- Aggregates feedback from all personas
- Identifies common themes
- Resolves conflicting feedback (with prioritization)
- Creates next iteration of design
- Outputs: `design_iteration_N+1.md`

**F2.5 - Design Convergence Detection**
- Detects when feedback becomes minimal
- Suggests design is ready for development
- Typically 2-4 iterations to convergence

**F2.6 - Design Review CLI**
- `python design_review.py --spec initial_spec.md`
- Interactive mode: user sees each iteration
- Auto mode: runs until convergence
- Outputs final spec to project prompts directory

---

### PHASE 3: Playwright + Visual UX

**F3.1 - Playwright Test Generation**
- Agent generates Playwright tests for key user flows
- Tests include screenshot capture at each step
- Tests stored in `tests/ux_flows/`
- Example flows: onboarding, checkout, settings

**F3.2 - Automated Test Execution**
- Runs Playwright tests after development completes
- Captures screenshots in `screenshots/` directory
- Organized by flow: `screenshots/onboarding/step1.png`
- Also captures video recordings

**F3.3 - Visual QA Agent**
- Analyzes each screenshot for visual bugs
- Checks: alignment, spacing, overflow, broken layouts
- Compares screenshots across viewports (mobile/tablet/desktop)
- Outputs: `visual_qa_report.md`

**F3.4 - Screenshot-Based UX Evaluation**
- Multiple specialist agents analyze screenshots:
  - Accessibility Auditor
  - Brand Consistency Checker
  - Mobile UX Specialist
  - Onboarding Flow Analyst
- Each provides score (1-10) + detailed feedback
- Outputs: `ux_evaluation_report.md`

**F3.5 - Persona User Testing**
- Each persona "uses" the app via screenshots
- Simulates first-time user experience
- Provides subjective feedback (impressions, confusion, delight)
- Answers: "Would you use this? Why/why not?"
- Outputs: `persona_user_tests.md`

**F3.6 - UX Report Generator**
- Aggregates all UX evaluation results
- Creates comprehensive report with:
  - Executive summary
  - Strengths (what works well)
  - Weaknesses (what needs improvement)
  - Bug list (visual/UX bugs to fix)
  - Suggested improvements (prioritized)
  - Feature ideas (from persona feedback)
- Outputs: `UX_REPORT_FINAL.md`

---

### PHASE 4: Continuous UX Monitoring

**F4.1 - UX Regression Testing**
- Playwright tests run on every major change
- Compares new screenshots to baseline
- Flags visual regressions
- Alerts if UX score decreases

**F4.2 - Iterative Refinement Loop**
- After UX evaluation, coding agent can fix issues
- Re-runs Playwright tests
- Re-evaluates UX
- Loop continues until UX score meets threshold

**F4.3 - A/B Design Comparison**
- Agent can generate 2-3 design variations
- Each variation evaluated by personas
- Quantitative comparison of feedback
- Recommendation for best approach

**F4.4 - Feature Suggestion Pipeline**
- Personas suggest features throughout development
- Suggestions tracked in `feature_suggestions.json`
- User can promote suggestions to features
- Feedback loop: suggestions → features → implementation

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOCODER ENHANCED SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              DESIGN PHASE (New)                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Design Agent │→│ Persona Panel│→│ Synthesizer │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │         │                                     │         │    │
│  │         └─────────────┬───────────────────────┘         │    │
│  │                       ▼                                 │    │
│  │              Final Design Spec                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                       │
│                         ▼                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           DEVELOPMENT PHASE (Existing + Enhanced)      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Initializer  │→│ Coding Agent │→│ Checkpoints │  │    │
│  │  │    Agent     │  │  (existing)  │  │   (new)     │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │                           │                  ▲          │    │
│  │                           │                  │          │    │
│  │                           └──────┬───────────┘          │    │
│  │                                  │                      │    │
│  │                    Every N features: Run checkpoint     │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                       │
│                         ▼                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              TESTING PHASE (New)                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │  Playwright  │→│  Visual QA   │→│ UX Evaluator│  │    │
│  │  │ Test Runner  │  │    Agent     │  │   Agents    │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │         │                                     │         │    │
│  │         └─────────────┬───────────────────────┘         │    │
│  │                       ▼                                 │    │
│  │               Screenshots Captured                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                       │
│                         ▼                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            UX EVALUATION PHASE (New)                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │   Persona    │→│ UX Specialist│→│   Report    │  │    │
│  │  │ User Testing │  │    Agents    │  │  Generator  │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  │                                             │           │    │
│  │                                             ▼           │    │
│  │                                   UX_REPORT_FINAL.md   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Communication

```python
# Agent registry with capabilities
AGENTS = {
    "design": {
        "type": "creator",
        "input": ["user_requirements", "reference_designs"],
        "output": "design_spec",
        "tools": ["read_file", "write_file"]
    },
    "persona_reviewer": {
        "type": "evaluator",
        "input": ["design_spec", "persona_config"],
        "output": "feedback",
        "tools": ["read_file"]
    },
    "synthesizer": {
        "type": "aggregator",
        "input": ["design_spec", "feedback_list"],
        "output": "improved_design_spec",
        "tools": ["read_file", "write_file"]
    },
    "checkpoint_code_review": {
        "type": "evaluator",
        "input": ["project_files", "recent_commits"],
        "output": "review_report",
        "tools": ["read_file", "grep", "git_diff"]
    },
    "playwright_runner": {
        "type": "executor",
        "input": ["project_url", "test_specs"],
        "output": "screenshots",
        "tools": ["run_playwright", "capture_screenshot"]
    },
    "visual_qa": {
        "type": "evaluator",
        "input": ["screenshots"],
        "output": "visual_qa_report",
        "tools": ["analyze_image"]
    },
    "ux_evaluator": {
        "type": "evaluator",
        "input": ["screenshots", "evaluation_criteria"],
        "output": "ux_scores",
        "tools": ["analyze_image", "score_criteria"]
    }
}
```

### Data Flow

```
User Input
    │
    ▼
Design Iteration (2-4 rounds)
    │
    ▼
Final Design Spec → prompts/app_spec.txt
    │
    ▼
Initializer Agent → features.db
    │
    ▼
Coding Loop (with checkpoints every N features)
    │
    ├─ Checkpoint 1 (10 features) → Continue
    ├─ Checkpoint 2 (20 features) → Fix warnings, Continue
    └─ Checkpoint 3 (30 features) → Critical issue, Pause
          │
          ▼
       User reviews → Approves fix → Continue
          │
          ▼
Development Complete
    │
    ▼
Playwright Tests → screenshots/
    │
    ▼
UX Evaluation → UX_REPORT_FINAL.md
    │
    ▼
User Reviews Report
    │
    ├─ Approve → Ship
    └─ Refinements needed → Create features, Continue coding
```

---

## Implementation Phases

### Phase 1: Foundation (Checkpoint System)
**Timeline:** 1 week
**Effort:** Medium

**Deliverables:**
- Checkpoint configuration system
- Code review checkpoint agent
- Security audit checkpoint agent
- Performance checkpoint agent
- Checkpoint aggregation and decision logic
- CLI commands: `--checkpoint-frequency N`

**Success Criteria:**
- Checkpoints run automatically every N features
- Critical issues pause development
- Checkpoint reports saved and readable

---

### Phase 2: Design Iteration
**Timeline:** 2 weeks
**Effort:** High

**Deliverables:**
- Persona definition system
- 7 built-in personas (JSON configs)
- Design iteration agent
- Persona review panel agent
- Design synthesis agent
- Convergence detection
- CLI tool: `design_review.py`

**Success Criteria:**
- User provides rough spec, gets polished spec after 3 iterations
- All 7 personas provide unique, relevant feedback
- Synthesis agent resolves conflicts appropriately
- Final spec includes improvements from persona feedback

---

### Phase 3: Playwright + Visual UX
**Timeline:** 3 weeks
**Effort:** High

**Deliverables:**
- Playwright test generation agent
- Automated test runner + screenshot capture
- Visual QA agent
- 4 UX specialist agents
- Persona user testing simulation
- UX report generator

**Success Criteria:**
- Playwright tests run successfully on sample apps
- Screenshots captured at each flow step
- Claude successfully analyzes screenshots
- UX report identifies 5+ actionable issues
- Persona feedback feels realistic and helpful

---

### Phase 4: Integration & Polish
**Timeline:** 1 week
**Effort:** Medium

**Deliverables:**
- Seamless workflow from design → dev → testing → UX eval
- Configuration file for enabling/disabling features
- Documentation and examples
- Sample project showcasing full workflow

**Success Criteria:**
- End-to-end demo works smoothly
- All phases integrate without manual intervention
- Documentation complete
- Users can customize persona and checkpoint behavior

---

## Configuration

### New Configuration File: `autocoder_config.yaml`

```yaml
# Checkpoint Configuration
checkpoints:
  enabled: true
  frequency: 10  # Every 10 features
  types:
    code_review: true
    security_audit: true
    performance_check: true
    accessibility_check: false  # Optional
  auto_pause_on_critical: true

# Design Iteration Configuration
design_iteration:
  enabled: true
  max_iterations: 4
  personas:
    - accessibility_advocate
    - power_user
    - novice
    - mobile_first
    - brand_aesthetics
  convergence_threshold: 0.8  # Stop when 80% of feedback is positive

# Playwright + UX Evaluation
ux_evaluation:
  enabled: true
  run_after_completion: true
  flows:
    - onboarding
    - dashboard
    - settings
    - checkout  # If applicable
  viewports:
    - desktop: 1920x1080
    - tablet: 768x1024
    - mobile: 375x667

  # UX scoring criteria (each scored 1-10)
  criteria:
    visual_hierarchy: true
    color_scheme: true
    spacing_alignment: true
    typography: true
    accessibility: true
    onboarding_clarity: true
    mobile_responsiveness: true

  # Persona user testing
  persona_testing: true

  # Minimum UX score to pass (average across all criteria)
  min_ux_score: 7.0

# General
output_directory: ./autocoder_output
verbose_logging: true
```

---

## Example Workflows

### Workflow 1: New Project with Design Iteration

```bash
# Step 1: User creates project
$ python start.py
[1] Create new project
> my-saas-dashboard

# Step 2: Design iteration (automatic)
Running design iteration...

Iteration 1: Created initial design spec
Persona feedback:
  Sarah (Accessibility): ⚠️  Missing keyboard navigation plan
  Marcus (Power User): ✅ Bulk operations look good
  Elena (Novice): ⚠️  Onboarding needs more steps
  David (Mobile): ❌ No mobile layout specified
  Aisha (Brand): ⚠️  Color palette undefined

Iteration 2: Addressing feedback...
  ✅ Added keyboard navigation spec
  ✅ Added mobile-first layouts
  ✅ Defined 5-step onboarding
  ✅ Created color palette (WCAG AA compliant)

Persona feedback:
  Sarah: ✅ Much better!
  Marcus: ✅ Great improvements
  Elena: ✅ Onboarding clear now
  David: ✅ Mobile layouts perfect
  Aisha: ✅ Love the color scheme

Design converged after 2 iterations.
✓ Final spec saved to prompts/app_spec.txt

# Step 3: Development begins (automatic)
Starting initializer agent...
Created 45 features from spec.

Starting coding agent...
[10 features complete] → Running checkpoint...
  ✅ Code review: PASS
  ✅ Security audit: PASS
  ⚠️  Performance: Bundle size growing (warning)

Continue? [Y/n] Y

[20 features complete] → Running checkpoint...
  ✅ Code review: PASS
  ❌ Security: SQL injection vulnerability in search

CRITICAL ISSUE - Development paused.
Fix required in: src/api/search.js:42

[Agent creates feature to fix vulnerability]

[Checkpoint re-run after fix]
  ✅ Security: PASS

Continue? [Y/n] Y

# Step 4: Development complete
All 45 features passing!

# Step 5: UX Evaluation (automatic)
Running Playwright tests...
  ✅ Captured 15 screenshots

Analyzing screenshots...
  Visual QA: Found 2 alignment issues
  Accessibility: WCAG AA compliant
  Mobile UX: Excellent (9.2/10)
  Onboarding: Clear and intuitive (8.7/10)

Persona user testing...
  Sarah: "Perfect keyboard navigation!"
  Marcus: "Love the bulk edit feature"
  Elena: "Easiest onboarding I've seen"
  David: "Works great on my phone"
  Aisha: "Beautiful design, on-brand"

UX Report saved to: UX_REPORT_FINAL.md
Overall UX Score: 8.4/10 ✅ PASS

# Step 6: User reviews and ships
$ cat UX_REPORT_FINAL.md

# Fixes 2 alignment issues
$ python start.py
[2] Continue existing project
> my-saas-dashboard

[Agent fixes alignment issues]

# Re-run UX eval
Overall UX Score: 8.9/10 ✅ EXCELLENT

# Ship it! 🚀
```

---

### Workflow 2: Checkpoint Catches Critical Issue

```bash
# Development in progress...
[28 features complete] → Running checkpoint...

Code Review:
  ⚠️  Duplicated logic in 3 files (refactor suggestion)

Security Audit:
  ❌ CRITICAL: JWT tokens stored in localStorage (XSS risk)
  ❌ CRITICAL: No rate limiting on login endpoint

Performance:
  ⚠️  Large dependency added (moment.js - suggest date-fns)

CRITICAL ISSUES DETECTED - Development paused.

Recommended fixes:
1. Move JWT to httpOnly cookies
2. Add express-rate-limit to login endpoint
3. Replace moment.js with date-fns (86% smaller)

Create fix features automatically? [Y/n] Y

Creating 3 fix features...
  Feature 29: Migrate JWT storage to httpOnly cookies
  Feature 30: Add rate limiting to authentication endpoints
  Feature 31: Replace moment.js with date-fns

Resuming development with fix features prioritized...

[Feature 29] Migrating JWT storage...
  ✅ Complete

[Feature 30] Adding rate limiting...
  ✅ Complete

[Feature 31] Replacing moment.js...
  ✅ Complete

[Checkpoint re-run]
  ✅ Code review: PASS
  ✅ Security audit: PASS
  ✅ Performance: PASS

All critical issues resolved. Continuing development...
```

---

## Metrics & Success Criteria

### Design Iteration Metrics
- **Iterations to convergence:** Target < 4
- **Persona satisfaction:** > 80% positive feedback in final iteration
- **Issues caught pre-development:** Track # of UX issues avoided

### Checkpoint Metrics
- **Critical issues caught:** Track # and type
- **False positive rate:** < 10% (issues flagged that aren't real issues)
- **Time to fix:** Avg time from checkpoint pause to resolution
- **Development velocity:** Features/hour with vs without checkpoints

### UX Evaluation Metrics
- **UX score:** Target > 8.0/10 average
- **Issues identified:** Track # of UX bugs found
- **Persona agreement:** % of personas that approve final product
- **Accessibility compliance:** WCAG AA target

---

## PHASE 5: Intelligent Skip Management & Benchmarking

### Problem Statement - Feature Skip Challenges

**Current behavior when a feature is skipped:**
- ✅ Feature moved to end of queue (priority = max + 1)
- ✅ Agent continues with other work
- ❌ No dependency tracking - downstream features may assume different implementation
- ❌ No distinction between "needs human input" vs "try again later"
- ❌ No way to measure if this approach is actually better than alternatives

**Real-world example:**
```
Feature #5: "User can authenticate with OAuth"
└─ Skipped: Needs environment variables (CLIENT_ID, CLIENT_SECRET)

Feature #12: "User profile shows OAuth avatar"
└─ Implemented: Assumes OAuth is done (built around placeholder)

[Later, Feature #5 implemented with different OAuth provider]
└─ Result: Feature #12 needs refactoring (rework!)
```

---

### F5.1 - Dependency-Aware Skip Management

**Goal:** When skipping a feature, understand and track downstream impact.

**F5.1.1 - Dependency Graph Construction**
- Analyze feature descriptions for dependency keywords
  - "requires", "depends on", "after", "once X is done"
  - Referenced feature IDs or categories
- Build dependency graph: `Feature A → [Feature D, Feature E, Feature F]`
- Store in database: `dependencies` table

**Example dependency detection:**
```json
{
  "id": 15,
  "name": "User profile displays OAuth avatar",
  "description": "After OAuth is implemented, show user's avatar from provider",
  "detected_dependencies": [5],  // Detected from "After OAuth"
  "dependency_confidence": 0.85
}
```

**F5.1.2 - Skip Impact Analysis**
- When skipping Feature X, check dependency graph
- Find all features that depend on X
- Report impact to agent and user:

```
⚠️  SKIP IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Skipping Feature #5: "OAuth authentication"

Downstream impact (3 features depend on this):
  • Feature #12: User profile OAuth avatar
  • Feature #23: Third-party account linking
  • Feature #31: Social media sharing

Recommendation:
  ⚠️  Implement these features with placeholders/mocks
  ⚠️  Mark them for review when #5 is implemented
  ✓  Skip and defer all dependent features too
```

**F5.1.3 - Smart Re-prioritization**
- Option 1: Skip all dependent features too (cascade)
- Option 2: Implement with documented assumptions
- Agent decides based on blocker type

**F5.1.4 - Implementation Assumptions Tracking**
- When implementing a feature that depends on a skipped feature
- Agent documents assumptions in code comments:

```javascript
// ASSUMPTION: OAuth feature #5 will use Google OAuth
// If different provider chosen, update avatar URL parsing
async function getOAuthAvatar(userId) {
  // Placeholder implementation
  return '/default-avatar.png';
}
```

- Store assumptions in database: `feature_assumptions` table
- When skipped feature finally implemented, review assumptions

---

### F5.2 - Human-in-the-Loop for Blockers

**Goal:** Detect when a skip requires human intervention and pause gracefully.

**F5.2.1 - Blocker Type Classification**

Agent classifies skip reason into categories:

| Blocker Type | Description | Requires Human | Example |
|--------------|-------------|----------------|---------|
| **Environment Config** | Missing env vars, API keys | ✅ YES | OAuth credentials, database URLs |
| **External Service** | Third-party service not set up | ✅ YES | Stripe account, email provider |
| **Technical Prerequisite** | Missing tech not yet implemented | ⚠️ MAYBE | Need API endpoint before frontend |
| **Unclear Requirements** | Ambiguous spec, need clarification | ✅ YES | "What should error message say?" |
| **Legitimate Deferral** | Can come back later safely | ❌ NO | "Polish animations" can wait |

**F5.2.2 - Blocker Detection Prompts**

Agent prompted to classify:
```
You're about to skip this feature. Why?

[1] Missing environment variable or API key
[2] External service not configured (Stripe, email, etc.)
[3] Depends on another feature not yet built
[4] Requirements unclear, need user input
[5] Can defer safely (polish, nice-to-have)

Select blocker type: _
```

**F5.2.3 - Human Intervention Workflow**

When blocker type = 1, 2, or 4:

```
🛑 HUMAN INPUT REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature #5: "OAuth authentication"
Blocker: Missing environment variables

Required information:
  • OAUTH_CLIENT_ID
  • OAUTH_CLIENT_SECRET
  • OAUTH_PROVIDER (google/github/facebook)

Actions:
  [1] Provide values now (continue immediately)
  [2] Defer (I'll add to .env later)
  [3] Mock (use fake values for now)

Select action: _
```

**User selects action:**

**Option 1: Provide values now**
- CLI prompts for each value (masked input for secrets)
- Writes to `.env` file automatically
- Agent resumes immediately with feature un-skipped

**Option 2: Defer**
- Creates `BLOCKERS.md` file with checklist
- Skips feature (priority = max + 1)
- Agent continues with other work
- User can manually mark as unblocked later

**Option 3: Mock**
- Agent implements with mock/fake values
- Adds `// TODO: Replace with real values` comments
- Feature marked as "passing with mocks"
- Tracked separately for production readiness

**F5.2.4 - Blocker Dashboard**

`BLOCKERS.md` auto-generated:
```markdown
# Blockers Requiring Human Input

Last updated: 2026-01-20 14:35

## Environment Variables Needed

- [ ] **Feature #5: OAuth authentication**
  - `OAUTH_CLIENT_ID` - Get from Google Cloud Console
  - `OAUTH_CLIENT_SECRET` - Get from Google Cloud Console
  - `OAUTH_PROVIDER` - Choose: google|github|facebook

## External Services to Configure

- [ ] **Feature #18: Email notifications**
  - Sign up for SendGrid account
  - Get API key
  - Add to `.env` as `SENDGRID_API_KEY`

## Requirements Clarifications Needed

- [ ] **Feature #25: User roles**
  - Q: What roles do we need? (admin/user/guest?)
  - Q: Can users have multiple roles?
  - Q: Who can assign roles?

---

**To unblock:** Add values to `.env`, then run:
`python start.py --unblock <feature_id>`
```

**F5.2.5 - Unblock Command**

New CLI command:
```bash
# Mark feature as unblocked
python start.py --unblock 5

# Or unblock all (agent will retry all blocked features)
python start.py --unblock-all
```

Agent picks up unblocked features in next session.

---

### F5.3 - Performance Benchmarking System

**Goal:** Measure if autocoder is actually better than alternatives.

**F5.3.1 - Benchmark Metrics**

Track across entire project lifecycle:

| Metric | Description | Target | Why It Matters |
|--------|-------------|--------|----------------|
| **Time to MVP** | Hours from spec to working prototype | < 24 hours | Speed vs manual coding |
| **Feature completion rate** | % of features passing on first try | > 60% | Quality indicator |
| **Rework ratio** | Features needing fixes / total features | < 20% | Efficiency measure |
| **Skipped feature rate** | % features skipped at least once | < 30% | Blocker frequency |
| **Human interventions** | # times user had to step in | < 10 | Autonomy level |
| **Code quality score** | Static analysis, linting, tests | > 85/100 | Maintainability |
| **Cost (API calls)** | Total Claude API cost | < $50 for MVP | Economic viability |
| **Lines of code generated** | Total LOC across all files | N/A | Productivity proxy |
| **Test coverage** | % code covered by tests | > 80% | Quality assurance |
| **WCAG compliance** | Accessibility score | AA minimum | UX quality |

**F5.3.2 - Comparative Benchmarking**

Compare against alternative approaches:

```
┌─────────────────────────────────────────────────────────────┐
│              AUTOCODER vs ALTERNATIVES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Approach              Time   Cost   Quality  Autonomy     │
│  ───────────────────────────────────────────────────────   │
│  Autocoder (this)      18h    $42    87/100   95%         │
│  Claude Code (skill)   24h    $28    82/100   60%         │
│  Cursor + Copilot      40h    $60    85/100   30%         │
│  Manual coding         120h   $0     90/100   0%          │
│                                                             │
│  Winner: Autocoder ✓                                       │
│  Advantages: Speed, autonomy                               │
│  Tradeoff: Higher cost, slightly lower quality            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**F5.3.3 - Real-Time Performance Dashboard**

During execution, display:
```
┌─────────────────────────────────────────────┐
│     AUTOCODER PERFORMANCE                   │
├─────────────────────────────────────────────┤
│ Runtime:              3h 24m                │
│ Features completed:   45/257 (18%)          │
│ Velocity:             13.2 features/hour    │
│ Estimated completion: 16h remaining         │
│                                             │
│ Efficiency:                                 │
│   Pass on first try:  28/45 (62%) ✓        │
│   Needed fixes:       17/45 (38%)           │
│   Skipped features:   12/257 (5%) ✓        │
│                                             │
│ Cost tracking:                              │
│   API calls:          1,247                 │
│   Estimated cost:     $18.50                │
│   Cost per feature:   $0.41                 │
│                                             │
│ Quality metrics:                            │
│   Code quality:       86/100 ✓             │
│   Test coverage:      79% (target: 80%)     │
│   Accessibility:      WCAG AA ✓             │
│                                             │
└─────────────────────────────────────────────┘
```

**F5.3.4 - Post-Completion Report**

When all features pass, generate comprehensive report:

```markdown
# Autocoder Performance Report

**Project:** SaaS Dashboard
**Completed:** 2026-01-20 18:45:22
**Total Time:** 18 hours 24 minutes

## Summary

✅ Successfully implemented 257/257 features (100%)
✅ Code quality score: 87/100
✅ WCAG AA compliant
⚠️  Total cost: $42.15 (within budget)

## Comparison to Alternatives

| Method | Estimated Time | Estimated Cost | Notes |
|--------|---------------|----------------|-------|
| **Autocoder** | **18.4h** | **$42.15** | Actual (this run) |
| Claude Code Skill | ~24h | ~$28 | Estimated (requires more manual intervention) |
| Cursor + Copilot | ~40h | ~$60 | Estimated (developer time + subscriptions) |
| Manual Coding | ~120h | $0 (API costs) | Estimated (senior dev at 2 feat/hour) |

**ROI Analysis:**
- Saved ~102 hours vs manual coding
- At $100/hour: Saved $10,200 in developer time
- Net savings: $10,158 after API costs
- **Conclusion: 242x ROI** ✓

## Detailed Metrics

### Development Velocity
- Average: 14.0 features/hour
- Fastest session: 22 features/hour (session #8)
- Slowest session: 6 features/hour (session #3 - debugging auth)

### Quality Metrics
- First-try success rate: 62% (159/257 features)
- Needed fixes: 38% (98/257 features)
- Average fixes per feature: 1.4
- Skipped features: 27 (10.5%) - all eventually completed

### Human Interventions
- Total interventions: 8
  - Environment variables: 5
  - Requirement clarifications: 2
  - External service setup: 1
- Average time to resolve: 12 minutes

### Cost Breakdown
- Total API calls: 3,845
- Average cost per call: $0.011
- Most expensive session: $4.80 (session #1 - initializer)
- Cheapest session: $0.85 (session #15)

### Code Quality
- Static analysis score: 87/100
  - No critical issues
  - 12 warnings (mostly minor linting)
  - 0 security vulnerabilities
- Test coverage: 82%
- Lines of code: 12,450
- Files created: 87

### Accessibility
- WCAG 2.1 AA: ✅ 100% compliant
- Color contrast: 7.2:1 (exceeds minimum)
- Keyboard navigation: ✅ Complete
- Screen reader: ✅ Optimized

## Bottlenecks Identified

1. **Feature skip rate higher than expected (10.5%)**
   - Recommendation: Better dependency analysis in initializer
   - Potential savings: ~1 hour

2. **Session #3 slowest (6 features/hour)**
   - Reason: Complex authentication debugging
   - Recommendation: Add auth-specific checkpoint agent

3. **5 environment variable pauses**
   - Recommendation: Pre-flight checklist in setup phase
   - Potential savings: ~1 hour

## Recommendations

### For Future Runs
1. ✅ Implement dependency-aware skip management (would save ~1.5h)
2. ✅ Add pre-flight checklist for env vars (would save ~1h)
3. ✅ Add auth-specific checkpoint agent (would improve quality)

### Is Autocoder Worth It?
**YES** - for projects with:
- ✅ Clear specifications (PRD or detailed requirements)
- ✅ Standard tech stacks (React, Node, etc.)
- ✅ 100+ features (where velocity matters)
- ✅ Budget for API costs ($40-100 for MVP)

**MAYBE** - for projects with:
- ⚠️  Novel/experimental tech (agent may struggle)
- ⚠️  Extremely complex business logic
- ⚠️  Lots of third-party integrations (more blockers)

**NO** - for projects with:
- ❌ < 20 features (overhead not worth it)
- ❌ Vague requirements (will need many clarifications)
- ❌ Heavy custom design (agent better at logic than aesthetics)

## Conclusion

**Autocoder successfully demonstrated 242x ROI** on this project, completing in 18.4 hours what would take ~120 hours manually. Code quality (87/100) and accessibility (WCAG AA) met targets. The 10.5% skip rate and 8 human interventions are acceptable but could be reduced with the recommended enhancements.

**Recommendation:** ✅ Use autocoder for similar projects
**Next steps:** Implement dependency tracking and pre-flight checklist
```

**F5.3.5 - A/B Testing Framework**

For direct comparison, support parallel runs:

```bash
# Run autocoder
python start.py --benchmark-mode autocoder

# Run with just Claude Code skill (for comparison)
claude /code --project my-app --benchmark-mode skill

# Generate comparison report
python benchmark_compare.py autocoder vs skill
```

Output:
```
╔════════════════════════════════════════════════════════════╗
║          AUTOCODER vs CLAUDE CODE SKILL                    ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Metric                  Autocoder    Claude Skill        ║
║  ─────────────────────────────────────────────────────    ║
║  Time to completion      18.4h        26.2h    (-30%)     ║
║  Total cost              $42.15       $31.80   (+33%)     ║
║  Features completed      257/257      245/257  (+5%)      ║
║  Code quality            87/100       89/100   (-2pts)    ║
║  Human interventions     8            22       (-64%)     ║
║  First-try success       62%          54%      (+8pts)    ║
║                                                            ║
║  Winner: Autocoder (faster, more autonomous)              ║
║  Tradeoff: Higher cost, slightly lower quality           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

Recommendation: Use autocoder when speed and autonomy matter more than cost.
```

---

### F5.4 - Continuous Improvement Loop

**F5.4.1 - Performance Data Collection**
- Every run saves metrics to `benchmarks/` directory
- JSON format for analysis
- Track improvements over time

**F5.4.2 - Pattern Recognition**
- Identify common skip reasons
- Detect bottleneck patterns (e.g., "auth features always slow")
- Find successful strategies (e.g., "implementing API first reduces skips")

**F5.4.3 - Prompt Optimization**
- A/B test different prompt variations
- Measure which prompts lead to better outcomes
- Auto-update prompts based on performance data

**F5.4.4 - Learning from Skips**
- Track: "Feature X was skipped, then implemented successfully after Y was done"
- Build skip pattern database
- Suggest order optimizations for future projects

---

## Open Questions

1. **Persona customization:** Should users be able to upload their own persona definitions? (YES - JSON format)

2. **Checkpoint override:** Should users be able to continue despite critical issues? (NO - but can disable checkpoint types)

3. **Design iteration input:** Should we support image uploads (wireframes/mockups) in addition to text specs? (FUTURE - Phase 5)

4. **Cost management:** Multiple agents = more API calls. How to optimize? (Batch operations, cache results, user-controlled frequency)

5. **Playwright test maintenance:** Who updates tests when UI changes? (Agent should auto-regenerate tests)

6. **Persona bias conflicts:** What if personas fundamentally disagree? (Synthesis agent should explain trade-offs, let user decide)

7. **Real user testing:** Should this supplement or replace real user testing? (SUPPLEMENT - AI personas are for rapid iteration, not replacement)

8. **Dependency detection accuracy:** How accurate is NLP-based dependency detection? (Target: 80%+ precision, manual override available)

9. **Human intervention timeout:** How long to wait for user input before auto-deferring? (Default: 5 minutes, configurable)

10. **Benchmark comparison fairness:** How to ensure fair comparison with other tools? (Same spec, same hardware, multiple runs averaged)

11. **Skip cascade depth:** How many levels of dependent features to cascade when skipping? (Default: 1 level, configurable up to 3)

12. **Mock vs defer default:** When env vars missing, should default be mock or defer? (USER CHOICE - ask via prompt, remember preference)

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **AI hallucinations in UX feedback** | Medium | Medium | Cross-validate with multiple personas, provide screenshots as ground truth |
| **Checkpoint false positives** | Medium | Low | Allow user to override warnings (but not critical), tune detection over time |
| **Playwright tests break frequently** | High | Medium | Auto-regenerate tests when UI changes, keep tests high-level |
| **Increased API costs** | High | Medium | User-controlled checkpoint/persona frequency, optimize batch operations |
| **Personas give generic feedback** | Medium | High | Detailed persona configs, use few-shot examples in prompts |
| **Design iteration doesn't converge** | Low | Medium | Max iteration limit (4), allow manual finalization |
| **UX scores too subjective** | Medium | Low | Use quantitative metrics where possible (contrast ratios, WCAG rules) |
| **Dependency detection false positives** | Medium | Medium | Manual dependency override, confidence scoring, user review |
| **Blocker classification errors** | Low | Medium | Agent can reclassify, user can override blocker type |
| **Human intervention delays** | High | Low | Auto-defer after timeout, track as metric |
| **Benchmark gaming** | Low | High | Use standardized test projects, audit outliers, multiple runs |
| **Over-engineering vs simpler tools** | Medium | High | Regular benchmarking, cost/benefit analysis, user feedback |
| **Rework due to skipped features** | Medium | Medium | Dependency tracking, implementation assumptions, review checkpoints |

---

## Future Enhancements (Phase 5+)

1. **Real User Integration**
   - Export persona feedback to user testing platforms
   - Import real user feedback to train personas
   - A/B test generator (creates variants for real user testing)

2. **Visual Design Generation**
   - Generate actual mockups/wireframes (via Figma API or similar)
   - Screenshot comparison (before/after iterations)
   - Style guide generation

3. **Multi-Modal Personas**
   - Voice-based personas (audio feedback)
   - Video walkthroughs from persona perspective
   - Emotion detection in persona responses

4. **Learning System**
   - Personas learn from project outcomes
   - "This persona was right about X" → increase weight
   - Adaptive evaluation criteria based on project type

5. **Collaborative Features**
   - Real team members can act as personas
   - Async design review (email digest of persona feedback)
   - Voting system (team upvotes best persona suggestions)

6. **Domain-Specific Personas**
   - Healthcare: HIPAA compliance expert
   - Finance: PCI-DSS compliance expert
   - Gaming: Retention specialist
   - E-commerce: Conversion optimizer

---

## Appendix A: Sample Persona Configuration

```json
{
  "personas": [
    {
      "id": "accessibility_advocate",
      "name": "Sarah Chen",
      "age": 34,
      "background": "Blind user since birth, works as accessibility consultant",
      "expertise": ["WCAG 2.1 AA/AAA", "ARIA", "Screen readers (JAWS, NVDA)", "Keyboard navigation"],
      "bias": "Prioritizes accessibility over aesthetics or efficiency",
      "personality": "Direct, thorough, passionate about inclusive design",
      "typical_concerns": [
        "Color contrast ratios",
        "Alt text completeness and quality",
        "Keyboard navigation completeness",
        "Focus indicators",
        "Screen reader announcements",
        "Form label associations",
        "Semantic HTML usage",
        "ARIA role correctness",
        "Dynamic content updates",
        "Error message clarity"
      ],
      "evaluation_rubric": {
        "keyboard_navigation": {
          "weight": 0.3,
          "criteria": "All interactive elements reachable via keyboard, logical tab order, visible focus indicators"
        },
        "screen_reader": {
          "weight": 0.3,
          "criteria": "All content accessible to screen readers, proper ARIA labels, meaningful announcements"
        },
        "color_contrast": {
          "weight": 0.2,
          "criteria": "WCAG AA minimum (4.5:1 for normal text, 3:1 for large text)"
        },
        "semantic_html": {
          "weight": 0.2,
          "criteria": "Proper use of headings, landmarks, lists, buttons vs links"
        }
      },
      "sample_feedback": {
        "positive": "Excellent use of semantic HTML and ARIA landmarks. The skip-to-main-content link is appreciated!",
        "negative": "The custom dropdown has no keyboard support and missing ARIA roles. This is completely unusable for me.",
        "suggestion": "Consider using a native <select> or add full keyboard navigation (Enter to open, Arrow keys to navigate, Escape to close)"
      }
    },
    {
      "id": "power_user",
      "name": "Marcus Rodriguez",
      "age": 29,
      "background": "Software engineer, uses 10+ SaaS tools daily, expects efficiency",
      "expertise": ["Keyboard shortcuts", "Automation", "API usage", "Data export"],
      "bias": "Values speed and efficiency over hand-holding",
      "personality": "Impatient, detail-oriented, appreciates power features",
      "typical_concerns": [
        "Keyboard shortcuts availability",
        "Bulk operations",
        "Search functionality",
        "Data export options",
        "API access",
        "Customization options",
        "Command palette / quick actions",
        "Multi-select capabilities",
        "Undo/redo functionality",
        "Workflow automation"
      ],
      "evaluation_rubric": {
        "efficiency": {
          "weight": 0.4,
          "criteria": "Common tasks can be completed in <3 clicks, keyboard shortcuts available"
        },
        "bulk_operations": {
          "weight": 0.3,
          "criteria": "Can select multiple items, perform batch actions"
        },
        "customization": {
          "weight": 0.2,
          "criteria": "Can configure defaults, create custom workflows, rearrange UI"
        },
        "export_api": {
          "weight": 0.1,
          "criteria": "Can export data in multiple formats, API available for automation"
        }
      },
      "sample_feedback": {
        "positive": "Love the command palette (Cmd+K). Bulk edit is smooth. Keyboard shortcuts are discoverable and intuitive.",
        "negative": "No way to export filtered data. Search doesn't support advanced queries. Can only delete items one at a time.",
        "suggestion": "Add regex support to search, export button with CSV/JSON options, and multi-select with shift-click"
      }
    }
  ]
}
```

---

## Appendix B: Checkpoint Report Example

```markdown
# Checkpoint Report #3
**Date:** 2026-01-20 14:32:15
**Features Completed:** 30 / 45 (67%)
**Trigger:** Every 10 features

---

## Summary

| Check Type | Status | Critical | Warnings | Info |
|------------|--------|----------|----------|------|
| Code Review | ⚠️ PASS WITH WARNINGS | 0 | 2 | 3 |
| Security Audit | ❌ FAIL | 2 | 1 | 0 |
| Performance | ✅ PASS | 0 | 0 | 2 |

**Decision:** 🛑 PAUSE - Critical security issues detected

---

## Code Review

**Status:** ⚠️ PASS WITH WARNINGS

### Warnings
1. **Duplicated Logic** (Medium)
   - **Location:** `src/api/users.js`, `src/api/projects.js`, `src/api/teams.js`
   - **Issue:** Pagination logic duplicated in 3 files
   - **Suggestion:** Extract to `src/utils/pagination.js`
   - **Estimated effort:** 15 minutes

2. **Magic Numbers** (Low)
   - **Location:** `src/config/limits.js:12`
   - **Issue:** Hard-coded `100` without explanation
   - **Suggestion:** Add constant `MAX_ITEMS_PER_PAGE = 100` with comment

### Info
- Code style consistent with project conventions
- TypeScript types properly defined
- Test coverage at 78% (target: 80%)

---

## Security Audit

**Status:** ❌ FAIL - CRITICAL ISSUES

### Critical Issues

1. **JWT Storage in localStorage** (Critical - OWASP A07:2021)
   - **Location:** `src/auth/tokenManager.js:23`
   - **Issue:** JWT tokens stored in localStorage are vulnerable to XSS attacks
   - **Code:**
     ```javascript
     localStorage.setItem('jwt_token', token);  // ❌ VULNERABLE
     ```
   - **Fix:** Use httpOnly cookies instead
   - **Suggested code:**
     ```javascript
     // Set httpOnly cookie server-side
     res.cookie('jwt_token', token, {
       httpOnly: true,
       secure: true,
       sameSite: 'strict',
       maxAge: 3600000
     });
     ```
   - **Feature created:** #29 "Migrate JWT storage to httpOnly cookies"

2. **No Rate Limiting on Auth Endpoint** (Critical - OWASP A07:2021)
   - **Location:** `src/api/routes/auth.js:45`
   - **Issue:** Login endpoint has no rate limiting, vulnerable to brute force
   - **Fix:** Add express-rate-limit middleware
   - **Suggested code:**
     ```javascript
     const rateLimit = require('express-rate-limit');

     const loginLimiter = rateLimit({
       windowMs: 15 * 60 * 1000, // 15 minutes
       max: 5, // 5 requests per window
       message: 'Too many login attempts, please try again later'
     });

     router.post('/login', loginLimiter, loginHandler);
     ```
   - **Feature created:** #30 "Add rate limiting to authentication"

### Warnings

1. **Sensitive Data in Logs** (Medium)
   - **Location:** `src/api/middleware/logger.js:18`
   - **Issue:** Request body logged (may contain passwords)
   - **Fix:** Sanitize logs to exclude sensitive fields

---

## Performance Check

**Status:** ✅ PASS

### Info

1. **Bundle Size Acceptable**
   - Main bundle: 245 KB (gzipped)
   - Target: < 300 KB
   - Largest dependencies: react (42KB), lodash (24KB)

2. **Moment.js Detected** (Optimization opportunity)
   - **Size:** 68 KB (gzipped)
   - **Usage:** Only date formatting
   - **Suggestion:** Replace with date-fns (14 KB) or dayjs (7 KB)
   - **Savings:** ~55 KB
   - **Feature created:** #31 "Replace moment.js with date-fns"

---

## Recommended Actions

1. ✅ **Auto-created fix features** (#29, #30, #31)
2. 🔄 **Re-run checkpoint after fixes** (automatically)
3. 📝 **Consider refactoring** pagination logic (optional)

---

**Next Steps:**
- Agent will implement features #29, #30, #31
- Checkpoint will re-run automatically after completion
- Development will resume if all critical issues resolved
```

---

## Appendix C: UX Report Example

```markdown
# UX Evaluation Report
**Project:** SaaS Dashboard
**Date:** 2026-01-20 16:45:22
**Evaluation Type:** Post-Development
**Overall Score:** 8.4 / 10 ✅ PASS

---

## Executive Summary

The SaaS Dashboard demonstrates **strong UX fundamentals** with particular strengths in accessibility and mobile responsiveness. Minor improvements needed in visual hierarchy and onboarding flow. All critical UX criteria meet or exceed targets.

**Key Findings:**
- ✅ WCAG AA compliant
- ✅ Excellent mobile experience
- ✅ Clear user flows
- ⚠️ Onboarding could be more concise
- ⚠️ 2 visual alignment issues detected

---

## Scoring by Criteria

| Criterion | Score | Status | Notes |
|-----------|-------|--------|-------|
| Visual Hierarchy | 8.2 | ✅ GOOD | Primary actions clear, minor CTA improvements needed |
| Color Scheme | 9.1 | ✅ EXCELLENT | Beautiful palette, WCAG AAA contrast achieved |
| Spacing & Alignment | 7.8 | ⚠️ GOOD | 2 alignment issues in settings page |
| Typography | 8.5 | ✅ EXCELLENT | Readable, good hierarchy, accessible sizes |
| Accessibility | 9.3 | ✅ EXCELLENT | Full keyboard nav, screen reader optimized |
| Onboarding Clarity | 7.6 | ⚠️ GOOD | Clear but could be more concise (5 steps → 3) |
| Mobile Responsiveness | 9.0 | ✅ EXCELLENT | Perfect adaptation across all viewports |

**Overall Average:** 8.4 / 10

---

## Strengths

### 1. Accessibility (9.3/10)
- ✅ Full keyboard navigation with visible focus indicators
- ✅ All images have descriptive alt text
- ✅ Color contrast exceeds WCAG AAA (7.2:1 on primary text)
- ✅ Semantic HTML with proper ARIA labels
- ✅ Screen reader tested and optimized

**Sarah (Accessibility Advocate):** "This is one of the most accessible dashboards I've tested. The keyboard navigation is flawless and the screen reader experience is excellent."

### 2. Mobile Experience (9.0/10)
- ✅ Responsive design works perfectly 375px → 1920px
- ✅ Touch targets all exceed 44x44px minimum
- ✅ No horizontal scrolling on mobile
- ✅ Fast load time on 3G (2.1s)

**David (Mobile-First User):** "Works beautifully on my phone. The hamburger menu is intuitive and everything is easily tappable."

### 3. Color Scheme (9.1/10)
- ✅ Professional, modern color palette
- ✅ Consistent with brand guidelines
- ✅ Excellent contrast ratios
- ✅ Color-blind friendly (tested with simulators)

**Aisha (Brand/Aesthetics):** "Love the color scheme! It's modern, professional, and the purple accent color really pops against the neutral grays."

---

## Weaknesses & Suggested Improvements

### 1. Onboarding Flow (7.6/10)

**Issue:** 5-step onboarding feels long for simple dashboard setup

**Current Flow:**
1. Welcome screen
2. Create workspace
3. Invite team members
4. Set preferences
5. Tour of features

**Suggested Improvement:**
- Combine steps 2+3: "Create workspace & invite team"
- Make step 4 optional: "Skip preferences for now"
- Reduce to 3 core steps

**Elena (Novice):** "The onboarding is helpful but a bit long. I just wanted to get started. Maybe make some steps optional?"

**Priority:** Medium
**Estimated Effort:** 2 hours
**Feature suggestion:** "Streamline onboarding to 3 core steps"

---

### 2. Visual Alignment Issues (7.8/10)

**Issue 1:** Settings page - Submit button not aligned with cancel
- **Location:** `screenshots/settings/preferences.png`
- **Description:** Submit button 4px lower than Cancel button
- **Fix:** Add `align-items: center` to button container
- **Priority:** Low
- **Estimated Effort:** 5 minutes

**Issue 2:** Dashboard cards - Inconsistent padding on mobile
- **Location:** `screenshots/dashboard/main.png` (mobile viewport)
- **Description:** Card padding is 16px on some cards, 20px on others
- **Fix:** Standardize to 16px in CSS
- **Priority:** Low
- **Estimated Effort:** 10 minutes

---

### 3. Visual Hierarchy (8.2/10)

**Issue:** Primary CTA not prominent enough on dashboard

**Current State:**
- "Create Project" button uses secondary style (outlined)
- Same visual weight as "View All" link

**Suggested Improvement:**
- Use solid button style for "Create Project"
- Increase size slightly (16px → 18px font)
- Add subtle shadow for depth

**Marcus (Power User):** "I kept missing the Create Project button. It should stand out more as the primary action."

**Priority:** Medium
**Estimated Effort:** 15 minutes

---

## Visual QA Issues

### Detected Automatically

1. **Settings Button Misalignment** (Fixed)
   - Screenshot: `screenshots/settings/preferences.png`
   - Issue: 4px vertical offset
   - Status: ⚠️ Needs fix

2. **Card Padding Inconsistency** (Fixed)
   - Screenshot: `screenshots/dashboard/main.png`
   - Issue: 16px vs 20px padding
   - Status: ⚠️ Needs fix

---

## Persona User Testing

### Sarah (Accessibility Advocate) - 9.5/10
**First Impression:** "Immediately impressed by keyboard navigation"

**Experience:**
- ✅ Could navigate entire app without mouse
- ✅ Screen reader announced all content clearly
- ✅ Form labels properly associated

**Would you use this?** "Absolutely! Finally a dashboard I can actually use."

**Suggestions:**
- Add keyboard shortcut reference (? key to open)
- Consider focus trap in modal dialogs

---

### Marcus (Power User) - 8.0/10
**First Impression:** "Clean interface, but where are the shortcuts?"

**Experience:**
- ✅ Search works well
- ⚠️ No bulk operations found
- ⚠️ No keyboard shortcuts

**Would you use this?** "Yes, but I'd be frustrated by the lack of power features."

**Suggestions:**
- Add Cmd+K command palette
- Bulk select and edit
- Data export functionality

---

### Elena (Novice) - 8.5/10
**First Impression:** "Looks professional but a bit overwhelming"

**Experience:**
- ✅ Onboarding helped a lot
- ✅ Error messages were clear
- ⚠️ Wish there was more help text

**Would you use this?** "Yes, once I got through onboarding it was pretty intuitive."

**Suggestions:**
- Shorter onboarding (3 steps instead of 5)
- Tooltips on complex features
- Video tutorials link

---

### David (Mobile-First) - 9.2/10
**First Impression:** "Wow, it actually works great on mobile!"

**Experience:**
- ✅ Perfect responsive design
- ✅ No horizontal scrolling
- ✅ Fast load times

**Would you use this?** "Definitely! I manage everything from my phone and this is perfect."

**Suggestions:**
- Offline mode would be amazing
- Swipe gestures for common actions

---

### Aisha (Brand/Aesthetics) - 9.0/10
**First Impression:** "Beautiful design, very modern"

**Experience:**
- ✅ Love the color palette
- ✅ Typography is excellent
- ✅ Spacing feels right

**Would you use this?** "Yes! It's one of the better-looking dashboards I've seen."

**Suggestions:**
- Subtle animations on interactions
- Illustrations for empty states
- Dark mode option

---

## Feature Suggestions (From Persona Feedback)

### High Priority
1. **Command Palette** (Marcus)
   - Cmd+K quick actions
   - Estimated effort: 8 hours
   - User demand: High

2. **Keyboard Shortcuts** (Sarah, Marcus)
   - Document and implement shortcuts
   - Estimated effort: 4 hours
   - User demand: High

### Medium Priority
3. **Bulk Operations** (Marcus)
   - Multi-select + batch actions
   - Estimated effort: 12 hours
   - User demand: Medium

4. **Dark Mode** (Aisha)
   - Toggle in settings
   - Estimated effort: 16 hours
   - User demand: Medium

5. **Tooltips & Help** (Elena)
   - Contextual help throughout app
   - Estimated effort: 6 hours
   - User demand: Medium

### Low Priority
6. **Offline Mode** (David)
   - Service worker + local storage
   - Estimated effort: 24 hours
   - User demand: Low

7. **Swipe Gestures** (David)
   - Mobile-specific interactions
   - Estimated effort: 8 hours
   - User demand: Low

---

## Accessibility Compliance

### WCAG 2.1 AA Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1.1.1 Non-text Content | ✅ PASS | All images have alt text |
| 1.3.1 Info and Relationships | ✅ PASS | Semantic HTML used throughout |
| 1.4.3 Contrast (Minimum) | ✅ PASS | 7.2:1 (exceeds 4.5:1 minimum) |
| 2.1.1 Keyboard | ✅ PASS | Full keyboard navigation |
| 2.4.3 Focus Order | ✅ PASS | Logical tab order |
| 2.4.7 Focus Visible | ✅ PASS | Clear focus indicators |
| 3.2.2 On Input | ✅ PASS | No unexpected changes |
| 4.1.2 Name, Role, Value | ✅ PASS | Proper ARIA usage |

**Overall WCAG AA Compliance:** ✅ 100%

**WCAG AAA (Optional):**
- 1.4.6 Contrast (Enhanced): ✅ PASS (7.2:1 exceeds 7:1)
- 2.4.8 Location: ⚠️ N/A (Single-page app)

---

## Recommended Actions

### Critical (Fix before launch)
*None - all critical criteria met*

### High Priority (Fix this week)
1. Fix button alignment in settings page (5 min)
2. Standardize card padding (10 min)
3. Increase Create Project button prominence (15 min)
4. Add keyboard shortcuts reference (2 hours)

### Medium Priority (Next sprint)
1. Streamline onboarding to 3 steps (2 hours)
2. Implement command palette (8 hours)
3. Add bulk operations (12 hours)

### Low Priority (Future)
1. Dark mode (16 hours)
2. Offline mode (24 hours)
3. Swipe gestures (8 hours)

---

## Conclusion

The SaaS Dashboard achieves an **excellent UX score of 8.4/10** with particular strengths in accessibility and mobile design. With minor refinements to visual alignment and onboarding flow, this product is ready for launch.

**Launch Readiness:** ✅ APPROVED
**Recommendation:** Fix 2 visual alignment issues, then ship. Add command palette in v1.1.

---

**Report Generated:** 2026-01-20 16:45:22
**Evaluation Duration:** 12 minutes
**Screenshots Analyzed:** 15
**Personas Consulted:** 5
**Issues Found:** 5 (0 critical, 3 medium, 2 low)
```

---

*End of Enhancement PRD*

---

## Questions for User

1. Which phase should we prioritize first?
   - [ ] Phase 1: Checkpoints (catch bugs during development)
   - [ ] Phase 2: Design Iteration (improve specs before coding)
   - [ ] Phase 3: Playwright + UX (validate final product)

2. What persona types are most valuable to you?
   - [ ] Accessibility-focused
   - [ ] Power user / efficiency
   - [ ] Novice / beginner-friendly
   - [ ] Mobile-first
   - [ ] Brand / aesthetics
   - [ ] Security / compliance
   - [ ] Other: ___________

3. Checkpoint frequency preference:
   - [ ] Every 5 features (frequent feedback)
   - [ ] Every 10 features (balanced)
   - [ ] Every 20 features (minimal interruption)
   - [ ] Manual only

4. Budget considerations:
   - [ ] Cost is not a concern
   - [ ] Keep API calls minimal (disable some features)
   - [ ] Need cost estimates before proceeding

5. **NEW: Skip management priorities (Phase 5)**
   - [ ] Dependency tracking (prevent rework when skipped features implemented)
   - [ ] Human-in-the-loop for blockers (pause for env vars, etc.)
   - [ ] Both equally important
   - [ ] Defer to later phase

6. **NEW: Human intervention preference for blockers:**
   - [ ] Always pause and ask (I want control)
   - [ ] Auto-defer with notification (keep running, I'll fix later)
   - [ ] Mock when possible (use fake values, mark for review)
   - [ ] Smart mode (agent decides based on blocker type)

7. **NEW: Performance benchmarking priority:**
   - [ ] Critical - Must prove ROI vs manual/other tools
   - [ ] Important - Want to track but not blocking
   - [ ] Nice to have - Interesting but not required
   - [ ] Skip - Not interested in benchmarking

8. **NEW: Comparison baseline (if benchmarking):**
   - [ ] Manual coding (traditional developer)
   - [ ] Claude Code skill (direct Claude usage)
   - [ ] Cursor + GitHub Copilot
   - [ ] Other AI coding tools (specify: _________)
   - [ ] All of the above

---

**Next Steps:** Review this PRD, provide feedback, and we'll begin implementation!

---

## User Feedback Notes (2026-01-20)

**Key insights from user:**

1. **Skip dependency tracking is critical** - "When we come back later and eventually code the skipped feature, we don't want re-work due to new decisions."
   - Priority: HIGH
   - Rationale: Prevents wasted effort refactoring downstream features

2. **Human-in-the-loop for blockers is necessary** - "Many of these skips require me to put in environment variables for example."
   - Priority: HIGH
   - Rationale: Env vars, API keys, service credentials are common blockers
   - User appreciates that agent "is getting to work first, and stopping second" (autonomy-first approach)

3. **Performance evaluation is essential** - "I would like to evaluate how we did versus other coding systems, or even just using something like a claude skill."
   - Priority: HIGH
   - Rationale: Need to prove autocoder isn't "over-engineered a worse way to code"
   - Must demonstrate ROI and compare to simpler alternatives

**Design principles derived:**
- ✅ Maximize autonomy (work first, ask second)
- ✅ Track downstream impact (prevent rework)
- ✅ Graceful degradation (pause for blockers, not fail)
- ✅ Prove value (benchmark vs alternatives)
