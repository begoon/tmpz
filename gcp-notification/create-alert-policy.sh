#!/usr/bin/env bash
# Creates a log-based alert policy in GCP Monitoring that fires whenever
# gcp-message.ts logs a message starting with "slack: ", and routes the
# notification to an existing Slack notification channel
# (https://console.cloud.google.com/monitoring/alerting/notifications?project=iproov-chiro).
#
# Usage:
#   ./create-alert-policy.sh [slack-channel-display-name]
#
# Examples:
#   ./create-alert-policy.sh                  # uses default "#alerts-chiro"
#   ./create-alert-policy.sh "#alerts-other"
#
# Env overrides:
#   PROJECT_ID   (default: iproov-chiro)
#   LOG_NAME     (default: gcp-message — must match --log used by gcp-message.ts)
#   PREFIX       (default: "slack: ")
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-iproov-chiro}"
LOG_NAME="${LOG_NAME:-gcp-message}"
PREFIX="${PREFIX:-slack: }"
SLACK_CHANNEL_NAME="${1:-#alerts-chiro}"
POLICY_DISPLAY_NAME="gcp-message slack relay (${SLACK_CHANNEL_NAME})"

# --- Find the Slack notification channel by its display name -----------------
# Channel display names in GCP are stored without the leading "#", so match
# both forms. Matching is done here rather than via --filter, which gcloud
# applies unreliably for notification channels.
BARE_NAME="${SLACK_CHANNEL_NAME#\#}"
echo "Looking up Slack notification channel '${BARE_NAME}' in ${PROJECT_ID}..."
CHANNELS=$(gcloud beta monitoring channels list \
  --project="${PROJECT_ID}" \
  --format="csv[no-heading](type,displayName,name)")

CHANNEL_ID=$(awk -F, -v want="${BARE_NAME}" \
  '$1 == "slack" && ($2 == want || $2 == "#" want) { print $3; exit }' \
  <<< "${CHANNELS}")

if [[ -z "${CHANNEL_ID}" ]]; then
  echo "ERROR: no Slack notification channel named '${BARE_NAME}' found." >&2
  echo "Existing Slack channels in ${PROJECT_ID}:" >&2
  awk -F, '$1 == "slack" { printf "  %s  (%s)\n", $2, $3 }' <<< "${CHANNELS}" >&2
  echo "Create one at: https://console.cloud.google.com/monitoring/alerting/notifications?project=${PROJECT_ID}" >&2
  exit 1
fi
echo "Found channel: ${CHANNEL_ID}"

# --- Skip if a policy with this display name already exists ------------------
EXISTING=$(gcloud alpha monitoring policies list \
  --project="${PROJECT_ID}" \
  --filter="displayName=\"${POLICY_DISPLAY_NAME}\"" \
  --format="value(name)" | head -n1)
if [[ -n "${EXISTING}" ]]; then
  echo "Policy already exists: ${EXISTING}" >&2
  echo "Delete it first to recreate: gcloud alpha monitoring policies delete ${EXISTING} --project=${PROJECT_ID}" >&2
  exit 1
fi

# --- Build the policy ---------------------------------------------------------
# Log-based alert (conditionMatchedLog) matching jsonPayload.message prefix.
POLICY_FILE=$(mktemp)
trap 'rm -f "${POLICY_FILE}"' EXIT

cat > "${POLICY_FILE}" <<EOF
{
  "displayName": "${POLICY_DISPLAY_NAME}",
  "documentation": {
    "content": "Message from gcp-message.ts:\n\n\${log.extracted_label.message}",
    "mimeType": "text/markdown"
  },
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "gcp-message log entry with '${PREFIX}' prefix",
      "conditionMatchedLog": {
        "filter": "logName=\"projects/${PROJECT_ID}/logs/${LOG_NAME}\" AND jsonPayload.message=~\"^${PREFIX}\"",
        "labelExtractors": {
          "message": "EXTRACT(jsonPayload.message)"
        }
      }
    }
  ],
  "alertStrategy": {
    "notificationRateLimit": {
      "period": "300s"
    },
    "autoClose": "1800s"
  },
  "notificationChannels": ["${CHANNEL_ID}"],
  "enabled": true
}
EOF

echo "Creating alert policy '${POLICY_DISPLAY_NAME}'..."
gcloud alpha monitoring policies create \
  --project="${PROJECT_ID}" \
  --policy-from-file="${POLICY_FILE}"

echo
echo "Done. Test it with:"
echo "  bun run gcp-message.ts --project ${PROJECT_ID} \"${PREFIX}hello from gcp-message\""
