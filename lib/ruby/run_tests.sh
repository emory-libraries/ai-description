#!/bin/bash

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

set -e

echo "🔧 Ruby Test Suite Runner"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if bundle is installed
if ! command -v bundle &> /dev/null; then
    echo -e "${RED}❌ Bundle is not installed. Please install Ruby and Bundler first.${NC}"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
bundle install

echo ""
echo "🧪 Running tests..."
echo ""

# Run different test suites based on arguments
case "${1:-all}" in
    unit)
        echo "Running unit tests only..."
        bundle exec rake spec:unit
        ;;
    integration)
        echo "Running integration tests only..."
        bundle exec rake spec:integration
        ;;
    coverage)
        echo "Running tests with coverage..."
        bundle exec rake spec:coverage
        ;;
    rubocop)
        echo "Running RuboCop linter..."
        bundle exec rake rubocop
        ;;
    ci)
        echo "Running full CI suite..."
        bundle exec rake ci
        ;;
    all|*)
        echo "Running all tests..."
        bundle exec rake spec
        echo ""
        echo "🔍 Running RuboCop..."
        bundle exec rake rubocop
        ;;
esac

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi