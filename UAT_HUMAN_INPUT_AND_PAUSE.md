# User Acceptance Testing (UAT) Script
## Human Input System & Pause/Drain Mode

**Last Updated:** 2026-02-16
**Version:** 1.0

---

## Overview

This UAT script validates two new features:
1. **Human Input System** - Agents can request structured input from humans
2. **Pause/Drain Mode** - Graceful pause that lets agents finish their current work

Both features support **two modes**:
- **Human Mode**: Requires actual human interaction (default)
- **Supervisory Agent Mode**: AI agent handles human input requests (full YOLO mode)

---

## Prerequisites

### Required Setup
- ✅ AutoCoder 2 installed and configured
- ✅ Python 3.11+ with virtual environment activated
- ✅ Test project registered in the system
- ✅ UI server running (`python start_ui.py`)

### Test Data
Create a test project with features that require human input:

```xml
<!-- prompts/app_spec.txt -->
<app>
  <name>OAuth Demo App</name>
  <description>
    A demo app that requires OAuth credentials to test human input gates.
  </description>

  <features>
    <feature priority="1">
      <name>Configure OAuth Provider</name>
      <description>
        Set up OAuth authentication with Google.
        IMPORTANT: You must use feature_request_human_input to get OAuth credentials.
        Do NOT proceed without actual client_id and client_secret from a human.
      </description>
    </feature>

    <feature priority="2">
      <name>Implement Login Flow</name>
      <description>
        Build the OAuth login flow using the credentials from Feature 1.
      </description>
      <dependencies>
        <dependency>Feature 1 (OAuth credentials)</dependency>
      </dependencies>
    </feature>

    <feature priority="3">
      <name>Add User Profile Page</name>
      <description>
        Display user information after successful authentication.
      </description>
      <dependencies>
        <dependency>Feature 2 (Login flow)</dependency>
      </dependencies>
    </feature>
  </features>
</app>
```

---

## Configuration Modes

### Mode 1: Human Gates (Default)
Features requiring credentials will pause and wait for human input.

**No special configuration needed** - this is the default behavior.

### Mode 2: Supervisory Agent (Full YOLO)
AI agent acts as supervisor and provides mock credentials automatically.

**Setup Instructions:**

1. Create supervisory agent prompt:
```bash
mkdir -p prompts/supervisor
cat > prompts/supervisor/supervisor_prompt.md << 'EOF'
You are a Supervisory Agent responsible for handling human input requests.

When you receive a human_input_request from a coding agent:
1. Analyze the request and understand what credentials/decisions are needed
2. For development/testing, provide reasonable mock values
3. Respond using the format expected by the coding agent

Guidelines:
- OAuth credentials: Use mock values (client_id: "mock-client-123", client_secret: "mock-secret-456")
- API keys: Use format "test-key-{random_string}"
- Design decisions: Choose the most standard/recommended option
- Configuration: Use safe defaults for development

Always respond promptly to unblock the coding agent.
EOF
```

2. Enable supervisory agent mode:
```bash
# In .env or environment:
export ENABLE_SUPERVISORY_AGENT=true
export SUPERVISORY_AGENT_MODEL=claude-sonnet-4-5
```

3. Start agent with supervisory mode:
```bash
python autonomous_agent_demo.py --project-dir oauth-demo --supervisory-agent
```

---

## Test Scenarios

### Scenario 1: Human Input Request (Human Mode)

**Objective:** Verify that agent correctly requests human input and waits.

**Steps:**

1. **Start the agent** (standard mode):
   ```bash
   python autonomous_agent_demo.py --project-dir oauth-demo
   ```

2. **Monitor agent progress** via UI or logs

3. **Wait for human input request**:
   - Agent should detect Feature 1 requires OAuth credentials
   - Agent should call `feature_request_human_input()`
   - Feature should move to `needs_human_input=True`
   - Agent should log: "Feature 'Configure OAuth Provider' is now blocked waiting for human input"

4. **Verify in UI**:
   - Navigate to `http://localhost:8000/`
   - Select the oauth-demo project
   - Look for a notification/badge showing "1 feature awaiting input"
   - Click to view the human input request

