---
layout: default
title: "Block 3: GitHub Actions and GHCR"
parent: 8. Spring Boot Platform Lab
nav_order: 6
---

# Block 3: GitHub Actions and GHCR

**Date started:** 2026-11-10
**Status:** In progress (first CI run failed; to be diagnosed)
**Code:** link the tag here when done: `block-3-done`

## Goal

Replace `kind load` with a real delivery path: every push to `main` is tested, built into an image, pushed to GHCR with the commit SHA as tag, and the SHA is committed into the Helm values so Git records what is deployed.

## Part A: Build and push

Workflow: `.github/workflows/ci.yml`

- Triggers: push to `main` and pull requests, filtered by `paths` (`demo/**`)
- `permissions: contents: read` at workflow level, `packages: write` only on the build job
- `concurrency` cancels superseded runs
- Steps: checkout, setup-java 21 with Maven cache, `mvn -B -ntp verify`, buildx, login to GHCR (push events only), build and push
- Image name is lowercase (GHCR rejects uppercase): `ghcr.io/pravatvmware/spring-boot-platform-lab/demo`
- Tags: full commit SHA (immutable) and `main` (convenience)
- Pull requests build and test but do not push

### First run

```
<paste: status of the first run and the failing step's log>
```

Diagnosis and fix: add the entry to the [troubleshooting log](troubleshooting-log).

Common first-run failures:

| Symptom | Cause | Fix |
|---|---|---|
| `invalid reference format` | Uppercase in image name | Keep it lowercase |
| `denied: permission_denied: write_package` | Missing `packages: write` or restricted workflow permissions | Job-level permissions, or Settings, Actions, General, Workflow permissions |
| Maven cannot find pom | Wrong working directory | `demo/` is the project root |
| `COPY target/*.jar` fails in Docker | Build stage produced no JAR | `docker build ./demo` locally |
| Workflow does not start | `paths` filter or file location | File must be in `.github/workflows/` at the repo root |

## Part B: GitOps update and registry pull

### Chart changes

- `image.repository` points to GHCR, `image.tag` is overwritten by CI in `values-dev.yaml`
- `imagePullSecrets` is a value, rendered into the Deployment only when set

### `update-deploy` job

Runs after `build` succeeds (`needs: build`), on push only. It uses `yq` to set `.image.tag` to the commit SHA in `values-dev.yaml`, commits as `github-actions[bot]` and pushes. CI changes Git only; it never talks to the cluster.

- No infinite loop: pushes made with `GITHUB_TOKEN` do not trigger workflows, and the commit touches only `deploy/**`
- `strenv(SHA)` keeps the value a string
- Lab simplification: values live in the same repo as the app. In a real setup this job writes to a separate deployment repo with a GitHub App or scoped token and opens a PR for prod

### Pull secret

```
kubectl create secret docker-registry ghcr-pull -n demo --docker-server=ghcr.io --docker-username=pravatvmware --docker-password=<PAT with read:packages>
```

The token is never committed. Git holds only the secret name. In production the secret would come from Vault through External Secrets Operator.

### Evidence to add

```
<paste: helm upgrade output and kubectl rollout status>
<paste: image of the running pod (full SHA) and 2/2 READY>
<paste: git log showing the bot commit and the tag line in values-dev.yaml>
<paste: failure when ghcr-pull is deleted (unauthorized) and recovery>
```

## imagePullSecrets reference

The kubelet pulls images, so it needs credentials for private registries. The Secret has type `kubernetes.io/dockerconfigjson`.

| Way to attach | When |
|---|---|
| In the pod spec (our chart) | Explicit and visible in Git |
| On the ServiceAccount | One place per namespace, every pod inherits it |
| Node-level or cloud identity (IRSA for ECR, managed identity for ACR) | No secret needed |

Rules that catch people:

1. Same namespace only. A pod can reference only Secrets in its own namespace.
2. The registry host in the Secret must match the image host.
3. With `IfNotPresent`, a cached image never triggers auth, so a pod can work on one node and fail on another.
4. Changing the Secret does not restart running pods.
5. Base64 is not encryption: restrict RBAC and enable etcd encryption.

| Event message | Meaning |
|---|---|
| `unauthorized` / `denied` / 401 | Missing, wrong or expired credentials, or secret not referenced |
| `manifest unknown` / `not found` | Tag or image does not exist |
| `repository does not exist` on docker.io | Image name has no registry host (the earlier `kind load` problem) |
| `no match for platform` | Wrong CPU architecture |
| `x509: certificate signed by unknown authority` | Private registry with internal CA |

## Checkpoint answers

1. The PR build skips the push so unreviewed code never reaches the registry, and fork PRs do not get write tokens.
2. The SHA is immutable and traceable, rollbacks are exact, and the same image is promoted across environments. `latest` is mutable and cannot be audited.
3. `permissions:` scopes `GITHUB_TOKEN`. Read-only by default and write only on the job that needs it is least privilege.
4. `GITHUB_TOKEN` is created per run, expires when the job ends and is scoped; a stored password lives on and can leak.
5. Mapping from GitLab and Jenkins: stages and jobs map to jobs and steps, templates to reusable workflows, runners to runners, CI variables to secrets, protected environments to Environments with reviewers.
6. `update-deploy` uses `needs: build` so a tag is only written for an image that was built, tested and pushed.
7. CI changes Git rather than running `helm upgrade` so Git stays the source of truth, CI needs no cluster credentials, and rollback is a `git revert`.

## How I would explain this in an interview

> "Every push is tested and built into an image tagged with the commit SHA, pushed to the registry, and the SHA is committed into the Helm values by the pipeline. CI never touches the cluster, so Git is the source of truth. The cluster pulls from the registry with a pull secret that lives in the cluster, not in Git."

## Next

[Block 4: Break things and fix them](04-break-and-fix)


## 2026-11-26: ImagePullBackOff after cluster rebuild
- **Symptom:** pod 1/2, demo container ImagePullBackOff
- **Root cause:** the chart pointed to a GHCR image that CI never pushed (CI failed), and the rebuilt cluster no longer had the side-loaded image
- **Fix:** pushed pravatvmware/springboot-demo:1 to Docker Hub, updated values.yaml, helm upgrade
- **Lesson:** the registry is a dependency of the cluster. Keep the image reference in values, verify the tag exists before deploying
