## Air-Gapped Deployment & Zero-Trust Hardening (`aegisops-enclave`)

This repository packages the **AegisOps** stack (`ui`, `api`, and `postgres`) into a self-contained, offline-capable `.tar.zst` artifact using **Zarf**, and enforces strict zero-trust pod-to-pod isolation inside **Kubernetes (K8s)** via `NetworkPolicy` manifests.

---

### How It Works (Architectural Overview)

Imagine delivering and running a high-security software application inside a **sealed vault with no internet connection** (such as a defense enclave, bank data center, or air-gapped factory).

Inside **Kubernetes** (the operating system that manages and runs our servers and containers), the application lives in an isolated virtual room called a **Namespace** (`aegisops-enclave`) and consists of three container workloads (**Pods**):
- **The UI Pod (User Interface):** The frontend web screen that users interact with.
- **The API Pod (The Brain):** The backend service that processes requests from the UI on port `8000`.
- **The Postgres Pod (The Filing Cabinet):** The database where application data is stored on port `5432`.

#### What Happened at Each Stage

1. **Installing the Air-Gap Packager (`Zarf`)**
   - Normally, Kubernetes pulls container images from public internet registries (like Docker Hub) when starting an app. In an offline environment, that fails.
   - **Zarf** is an air-gap packaging tool that downloads all required container images and setup files ahead of time on a connected machine and bundles them into a single portable archive. We first installed the `zarf` CLI binary into `/usr/local/bin/` so the control plane could build and unpack offline bundles.

2. **Locking All Doors Inside Kubernetes (`NetworkPolicy`, `Ingress` & `Egress`)**
   - By default in Kubernetes, every pod inside a cluster can freely send network traffic to every other pod. If an attacker compromises the public-facing **UI** pod, they could connect directly to the **Postgres** database.
   - We added **Kubernetes NetworkPolicies**, which act like automated firewall keycards controlling **Ingress** (incoming traffic into a pod) and **Egress** (outgoing traffic leaving a pod):
     - **`default-deny-all` (Lock Every Door):** Blocks all incoming (`Ingress`) and outgoing (`Egress`) traffic for every pod in `aegisops-enclave` by default.
     - **`allow-ui-egress` (UI → API only):** Gives the `ui` pod a keycard to send `Egress` traffic *only* to the `api` pod on TCP port `8000`.
     - **`allow-api-traffic` (API → Postgres only):** Allows the `api` pod to receive `Ingress` from `ui` (port `8000`) and send `Egress` *only* to `postgres` on TCP port `5432`.
     - **`allow-postgres-ingress` (Database Lock):** Allows `postgres` to accept `Ingress` *only* from the `api` pod on port `5432`, with zero outbound access.
     - **Internal Phonebook (`CoreDNS`):** Because `default-deny-all` blocks all outbound calls, pods cannot look up internal addresses like `http://api:8000`. We added an `Egress` exception on UDP/TCP port `53` to Kubernetes' built-in directory service (**CoreDNS** in `kube-system`).

3. **Packing Everything into One Sealed Box (`.tar.zst`)**
   - Using `zarf package create`, we bundled the container images, Kubernetes YAML manifests, and `NetworkPolicy` rules into one compressed `.tar.zst` file. This single file can be carried across an air-gap (via USB or secure transfer) and deployed without internet access.