5. **Review request details**:
   ```json
   {
     "prompt": "Need OAuth credentials for Google API",
     "fields": [
       {
         "id": "client_id",
         "label": "OAuth Client ID",
         "type": "text",
         "required": true,
         "placeholder": "Enter your Google OAuth client ID"
       },
       {
         "id": "client_secret",
         "label": "OAuth Client Secret",
         "type": "text",
         "required": true,
         "placeholder": "Enter your Google OAuth client secret"
       }
     ]
   }
   ```

6. **Provide response** (via UI or API):

   **Option A - UI (Recommended):**
   - Fill in the form with test credentials
   - Click "Submit Response"

   **Option B - API:**
   ```bash
   curl -X POST http://localhost:8000/api/projects/oauth-demo/features/1/human-input \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "123456789.apps.googleusercontent.com",
       "client_secret": "GOCSPX-test_secret_123"
     }'
   ```

7. **Verify feature resumes**:
   - Feature should move back to pending queue
   - `needs_human_input` should be `False`
   - `human_input_response` should contain your values
   - Agent should pick up Feature 1 again on next poll
   - Agent should access credentials via `human_input_response`

**Expected Result:**
✅ Agent successfully requests input, waits, receives response, and resumes with credentials

**Failure Cases to Test:**
- ❌ Missing required field: API should return 400 error
- ❌ Response to non-waiting feature: API should return 400 error
- ❌ Invalid feature ID: API should return 404 error

---

### Scenario 2: Human Input Request (Supervisory Agent Mode)

**Objective:** Verify that supervisory agent handles input requests automatically.

**Steps:**

1. **Start agent with supervisory mode**:
   ```bash
   python autonomous_agent_demo.py --project-dir oauth-demo --supervisory-agent
   ```

2. **Monitor progress** - should be fully automated

3. **Verify supervisory agent activation**:
   - When Feature 1 calls `feature_request_human_input()`
   - Supervisory agent should be triggered automatically
   - Supervisory agent should analyze the request
   - Supervisory agent should provide mock credentials
   - Feature should resume without human intervention

4. **Check logs for supervisory agent activity**:
   ```
   [SUPERVISOR] Received human input request for Feature 1
   [SUPERVISOR] Request: Need OAuth credentials for Google API
   [SUPERVISOR] Providing mock credentials for development
   [SUPERVISOR] Response submitted: client_id=mock-client-123, client_secret=mock-secret-456
   ```

5. **Verify feature completion**:
   - Feature 1 should complete with mock credentials
   - Feature 2 should start automatically (dependency satisfied)
   - No human intervention required

**Expected Result:**
✅ Supervisory agent handles all human input requests automatically with sensible defaults

---

### Scenario 3: Pause/Drain Mode (Graceful Pause)

**Objective:** Verify that pause gracefully drains running agents.

**Steps:**

1. **Start agent with parallel mode**:
   ```bash
   python autonomous_agent_demo.py --project-dir oauth-demo --parallel --max-concurrency 3
   ```

2. **Wait for agents to start** (3 features should be in progress)

3. **Request pause** (via UI or API):

   **Option A - UI:**
   - Click "Pause" button in agent controls
   - Should show "Draining..." status

   **Option B - API:**
   ```bash
   curl -X POST http://localhost:8000/api/projects/oauth-demo/agent/pause
   ```

4. **Observe drain behavior**:
   - New features should NOT be started
   - Running agents should continue their current features
   - UI should show "Paused (draining X agents)"
   - Log should show: "Graceful pause requested - draining running agents..."

5. **Wait for all agents to complete**:
   - As each agent finishes, count should decrement
   - When all agents finish: "All agents drained - paused."
   - No new agents should spawn

6. **Verify paused state**:
   - Agent status should be "paused"
   - `.autocoder/.pause_drain` file should exist
   - UI should show "Paused" status with resume button enabled

7. **Resume from pause**:

   **Option A - UI:**
   - Click "Resume" button

   **Option B - API:**
   ```bash
   curl -X POST http://localhost:8000/api/projects/oauth-demo/agent/resume
   ```

8. **Verify resumption**:
   - Log should show: "Resuming from graceful pause..."
   - Agents should start spawning again
   - Work should continue normally
   - `.autocoder/.pause_drain` file should be deleted

