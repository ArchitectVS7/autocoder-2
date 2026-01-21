"""
Tests for Phase 5 - Task 5.1: Playwright Test Generation

This test suite validates the Playwright test generation functionality,
ensuring that user flows are correctly converted into executable Playwright tests.
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil

from ux_eval.playwright_generator import (
    PlaywrightTestGenerator,
    UserFlow,
    TestStep,
    create_default_onboarding_flow,
    create_default_dashboard_flow,
    create_default_settings_flow
)


class TestTestStep:
    """Test the TestStep dataclass."""

    def test_create_test_step(self):
        """Test creating a TestStep instance."""
        step = TestStep(
            action="navigate",
            description="Go to homepage",
            value="https://example.com"
        )

        assert step.action == "navigate"
        assert step.description == "Go to homepage"
        assert step.value == "https://example.com"
        assert step.selector is None
        assert step.timeout == 5000

    def test_test_step_to_dict(self):
        """Test converting TestStep to dictionary."""
        step = TestStep(
            action="click",
            description="Click button",
            selector="#submit-btn"
        )

        step_dict = step.to_dict()

        assert step_dict["action"] == "click"
        assert step_dict["description"] == "Click button"
        assert step_dict["selector"] == "#submit-btn"
        assert "value" in step_dict
        assert "timeout" in step_dict

    def test_test_step_from_dict(self):
        """Test creating TestStep from dictionary."""
        data = {
            "action": "fill",
            "description": "Enter email",
            "selector": "input[name='email']",
            "value": "test@example.com",
            "timeout": 5000,
            "screenshot_name": None
        }

        step = TestStep.from_dict(data)

        assert step.action == "fill"
        assert step.description == "Enter email"
        assert step.selector == "input[name='email']"
        assert step.value == "test@example.com"

    def test_screenshot_step(self):
        """Test creating a screenshot step."""
        step = TestStep(
            action="screenshot",
            description="Capture page",
            screenshot_name="homepage"
        )

        assert step.action == "screenshot"
        assert step.screenshot_name == "homepage"


class TestUserFlow:
    """Test the UserFlow dataclass."""

    def test_create_user_flow(self):
        """Test creating a UserFlow instance."""
        flow = UserFlow(
            flow_id="test-flow",
            name="Test Flow",
            description="A test user flow"
        )

        assert flow.flow_id == "test-flow"
        assert flow.name == "Test Flow"
        assert flow.description == "A test user flow"
        assert len(flow.steps) == 0
        assert flow.viewport == {"width": 1920, "height": 1080}
        assert flow.base_url == "http://localhost:3000"

    def test_add_step_to_flow(self):
        """Test adding steps to a user flow."""
        flow = UserFlow(
            flow_id="test-flow",
            name="Test Flow",
            description="A test user flow"
        )

        step1 = TestStep(action="navigate", description="Go to page", value="/home")
        step2 = TestStep(action="click", description="Click button", selector="#btn")

        flow.add_step(step1)
        flow.add_step(step2)

        assert len(flow.steps) == 2
        assert flow.steps[0].action == "navigate"
        assert flow.steps[1].action == "click"

    def test_user_flow_to_dict(self):
        """Test converting UserFlow to dictionary."""
        flow = UserFlow(
            flow_id="test-flow",
            name="Test Flow",
            description="A test user flow"
        )

        step = TestStep(action="navigate", description="Go to page", value="/home")
        flow.add_step(step)

        flow_dict = flow.to_dict()

        assert flow_dict["flow_id"] == "test-flow"
        assert flow_dict["name"] == "Test Flow"
        assert len(flow_dict["steps"]) == 1
        assert flow_dict["viewport"]["width"] == 1920

    def test_user_flow_from_dict(self):
        """Test creating UserFlow from dictionary."""
        data = {
            "flow_id": "test-flow",
            "name": "Test Flow",
            "description": "A test user flow",
            "steps": [
                {
                    "action": "navigate",
                    "description": "Go to page",
                    "selector": None,
                    "value": "/home",
                    "timeout": 5000,
                    "screenshot_name": None
                }
            ],
            "viewport": {"width": 1280, "height": 720},
            "base_url": "http://localhost:8080"
        }

        flow = UserFlow.from_dict(data)

        assert flow.flow_id == "test-flow"
        assert flow.name == "Test Flow"
        assert len(flow.steps) == 1
        assert flow.viewport["width"] == 1280
        assert flow.base_url == "http://localhost:8080"

    def test_custom_viewport(self):
        """Test creating flow with custom viewport."""
        flow = UserFlow(
            flow_id="mobile-flow",
            name="Mobile Flow",
            description="Mobile test",
            viewport={"width": 375, "height": 667}
        )

        assert flow.viewport["width"] == 375
        assert flow.viewport["height"] == 667


class TestPlaywrightTestGenerator:
    """Test the PlaywrightTestGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test output."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create a PlaywrightTestGenerator instance."""
        return PlaywrightTestGenerator(output_dir=temp_dir)

    @pytest.fixture
    def simple_flow(self):
        """Create a simple test flow."""
        flow = UserFlow(
            flow_id="simple-flow",
            name="Simple Flow",
            description="A simple test flow"
        )

        flow.add_step(TestStep(
            action="navigate",
            description="Go to homepage",
            value="http://localhost:3000"
        ))

        flow.add_step(TestStep(
            action="screenshot",
            description="Capture homepage",
            screenshot_name="homepage"
        ))

        flow.add_step(TestStep(
            action="click",
            description="Click button",
            selector="#start-btn"
        ))

        return flow

    def test_generator_initialization(self, temp_dir):
        """Test initializing PlaywrightTestGenerator."""
        generator = PlaywrightTestGenerator(output_dir=temp_dir)

        assert generator.output_dir == temp_dir
        assert temp_dir.exists()

    def test_generate_test_code(self, generator, simple_flow):
        """Test generating Playwright test code."""
        test_code = generator.generate_test_code(simple_flow)

        assert "def test_simple_flow(page: Page)" in test_code
        assert "Simple Flow" in test_code
        assert "page.goto" in test_code
        assert "page.screenshot" in test_code
        assert "page.click" in test_code
        assert "#start-btn" in test_code

    def test_generate_header(self, generator, simple_flow):
        """Test generating test file header."""
        header = generator._generate_header(simple_flow)

        assert "from playwright.sync_api import Page, expect" in header
        assert "from pathlib import Path" in header
        assert "Simple Flow" in header

    def test_generate_navigate_step(self, generator):
        """Test generating navigate action code."""
        step = TestStep(
            action="navigate",
            description="Go to page",
            value="http://localhost:3000"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.goto("http://localhost:3000")' in code

    def test_generate_click_step(self, generator):
        """Test generating click action code."""
        step = TestStep(
            action="click",
            description="Click button",
            selector="button#submit"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.click("button#submit")' in code

    def test_generate_fill_step(self, generator):
        """Test generating fill action code."""
        step = TestStep(
            action="fill",
            description="Enter text",
            selector="input[name='email']",
            value="test@example.com"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.fill("input[name=\'email\']", "test@example.com")' in code

    def test_generate_screenshot_step(self, generator):
        """Test generating screenshot action code."""
        step = TestStep(
            action="screenshot",
            description="Capture page",
            screenshot_name="page_screenshot"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.screenshot(path=screenshots_dir / "page_screenshot.png"' in code
        assert "full_page=True" in code

    def test_generate_assert_text_step(self, generator):
        """Test generating assert_text action code."""
        step = TestStep(
            action="assert_text",
            description="Verify text",
            selector="h1",
            value="Welcome"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'expect(page.locator("h1")).to_contain_text("Welcome")' in code

    def test_generate_assert_visible_step(self, generator):
        """Test generating assert_visible action code."""
        step = TestStep(
            action="assert_visible",
            description="Verify element visible",
            selector="#success-message"
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'expect(page.locator("#success-message")).to_be_visible()' in code

    def test_generate_wait_with_selector_step(self, generator):
        """Test generating wait action with selector."""
        step = TestStep(
            action="wait",
            description="Wait for element",
            selector="#loading-complete",
            timeout=10000
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.wait_for_selector("#loading-complete", timeout=10000)' in code

    def test_generate_wait_without_selector_step(self, generator):
        """Test generating wait action without selector (timeout only)."""
        step = TestStep(
            action="wait",
            description="Wait 2 seconds",
            timeout=2000
        )

        code = generator._generate_step_code(step, "test-flow")

        assert 'page.wait_for_timeout(2000)' in code

    def test_save_test(self, generator, simple_flow):
        """Test saving generated test to file."""
        test_file = generator.save_test(simple_flow)

        assert test_file.exists()
        assert test_file.name == "test_simple_flow.py"

        content = test_file.read_text()
        assert "def test_simple_flow(page: Page)" in content

    def test_save_flow_definition(self, generator, simple_flow):
        """Test saving flow definition as JSON."""
        json_file = generator.save_flow_definition(simple_flow)

        assert json_file.exists()
        assert json_file.name == "simple-flow.json"

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert data["flow_id"] == "simple-flow"
        assert data["name"] == "Simple Flow"
        assert len(data["steps"]) == 3

    def test_load_flow_definition(self, generator, simple_flow):
        """Test loading flow definition from JSON."""
        # First save it
        generator.save_flow_definition(simple_flow)

        # Then load it
        loaded_flow = generator.load_flow_definition("simple-flow")

        assert loaded_flow.flow_id == simple_flow.flow_id
        assert loaded_flow.name == simple_flow.name
        assert len(loaded_flow.steps) == len(simple_flow.steps)

    def test_generate_all_tests(self, generator, simple_flow):
        """Test generating tests for multiple flows."""
        flow1 = simple_flow
        flow2 = UserFlow(
            flow_id="another-flow",
            name="Another Flow",
            description="Another test flow"
        )
        flow2.add_step(TestStep(action="navigate", description="Go", value="/"))

        test_files = generator.generate_all_tests([flow1, flow2])

        assert len(test_files) == 2
        assert all(f.exists() for f in test_files)

        # Check that JSON files were also created
        json_file1 = generator.output_dir / "simple-flow.json"
        json_file2 = generator.output_dir / "another-flow.json"
        assert json_file1.exists()
        assert json_file2.exists()

    def test_test_function_has_viewport_setup(self, generator, simple_flow):
        """Test that generated test includes viewport setup."""
        test_code = generator.generate_test_code(simple_flow)

        assert "page.set_viewport_size" in test_code
        assert '"width": 1920' in test_code
        assert '"height": 1080' in test_code

    def test_test_function_creates_screenshots_dir(self, generator, simple_flow):
        """Test that generated test creates screenshots directory."""
        test_code = generator.generate_test_code(simple_flow)

        assert 'screenshots_dir = Path("screenshots/simple-flow")' in test_code
        assert "screenshots_dir.mkdir(parents=True, exist_ok=True)" in test_code

    def test_step_comments_in_generated_code(self, generator, simple_flow):
        """Test that generated code includes descriptive comments."""
        test_code = generator.generate_test_code(simple_flow)

        assert "# Step 1: Go to homepage" in test_code
        assert "# Step 2: Capture homepage" in test_code
        assert "# Step 3: Click button" in test_code


class TestDefaultFlows:
    """Test the default flow creation functions."""

    def test_create_default_onboarding_flow(self):
        """Test creating default onboarding flow."""
        flow = create_default_onboarding_flow()

        assert flow.flow_id == "onboarding"
        assert flow.name == "User Onboarding Flow"
        assert len(flow.steps) > 0

        # Check for key steps
        step_actions = [step.action for step in flow.steps]
        assert "navigate" in step_actions
        assert "screenshot" in step_actions
        assert "click" in step_actions
        assert "fill" in step_actions
        assert "assert_visible" in step_actions

    def test_create_default_dashboard_flow(self):
        """Test creating default dashboard flow."""
        flow = create_default_dashboard_flow()

        assert flow.flow_id == "dashboard-navigation"
        assert flow.name == "Dashboard Navigation Flow"
        assert len(flow.steps) > 0

        # Check for navigation steps
        step_actions = [step.action for step in flow.steps]
        assert "navigate" in step_actions
        assert "click" in step_actions
        assert "screenshot" in step_actions

    def test_create_default_settings_flow(self):
        """Test creating default settings flow."""
        flow = create_default_settings_flow()

        assert flow.flow_id == "settings"
        assert flow.name == "Settings Configuration Flow"
        assert len(flow.steps) > 0

        # Check for settings-specific steps
        step_actions = [step.action for step in flow.steps]
        assert "navigate" in step_actions
        assert "fill" in step_actions
        assert "select" in step_actions
        assert "screenshot" in step_actions

    def test_onboarding_flow_has_screenshots(self):
        """Test that onboarding flow includes screenshots."""
        flow = create_default_onboarding_flow()

        screenshot_steps = [s for s in flow.steps if s.action == "screenshot"]
        assert len(screenshot_steps) >= 3  # Landing, signup, dashboard

    def test_flows_use_correct_base_url(self):
        """Test that default flows use correct base URL."""
        flows = [
            create_default_onboarding_flow(),
            create_default_dashboard_flow(),
            create_default_settings_flow()
        ]

        for flow in flows:
            assert flow.base_url == "http://localhost:3000"

    def test_flows_use_default_viewport(self):
        """Test that default flows use desktop viewport."""
        flows = [
            create_default_onboarding_flow(),
            create_default_dashboard_flow(),
            create_default_settings_flow()
        ]

        for flow in flows:
            assert flow.viewport == {"width": 1920, "height": 1080}


class TestGeneratedTestExecutability:
    """Test that generated tests are valid Python code."""

    @pytest.fixture
    def generator(self):
        """Create a PlaywrightTestGenerator instance with temp dir."""
        temp_path = Path(tempfile.mkdtemp())
        yield PlaywrightTestGenerator(output_dir=temp_path)
        shutil.rmtree(temp_path)

    def test_generated_code_is_valid_python(self, generator):
        """Test that generated code is syntactically valid Python."""
        flow = create_default_onboarding_flow()
        test_code = generator.generate_test_code(flow)

        # Try to compile the code (will raise SyntaxError if invalid)
        try:
            compile(test_code, '<string>', 'exec')
            valid = True
        except SyntaxError:
            valid = False

        assert valid, "Generated code should be valid Python"

    def test_generated_file_has_correct_extension(self, generator):
        """Test that generated test file has .py extension."""
        flow = create_default_onboarding_flow()
        test_file = generator.save_test(flow)

        assert test_file.suffix == ".py"

    def test_generated_file_is_readable(self, generator):
        """Test that generated test file can be read."""
        flow = create_default_onboarding_flow()
        test_file = generator.save_test(flow)

        content = test_file.read_text()
        assert len(content) > 0
        assert "def test_" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
