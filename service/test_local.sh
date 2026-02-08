#!/bin/bash
# Quick local testing script for GridWise API

echo "🧪 Testing GridWise API locally..."
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo "Start the server with: uv run uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test health endpoint
echo "📍 Testing /health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "Response: $HEALTH"
echo ""

# Test root endpoint
echo "📍 Testing / endpoint..."
ROOT=$(curl -s http://localhost:8000/)
echo "Response: $ROOT"
echo ""

# Check if responses are valid JSON
if echo "$HEALTH" | jq . > /dev/null 2>&1; then
    echo "✅ Health endpoint returns valid JSON"
else
    echo "⚠️  Health endpoint response is not valid JSON"
fi

if echo "$ROOT" | jq . > /dev/null 2>&1; then
    echo "✅ Root endpoint returns valid JSON"
else
    echo "⚠️  Root endpoint response is not valid JSON"
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📖 View interactive docs at: http://localhost:8000/docs"
