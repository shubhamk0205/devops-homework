#!/usr/bin/env bash
# Creates the lab namespace and the runtime secrets the broken scenarios need.
# The lab backends use the real HelpDesk PostgreSQL in the "helpdesk" namespace.
set -euo pipefail
kubectl create namespace helpdesk-lab --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret docker-registry ghcr-pull -n helpdesk-lab \
  --docker-server=ghcr.io --docker-username=shubhamk0205 --docker-password="$(gh auth token)" \
  --dry-run=client -o yaml | kubectl apply -f -
# copy the DB secret from the app namespace (value never printed)
kubectl get secret helpdesk-db -n helpdesk -o json \
  | jq 'del(.metadata.namespace,.metadata.uid,.metadata.resourceVersion,.metadata.creationTimestamp,.metadata.ownerReferences,.metadata.annotations)' \
  | kubectl apply -n helpdesk-lab -f -
