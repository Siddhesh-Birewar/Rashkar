"""
CropNet AI Phase 5.5 — Comprehensive Performance & Latency Benchmark Script.

Measures:
1. Cache initialization & priming time (KnowledgeRetriever).
2. Pure internal decision engine evaluation (cold vs warm cache).
3. Full HTTP loopback API response time (FastAPI on port 8000).
4. Full AI explanation generation response time (Qwen3:8B via Ollama).
5. Follow-up re-evaluation response time.
6. Concurrent request throughput & latency percentiles.
7. Peak memory footprint.
"""
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
import httpx
import psutil

# Ensure cropnet is in python path
import sys
import os
sys.path.insert(0, "/Users/siddheshbirewar/Downloads/Cropnet Feature")

from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import KnowledgeRetriever
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine
from cropnet.services.api.app.schemas.agriculture_intelligence import FarmContextInput

API_BASE = "http://127.0.0.1:8000/api/v1"

def benchmark_cache_init(samples=10):
    durations = []
    for _ in range(samples):
        t0 = time.perf_counter()
        r = KnowledgeRetriever()
        t1 = time.perf_counter()
        durations.append((t1 - t0) * 1000.0)
    return {
        "mean_ms": statistics.mean(durations),
        "median_ms": statistics.median(durations),
        "min_ms": min(durations),
        "max_ms": max(durations),
        "samples": samples
    }

def benchmark_decision_engine_internal(samples=50):
    # Cold cache test (clear cache each time)
    cold_durations = []
    retriever = KnowledgeRetriever()
    engine = DeterministicDecisionEngine(retriever=retriever)
    ctx = FarmContextInput(
        taluka="Baramati",
        district="Pune",
        soil_texture="clay",
        soil_ph=7.5,
        irrigation_available=True,
        irrigation_source="canal",
        target_season="kharif"
    )

    for _ in range(10):
        retriever.clear_cache()
        t0 = time.perf_counter()
        res = engine.evaluate_farm(ctx)
        t1 = time.perf_counter()
        cold_durations.append((t1 - t0) * 1000.0)

    # Warm cache test (repeated queries)
    warm_durations = []
    for _ in range(samples):
        t0 = time.perf_counter()
        res = engine.evaluate_farm(ctx)
        t1 = time.perf_counter()
        warm_durations.append((t1 - t0) * 1000.0)

    return {
        "cold": {
            "mean_ms": statistics.mean(cold_durations),
            "median_ms": statistics.median(cold_durations),
            "min_ms": min(cold_durations),
            "max_ms": max(cold_durations),
            "samples": 10
        },
        "warm": {
            "mean_ms": statistics.mean(warm_durations),
            "median_ms": statistics.median(warm_durations),
            "min_ms": min(warm_durations),
            "max_ms": max(warm_durations),
            "samples": samples
        }
    }

def benchmark_http_evaluate_farm(samples=30):
    payload = {
        "farm_context": {
            "taluka": "Baramati",
            "district": "Pune",
            "soil_texture": "clay",
            "soil_ph": 7.5,
            "irrigation_source": "canal",
            "irrigation_available": True,
            "target_season": "kharif"
        }
    }
    durations = []
    decision_ids = []
    with httpx.Client(timeout=10.0) as client:
        # Warmup
        client.post(f"{API_BASE}/agriculture/evaluate-farm", json=payload)

        for _ in range(samples):
            t0 = time.perf_counter()
            r = client.post(f"{API_BASE}/agriculture/evaluate-farm", json=payload)
            t1 = time.perf_counter()
            assert r.status_code == 200
            durations.append((t1 - t0) * 1000.0)
            decision_ids.append(r.json()["decision_id"])

    return {
        "mean_ms": statistics.mean(durations),
        "median_ms": statistics.median(durations),
        "p95_ms": sorted(durations)[int(samples * 0.95)],
        "min_ms": min(durations),
        "max_ms": max(durations),
        "samples": samples,
        "sample_decision_id": decision_ids[0]
    }

def benchmark_http_explain_decision(decision_id, samples=3):
    durations = []
    sources = []
    with httpx.Client(timeout=45.0) as client:
        for _ in range(samples):
            t0 = time.perf_counter()
            r = client.post(
                f"{API_BASE}/agriculture/explain-decision",
                json={"decision_id": decision_id, "language": "en"}
            )
            t1 = time.perf_counter()
            assert r.status_code == 200
            data = r.json()
            durations.append((t1 - t0))
            sources.append(data.get("generation_source"))

    return {
        "mean_s": statistics.mean(durations),
        "min_s": min(durations),
        "max_s": max(durations),
        "samples": samples,
        "source": sources[0]
    }

