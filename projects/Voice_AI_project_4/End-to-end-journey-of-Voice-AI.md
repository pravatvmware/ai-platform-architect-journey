---
title: "End-to-end journey of a Voice AI request"
parent: "6. Project gcp voice AI"
nav_order: 2
---

# Project 4: End-to-end journey of a Voice AI request

Here is the end-to-end journey of a Voice AI request, from the moment a user speaks into the client application down to the specific GKE pod processing the inference.

## 1. The Global Entry Point (GCP Load Balancer & Cloud Armor)
The client application sends a payload—likely using gRPC or WebSockets for real-time Voice AI—to your public domain.

* The traffic first passes through Google Cloud Armor to filter out DDoS attacks, block bad IPs, and enforce WAF rules (a mandatory compliance step for UK financial institutions). 

Ref: [Routing Traffic from Google Load balancer to ISTIO](https://medium.com/@sathishyellanty/routing-traffic-from-google-load-balancer-to-istio-ingress-gateway-using-terraform-993c79737b99#:~:text=Google%20Cloud%20Armor%3A%20This%20security%20service%20sits,kubeconfig%20file%20saved%20on%20the%20local%20system.)

* The allowed traffic hits the GCP External HTTP(S) Load Balancer. This provides a single global IP address, terminates the external TLS connection, and handles initial load distribution.


## 2. Bridging GCP to the Mesh (Container-Native Load Balancing)
To minimize latency for voice workloads, traffic should not bounce randomly between GKE nodes.

* The GCP Load Balancer utilizes Network Endpoint Groups (NEGs). NEGs allow the load balancer to route traffic directly to the IP addresses of the Istio Ingress Gateway pods, entirely bypassing the standard kube-proxy network hops.


## 3. The Mesh Edge (Istio Ingress Gateway)
The Istio Ingress Gateway (an Envoy proxy running at the edge of the mesh) receives the traffic.
Ref: [ISTIO / Ingress Gateway](https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/#:~:text=See%20also%20*%20Direct%20encrypted%20traffic%20from,a%20custom%20ingress%20gateway%20using%20cert%2Dmanager%20manually.)

* The Istio Gateway resource acts as the bouncer. It does not route traffic; rather, it dictates which hosts (e.g., voice.finance-corp.co.uk) and which protocols/ports are permitted to enter the service mesh.

Ref: [ISTIO / Ingrss Gateway](https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/#:~:text=The%20Gateway%20configuration%20resources%20allow%20external%20traffic,endpoint%20of%20the%20service%20to%20external%20traffic.)

## 4. Intelligent Routing (Istio VirtualService & DestinationRule)
Once the traffic is admitted by the Gateway, it needs directions. The Istio VirtualService acts as the routing engine.

* **Context-Aware Routing:** For a Voice AI workload, you can use header-based routing. If a request header indicates a premium or institutional banking client, the VirtualService can route that specific traffic to a dedicated backend backed by higher-tier GPUs.

* **Traffic Splitting (Canary):** When deploying a new version of the Voice AI model, the VirtualService is configured to send 95% of traffic to the stable version (v1) and 5% to the new version (v2).

* The DestinationRule defines the actual subsets (v1 vs v2) and configures load balancing policies and circuit breakers to prevent cascading failures if the AI model becomes overloaded.

## 5. Zero-Trust Secure Delivery (Strict mTLS)
The Ingress Gateway proxy must now send the payload to the actual application pod.

* To meet financial regulatory standards, the mesh is configured with Strict mTLS.

* The Ingress Gateway proxy establishes a mutually authenticated, encrypted tunnel with the Envoy sidecar proxy running inside your application's pod.

* The application's sidecar proxy intercepts the traffic, verifies the identity certificates, decrypts the payload, and hands it directly to the Voice AI application via localhost.
