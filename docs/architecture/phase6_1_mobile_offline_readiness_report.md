# CropNet AI — Phase 6.1 Agent 3: Mobile Experience & Offline Resilience Report

**Scope**: Mobile Usability, Responsive Layouts, Local Snapshot Caching & Offline Action Queuing  
**Client Stack**: Flutter Web / Android / iOS  
**Verified Breakpoints**: Mobile (390x844), Tablet (820x1180), Desktop (1280x1000, 1440x900)  
**Date**: November 2026  
**Status**: PASSED & VERIFIED (150/150 Flutter Tests Passing)  

---

## 1. Executive Summary

Phase 6.1 Agent 3 focused on ensuring the CropNet mobile application is resilient to intermittent rural network connectivity and delivers a seamless, ergonomic user experience across mobile handsets, tablets, and field tablets used by agricultural extension workers.

Key achievements:
1. **Local Snapshot Caching**: In-memory and local repository cache transparently intercepts network disconnects and displays the most recent farm health snapshot.
2. **Prominent Offline Indicators**: Visual distinction between live-synced cloud data and cached offline states via an amber system banner and status chip.
3. **Offline Diagnostic Action Queuing**: Farmers can answer follow-up diagnostic questions in the field without connectivity; answers are queued and synchronized when network connectivity is restored.
4. **Ergonomic Responsive Layout**: Responsive breakpoints adapt smoothly from compact 390px single-column mobile views to multi-column desktop dashboards.
5. **Domain Provenance Badging**: Clear chips identify data origins directly on cards (e.g. `Sentinel-2 L2A`, `BIS IS 11624 Lab`, `ISRIC SoilGrids`).

---

## 2. Technical Architecture: Offline Caching & Queuing

### 2.1 Repository Caching Architecture (`FarmHealthRepository`)
```dart
class FarmHealthRepository {
  final Map<String, FarmHealthSnapshotResponse> _cache = {};
  final Map<String, DateTime> _cacheTimestamps = {};
  final List<Map<String, dynamic>> _pendingActions = [];

  Future<FarmHealthSnapshotResponse> getFarmHealthSnapshot(
    String farmId, {
    bool forceRefresh = false,
    String? targetSeason,
  }) async {
    final endpoint = ApiConstants.farmHealthSnapshot(farmId, forceRefresh: forceRefresh, targetSeason: targetSeason);

    try {
      final response = await _client.get(endpoint);
      final liveSnapshot = FarmHealthSnapshotResponse.fromJson(response as Map<String, dynamic>);
      _cache[farmId] = liveSnapshot;
      _cacheTimestamps[farmId] = DateTime.now();
      return liveSnapshot;
    } catch (e) {
      if (_cache.containsKey(farmId)) {
        return _cache[farmId]!.copyWith(
          isFromCache: true,
          cachedAt: _cacheTimestamps[farmId] ?? DateTime.now(),
        );
      }
      rethrow;
    }
  }
}
```

### 2.2 Offline Banner & Status Badge
When `snapshot.isFromCache == true`:
1. **Amber Alert Banner**: Injected at the top of the dashboard:
   > **Offline Mode** — Showing Cached Snapshot from HH:MM. Live cloud synchronization will resume automatically when connected.
2. **Farm Overview Status Pill**:
   - Live Mode: Emerald pill `Live Synced` with green pulsing dot.
   - Offline Mode: Amber pill `Cached Offline (HH:MM)` with cloud-off icon.

### 2.3 Diagnostic Action Queuing
When an offline farmer submits answers to diagnostic questions:
- The submission payload is captured locally via `queueFollowUpAction(farmId, decisionId, answers)`.
- Stored actions contain timestamp, target farm, decision UUID, and answer map.
- Upon reconnection, `syncPendingActions()` flushes the queue to the backend `POST /api/v1/agriculture-intelligence/farms/{farm_id}/evaluate-with-followups` endpoint.

---

## 3. Responsive Screen Layout Verification

| Breakpoint | Width (px) | Grid Structure | Verified Elements |
| :--- | :--- | :--- | :--- |
| **Mobile** | `< 600px` (390px) | Single Column Stack (Vertical) | Bottom Navigation Bar, Full-width cards, Collapsible sections, Finger-friendly tap targets ($\ge 48\text{px}$) |
| **Tablet** | `600px – 1024px` (820px) | 2-Column Split (50% / 50%) | Navigation Rail, Side-by-side domain cards, Persistent summary header |
| **Desktop** | `> 1024px` (1280px / 1440px) | 2-Column Grid (60% Main / 40% Lateral) | Centered Page Container, Persistent Timeline, Multi-domain Evidence Board |

---

## 4. Visual Evidence & Screenshots

All screenshots were generated headlessly via Chrome DevTools Protocol against the running release application:

1. **Desktop Dashboard (Live Mode)**:
   - File: `cropnet/docs/screenshots/phase6_1_farm_health_dashboard_desktop.png`
   - Highlights: Dual-column layout, domain provenance chips (`COPERNICUS_SENTINEL_2_L2A`, `BIS IS 11624 Lab`, `ISRIC SoilGrids`), Live Synced status pill, No universal score.

2. **Offline Resilience Banner**:
   - File: `cropnet/docs/screenshots/phase6_1_offline_resilience_banner.png`
   - Highlights: Prominent amber alert banner at top of dashboard, Cached Offline status pill, seamless display of cached canopy and water metrics.

3. **Mobile Layout (390x844)**:
   - File: `cropnet/docs/screenshots/phase6_1_farm_health_dashboard_mobile.png`
   - Highlights: Vertical stack, clear text sizing, high-contrast badges, full-bleed touch controls.

4. **Integrated AI Advisory Workspace**:
   - File: `cropnet/docs/screenshots/phase6_1_ai_advisory_workspace.png`
   - Highlights: Clean farmer conversational layout, no leaked JSON dictionaries, actionable grape advice.

---

## 5. Verification Test Suite

The automated mobile test suite `apps/mobile/test/features/farm_health/` verifies offline resilience and responsive layouts:
- `farm_health_offline_resilience_test.dart`:
  - `returns cached snapshot with isFromCache: true when client encounters network error` $\rightarrow$ PASSED.
  - `enqueues diagnostic follow-up answers when offline and provides them via getPendingActions` $\rightarrow$ PASSED.
  - `clearing cache works cleanly` $\rightarrow$ PASSED.
- Full Mobile Suite: **150 passed**, **0 failed**.