def benchmark_http_follow_up(decision_id, samples=10):
    durations = []
    with httpx.Client(timeout=10.0) as client:
        for _ in range(samples):
            t0 = time.perf_counter()
            r = client.post(
                f"{API_BASE}/agriculture/follow-up",
                json={"decision_id": decision_id, "answers": {"soil_texture": "clay"}}
            )
            t1 = time.perf_counter()
            assert r.status_code == 200
            durations.append((t1 - t0) * 1000.0)

    return {
        "mean_ms": statistics.mean(durations),
        "median_ms": statistics.median(durations),
        "min_ms": min(durations),
        "max_ms": max(durations),
        "samples": samples
    }

def benchmark_concurrent_evaluations(concurrency=10, total_requests=50):
    payload = {
        "farm_context": {
            "taluka": "Baramati",
            "district": "Pune",
            "soil_texture": "clay",
            "soil_ph": 7.5,
            "irrigation_source": "canal",
            "irrigation_available": True,
            "target_season": "kharif"
        }
    }
    durations = []

    def make_req():
        with httpx.Client(timeout=10.0) as client:
            t0 = time.perf_counter()
            r = client.post(f"{API_BASE}/agriculture/evaluate-farm", json=payload)
            t1 = time.perf_counter()
            assert r.status_code == 200
            return (t1 - t0) * 1000.0

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_req) for _ in range(total_requests)]
        for f in futures:
            durations.append(f.result())
    t_end = time.perf_counter()

    wall_clock_time = t_end - t_start
    throughput_rps = total_requests / wall_clock_time

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "throughput_rps": throughput_rps,
        "mean_latency_ms": statistics.mean(durations),
        "p95_latency_ms": sorted(durations)[int(total_requests * 0.95)],
        "wall_clock_sec": wall_clock_time
    }

def get_system_memory():
    vm = psutil.virtual_memory()
    # Find FastAPI uvicorn process
    uvicorn_rss_mb = 0.0
    for p in psutil.process_iter(['name', 'cmdline', 'memory_info']):
        try:
            cmd = " ".join(p.info['cmdline'] or [])
            if "uvicorn" in cmd and "cropnet" in cmd:
                uvicorn_rss_mb = p.info['memory_info'].rss / (1024 * 1024)
                break
        except Exception:
            pass

    return {
        "total_ram_gb": vm.total / (1024**3),
        "available_ram_gb": vm.available / (1024**3),
        "used_pct": vm.percent,
        "fastapi_rss_mb": uvicorn_rss_mb
    }

if __name__ == "__main__":
    print("==================================================================")
    print(" CROPNET AI PHASE 5.5 — PERFORMANCE PROFILING SUITE")
    print("==================================================================")

    print("\n1. Measuring Cache Initialization...")
    c_init = benchmark_cache_init()
    print(f"   • Cache Init Mean: {c_init['mean_ms']:.3f} ms (N={c_init['samples']})")

    print("\n2. Measuring Pure Internal Decision Engine (Python Logic Only)...")
    c_eng = benchmark_decision_engine_internal()
    print(f"   • Cold-Cache Evaluation: {c_eng['cold']['mean_ms']:.3f} ms (N={c_eng['cold']['samples']})")
    print(f"   • Warm-Cache Evaluation: {c_eng['warm']['mean_ms']:.3f} ms (N={c_eng['warm']['samples']})")

    print("\n3. Measuring Full HTTP API Loopback (FastAPI on Port 8000)...")
    c_http = benchmark_http_evaluate_farm()
    print(f"   • Complete HTTP evaluate-farm Mean: {c_http['mean_ms']:.3f} ms (P95: {c_http['p95_ms']:.3f} ms, N={c_http['samples']})")

    print("\n4. Measuring AI Explanation API (Qwen3:8B / Ollama)...")
    c_exp = benchmark_http_explain_decision(c_http["sample_decision_id"])
    print(f"   • Complete AI Explanation Mean: {c_exp['mean_s']:.2f} s (Source: {c_exp['source']}, N={c_exp['samples']})")

    print("\n5. Measuring Follow-Up Re-Evaluation API...")
    c_fu = benchmark_http_follow_up(c_http["sample_decision_id"])
    print(f"   • Complete HTTP Follow-Up Mean: {c_fu['mean_ms']:.3f} ms (N={c_fu['samples']})")

    print("\n6. Measuring Concurrent Throughput (10 Workers, 50 Requests)...")
    c_conc = benchmark_concurrent_evaluations()
    print(f"   • Concurrency: {c_conc['concurrency']} workers | Wall Clock: {c_conc['wall_clock_sec']:.2f} s")
    print(f"   • Throughput: {c_conc['throughput_rps']:.1f} req/sec | Mean Latency: {c_conc['mean_latency_ms']:.2f} ms")

    print("\n7. System Memory Footprint...")
    mem = get_system_memory()
    print(f"   • Total System RAM: {mem['total_ram_gb']:.1f} GB (Available: {mem['available_ram_gb']:.1f} GB, Used: {mem['used_pct']}%)")
    print(f"   • FastAPI RSS: {mem['fastapi_rss_mb']:.1f} MB")
    print("==================================================================")
