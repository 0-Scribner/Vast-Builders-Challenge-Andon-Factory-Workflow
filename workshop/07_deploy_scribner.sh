#!/usr/bin/env bash
# Deliverable 7: deploy Scribner to the existing team host at /app. No Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -z "${KUBECONFIG:-}" ]]; then
  # The workshop VM ships the kubeconfig under its canonical name or a team-prefixed alias.
  for candidate in /config/kubeconfig /config/*-k8s.yaml; do
    [[ -f "$candidate" ]] && { export KUBECONFIG="$candidate"; break; }
  done
fi
[[ -n "${KUBECONFIG:-}" && -f "$KUBECONFIG" ]] || { echo "no kubeconfig under /config" >&2; exit 1; }

mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
(( ${#TEAM_CONFIGS[@]} == 1 )) || { echo "expected exactly one /config/*.config" >&2; exit 1; }
set -a && source "${TEAM_CONFIGS[0]}" && set +a

: "${USERNAME:?USERNAME missing}"
: "${PASSWORD:?PASSWORD missing}"
: "${INGRESS_URL:?INGRESS_URL missing}"

NS="$USERNAME"
APP_NAME=scribner
APP_DIR=tools/scribner
APP_PORT=8080
APP_SCHEME="${INGRESS_URL%%://*}"
[[ "$APP_SCHEME" == "http" || "$APP_SCHEME" == "https" ]] || APP_SCHEME=http
APP_HOST="${INGRESS_URL#http://}"; APP_HOST="${APP_HOST#https://}"; APP_HOST="${APP_HOST%%/*}"
APP_URL="${APP_SCHEME}://${APP_HOST}/app"

kubectl -n "$NS" auth can-i create deployments.apps | grep -qx yes || { echo "No deployment permission in assigned namespace" >&2; exit 1; }

rm -rf /tmp/scribner-cm && mkdir -p /tmp/scribner-cm
cp "$APP_DIR"/*.py /tmp/scribner-cm/
cp "$APP_DIR"/requirements.txt /tmp/scribner-cm/
cp "$APP_DIR"/builders_stack_lock.json /tmp/scribner-cm/

# ConfigMaps: code and static are separate because --from-file on a directory is non-recursive.
CODE_JSON="$(kubectl -n "$NS" create configmap "${APP_NAME}-code" --from-file=/tmp/scribner-cm --dry-run=client -o json)"
STATIC_JSON="$(kubectl -n "$NS" create configmap "${APP_NAME}-static" --from-file="$APP_DIR/static" --dry-run=client -o json)"
(( ${#CODE_JSON} < 900000 && ${#STATIC_JSON} < 900000 )) || { echo "ConfigMap too large" >&2; exit 1; }
printf '%s' "$CODE_JSON" | kubectl apply -f - >/dev/null
printf '%s' "$STATIC_JSON" | kubectl apply -f - >/dev/null

kubectl -n "$NS" create secret generic "${APP_NAME}-vss-creds" \
  --from-literal=VSS_URL="$INGRESS_URL" \
  --from-literal=VSS_USERNAME="$USERNAME" \
  --from-literal=VSS_PASSWORD="$PASSWORD" \
  --from-literal=WANDB_API_KEY="${WANDB_API_KEY:-}" \
  --from-literal=WANDB_TEAM="${WANDB_TEAM:-}" \
  --from-literal=WANDB_PROJECT="${WANDB_PROJECT:-}" \
  --from-literal=SCRIBNER_MODEL="${SCRIBNER_MODEL:-}" \
  --from-literal=GPU_BEARER_TOKEN="${GPU_BEARER_TOKEN:-}" \
  --from-literal=COSMOS3_REASON_URL="${COSMOS3_REASON_URL:-}" \
  --from-literal=YOLO_URL="${YOLO_URL:-}" \
  --from-literal=COSMOS_EMBED1_URL="${COSMOS_EMBED1_URL:-}" \
  --from-literal=COSMOS3_REASON_MODEL="${COSMOS3_REASON_MODEL:-nvidia/cosmos3-reason}" \
  --from-literal=COSMOS_EMBED1_MODEL="${COSMOS_EMBED1_MODEL:-nvidia/cosmos-embed1}" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Review labels and the scorer live under /data. SCRIBNER_PVC=1 backs it with a 256Mi
# PVC (needs a StorageClass the team namespace can use; the claim binds when the pod
# schedules). Otherwise an emptyDir keeps them for the pod's lifetime.
if [[ "${SCRIBNER_PVC:-0}" == "1" ]]; then
  kubectl -n "$NS" apply -f - <<EOF >/dev/null
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: scribner-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 256Mi
EOF
  DATA_VOLUME='persistentVolumeClaim: { claimName: scribner-data }'
  echo "review state: PVC scribner-data"
else
  DATA_VOLUME='emptyDir: {}'
  echo "review state: emptyDir, kept for the pod's lifetime (set SCRIBNER_PVC=1 for a PVC)"
fi

kubectl -n "$NS" apply -f - <<EOF >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  labels: { app: ${APP_NAME} }
spec:
  replicas: 1
  selector: { matchLabels: { app: ${APP_NAME} } }
  template:
    metadata: { labels: { app: ${APP_NAME} } }
    spec:
      containers:
      - name: app
        image: python:3.12-slim
        imagePullPolicy: IfNotPresent
        ports: [{ containerPort: ${APP_PORT} }]
        env:
        - { name: PORT, value: "${APP_PORT}" }
        - { name: SCRIBNER_MOCK, value: "0" }
        - { name: SCRIBNER_PACK, value: "C" }
        - { name: SCRIBNER_CAMERA_ID, value: "sdg_warehouse_cam-2" }
        - { name: SCRIBNER_DATA_DIR, value: "/data/scribner" }
        - name: VSS_URL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: VSS_URL } }
        - name: VSS_USERNAME
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: VSS_USERNAME } }
        - name: VSS_PASSWORD
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: VSS_PASSWORD } }
        - name: WANDB_API_KEY
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: WANDB_API_KEY } }
        - name: WANDB_TEAM
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: WANDB_TEAM } }
        - name: WANDB_PROJECT
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: WANDB_PROJECT } }
        - name: SCRIBNER_MODEL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: SCRIBNER_MODEL } }
        - name: GPU_BEARER_TOKEN
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: GPU_BEARER_TOKEN } }
        - name: COSMOS3_REASON_URL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: COSMOS3_REASON_URL } }
        - name: YOLO_URL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: YOLO_URL } }
        - name: COSMOS_EMBED1_URL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: COSMOS_EMBED1_URL } }
        - name: COSMOS3_REASON_MODEL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: COSMOS3_REASON_MODEL } }
        - name: COSMOS_EMBED1_MODEL
          valueFrom: { secretKeyRef: { name: ${APP_NAME}-vss-creds, key: COSMOS_EMBED1_MODEL } }
        volumeMounts:
        - { name: code, mountPath: /code }
        - { name: static, mountPath: /code/static }
        - { name: data, mountPath: /data }
        workingDir: /code
        command: ["bash", "-c"]
        args: ["set -euo pipefail; pip install --no-cache-dir -q -r requirements.txt; exec python main.py"]
        readinessProbe:
          httpGet: { path: /health, port: ${APP_PORT} }
          initialDelaySeconds: 15
          periodSeconds: 10
      volumes:
      - name: code
        configMap: { name: ${APP_NAME}-code }
      - name: static
        configMap: { name: ${APP_NAME}-static }
      - name: data
        ${DATA_VOLUME}
---
apiVersion: v1
kind: Service
metadata: { name: ${APP_NAME} }
spec:
  selector: { app: ${APP_NAME} }
  ports: [{ name: http, port: 80, targetPort: ${APP_PORT} }]
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${APP_NAME}
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /\$2
spec:
  ingressClassName: nginx
  rules:
  - host: ${APP_HOST}
    http:
      paths:
      - path: /app(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service: { name: ${APP_NAME}, port: { number: 80 } }
EOF

kubectl -n "$NS" rollout restart deploy/"$APP_NAME" >/dev/null
kubectl -n "$NS" rollout status deploy/"$APP_NAME" --timeout=180s
# The Ingress can take a few seconds to route a new backend.
curl --fail --silent --show-error --retry 10 --retry-delay 3 --retry-all-errors "$APP_URL" >/dev/null
curl --fail --silent --show-error "$APP_URL/" >/dev/null
curl --fail --silent --show-error "$APP_URL/health" >/tmp/scribner-deploy-health.json
curl --fail --silent --show-error "$APP_URL/api/andon" >/tmp/scribner-deploy-andon.json
curl --fail --silent --show-error "$APP_URL/api/report" >/tmp/scribner-deploy-report.md

echo "OK deployed: $APP_URL"
echo "Next: python workshop/05_verify_live_scribner.py --app-url '$APP_URL'"
echo "Then restart once and rerun the verifier to prove PVC-backed review state behavior."
