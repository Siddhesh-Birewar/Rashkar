# CropNet AI — Responsive Browser Experience & Multi-Viewport Test Report

**Document Version:** 1.0.0  
**Audit Date:** November 7, 2026  
**Target Platform:** Flutter Web (Google Chrome)  
**Evaluator:** Antigravity Autonomous Agent (UX & Browser Architecture Workstream)  

---

## 1. Executive Summary

This report documents the responsive layout verification and multi-viewport testing of the CropNet AI Web Application prototype. The evaluation verified that both core agricultural intelligence features:
1. **Soil Intelligence & Crop Recommendation (Feature 1)**
2. **AI Agricultural Assistant (Feature 2)**

render fluidly and operate without horizontal overflow errors (`A RenderFlex overflowed...`) across mobile, tablet, and desktop viewports. All UI components, including the interactive boundary map, soil metric cards, deterministic evaluation cards, bilingual dialogue bubbles, and Marathi Devanagari typography, adapt dynamically to screen size.

---

## 2. Multi-Viewport Testing Matrix

| Viewport Profile | Resolution (px) | Device Archetype | Navigation Adaptation | Layout Structure | Result |
|---|---|---|---|---|---|
| **Mobile Compact** | 375 × 667 | iPhone SE | Bottom Navigation Bar | Single-column stacked cards, horizontal scroll context bar | **PASS** |
| **Mobile Standard** | 412 × 915 | Pixel 7 / Galaxy S23 | Bottom Navigation Bar | Single-column stacked cards, full-width chat bubbles (85% max) | **PASS** |
| **Tablet Portrait** | 768 × 1024 | iPad Mini / 10" Tablet | Bottom Navigation Bar | 2-column metric cards, expanded dialog panels | **PASS** |
| **Desktop Standard**| 1280 × 800 | Laptop 13"/14" | Top Navigation / Sidebar | Side-by-side evaluation & chat panels, 3-column crop grid | **PASS** |
| **Desktop Wide** | 1920 × 1080 | Full HD Monitor | Top Navigation / Sidebar | Max content constraint (1200px centered), multi-column analytics | **PASS** |

---

## 3. Responsive Screen-by-Screen Audit

### 3.1 Authentication Screen (`/login`, `/register`)
- **Desktop (1280px+):** Centered card container constrained to `440px` max-width with subtle drop shadow. Background displays soothing agricultural gradient.
- **Mobile (375px–412px):** Card expands to 100% width with 16px screen padding. Input fields adapt keyboard view with `SingleChildScrollView` to prevent keyboard overflow.

### 3.2 Farm Dashboard & Boundary Drawing (`/farms`, `/farms/new`)
- **Desktop:**
  - Split view: map viewport occupies 60% width on left; farm properties, taluka selectors, and vertices summary occupy 40% width on right.
  - Mouse click adds boundary vertices; live geodesic area updates dynamically.
- **Mobile:**
  - Stacked view: interactive satellite map preview occupies top `280px` height; form controls scroll underneath.
  - Touch tap adds boundary vertices; Undo and Clear buttons positioned as floating controls over map.

### 3.3 Soil Intelligence & Scientific Provenance (`/soil`, `/soil/:farmId`)
- **Desktop:**
  - Soil parameters displayed in a 3-column grid:
    - Column 1: Physical Parameters (Texture, Clay %, Sand %, Silt %).
    - Column 2: Chemical Parameters (pH 7.3, Organic Carbon, CEC).
    - Column 3: Digital Map Provenance & Critical Agronomic Safeguard.
- **Mobile:**
  - Cards stack into a single vertical scroll view.
  - Critical safeguard badge (*"Lab Soil Test Required — Available NPK not inferred from digital map"*) rendered in full-width warning amber card with clear explanatory text.

### 3.4 Weather & 30-Year Climatology (`/weather`, `/weather/:farmId`)
- **Desktop:**
  - Current meteorological conditions rendered in hero card.
  - 5-Day forecast cards arranged horizontally with smooth scroll.
  - 30-Year NASA POWER climatological normals rendered in side-by-side data tables.
- **Mobile:**
  - Current conditions hero card adapts font sizes to fit 375px width.
  - 5-day forecasts scroll horizontally in compact cards (`width: 140px`).
  - Climatology summary stacks neatly into collapsible sections.

### 3.5 Crop Catalogue & Agronomic Requirements (`/crops`, `/crops/:cropId`)
- **Desktop:** 3-column grid of crop cards with thumbnail, botanical classification, and season badge.
- **Mobile:** 1-column list of expandable crop cards.
- **Crop Detail Screen:** Responsive table displaying ICAR/MPKV water requirement (mm), soil pH tolerance, and sowing windows with a sticky *"Evaluate for My Farm"* button at bottom.

### 3.6 AI Agricultural Assistant (`/advisory`)
- **Context Bar Adaptation:**
  - Previously identified overflow issue on narrow viewports: `A RenderFlex overflowed by 0.200 pixels on the right` in `DropdownButton`.
  - **Resolution:** Context bar wrapped in `SingleChildScrollView(scrollDirection: Axis.horizontal)`. Farm selector, taluka selector, target season, and language toggle scroll smoothly on mobile without clipping.
- **Chat Dialogue Bubbles:**
  - User messages aligned right (`color: Color(0xFFE8F5E9)`).
  - Assistant messages aligned left (`color: Colors.white`).
  - Max bubble width constrained to `85%` of screen width.
  - Devanagari Marathi text rendered in UTF-8 with zero font glyph clipping or text overflow.
- **Deterministic Decision Summary:**
  - Evaluated crop outcomes presented with clear status pills:
    - `SUITED` (Green)
    - `REGIONAL_SCREENING_ONLY` (Amber)
    - `DISQUALIFIED` (Red)
  - Diagnostic follow-up question chips wrap horizontally with `Wrap(spacing: 8, runSpacing: 8)`.

---

## 4. Devanagari Typography & Multi-Language Verification

Marathi localization was tested across all responsive viewports.

| String Key / Concept | Marathi Rendering (Devanagari) | Verification Status |
|---|---|---|
| **Welcome Advisory** | नमस्ते! क्रॉपनेट एआय कृषी सल्लागार प्रणालीमध्ये आपले स्वागत आहे. | **PASS** — Crisp font rendering |
| **Decision Status (Suited)** | प्रमाणित पिके / अनुकूल | **PASS** — No glyph truncation |
| **Decision Status (Screening)**| प्रादेशिक चाळणी पातळी | **PASS** — Correct ligatures |
| **Diagnostic Follow-up** | काळी मध्यम ते भारी व्हर्टिसोल जमीन, सामू ७.३ | **PASS** — Numerals & conjuncts correct |
| **Crop Names** | ऊस, सोयाबीन, हरभरा, डाळिंब, ज्वारी, बाजरी, गहू | **PASS** — Authentic agricultural Marathi |

---

## 5. Automated Verification Evidence

```bash
# 1. Static Analysis
cd apps/mobile && dart analyze
# Result: Analyzing mobile... No issues found!

# 2. Chrome Test Suite across Responsive Router & Layout
flutter test --platform chrome
# Result: 90/90 tests passed

# 3. Web Release Build Verification
flutter build web --no-tree-shake-icons
# Result: Compiling lib/main.dart to JavaScript... Success (18.5s)
```

---

## 6. Conclusion

CropNet AI delivers an intuitive, accessible responsive web experience. Farmers accessing the prototype on standard Android/iOS mobile browsers experience lightweight single-column layouts and touch-friendly controls, while desktop users benefit from expansive multi-column dashboards and side-by-side analytical views. Zero layout overflow defects remain in the consolidated build.
