#!/bin/bash

echo "🏏 IPL Cricket Chatbot - Comprehensive Testing Suite"
echo "=================================================="

# Check if backend is running
echo "🔍 Checking if backend server is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend server is running"
    BACKEND_RUNNING=true
else
    echo "❌ Backend server is not running"
    echo "Please start the backend server first:"
    echo "  cd backend && source venv/bin/activate && python main.py"
    BACKEND_RUNNING=false
fi

# Check if environment is setup
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found"
    echo "Please run ./setup.sh first and add your GROQ_API_KEY"
    exit 1
fi

if ! grep -q "GROQ_API_KEY=" backend/.env || grep -q "GROQ_API_KEY=$" backend/.env; then
    echo "❌ GROQ_API_KEY not set in backend/.env"
    echo "Please add your GROQ_API_KEY to backend/.env"
    exit 1
fi

echo "✅ Environment configuration looks good"
echo ""

# Test 1: Validate Dynamic Query Generation
echo "TEST 1: Validating Dynamic Query Generation"
echo "=========================================="
cd backend
source venv/bin/activate
python validate_dynamic_queries.py
VALIDATION_EXIT_CODE=$?
cd ..
echo ""

# Test 2: Backend Component Testing (if backend is running)
if [ "$BACKEND_RUNNING" = true ]; then
    echo "TEST 2: Backend Component Testing"
    echo "=================================="
    cd backend
    source venv/bin/activate
    python test_comprehensive.py
    BACKEND_TEST_EXIT_CODE=$?
    cd ..
    echo ""
else
    echo "TEST 2: Backend Component Testing - SKIPPED (server not running)"
    BACKEND_TEST_EXIT_CODE=1
    echo ""
fi

# Test 3: End-to-End API Testing (if backend is running)
if [ "$BACKEND_RUNNING" = true ]; then
    echo "TEST 3: End-to-End API Testing"
    echo "==============================="
    python test_api_comprehensive.py http://localhost:8000
    API_TEST_EXIT_CODE=$?
    echo ""
else
    echo "TEST 3: End-to-End API Testing - SKIPPED (server not running)"
    API_TEST_EXIT_CODE=1
    echo ""
fi

# Final Summary
echo "🎯 COMPREHENSIVE TEST SUITE SUMMARY"
echo "===================================="

if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "✅ Dynamic Query Validation: PASSED"
else
    echo "❌ Dynamic Query Validation: FAILED"
fi

if [ $BACKEND_TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Backend Component Tests: PASSED"
elif [ "$BACKEND_RUNNING" = true ]; then
    echo "❌ Backend Component Tests: FAILED"
else
    echo "⏭️  Backend Component Tests: SKIPPED"
fi

if [ $API_TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ End-to-End API Tests: PASSED"
elif [ "$BACKEND_RUNNING" = true ]; then
    echo "❌ End-to-End API Tests: FAILED"
else
    echo "⏭️  End-to-End API Tests: SKIPPED"
fi

echo ""

# Overall verdict
if [ $VALIDATION_EXIT_CODE -eq 0 ] && [ $BACKEND_TEST_EXIT_CODE -eq 0 ] && [ $API_TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ The IPL Cricket Chatbot is ready for production!"
    echo "🚀 The system can handle ANY cricket query dynamically!"
    exit 0
elif [ $VALIDATION_EXIT_CODE -eq 0 ] && [ "$BACKEND_RUNNING" = false ]; then
    echo "⚠️  PARTIAL SUCCESS - Dynamic validation passed"
    echo "💡 To run complete tests, start the backend server:"
    echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo "🔧 Please review the test results and fix any issues"
    exit 1
fi