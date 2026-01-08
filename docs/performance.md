# Performance Specifications

This document defines the performance requirements and optimization strategies for the MAID LSP server.

## Response Time Targets

| Operation | Target | P95 Target | Notes |
|-----------|--------|------------|-------|
| Document open | <100ms | <200ms | Initial validation |
| Document change | <50ms | <100ms | Debounced, incremental |
| Hover | <30ms | <50ms | Cached artifact info |
| Code action | <50ms | <100ms | Triggered by diagnostics |

These targets align with the IDE Integration epic requirement of "sub-50 millisecond validation response times in IDE environments."

## Optimization Strategies

### 1. Debouncing

Document changes are debounced to avoid excessive validation during rapid typing.

**Configuration:**
- Default delay: 100ms
- Configurable via initialization options

**Implementation:**
```python
class Debouncer:
    def __init__(self, delay_ms: float = 100):
        self._delay = delay_ms / 1000.0
        self._tasks: dict[str, asyncio.Task] = {}

    async def debounce(self, key: str, func: Callable):
        # Cancel pending task for this key
        if key in self._tasks:
            self._tasks[key].cancel()

        # Schedule new task with delay
        async def delayed_call():
            await asyncio.sleep(self._delay)
            return await func()

        self._tasks[key] = asyncio.create_task(delayed_call())
        return await self._tasks[key]
```

### 2. Caching

Multiple levels of caching reduce repeated work:

| Cache | TTL | Invalidation |
|-------|-----|--------------|
| Validation results | 5min | On file change |
| Manifest chain | Inherited from maid-runner | On manifest change |
| Artifact metadata | 5min | On source file change |

**Note:** maid-runner already implements manifest chain caching, which the LSP leverages.

### 3. Async Execution

All validation runs asynchronously to keep the server responsive:

```python
# Non-blocking subprocess execution
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await process.communicate()
```

### 4. Incremental Validation

For future optimization, track changed regions to validate only affected parts:

**Current:** Full manifest validation on each change
**Future:** Incremental validation for unchanged sections

### 5. Process Pooling (Future)

Maintain a pool of maid-runner processes for faster validation:

**Current:** New subprocess per validation
**Future:** Reuse warmed processes to reduce startup overhead

## Resource Limits

### Concurrency

| Resource | Limit | Rationale |
|----------|-------|-----------|
| Concurrent validations | 3 | Prevent CPU overload |
| Pending debounce tasks | Unlimited | Low memory footprint |
| Cached results | 100 documents | Memory bounds |

### Timeouts

| Operation | Timeout | Configurable |
|-----------|---------|--------------|
| Validation | 10s | Yes |
| Server startup | 5s | Via LSP config |
| Server shutdown | 3s | Via LSP config |

### Memory

| Component | Estimate | Notes |
|-----------|----------|-------|
| Server baseline | ~20MB | pygls + Python runtime |
| Per-document cache | ~50KB | Diagnostics + metadata |
| Max memory | ~100MB | With full cache |

## Benchmarking

### Test Scenarios

1. **Simple Manifest**: Single file, few artifacts
   - Target: <20ms validation

2. **Medium Manifest**: 3-5 files, 10-20 artifacts
   - Target: <50ms validation

3. **Complex Manifest**: 10+ files, 50+ artifacts, manifest chain
   - Target: <100ms validation

4. **Rapid Typing**: 10 changes per second
   - Target: Single validation per debounce window

### Measurement Points

```
[Event received] → [Debounce wait] → [Subprocess start] →
[maid-runner execution] → [Output parsing] → [Diagnostics published]
```

Key metrics:
- **E2E latency**: Event received to diagnostics published
- **Validation time**: maid-runner execution time
- **Parse time**: JSON to diagnostics conversion

### Benchmark Script

```python
import asyncio
import time
from maid_lsp.validation.runner import MaidRunner, ValidationMode

async def benchmark_validation():
    runner = MaidRunner()
    manifest = Path("manifests/task-001.manifest.json")

    # Warm-up
    await runner.validate(manifest, ValidationMode.IMPLEMENTATION)

    # Benchmark
    times = []
    for _ in range(10):
        start = time.perf_counter()
        await runner.validate(manifest, ValidationMode.IMPLEMENTATION)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    print(f"Mean: {sum(times)/len(times):.1f}ms")
    print(f"P95: {sorted(times)[9]:.1f}ms")
```

## Monitoring

### Metrics to Track

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| Validation latency | Histogram | P95 > 200ms |
| Validation errors | Counter | N/A |
| Timeout count | Counter | >5/min |
| Memory usage | Gauge | >150MB |

### Logging

Performance-related log entries:

```
INFO  Validation completed in 45ms: manifests/task-001.manifest.json
WARN  Validation exceeded target (120ms > 50ms): manifests/task-002.manifest.json
DEBUG Debounce cancelled for: file:///project/manifests/task-001.manifest.json
```

## Configuration Options

### Server Initialization Options

```json
{
  "initializationOptions": {
    "maid.validation.debounceMs": 100,
    "maid.validation.timeout": 10000,
    "maid.validation.maxConcurrent": 3,
    "maid.cache.enabled": true,
    "maid.cache.ttlSeconds": 300
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAID_LSP_DEBOUNCE_MS` | 100 | Debounce delay |
| `MAID_LSP_TIMEOUT_MS` | 10000 | Validation timeout |
| `MAID_LSP_LOG_LEVEL` | INFO | Logging verbosity |

## Optimization Roadmap

### v2.0 (Current)

- [x] Debouncing
- [x] Async subprocess execution
- [ ] Basic caching

### v2.1 (Planned)

- [ ] Process pooling
- [ ] Incremental validation
- [ ] Workspace-level caching

### v2.2 (Future)

- [ ] Parallel manifest chain validation
- [ ] Smart cache invalidation
- [ ] Performance profiling dashboard
