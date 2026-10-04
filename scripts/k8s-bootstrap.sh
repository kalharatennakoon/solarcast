#!/usr/bin/env bash
# Sets up SolarCast on a Kubernetes cluster from nothing: installs Argo CD,
# gives it access to the repository, loads the data and creates the dev and
# prod applications. Safe to re-run; every step creates or updates.
#
#   ./scripts/k8s-bootstrap.sh
#
# Needs: kubectl pointing at the target cluster (Docker Desktop's built-in
# Kubernetes is what this was written for).
set -euo pipefail

cd "$(dirname "$0")/.."

REPO_URL="https://github.com/kalharatennakoon/solarcast.git"
ARGOCD_NS="argocd"

step() { printf '\n==> %s\n' "$1"; }

# ── 0. Make sure we are talking to the intended cluster ─────────────────────
context="$(kubectl config current-context)"
echo "kubectl context: $context"
if [ "$context" != "docker-desktop" ] && [ "${BOOTSTRAP_ANY_CONTEXT:-}" != "yes" ]; then
  echo "This is not the docker-desktop context. To continue anyway, re-run with:" >&2
  echo "  BOOTSTRAP_ANY_CONTEXT=yes $0" >&2
  exit 1
fi

# ── 1. Install Argo CD and wait until it is running ─────────────────────────
step "Installing Argo CD"
kubectl apply -k deploy/argocd --server-side --force-conflicts
kubectl wait deployment --all --namespace "$ARGOCD_NS" --for=condition=Available --timeout=300s
kubectl rollout status statefulset/argocd-application-controller --namespace "$ARGOCD_NS" --timeout=300s

# ── 2. Repository access (only needed while the repository is private) ──────
step "Repository credentials"
if kubectl get secret repo-solarcast --namespace "$ARGOCD_NS" >/dev/null 2>&1; then
  echo "Already configured."
else
  token="${GITHUB_TOKEN:-}"
  if [ -z "$token" ]; then
    echo "Paste a GitHub token with read-only access to the repository contents,"
    echo "or just press Enter to skip if the repository is public."
    read -r -s -p "Token: " token
    echo
  fi
  if [ -n "$token" ]; then
    kubectl create secret generic repo-solarcast --namespace "$ARGOCD_NS" \
      --from-literal=type=git \
      --from-literal=url="$REPO_URL" \
      --from-literal=username=git \
      --from-literal=password="$token"
    kubectl label secret repo-solarcast --namespace "$ARGOCD_NS" \
      argocd.argoproj.io/secret-type=repository
  else
    echo "Skipped: Argo CD will read the repository anonymously."
  fi
fi

# ── 3. Data: dev gets the synthetic set, prod the real readings ─────────────
step "Loading data"
./scripts/k8s-load-data.sh solarcast-dev backend/sample_data
if ls backend/data/*-summary.csv >/dev/null 2>&1; then
  ./scripts/k8s-load-data.sh solarcast-prod backend/data
else
  echo "No private data in backend/data, so prod uses the sample data too."
  ./scripts/k8s-load-data.sh solarcast-prod backend/sample_data
fi

# ── 4. Hand both environments to Argo CD ────────────────────────────────────
step "Creating the Argo CD applications"
kubectl apply -f deploy/argocd/apps/

cat <<'NEXT'

Done. Argo CD now deploys both environments from Git.

  Argo CD UI     kubectl port-forward -n argocd svc/argocd-server 8443:443
                 https://localhost:8443   (user: admin)
  Password       kubectl get secret argocd-initial-admin-secret -n argocd \
                   -o jsonpath='{.data.password}' | base64 -d; echo
  Dev dashboard  kubectl port-forward -n solarcast-dev svc/frontend 8081:8080
  Prod dashboard kubectl port-forward -n solarcast-prod svc/frontend 8082:8080

Each dashboard needs "Train Model" clicked once after a fresh install.
NEXT
