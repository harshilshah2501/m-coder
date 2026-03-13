#!/bin/bash
# Test the semantic context API endpoint

echo "🧪 Testing /v1/semantic-context endpoint"
echo "=========================================="
echo ""

curl -X POST http://localhost:8081/v1/semantic-context \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main/java/com/mindarray/store/GroupConfigStore.java",
    "method_name": "getItemsByUserProfile",
    "task_description": "Add logging statement at the start of the method"
  }' | jq -r '.context' | head -80

echo ""
echo "=========================================="
echo "✅ Test complete!"

