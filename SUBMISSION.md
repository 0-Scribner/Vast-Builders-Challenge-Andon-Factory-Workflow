# team-pending

## Project
Scribner is an aisle gate on official Pack C warehouse video. It parses a path-safety caption from Cosmos Reason (PERSON, VEHICLE, PATH_CLEAR, NEAR_MISS), holds uncertain clips for a human, and retrains a prior-anchored logistic gate from those labels so coverage rises without auto-clearing a person close to a moving vehicle. That phrase is the official cross-pack search query and the product identity.

**Stack:** Cursor skills; VAST S3 / DataEngine / VastDB; NVIDIA Cosmos Reason (captions), Cosmos Embed1 (search index), YOLO11 (person/vehicle corroboration); optional Weights & Biases serverless inference (prior); numpy logistic regression in `tools/scribner`. Bound to https://github.com/vast-data/vast-builders-challenge only. Corpus: Pack C `sdg_warehouse_cam-2`.
**Code:** NOT PROVIDED — mirror this repo to a public URL judges can open.
**Live app:** none yet — workshop Ingress `http://video-lab-team-<N>.cosmos.vastdata.com/app` after deploy.
**Supplementary:** none

## Feedback
NOT PROVIDED — fill on the day via the workshop submission skill.

<!-- Agent: replace team-pending from $USERNAME. Do not invent a GitHub URL. Never add personal names or emails. -->
