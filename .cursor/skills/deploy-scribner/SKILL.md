---
name: deploy-scribner
description: >-
  Deploy Scribner on the workshop Kubernetes cluster at Ingress path /app
  without Docker build/push (ConfigMap + python:3.12-slim + Secret). Use
  when the team is on the VM and ready to demo, or says "deploy", "ship
  to /app", "k8s the gate".
---

# Deploy Scribner at `/app`

Follow the workshop `deployment/deploy-app-no-registry` pattern. **Never**
`docker build`. **Never** use Ingress path `/` (that is the VSS UI).
**Never** ship localhost as the judged demo.

Full kubectl is in [deploy/DEPLOY.md](../../../deploy/DEPLOY.md). Summary:

1. `export KUBECONFIG=/config/kubeconfig`
2. Source the single `/config/*.config` (do not print it).
3. `NS="$USERNAME"`  `APP_HOST` from `$INGRESS_URL`  `APP_NAME=scribner`
4. ConfigMap from `tools/scribner/` (exclude `tests/`, keep ≤1 MiB).
5. Secret with official stack names only: `VSS_URL`, `VSS_USERNAME`, `VSS_PASSWORD`
   (deploy-app-no-registry aliases of `INGRESS_URL` / `USERNAME` / `PASSWORD`),
   plus `WANDB_API_KEY`, `WANDB_TEAM`, `WANDB_PROJECT`, `GPU_BEARER_TOKEN`,
   `COSMOS3_REASON_URL`, `YOLO_URL`, `COSMOS_EMBED1_URL`,
   `COSMOS3_REASON_MODEL`, `COSMOS_EMBED1_MODEL`. Never `CANARY_1B_URL`.
6. Set `SCRIBNER_MOCK=0` in the Deployment env when live clips exist;
   `SCRIBNER_MOCK=1` only for a pipeline smoke test.
7. Ingress host=`$APP_HOST` path=`/app(/|$)(.*)` rewrite to `/$2`.
8. Prove `curl http://$APP_HOST/app/health`.

After code changes: recreate ConfigMap, `kubectl -n $NS rollout restart deploy/scribner`.

## Agent rules

- Stay in this team's namespace.
- Do not echo Secret values.
- If ImagePullBackOff, ask organizers — do not fall back to a local server as the demo.
- `workingDir: /code`, `command: python main.py`, `PORT=8080`, probe `/health`.
