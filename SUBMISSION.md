# team-pending

## Project
Scribner turns official Pack C warehouse aisle video into a pass/fail completeness check. It parses a bill-of-materials caption from Cosmos Reason (PRESENT, MISSING, COMPLETE), holds uncertain clips for a human, and retrains a prior-anchored logistic gate from those labels so coverage rises without auto-passing a missing person-vehicle gap. The same schema is the official cross-pack query *person close to a moving vehicle*.

**Stack:** Cursor skills; VAST S3 / DataEngine / VastDB; NVIDIA Cosmos Reason (captions), Cosmos Embed1 (search index), YOLO11 (occlusion on optional own clips); optional Weights & Biases serverless inference (prior); numpy logistic regression in `tools/scribner`. Bound to https://github.com/vast-data/vast-builders-challenge only. Corpus: Pack C `sdg_warehouse_cam-2`.
**Code:** NOT PROVIDED — mirror this repo to a public URL judges can open.
**Live app:** none yet — workshop Ingress `http://video-lab-team-<N>.cosmos.vastdata.com/app` after deploy.
**Supplementary:** none

## Feedback
NOT PROVIDED — fill on the day via the workshop submission skill.

<!-- Agent: replace team-pending from $USERNAME. Do not invent a GitHub URL. Never add personal names or emails. -->
