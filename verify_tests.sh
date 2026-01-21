#!/bin/bash
#
# Test Verification Script for FEATURE_TESTING_MATRIX.md
# Run this to verify all tests marked "written" and identify missing tests
#

set -e

echo "========================================="
echo "Test Verification Script"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if pytest is installed
echo "Step 1: Checking environment..."
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo -e "${RED}✗ pytest not installed${NC}"
    echo "  Install with: pip install -r requirements.txt"
    exit 1
fi
echo -e "${GREEN}✓ pytest installed${NC}"
echo ""

# Step 2: Run Phase 1 tests
echo "Step 2: Running Phase 1 tests..."
echo "========================================="
python3 -m pytest tests/test_phase1_integration.py -v --tb=short || true
echo ""

# Step 3: Run Phase 2 tests
echo "Step 3: Running Phase 2 tests..."
echo "========================================="
python3 -m pytest tests/test_phase2_integration.py -v --tb=short || true
echo ""

# Step 4: Check for specific tests marked "written"
echo "Step 4: Verifying tests marked 'written'..."
echo "========================================="

echo "Checking for migration test (Task 1.1.5)..."
if grep -q "def test.*migrat" tests/test_phase1_integration.py; then
    echo -e "${GREEN}✓ Migration test found${NC}"
else
    echo -e "${YELLOW}⚠ Migration test NOT found - needs to be written${NC}"
fi

echo "Checking for assumption prompts test (Task 1.8.6)..."
if grep -q "ASSUMPTION_DOCUMENTATION_PROMPT\|ASSUMPTION_REVIEW_PROMPT" tests/test_phase1_integration.py; then
    echo -e "${GREEN}✓ Assumption prompts test found${NC}"
else
    echo -e "${YELLOW}⚠ Assumption prompts test NOT found - needs to be written${NC}"
fi

echo "Checking for recommendations test (Task 2.3.6)..."
if grep -q "def test.*recommend" tests/test_phase2_integration.py; then
    echo -e "${GREEN}✓ Recommendations test found${NC}"
else
    echo -e "${YELLOW}⚠ Recommendations test NOT found - needs to be written${NC}"
fi

echo "Checking for decision framework test (Task 2.3.7)..."
if grep -q "worth_it\|decision" tests/test_phase2_integration.py; then
    echo -e "${GREEN}✓ Decision framework test found${NC}"
else
    echo -e "${YELLOW}⚠ Decision framework test NOT found - needs to be written${NC}"
fi

echo ""

# Step 5: Check for missing tests
echo "Step 5: Checking for missing tests (marked N/A but should exist)..."
echo "========================================="

MISSING_TESTS=0

# Task 1.2.3 - Category-based dependency detection
if ! grep -q "test.*category.*depend" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.2.3: Category-based dependency detection test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.2.5 - Batch processing
if ! grep -q "test.*detect_all_dependencies\|test.*batch.*depend" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.2.5: Batch processing test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.2.6 - Dependency graph
if ! grep -q "test.*graph\|test.*visualiz.*depend" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.2.6: Dependency graph generation test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.3.2 - get_dependent_features
if ! grep -q "test.*get_dependent_features\|test.*recursive.*depend" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.3.2: get_dependent_features test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.3.4 - Impact report formatting
if ! grep -q "test.*impact.*format\|test.*tree.*visualiz" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.3.4: Impact report formatting test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.4.3 - TECH_PREREQUISITE
if ! grep -q "TECH_PREREQUISITE" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.4.3: TECH_PREREQUISITE blocker test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.4.5 - LEGITIMATE_DEFERRAL
if ! grep -q "LEGITIMATE_DEFERRAL" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.4.5: LEGITIMATE_DEFERRAL blocker test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 1.8.7 - assumptions CLI
if ! grep -q "test.*assumptions.*cli\|TestAssumptionsCLI" tests/test_phase1_integration.py; then
    echo -e "${YELLOW}⚠ Task 1.8.7: Assumptions CLI test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 2.2.4 - ETA calculation
if ! grep -q "test.*eta\|test.*estimated.*time" tests/test_phase2_integration.py; then
    echo -e "${YELLOW}⚠ Task 2.2.4: ETA calculation test missing${NC}"
    ((MISSING_TESTS++))
fi

# Task 2.4.6 - Benchmark CLI
if ! grep -q "test.*benchmark.*cli\|TestBenchmarkCLI" tests/test_phase2_integration.py; then
    echo -e "${YELLOW}⚠ Task 2.4.6: Benchmark CLI test missing${NC}"
    ((MISSING_TESTS++))
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo -e "Missing tests that should be written: ${YELLOW}${MISSING_TESTS}${NC}"
echo ""
echo "See TEST_STATUS_ANALYSIS.md for detailed recommendations"
echo ""
