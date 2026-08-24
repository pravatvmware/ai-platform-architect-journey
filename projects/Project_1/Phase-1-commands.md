Phase 1: Build the Local Cluster & Istio Service Mesh:

1: Install kind multi node capable cluster.
curl.exe -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.24.0/kind-windows-amd64
Move-Item .\kind-windows-amd64.exe c:\windows\system32\kind.exe

kind --version

2: Install instioctl.
winget install Istio.Istio

3: Create multi-node-capable Kubernetes cluster running locally on your Windows machine.
 kind create cluster --name enterprise-sandbox --image kindest/node:v1.32.0
Creating cluster "enterprise-sandbox" ...
 ✓ Ensuring node image (kindest/node:v1.32.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-enterprise-sandbox"
You can now use your cluster with:

kubectl cluster-info --context kind-enterprise-sandbox

Thanks for using kind! 😊


kubectl cluster-info --context kind-enterprise-sandbox
Kubernetes control plane is running at https://127.0.0.1:49266
CoreDNS is running at https://127.0.0.1:49266/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

4: 1. Install the Istio Control Plane
This command installs Istio using the demo profile, which is perfect for local sandboxes because it includes the core components without consuming too much memory.

PowerShell
Istio core installed ⛵️
✔ Istiod installed 🧠
✔ Ingress gateways installed 🛬
✔ Egress gateways installed 🛫
✔ Installation complete


5: 2. Enable Automatic Sidecar Injection
In a service mesh, every application pod needs a tiny "proxy" container (Envoy) running alongside it to intercept and secure traffic. This command tells Kubernetes to automatically inject that proxy into any new pod you create in the default namespace.

PowerShell
kubectl label namespace default istio-injection=enabled

kubectl label namespace default istio-injection=enabled
namespace/default labeled

6: 3. Verify the Installation
Let's make sure Istio's core components (the control plane) are up and running:

PowerShell
kubectl get pods -n istio-system

kubectl get pods -n istio-system
NAME                                    READY   STATUS    RESTARTS   AGE
istio-egressgateway-55f7bd68d6-8hvnd    1/1     Running   0          6m16s
istio-ingressgateway-785ccc95f6-j2zlb   1/1     Running   0          6m16s
istiod-cc757dcc7-gqdd9                  1/1     Running   0          6m40s