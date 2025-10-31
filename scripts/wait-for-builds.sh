#!/bin/bash
set -e

BUILD_IDS="$1"

echo "Waiting for builds to complete..."

while true; do
  STATUSES=$(gcloud builds list --limit=10 --format="csv[no-heading](id,status)" --filter="id:(${BUILD_IDS})" | sort)

  echo "Current build statuses:"
  echo "$STATUSES"

  # Check if all builds are done (no WORKING or QUEUED)
  if echo "$STATUSES" | grep -qE "WORKING|QUEUED"; then
    echo "Builds still in progress, waiting..."
    sleep 15
  else
    # Check if all succeeded
    FAILED=$(echo "$STATUSES" | grep -v SUCCESS | wc -l)
    if [ "$FAILED" -gt 0 ]; then
      echo "❌ Some builds failed!"
      exit 1
    else
      echo "✅ All builds completed successfully!"
      exit 0
    fi
  fi
done