**Expected Result:**
✅ Pause gracefully drains agents, waits for completion, and resumes cleanly

**Timing Expectations:**
- Pause request: Immediate (<1s)
- Drain completion: Depends on feature complexity (30s-5min typical)
- Resume: Immediate (<1s)

---

### Scenario 4: Multiple Human Input Requests

**Objective:** Verify handling of multiple features awaiting input simultaneously.

**Steps:**

1. Create a spec with 3 features that all need human input:
   ```xml
   <feature priority="1">
     <name>Get OpenAI API Key</name>
     <description>Request OpenAI API key from human</description>
   </feature>

   <feature priority="2">
     <name>Get Stripe API Key</name>
     <description>Request Stripe API key from human</description>
   </feature>

   <feature priority="3">
     <name>Get SendGrid API Key</name>
     <description>Request SendGrid API key from human</description>
   </feature>
   ```

2. **Start agent with parallel mode**:
   ```bash
   python autonomous_agent_demo.py --project-dir api-keys --parallel --max-concurrency 3
   ```

3. **Verify all 3 features request input**:
   - All 3 should call `feature_request_human_input()` concurrently
   - All 3 should appear in the "Awaiting Input" list

4. **Query via API**:
   ```bash
   curl http://localhost:8000/api/projects/api-keys/features/human-input
   ```

   **Expected response:**
   ```json
   {
     "features": [
       {
         "id": 1,
         "name": "Get OpenAI API Key",
         "needs_human_input": true,
         "human_input_request": {...}
       },
       {
         "id": 2,
         "name": "Get Stripe API Key",
         "needs_human_input": true,
         "human_input_request": {...}
       },
       {
         "id": 3,
         "name": "Get SendGrid API Key",
         "needs_human_input": true,
         "human_input_request": {...}
       }
     ],
     "total": 3
   }
   ```

5. **Respond to each request** (in any order):
   - Respond to Feature 2 first
   - Then Feature 1
   - Finally Feature 3

6. **Verify features resume in priority order**:
   - Feature 1 should resume first (highest priority)
   - Then Feature 2
   - Then Feature 3

**Expected Result:**
✅ Multiple human input requests handled independently and correctly

---

### Scenario 5: Pause During Human Input Wait

**Objective:** Verify pause works when features are awaiting human input.

**Steps:**

1. **Start agent** and let it request human input for Feature 1

2. **Verify feature is waiting** (needs_human_input=True)

3. **Request pause** via UI or API

4. **Verify immediate pause**:
   - No agents are running
   - Pause should complete immediately (no drain needed)
   - Status should show "Paused (0 running agents)"

5. **Provide human input** while paused:
   ```bash
   curl -X POST http://localhost:8000/api/projects/oauth-demo/features/1/human-input \
     -H "Content-Type: application/json" \
     -d '{"client_id": "test", "client_secret": "test"}'
   ```

6. **Verify input is recorded** but feature doesn't start yet

7. **Resume agent**:
   ```bash
   curl -X POST http://localhost:8000/api/projects/oauth-demo/agent/resume
   ```

8. **Verify feature picks up** with the provided input

**Expected Result:**
✅ Human input can be provided while paused, and feature resumes when agent resumes

---

## Test Data Summary

### Human Mode Test Features

```python
# Feature 1: OAuth Configuration (requires human input)
{
    "name": "Configure OAuth Provider",
    "human_input_request": {
        "prompt": "Need OAuth credentials for Google API",
        "fields": [
            {"id": "client_id", "type": "text", "required": true},
            {"id": "client_secret", "type": "text", "required": true}
        ]
    }
}

# Feature 2: API Key Configuration (requires human input)
{
    "name": "Configure External APIs",
    "human_input_request": {
        "prompt": "Need API keys for external services",
        "fields": [
            {"id": "openai_key", "type": "text", "required": true},
            {"id": "stripe_key", "type": "text", "required": false},
            {
                "id": "environment",
                "type": "select",
                "options": [
                    {"value": "dev", "label": "Development"},
                    {"value": "prod", "label": "Production"}
                ],
                "required": true
            }
        ]
    }
}

# Feature 3: Design Decision (requires human input)
{
    "name": "Choose UI Framework",
    "human_input_request": {
        "prompt": "Which UI framework should we use?",
        "fields": [
            {
                "id": "framework",
                "type": "select",
                "options": [
                    {"value": "react", "label": "React"},
                    {"value": "vue", "label": "Vue.js"},
                    {"value": "svelte", "label": "Svelte"}
                ],
                "required": true
            },
            {
                "id": "use_typescript",
                "type": "boolean",
                "required": true
            }
        ]
    }
}
```

