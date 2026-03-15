#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/docs/developer_loop/_template"

usage() {
  cat <<'EOF'
Usage:
  scripts/bootstrap_developer_loop.sh <proposal_id> [layer] [kind]

Arguments:
  proposal_id   Required. Example: prop_l2_softmax_tile_fusion_v1
  layer         Optional. Default: layer2
  kind          Optional. Default: architecture

This creates:
  docs/developer_loop/<proposal_id>/

from the template workspace and stamps the proposal id, timestamp, layer, and
kind into the initial files.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage >&2
  exit 2
fi

proposal_id="$1"
layer="${2:-layer2}"
kind="${3:-architecture}"
created_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
target_dir="$REPO_ROOT/docs/developer_loop/$proposal_id"

case "$proposal_id" in
  prop_*)
    ;;
  *)
    echo "ERROR: proposal_id should start with 'prop_'" >&2
    exit 2
    ;;
esac

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "ERROR: template directory not found: $TEMPLATE_DIR" >&2
  exit 2
fi

if [[ -e "$target_dir" ]]; then
  echo "ERROR: target already exists: $target_dir" >&2
  exit 2
fi

mkdir -p "$target_dir"
cp -R "$TEMPLATE_DIR"/. "$target_dir"/

python3 - <<'PY' "$target_dir" "$proposal_id" "$layer" "$kind" "$created_utc"
import json
import sys
from pathlib import Path

target_dir = Path(sys.argv[1])
proposal_id = sys.argv[2]
layer = sys.argv[3]
kind = sys.argv[4]
created_utc = sys.argv[5]

proposal_path = target_dir / "proposal.json"
proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
proposal["proposal_id"] = proposal_id
proposal["created_utc"] = created_utc
proposal["layer"] = layer
proposal["kind"] = kind
proposal_path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")

eval_requests_path = target_dir / "evaluation_requests.json"
eval_requests = json.loads(eval_requests_path.read_text(encoding="utf-8"))
eval_requests["proposal_id"] = proposal_id
eval_requests_path.write_text(json.dumps(eval_requests, indent=2) + "\n", encoding="utf-8")

promotion_decision_path = target_dir / "promotion_decision.json"
promotion_decision = json.loads(promotion_decision_path.read_text(encoding="utf-8"))
promotion_decision["proposal_id"] = proposal_id
promotion_decision_path.write_text(
    json.dumps(promotion_decision, indent=2) + "\n", encoding="utf-8"
)

promotion_result_path = target_dir / "promotion_result.json"
promotion_result = json.loads(promotion_result_path.read_text(encoding="utf-8"))
promotion_result["proposal_id"] = proposal_id
promotion_result["merged_utc"] = created_utc
promotion_result_path.write_text(
    json.dumps(promotion_result, indent=2) + "\n", encoding="utf-8"
)
PY

sed -i \
  -e "s/prop_example_v1/$proposal_id/g" \
  -e "s/2026-03-15T00:00:00Z/$created_utc/g" \
  "$target_dir"/design_brief.md \
  "$target_dir"/implementation_summary.md \
  "$target_dir"/analysis_report.md

echo "Created developer-loop workspace:"
echo "  $target_dir"
echo
echo "Next steps:"
echo "  1. git switch -c dev/$proposal_id"
echo "  2. edit $target_dir/design_brief.md"
echo "  3. edit $target_dir/proposal.json"
