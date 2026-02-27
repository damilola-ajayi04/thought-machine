#!/usr/bin/env python3
"""
k8s_health_check.py

A reusable Kubernetes cluster health-check tool.
Checks Deployments, Pods, Services, and optional HTTP endpoints.
"""

import sys
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def load_k8s_config():
    """Load Kubernetes configuration"""
    try:
        config.load_kube_config()
    except Exception:
        try:
            config.load_incluster_config()
        except Exception as e:
            print(f"[ERROR] Cannot load Kubernetes configuration: {e}")
            sys.exit(1)


def check_pods(namespace=None):
    """Check the status of all pods"""
    v1 = client.CoreV1Api()
    print("\n[INFO] Checking Pods...")
    try:
        pods = v1.list_namespaced_pod(namespace) if namespace else v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            print(f"Pod: {pod.metadata.name:30} Namespace: {pod.metadata.namespace:15} "
                  f"Status: {pod.status.phase:10} Containers Ready: "
                  f"{sum([1 for cs in pod.status.container_statuses if cs.ready]) if pod.status.container_statuses else 0}/"
                  f"{len(pod.spec.containers)}")
    except ApiException as e:
        print(f"[ERROR] Failed to list pods: {e}")


def check_deployments(namespace=None):
    """Check the status of all deployments"""
    apps_v1 = client.AppsV1Api()
    print("\n[INFO] Checking Deployments...")
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace) if namespace else apps_v1.list_deployment_for_all_namespaces()
        for deploy in deployments.items:
            print(f"Deployment: {deploy.metadata.name:30} Namespace: {deploy.metadata.namespace:15} "
                  f"Replicas: {deploy.status.replicas or 0}, Ready: {deploy.status.ready_replicas or 0}")
    except ApiException as e:
        print(f"[ERROR] Failed to list deployments: {e}")


def check_services(namespace=None):
    """Check the services in the cluster"""
    v1 = client.CoreV1Api()
    print("\n[INFO] Checking Services...")
    try:
        services = v1.list_namespaced_service(namespace) if namespace else v1.list_service_for_all_namespaces()
        for svc in services.items:
            ports = ', '.join([str(p.port) for p in svc.spec.ports])
            print(f"Service: {svc.metadata.name:30} Namespace: {svc.metadata.namespace:15} Ports: {ports}")
    except ApiException as e:
        print(f"[ERROR] Failed to list services: {e}")


def check_http_endpoint(url):
    """Check a simple HTTP endpoint"""
    try:
        r = requests.get(url, timeout=5)
        status = "OK" if r.status_code == 200 else f"FAIL ({r.status_code})"
        print(f"HTTP check for {url}: {status}")
    except Exception as e:
        print(f"HTTP check for {url} failed: {e}")


if __name__ == "__main__":
    # Load kubeconfig
    load_k8s_config()

    # Check cluster health
    check_pods()
    check_deployments()
    check_services()

    # Optional HTTP checks (example: Prometheus or frontend)
    urls_to_check = [
        "http://localhost:9090/metrics",   # Prometheus
        "http://localhost:8080"            # Frontend/Whereami
    ]
    for url in urls_to_check:
        check_http_endpoint(url)