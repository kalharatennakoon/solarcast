#!/usr/bin/env bash
# Loads a folder of CSV summaries into a namespace as the Secret that the
# backend mounts at /data. Safe to re-run: it creates the Secret or updates it.
#
#   ./scripts/k8s-load-data.sh solarcast-dev  backend/sample_data
#   ./scripts/k8s-load-data.sh solarcast-prod backend/data
#
# The data goes straight from your disk into the cluster. It is never
# written to a file in the repository.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <namespace> <folder containing *-summary.csv files>" >&2
  exit 1
fi

namespace="$1"
folder="$2"

shopt -s nullglob
files=("$folder"/*-summary.csv)
if [ "${#files[@]}" -eq 0 ]; then
  echo "No *-summary.csv files found in $folder" >&2
  exit 1
fi

from_file_args=()
for file in "${files[@]}"; do
  from_file_args+=("--from-file=$file")
done

# "create --dry-run -o yaml | apply" is the usual way to create-or-update.
kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic solarcast-data --namespace "$namespace" \
  "${from_file_args[@]}" --dry-run=client -o yaml | kubectl apply -f -

echo "Loaded ${#files[@]} file(s) from $folder into $namespace."

# A running backend picks the new files up on a restart.
if kubectl get deployment backend --namespace "$namespace" >/dev/null 2>&1; then
  kubectl rollout restart deployment/backend --namespace "$namespace"
  kubectl rollout status deployment/backend --namespace "$namespace" --timeout=120s
fi