4. **Resolving the `Helm` Ownership Conflict & Deploying Offline**
   - Under the hood, **Zarf** uses **Helm** (Kubernetes' package manager) to install and track resources. When Zarf deploys raw Kubernetes YAML files, it automatically wraps them into an internal Helm chart and stamps every resource with tracking labels (`app.kubernetes.io/managed-by: Helm`).
   - When we first ran `zarf package deploy`, Helm halted with an **`invalid ownership metadata`** error on `default-deny-all` and `Deployment "aegisops-api"`. Earlier manual tests (`kubectl apply`) had left unmanaged copies of those resources inside `aegisops-enclave` without Helm tracking tags, and Helm refuses to overwrite resources it does not own.
   - Once we deleted the pre-existing unmanaged resources from `aegisops-enclave`, Zarf pushed the bundled images into the cluster's local internal registry, rewrote the pod image paths to pull locally, and installed the entire hardened stack cleanly via Helm.

---

### Zero-Trust Network Architecture

```text
+-------------------------------------------------------------------+

| Namespace: aegisops-enclave (default-deny-all Ingress & Egress)   |
|                                                                   |
|   +------------+   TCP :8000   +------------+   TCP :5432   +------------+

|   |   ui pod   | ------------> |  api pod   | ------------> |  postgres  |
|   +------------+               +------------+               +------------+

|         |                            |                            |
|         | UDP/TCP :53                | UDP/TCP :53                |
|         v                            v                            |
|   +------------------------------------------+                    |
|   | kube-system / CoreDNS (Service Discovery)| (No Egress Needed) |
|   +------------------------------------------+                    |
+-------------------------------------------------------------------+
```

---

### Step-by-Step Implementation & Commands

#### Stage 1: Install Zarf CLI
Downloaded and installed the standalone `zarf` binary onto the control plane node (`Linux_amd64`):

```bash
ZARF_VERSION=\$(curl -sIX HEAD https://github.com | grep -i ^location: | grep -Eo 'v[0-9]+\.[0-9]+\.[0-9]+')
curl -sL "https://github.com\({ZARF_VERSION}/zarf_\){ZARF_VERSION}_Linux_amd64" -o zarf
chmod +x zarf
mv zarf /usr/local/bin/zarf
zarf version
```

#### Stage 2: Enforce Zero-Trust `NetworkPolicy` Rules
Defined four policies in the component manifests to enforce default-deny isolation while allowing required communication:
- **`default-deny-all`:** Blocks all ingress and egress for every pod in `aegisops-enclave`.
- **`allow-ui-egress`:** Permits `ui` pods to reach `api` pods on `TCP/8000` and CoreDNS on `UDP/TCP 53`.
- **`allow-api-traffic`:** Permits ingress from `ui` on `TCP/8000`, egress to `postgres` on `TCP/5432`, and CoreDNS on `UDP/TCP 53`.
- **`allow-postgres-ingress`:** Permits ingress exclusively from `api` pods on `TCP/5432`.

#### Stage 3: Build the Air-Gapped `.tar.zst` Package
Bundled all container images and hardened Kubernetes manifests into a single offline archive:

```bash
zarf package create . --confirm
```

#### Stage 4: Clean Unmanaged Resources & Deploy Offline
Cleared pre-existing manual resources in `aegisops-enclave` that conflicted with Helm ownership metadata, then deployed the `.tar.zst` bundle:

```bash
# Remove pre-existing unmanaged resources in the target namespace
kubectl delete deployments,statefulsets,services,configmaps,networkpolicies --all -n aegisops-enclave

# Deploy the offline package into the cluster
zarf package deploy zarf-package-*.tar.zst --confirm
```

#### Stage 5: Verify Deployment & Policies
Confirmed that all workloads reached `Running` state and all four network policies were applied:

```bash
kubectl get pods,networkpolicies -n aegisops-enclave
```
e.g.
NAME                                READY   STATUS    RESTARTS   AGE
pod/aegisops-api-58cdfbfd4b-bqtlr   1/1     Running   0          36s
pod/aegisops-ui-68998b89f-bvsss     1/1     Running   0          36s

NAME                                                POD-SELECTOR   AGE
networkpolicy.networking.k8s.io/allow-api-traffic   app=api        37s
networkpolicy.networking.k8s.io/allow-ui-egress     app=ui         37s
networkpolicy.networking.k8s.io/default-deny-all    <none>         37s

---

### Troubleshooting

#### 1. `Command 'zarf' not found`
- **Cause:** `zarf` is not distributed via standard OS package managers (`apt`/`yum`).
- **Fix:** Download the release binary directly from GitHub Releases and move it to `/usr/local/bin/zarf` (see Stage 1).

#### 2. `invalid ownership metadata; label validation error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"`
- **Cause:** Zarf wraps raw Kubernetes manifests into an internal Helm chart during deployment. If a resource (`NetworkPolicy`, `Deployment`, `Service`, etc.) was previously created via `kubectl apply`, Helm refuses to overwrite it without ownership labels and annotations.
- **Fix (Option A — Clean Reset):** Delete the pre-existing unmanaged resources or recreate the namespace before redeploying:
  ```bash
  kubectl delete namespace aegisops-enclave && kubectl create namespace aegisops-enclave
  zarf package deploy zarf-package-*.tar.zst --confirm
  ```
- **Fix (Option B — In-Place Adoption):** Stamp the required Helm metadata onto the existing resource if it cannot be deleted:
  ```bash
  kubectl label <kind> <name> -n aegisops-enclave app.kubernetes.io/managed-by=Helm --overwrite
  kubectl annotate <kind> <name> -n aegisops-enclave \
    meta.helm.sh/release-name=<zarf-release-name> \
    meta.helm.sh/release-namespace=aegisops-enclave --overwrite
  ```

#### 3. Pods Cannot Resolve Service Names After Enabling `default-deny-all`
- **Cause:** A `default-deny-all` policy with `Egress` enabled blocks outbound DNS queries to CoreDNS (`kube-system`).
- **Fix:** Ensure `egress` rules for `ui` and `api` pods explicitly allow `UDP` and `TCP` port `53` to the `kube-system` namespace, and confirm your cluster CNI (e.g., Calico, Cilium) supports `NetworkPolicy` enforcement:
  ```bash
  kubectl describe networkpolicy allow-ui-egress allow-api-traffic -n aegisops-enclave
  ```
