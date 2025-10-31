#!/bin/bash
# Terminate old DocumentIngestionWorkflow instances from Temporal

set -e

echo "🔍 Finding old DocumentIngestionWorkflow instances..."

# Use temporal CLI to list and terminate workflows
# Workflow ID pattern: ingestion-*
docker exec vdb-temporal temporal workflow list \
    --namespace default \
    --query "WorkflowType='DocumentIngestionWorkflow'" \
    --fields long \
    --limit 100 || echo "No workflows found or temporal CLI not available"

echo ""
echo "To terminate a specific workflow, run:"
echo "  docker exec vdb-temporal temporal workflow terminate \\"
echo "    --workflow-id <WORKFLOW_ID> \\"
echo "    --namespace default \\"
echo "    --reason 'DocumentIngestionWorkflow removed from codebase'"
echo ""

# Terminate the specific workflow from the logs
WORKFLOW_ID="ingestion-667ae7a9-93e2-4eee-b8a1-bdec98a33de3"
echo "🛑 Terminating known old workflow: $WORKFLOW_ID"

docker exec vdb-temporal temporal workflow terminate \
    --workflow-id "$WORKFLOW_ID" \
    --namespace default \
    --reason "DocumentIngestionWorkflow removed from codebase" 2>/dev/null \
    && echo "✅ Terminated workflow $WORKFLOW_ID" \
    || echo "⚠️  Workflow may already be terminated or not found"

echo ""
echo "✅ Done! Old workflows terminated."
echo ""
echo "Alternative: Clean Temporal database completely with:"
echo "  docker-compose down"
echo "  docker volume rm stackai_temporal-data"
echo "  docker-compose up -d"
