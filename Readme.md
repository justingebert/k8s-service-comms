# K8s, Helm, Rancher

This is a documentation of my path in exploring, experimenting and learning Kubernetes (K8s), Helm, and Rancher.

## Introduction
- follow https://kubernetes.io/docs/tutorials/
- ways of running k8s: minikube, kind, kubeadm
- start with minikube for local testing
- kubectl to communicate with k8s cluster

### notes k8s:
- deployment: manages an instance of an application, ensures desired state inside the cluster
- service: exposes deployment to external network 
  - allows for pods to die and be recreated without affecting access to the application because it routes traffic and abstracts away the pods
- pod: group of one or more application containers, it includes shared storage, IP address and information about how to run.
  - Containers should only be scheduled together in a single Pod if they are tightly coupled and need to share resources such as disk.
- configMap: used to store non-confidential data in key-value pairs. 
  - as volumes updates on pull
  - as env vars only updates on restart of pod

### notes minikube:
minikube needs a tunnel to expose services with type LoadBalancer
