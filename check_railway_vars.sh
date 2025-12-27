#!/bin/bash

# Load secrets from .env or environment
RAILWAY_TOKEN=${RAILWAY_TOKEN:-$(grep RAILWAY_TOKEN .env 2>/dev/null | cut -d'=' -f2)}
RAILWAY_PROJECT_ID=${RAILWAY_PROJECT_ID:-$(grep RAILWAY_PROJECT_ID .env 2>/dev/null | cut -d'=' -f2)}

if [ -z "$RAILWAY_TOKEN" ] || [ -z "$RAILWAY_PROJECT_ID" ]; then
  echo "Error: RAILWAY_TOKEN or RAILWAY_PROJECT_ID not set"
  echo "Please set as environment variables or add to .env"
  exit 1
fi

echo "Fetching Railway project metadata..."
META=$(curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"query { project(id: \\\"$RAILWAY_PROJECT_ID\\\") { name environments { edges { node { id name } } } services { edges { node { id name } } } } }\"}")

echo "Project Info:"
echo "$META" | jq .

ENV_ID=$(echo "$META" | jq -r '.data.project.environments.edges[0].node.id')
ENV_NAME=$(echo "$META" | jq -r '.data.project.environments.edges[0].node.name')
SERVICE_ID=$(echo "$META" | jq -r '.data.project.services.edges[0].node.id')
SERVICE_NAME=$(echo "$META" | jq -r '.data.project.services.edges[0].node.name')

echo ""
echo "Environment: $ENV_NAME ($ENV_ID)"
echo "Service: $SERVICE_NAME ($SERVICE_ID)"
echo ""
echo "Fetching current variables..."

VARS=$(curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"query { variables(environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\", projectId: \\\"$RAILWAY_PROJECT_ID\\\") { edges { node { name value } } } }\"}")

echo "Current Variables:"
echo "$VARS" | jq '.data.variables.edges[] | .node | {name: .name, value: (.value | if length > 20 then .[:20] + "..." else . end)}'