### Supervisory Agent Responses

```python
# Supervisory agent should provide these mock values:

# OAuth credentials
{
    "client_id": "mock-client-123.apps.googleusercontent.com",
    "client_secret": "GOCSPX-mock-secret-456"
}

# API keys
{
    "openai_key": "sk-test-openai-mock-key-789",
    "stripe_key": "sk_test_stripe_mock_key_abc",
    "environment": "dev"
}

# Design decisions
{
    "framework": "react",
    "use_typescript": true
}
```

---

## Success Criteria

### Human Input System
- ✅ Agent correctly identifies when human input is needed
- ✅ `feature_request_human_input()` creates request with valid schema
- ✅ Feature state transitions: in_progress → needs_human_input
- ✅ UI displays human input requests with proper formatting
- ✅ Human can provide responses via UI or API
- ✅ Validation rejects missing required fields
- ✅ Feature resumes after receiving valid response
- ✅ Multiple concurrent human input requests handled independently
- ✅ Supervisory agent mode handles requests automatically (full YOLO)

### Pause/Drain Mode
- ✅ Pause request creates `.autocoder/.pause_drain` signal file
- ✅ Orchestrator detects pause signal within 1 polling interval (<5s)
- ✅ New agents stop spawning after pause detected
- ✅ Running agents complete their current features
- ✅ Agent enters paused state when all agents drained
- ✅ Resume removes signal file and resumes spawning
- ✅ Multiple pause/resume cycles work correctly
- ✅ Pause works when no agents are running (immediate)
- ✅ Pause works when agents are awaiting human input

---

## Troubleshooting

### Issue: Human input request not appearing in UI
**Diagnosis:**
```bash
# Check database directly
sqlite3 <project-dir>/features.db "SELECT id, name, needs_human_input, human_input_request FROM features WHERE needs_human_input=1;"
```

**Fix:**
- Verify WebSocket connection is active
- Check browser console for errors
- Refresh UI page

### Issue: Pause not draining agents
**Diagnosis:**
```bash
# Check if signal file exists
ls -la <project-dir>/.autocoder/.pause_drain

# Check orchestrator logs
tail -f agent_output.log | grep -i drain
```

**Fix:**
- Verify signal file was created
- Check orchestrator is polling (should log every 5s)
- Ensure agents aren't stuck/crashed

### Issue: Supervisory agent not responding
**Diagnosis:**
```bash
# Check supervisory agent is enabled
echo $ENABLE_SUPERVISORY_AGENT

# Check logs for supervisor activity
grep -i supervisor agent_output.log
```

**Fix:**
- Verify environment variable is set correctly
- Check supervisor prompt file exists
- Ensure supervisor agent model is valid

---

## Appendix: API Reference

### Get Features Needing Human Input
```bash
GET /api/projects/{project_name}/features/human-input

Response:
{
  "features": [...],
  "total": 3
}
```

### Respond to Human Input
```bash
POST /api/projects/{project_name}/features/{feature_id}/human-input
Content-Type: application/json

{
  "field_id_1": "value1",
  "field_id_2": "value2"
}

Response:
{
  "success": true,
  "feature_id": 1,
  "message": "Human input recorded for feature 'Configure OAuth'"
}
```

### Pause Agent
```bash
POST /api/projects/{project_name}/agent/pause

Response:
{
  "success": true,
  "status": "paused",
  "message": "Graceful pause requested - draining running agents"
}
```

### Resume Agent
```bash
POST /api/projects/{project_name}/agent/resume

Response:
{
  "success": true,
  "status": "running",
  "message": "Agent resumed from pause"
}
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-16 | 1.0 | Initial UAT script creation |

---

**END OF UAT SCRIPT**
