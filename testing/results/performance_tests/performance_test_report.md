# Performance Testing Report

Generated: 2025-06-17T20:31:40.269723
Mock Mode: True

## Endpoint Group: /users/register

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.14 | 49.18 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 30.28 | 48.08 | 39.65 |

## Endpoint Group: /users/login

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.01 | 47.22 | 10.00 |
| 20 | 20 | 794 | 794 | 0 | 30.34 | 48.40 | 39.70 |

## Endpoint Group: /users/<int:user_id>

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 28.55 | 48.09 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 29.29 | 48.15 | 39.65 |

## Endpoint Group: /posts

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.75 | 47.98 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 30.26 | 48.21 | 39.65 |

## Endpoint Group: /posts

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.81 | 47.80 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 29.83 | 47.79 | 39.65 |

## Endpoint Group: /feed

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 31.11 | 48.56 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 30.45 | 48.29 | 39.65 |

## Endpoint Group: /conversations

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.87 | 49.16 | 10.00 |
| 20 | 20 | 794 | 794 | 0 | 30.18 | 48.23 | 39.70 |

## Endpoint Group: /conversations

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 31.17 | 46.83 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 29.43 | 47.87 | 39.65 |

## Endpoint Group: /ai/modules

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.41 | 48.70 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 30.33 | 48.25 | 39.65 |

## Endpoint Group: /ai/preferences

| Concurrent Users | Duration (s) | Total Requests | Successful | Failed | Avg Latency (ms) | P95 Latency (ms) | RPS |
|------------------|--------------|----------------|------------|--------|------------------|------------------|-----|
| 5 | 10 | 100 | 100 | 0 | 30.23 | 48.70 | 10.00 |
| 20 | 20 | 793 | 793 | 0 | 29.97 | 47.73 | 39.65 |

## Summary & Recommendations

- Review endpoints with high latencies or high failure rates under load.
- Consider optimizing database queries and application logic for critical paths.
- Scale resources appropriately based on expected user load.
- If P95 latency is significantly higher than average, investigate outliers and long-tail responses.
