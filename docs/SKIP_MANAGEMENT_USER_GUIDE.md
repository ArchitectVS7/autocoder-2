# Skip Management User Guide

**Version:** 1.0
**Phase:** Phase 1 Complete
**Last Updated:** 2026-01-21

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Understanding Skip Behavior](#understanding-skip-behavior)
4. [Human Intervention Workflow](#human-intervention-workflow)
5. [Working with Blockers](#working-with-blockers)
6. [Managing Assumptions](#managing-assumptions)
7. [CLI Reference](#cli-reference)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Skip Management system in Autocoder prevents rework by intelligently handling features that can't be implemented immediately. When a feature is skipped, the system:

- **Tracks dependencies** automatically to understand downstream impact
- **Classifies blockers** to determine if human input is needed
- **Documents assumptions** when building on skipped features
- **Reviews assumptions** when skipped features are eventually implemented

This ensures that when you come back to implement a skipped feature later, you won't have to refactor downstream work.

---

## Core Concepts

### Dependencies

A **dependency** is when one feature requires another feature to be completed first.

```
Feature #5: OAuth authentication
    ↓ (depends on)
Feature #12: Show OAuth avatar in profile
```

Dependencies are detected automatically through:
- Explicit references: `"#5"`, `"Feature 12"`, `"Task #3"`
- Keywords: `"after"`, `"once"`, `"depends on"`, `"requires"`
- Categories: Features in the same category may have implicit dependencies

### Skipped Features

When the agent encounters a feature it can't implement, it **skips** the feature by moving it to the end of the queue. The feature is marked with:
- `was_skipped = True`
- `skip_count` increments each time it's skipped
- `blocker_type` and `blocker_description` explain why

### Blockers

A **blocker** is a reason why a feature can't be implemented. Types include:

| Blocker Type | Requires Human | Description | Example |
|--------------|----------------|-------------|---------|
| **ENV_CONFIG** | ✅ Yes | Missing environment variables or API keys | `OAUTH_CLIENT_ID`, `DATABASE_URL` |
| **EXTERNAL_SERVICE** | ✅ Yes | Third-party service not set up | Stripe account, SendGrid API |
| **TECH_PREREQUISITE** | ⚠️ Maybe | Depends on unbuilt feature | Need API endpoint before frontend |
| **UNCLEAR_REQUIREMENTS** | ✅ Yes | Ambiguous specification | "What should error message say?" |
| **LEGITIMATE_DEFERRAL** | ❌ No | Can safely defer | Polish animations, nice-to-haves |

### Assumptions

When the agent implements a feature that depends on a **skipped** feature, it documents **assumptions** about how the skipped feature will eventually work.

```javascript
// ASSUMPTION: OAuth feature #5 will use Google OAuth
// If different provider chosen, update avatar URL parsing
// See: features.db assumption #123
async function getOAuthAvatar(userId) {
  // Placeholder until OAuth (#5) is implemented
  return '/default-avatar.png';
}
```

---

## Understanding Skip Behavior

### Skip Impact Analysis

When a feature is skipped, the system analyzes downstream impact:

```
⚠️  SKIP IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Skipping Feature #5: "OAuth authentication"

⚠️  Downstream impact (3 features depend on this):
  🔴 Feature #12: User profile OAuth avatar (confidence: 85%)
  🔴 Feature #23: Third-party account linking (confidence: 92%)
  🟡 Feature #31: Social media sharing (confidence: 78%)

  + 2 more features indirectly affected (cascade depth: 2-3 levels)

📋 RECOMMENDATION: IMPLEMENT_WITH_MOCKS
  Implement dependent features with documented assumptions
  Mark them for review when #5 is implemented

🎯 ACTIONS
  [1] Skip all dependent features (cascade)
  [2] Implement dependents with mocks/placeholders
  [3] Cancel skip (implement this feature now)
  [4] Continue anyway (expert mode)
```

**Recommendations:**
- **SAFE_TO_SKIP** - No dependencies, skip without issue
- **CASCADE_SKIP** - Many dependents (5+), skip them too
- **IMPLEMENT_WITH_MOCKS** - Few dependents (1-3), use placeholders
- **REVIEW_DEPENDENCIES** - Moderate impact, review carefully

---

## Human Intervention Workflow

When the agent encounters a blocker requiring human input, it pauses and prompts you:

```
🛑 HUMAN INPUT REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature #5: "OAuth authentication"
Blocker Type: Environment Configuration

Missing environment variables: OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET

Required information:
  • OAUTH_CLIENT_ID (from Google Cloud Console)
  • OAUTH_CLIENT_SECRET (from Google Cloud Console)
  • OAUTH_PROVIDER (google/github/facebook)

🎯 ACTIONS
  [1] Provide values now (continue immediately)
  [2] Defer (I'll add to .env later)
  [3] Mock (use fake values for now)

Select action (1-3): _
```

### Action 1: Provide Values Now

The CLI prompts for each required value:

```
📝 Please provide the following values:

  OAUTH_CLIENT_ID: 123456789.apps.googleusercontent.com
  OAUTH_CLIENT_SECRET: *********** (masked)
  OAUTH_PROVIDER: google

✓ Values provided and saved to .env
→ Agent will resume immediately
```

- Values are automatically written to `.env` file
- Secrets are masked during input
- Agent continues immediately with the feature

### Action 2: Defer

The feature is skipped and added to `BLOCKERS.md`:

```markdown
# Blockers Requiring Human Input

Last updated: 2026-01-21 14:35:22
Total blockers: 3

## Environment Variables Needed

- [ ] **Feature #5: OAuth authentication**
  - Missing OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET
  - `OAUTH_CLIENT_ID` - Get from Google Cloud Console
  - `OAUTH_CLIENT_SECRET` - Get from Google Cloud Console
  - `OAUTH_PROVIDER` - Choose: google|github|facebook
  - **To unblock:** `python start.py --unblock 5`
```

You can unblock later with: `python start.py --unblock 5`

### Action 3: Mock

The agent implements with fake/placeholder values:

```javascript
// MOCK IMPLEMENTATION - Replace with real values
const OAUTH_CLIENT_ID = 'mock-client-id-12345';
const OAUTH_CLIENT_SECRET = 'mock-secret-67890';

// TODO: Feature #5 - Replace mocks when real OAuth is configured
```

- Feature marked as `passing_with_mocks = True`
- Tracked separately for production readiness review

---

## Working with Blockers

### Viewing Active Blockers

```bash
# Show all active blockers
python blockers_cli.py --project-dir my-app --show-blockers

# Output:
Active Blockers (3):

#5  OAuth authentication [Environment Configuration]
    Missing OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET

#18 Email notifications [External Service Setup]
    Need SendGrid account and API key

#25 User roles system [Requirements Clarification]
    Role types and permissions need definition
```

### Unblocking Features

After you've resolved a blocker (added env vars, set up services, etc.):

```bash
# Unblock specific feature
python blockers_cli.py --project-dir my-app --unblock 5

# Output:
✓ Feature #5 'OAuth authentication' unblocked
✓ Removed from BLOCKERS.md
→ Agent will retry this feature in next session
```

Unblock all at once:

```bash
python blockers_cli.py --project-dir my-app --unblock-all

# Output:
✓ Unblocked 3 features:
  • #5 OAuth authentication
  • #18 Email notifications
  • #25 User roles system

→ Agent will retry all unblocked features in next session
```

### Viewing Dependencies

See what a feature depends on (and what depends on it):

```bash
python blockers_cli.py --project-dir my-app --dependencies 12

# Output:
Feature #12: User profile OAuth avatar

📦 Dependencies (1) - This feature depends on:
  🔴 #5 OAuth authentication (85%) ⏳
      Detected via: keyword_detection

⬆️  Dependents (2) - These features depend on this one:
  🟡 #45 Avatar in email notifications (70%) ⏳
  🟡 #67 Social media profile sync (65%) ⏳
```

---

## Managing Assumptions

### What Are Assumptions?

When the agent implements Feature B that depends on skipped Feature A, it documents **assumptions** about how Feature A will work.

### Viewing Assumptions

```bash
# Show assumptions for a specific feature
python assumptions_cli.py --project-dir my-app --feature 12

# Output:
============================================================
Feature #12: User profile OAuth avatar
============================================================

Total assumptions: 1

📝 Assumption #1 [ACTIVE]
   Depends on: Feature #5 - OAuth authentication
   Assumption: OAuth will use Google OAuth provider
   Location: src/api/users.js:145-152
   Impact: If different provider chosen, avatar URL parsing needs update
```

View all assumptions:

```bash
# Show all active assumptions
python assumptions_cli.py --project-dir my-app --show-all

# Filter by status
python assumptions_cli.py --project-dir my-app --show-all --status NEEDS_REVIEW
```

### Reviewing Assumptions

When a previously skipped feature is implemented, review its assumptions:

```bash
python assumptions_cli.py --project-dir my-app --review 5

# Output:
============================================================
✓ Feature #5 'OAuth authentication' marked as passing
============================================================

⚠️  ASSUMPTION REVIEW REQUIRED

3 features made assumptions about this implementation:

Feature #12: User profile OAuth avatar
  Assumption: "OAuth will use Google OAuth provider"
  Location: src/api/users.js:145-152
  Status: ⚠️ NEEDS_REVIEW

Feature #23: Third-party account linking
  Assumption: "OAuth tokens stored in JWT"
  Location: src/api/auth.js:67-82
  Status: ⚠️ NEEDS_REVIEW

Feature #31: Social media sharing
  Assumption: "OAuth includes social media scopes"
  Location: src/api/sharing.js:34-41
  Status: ⚠️ NEEDS_REVIEW
```

### Validating/Invalidating Assumptions

After reviewing the implementation:

```bash
# Mark assumption as correct
python assumptions_cli.py --project-dir my-app --validate-assumption 1

# Output:
✓ Assumption #1 marked as VALIDATED
  Feature: #12 - User profile OAuth avatar
  Assumption: OAuth will use Google OAuth provider
  → No rework needed for this feature

# Mark assumption as incorrect
python assumptions_cli.py --project-dir my-app --invalidate-assumption 2

# Output:
⚠️  Assumption #2 marked as INVALID
  Feature: #23 - Third-party account linking
  Assumption: OAuth tokens stored in JWT
  → Feature #23 may need rework

Recommended action:
  - Review the implementation in: src/api/auth.js:67-82
  - Consider creating a fix feature
  - Impact: Must update token storage approach
```

---

## CLI Reference

### Blocker Management

```bash
# Show active blockers
python blockers_cli.py --project-dir <path> --show-blockers

# Unblock specific feature
python blockers_cli.py --project-dir <path> --unblock <feature_id>

# Unblock all features
python blockers_cli.py --project-dir <path> --unblock-all

# Show dependencies
python blockers_cli.py --project-dir <path> --dependencies <feature_id>

# Verbose output
python blockers_cli.py --project-dir <path> --show-blockers -v
```

### Assumption Management

```bash
# Show assumptions for a feature
python assumptions_cli.py --project-dir <path> --feature <feature_id>

# Show all assumptions
python assumptions_cli.py --project-dir <path> --show-all

# Filter by status
python assumptions_cli.py --project-dir <path> --show-all --status ACTIVE

# Review assumptions when feature completed
python assumptions_cli.py --project-dir <path> --review <feature_id>

# Validate assumption (correct)
python assumptions_cli.py --project-dir <path> --validate-assumption <id>

# Invalidate assumption (incorrect)
python assumptions_cli.py --project-dir <path> --invalidate-assumption <id>

# Verbose output
python assumptions_cli.py --project-dir <path> --feature <id> -v
```

### Dependency Detection

```bash
# Run dependency detection manually
python dependency_detector.py <project_dir>

# Output:
Total features: 45
Total dependencies: 23
Features with dependencies: 18
```

### Skip Impact Analysis

```bash
# Analyze impact of skipping a feature
python skip_analyzer.py <project_dir> <feature_id>

# Example:
python skip_analyzer.py my-app 5
```

---

## Best Practices

### 1. Review BLOCKERS.md Regularly

Check `BLOCKERS.md` in your project directory to see what's blocking progress:

```bash
cat my-app/BLOCKERS.md
```

Prioritize resolving blockers that affect many features.

### 2. Unblock Early

When you have the information (env vars, service credentials), unblock immediately:

```bash
# Add to .env
echo "OAUTH_CLIENT_ID=your-client-id" >> .env
echo "OAUTH_CLIENT_SECRET=your-secret" >> .env

# Unblock the feature
python blockers_cli.py --project-dir my-app --unblock 5
```

### 3. Review Assumptions Promptly

When a previously skipped feature is completed, review assumptions immediately:

```bash
python assumptions_cli.py --project-dir my-app --review 5
```

Don't let invalid assumptions linger - they compound over time.

### 4. Use Mocks for Prototyping

If you're in rapid prototyping mode, use Action 3 (Mock) to keep moving:

- Faster iteration
- Test integration logic
- Replace mocks with real implementation later

### 5. Document Environment Variables Upfront

Create a `.env.example` file with all required variables:

```bash
# .env.example
OAUTH_CLIENT_ID=your-client-id-here
OAUTH_CLIENT_SECRET=your-secret-here
OAUTH_PROVIDER=google
DATABASE_URL=postgresql://localhost/myapp
SENDGRID_API_KEY=your-api-key-here
```

This helps avoid blocker pauses.

---

## Troubleshooting

### Feature Keeps Getting Skipped

**Problem:** Feature skips repeatedly (`skip_count` increases)

**Solutions:**
1. Check blocker type: `python blockers_cli.py --project-dir . --show-blockers`
2. If ENV_CONFIG: Add missing env vars and unblock
3. If TECH_PREREQUISITE: Ensure dependency is completed first
4. If UNCLEAR_REQUIREMENTS: Clarify the feature description

### Dependencies Not Detected

**Problem:** Feature has dependencies but they weren't detected

**Solutions:**
1. Make dependencies explicit in description: `"After feature #5 is done..."`
2. Run manual detection: `python dependency_detector.py .`
3. Check dependency confidence scores (may need threshold adjustment)

### Assumptions Not Showing

**Problem:** Assumptions aren't being tracked

**Solutions:**
1. Ensure dependent feature references skipped feature in description
2. Check if dependency was detected: `python blockers_cli.py --project-dir . --dependencies <id>`
3. Look for assumptions: `python assumptions_cli.py --project-dir . --feature <id>`

### BLOCKERS.md Not Updating

**Problem:** BLOCKERS.md file is out of sync

**Solutions:**
1. Regenerate manually: `python blockers_md_generator.py .`
2. Check file permissions (should be writable)
3. Verify blockers exist in database

### Agent Not Resuming After Unblock

**Problem:** Unblocked feature but agent doesn't retry

**Solutions:**
1. Verify unblock worked: `python blockers_cli.py --project-dir . --show-blockers`
2. Check feature status: Feature should have `is_blocked = False`
3. Restart agent session to pick up changes

---

## Next Steps

- **Developer Guide:** Learn how to extend the skip management system
- **Troubleshooting Guide:** Detailed debugging for common issues
- **API Reference:** Integrate skip management into custom workflows

---

**Need Help?**
- Check [Troubleshooting Guide](./TROUBLESHOOTING.md)
- See [Developer Guide](./DEVELOPER_GUIDE.md) for extending the system
- Report issues at: https://github.com/anthropics/autocoder/issues
