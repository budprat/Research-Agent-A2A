#!/bin/bash
# ABOUTME: Test runner script for A2A MCP Framework
# ABOUTME: Provides convenient commands for running tests with various options

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Default values
COVERAGE=false
VERBOSE=false
TEST_TYPE="all"
MARKERS=""
FAILFAST=false
COVERAGE_MIN=30

# Help message
show_help() {
    cat << EOF
Usage: ./run_tests.sh [OPTIONS] [TEST_PATH]

Run tests for A2A MCP Framework with various options.

OPTIONS:
    -h, --help              Show this help message
    -c, --coverage          Run with coverage report (HTML + terminal)
    -v, --verbose           Verbose output with detailed test information
    -u, --unit              Run only unit tests
    -i, --integration       Run only integration tests
    -e, --e2e               Run only end-to-end tests
    -f, --failfast          Stop on first failure
    -s, --slow              Include slow tests (excluded by default)
    -m, --min-coverage NUM  Minimum coverage percentage (default: 30)
    -k, --keyword EXPR      Run tests matching keyword expression
    --markers               Show available test markers

EXAMPLES:
    ./run_tests.sh                          # Run all tests (excluding slow)
    ./run_tests.sh -c                       # Run with coverage report
    ./run_tests.sh -u -c                    # Run unit tests with coverage
    ./run_tests.sh -v -f                    # Verbose output, stop on first fail
    ./run_tests.sh tests/unit/test_a2a*    # Run specific test file
    ./run_tests.sh -k "config"              # Run tests matching 'config'
    ./run_tests.sh -i -c --min-coverage 50  # Integration tests, 50% coverage required

TEST MARKERS:
    unit            - Unit tests (individual components)
    integration     - Integration tests (component interactions)
    e2e             - End-to-end tests (complete workflows)
    slow            - Slow tests (excluded by default)
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -u|--unit)
            TEST_TYPE="unit"
            MARKERS="-m unit"
            shift
            ;;
        -i|--integration)
            TEST_TYPE="integration"
            MARKERS="-m integration"
            shift
            ;;
        -e|--e2e)
            TEST_TYPE="e2e"
            MARKERS="-m e2e"
            shift
            ;;
        -f|--failfast)
            FAILFAST=true
            shift
            ;;
        -s|--slow)
            INCLUDE_SLOW=true
            shift
            ;;
        -m|--min-coverage)
            COVERAGE_MIN="$2"
            shift 2
            ;;
        -k|--keyword)
            KEYWORD="-k $2"
            shift 2
            ;;
        --markers)
            python -m pytest --markers
            exit 0
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d ".venv" ]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source .venv/bin/activate
    else
        echo -e "${RED}Error: No virtual environment found${NC}"
        echo "Please run ./start.sh first to set up the environment"
        exit 1
    fi
fi

# Install test dependencies if needed
echo -e "${YELLOW}Checking test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov pytest-mock 2>/dev/null || true

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add test path
if [ -n "$TEST_PATH" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_PATH"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Add keyword filter
if [ -n "$KEYWORD" ]; then
    PYTEST_CMD="$PYTEST_CMD $KEYWORD"
fi

# Exclude slow tests unless explicitly included
if [ "$INCLUDE_SLOW" != "true" ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add failfast flag
if [ "$FAILFAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/a2a_mcp --cov-report=html --cov-report=term-missing --cov-fail-under=$COVERAGE_MIN"
fi

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}A2A MCP Framework - Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Test Type: ${GREEN}$TEST_TYPE${NC}"
echo -e "Coverage:  ${GREEN}$COVERAGE${NC}"
echo -e "Verbose:   ${GREEN}$VERBOSE${NC}"
if [ "$COVERAGE" = true ]; then
    echo -e "Min Coverage: ${GREEN}${COVERAGE_MIN}%${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""

# Run tests
echo -e "${YELLOW}Running command:${NC} $PYTEST_CMD"
echo ""

eval $PYTEST_CMD
TEST_EXIT_CODE=$?

# Print results
echo ""
echo -e "${BLUE}========================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed successfully!${NC}"
else
    echo -e "${RED}✗ Tests failed!${NC}"
fi
echo -e "${BLUE}========================================${NC}"

# Show coverage report location if generated
if [ "$COVERAGE" = true ] && [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Coverage report generated:${NC}"
    echo -e "  HTML: ${YELLOW}htmlcov/index.html${NC}"
    echo -e "  Open with: ${YELLOW}open htmlcov/index.html${NC} (macOS)"
    echo -e "            ${YELLOW}xdg-open htmlcov/index.html${NC} (Linux)"
fi

exit $TEST_EXIT_CODE
