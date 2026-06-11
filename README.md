# Kubernetes Observability Research

Practical research project dedicated to evaluating observability configurations for microservice applications running in Kubernetes.

## Overview

Modern Kubernetes-based systems generate large volumes of telemetry data. Choosing an appropriate observability configuration directly affects incident investigation speed, infrastructure costs, and operational complexity.

This project investigates several levels of observability and evaluates their effectiveness using practical experiments conducted on a real Kubernetes environment.

> How much observability is actually needed to efficiently diagnose failures in Kubernetes-based microservice applications?

## Research Goals

- Build a production-like Kubernetes environment.
- Deploy a microservice application with OpenTelemetry instrumentation.
- Implement multiple observability configurations.
- Measure diagnostic efficiency under various failure scenarios.
- Evaluate operational overhead and resource consumption.
- Develop a model for selecting an appropriate observability level.

## Observability Configurations

### Level A — Metrics

- Prometheus
- Grafana

### Level B — Metrics + Logs

- Prometheus
- Grafana
- Loki

### Level C — Full Observability

- Prometheus
- Grafana
- Loki
- Tempo
- OpenTelemetry Collector

## Test Environment

### Kubernetes

- Kubernetes
- Helm
- OpenTelemetry

### Demo Application

PulseHub — a microservice application deployed in Kubernetes and instrumented with OpenTelemetry.

## Evaluation Criteria

- Incident investigation time
- Successful root-cause identification rate
- CPU consumption
- Memory consumption
- Storage requirements
- Operational complexity

## Experimental Scenarios

- Application errors
- Service communication failures
- Increased response latency
- Infrastructure failures
- Kubernetes pod restarts

## Technologies

- Kubernetes
- Helm
- OpenTelemetry
- Prometheus
- Grafana
- Loki
- Tempo
- Docker

## Author

Danila Krasov

Master's Thesis Project

ITMO University
