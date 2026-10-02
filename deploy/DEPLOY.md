# Deploy Scribner on the workshop cluster

Agent note: this is the human-readable twin of `.cursor/skills/deploy-scribner`.
The VM has **no Docker daemon**. Code is a ConfigMap. Image is public
`python:3.12-slim`. Ingress path is **`/app`** on the team's existing host.

## 1. Identity

```bash
export KUBECONFIG=/config/kubeconfig
kubectl cluster-info

mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
(( ${#TEAM_CONFIGS[@]} == 1 )) || { echo "expected exactly one /config/*.config"; exit 1; }
set -a && source "${TEAM_CONFIGS[0]}" && set +a

NS="$USERNAME"
APP_HOST="${INGRESS_URL#http://}"
APP_HOST="${APP_HOST#https://}"
APP_HOST="${APP_HOST%%/*}"
APP_NAME=scribner
APP_DIR=tools/scribner   # from the Scribner repo root on the VM
```

Never `echo` the sourced file.

## 2. ConfigMap (code)

Exclude tests to stay under ~1 MiB:

```bash
# copy a slim tree
rm -rf /tmp/scribner-cm && mkdir -p /tmp/scribner-cm
cp "$APP_DIR"/*.py /tmp/scribner-cm/
cp "$APP_DIR"/requirements.txt /tmp/scribner-cm/
mkdir -p /tmp/scribner-cm/static
cp "$APP_DIR"/static/index.html /tmp/scribner-cm/static/

kubectl -n "$NS" create configmap "${APP_NAME}-code" \
  --from-file=/tmp/scribner-cm \
  --dry-run=client -o yaml | kubectl apply -f -
```

ConfigMap `--from-file` on a directory does **not** recurse into `static/`.
If the UI 404s, create a second ConfigMap for `static/index.html` **or**
flatten: the Deployment below mounts `static` from a dedicated ConfigMap.

Preferred flatten (index.html next to main.py is already loaded via
`STATIC_DIR / "index.html"` — keep `static/` as a nested key using):

```bash
kubectl -n "$NS" create configmap "${APP_NAME}-code" \
  --from-file=/tmp/scribner-cm \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$NS" create configmap "${APP_NAME}-static" \
  --from-file="$APP_DIR/static" \
  --dry-run=client -o yaml | kubectl apply -f -
```

Mount both: code at `/code`, static at `/code/static`.

## 3. Secret

```bash
kubectl -n "$NS" create secret generic "${APP_NAME}-vss-creds" \
  --from-literal=VSS_URL="$INGRESS_URL" \
  --from-literal=VSS_USERNAME="$USERNAME" \
  --from-literal=VSS_PASSWORD="$PASSWORD" \
  --from-literal=WANDB_API_KEY="${WANDB_API_KEY:-}" \
  --from-literal=WANDB_TEAM="${WANDB_TEAM:-}" \
  --from-literal=WANDB_PROJECT="${WANDB_PROJECT:-}" \
  --from-literal=GPU_BEARER_TOKEN="${GPU_BEARER_TOKEN:-}" \
  --from-literal=COSMOS3_REASON_URL="${COSMOS3_REASON_URL:-}" \
  --from-literal=YOLO_URL="${YOLO_URL:-}" \
  --from-literal=COSMOS_EMBED1_URL="${COSMOS_EMBED1_URL:-}" \
  --from-literal=COSMOS3_REASON_MODEL="${COSMOS3_REASON_MODEL:-nvidia/cosmos3-reason}" \
  --from-literal=COSMOS_EMBED1_MODEL="${COSMOS_EMBED1_MODEL:-nvidia/cosmos-embed1}" \
  --dry-run=client -o yaml | kubectl apply -f -
# Do not inject CANARY_1B_URL. Canary is optional ASR and is not wired.
```

## 4. Deployment + Service + Ingress

```bash
APP_PORT=8080
kubectl -n "$NS" apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  labels:
    app: ${APP_NAME}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${APP_NAME}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
    spec:
      containers:
      - name: app
        image: python:3.12-slim
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: ${APP_PORT}
        env:
        - name: PORT
          value: "${APP_PORT}"
        - name: SCRIBNER_MOCK
          value: "0"
        - name: SCRIBNER_DATA_DIR
          value: "/tmp/scribner"
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
        - name: code
          mountPath: /code
        - name: static
          mountPath: /code/static
        workingDir: /code
        command: ["bash", "-c"]
        args:
        - |
          set -euo pipefail
          pip install --no-cache-dir -q -r requirements.txt
          exec python main.py
        readinessProbe:
          httpGet:
            path: /health
            port: ${APP_PORT}
          initialDelaySeconds: 15
          periodSeconds: 10
      volumes:
      - name: code
        configMap:
          name: ${APP_NAME}-code
      - name: static
        configMap:
          name: ${APP_NAME}-static
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}
spec:
  selector:
    app: ${APP_NAME}
  ports:
  - name: http
    port: 80
    targetPort: ${APP_PORT}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${APP_NAME}
  annotations:
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
          service:
            name: ${APP_NAME}
            port:
              number: 80
EOF
```

Public URL: `http://${APP_HOST}/app`

## 5. Verify

```bash
kubectl -n "$NS" rollout status deploy/"$APP_NAME"
curl -sS "http://${APP_HOST}/app/health"
curl -sS -o /dev/null -w "%{http_code}\n" "http://${APP_HOST}/app"
```

## Update loop

| Change | Action |
|--------|--------|
| Python or HTML | Recreate ConfigMap(s), `kubectl -n $NS rollout restart deploy/scribner` |
| Credentials | Recreate Secret, restart |

If live Explore has no `PATH_CLEAR:` captions yet, re-ingest Pack C
(`sdg_warehouse_cam-2`) with skill `ingest-kits` before claiming
the live gate. Scene id is inferred from `camera_id` (Pack C →
`warehouse-aisle`).
