# CropNet AI — Source ID Discrepancy & Alias Reconciliation Report (Phase 5.0.1)

**Audit Target:** Benchmark Dataset (`benchmark_dataset.json`), Source Mappings, Audit Reports, and Supabase Production Database (`agricultural_knowledge_sources`)  
**Audit Status:** Complete & Reconciled  
**Cardinal Rule:** No silent renaming. Aliases are only mapped to canonical IDs if the underlying document is demonstrably the same entity.  

---

## 1. Discrepancy & Alias Inventory

During the Phase 4 audit and Phase 5 benchmark creation, several source IDs and aliases appeared across historical markdown reports, drafts, and initial benchmark JSON definitions. The table below audits every discrepancy against the 12 canonical IDs registered in Supabase:

| Referenced String / Alias | Location Found | Canonical Supabase Source ID | Underlying Document Entity Match | Audit Finding & Reconciliation Action |
|---|---|---|---|---|
| `icar_cicr_cotton_2021` | `agricultural_reference_document_audit.md`, Early benchmark draft | `icar_cicr_cotton_2022` | **YES** (ICAR-CICR Nagpur Cotton Production Technology) | **VALIDATED ALIAS:** 2021 represented a provisional citation year during Phase 4 scoping. The registered database entry is officially `icar_cicr_cotton_2022`. Benchmark references updated to `icar_cicr_cotton_2022`. |
| `icar_iisr_soybean_2021` | `agricultural_reference_document_audit.md`, Early benchmark draft | `icar_iisr_soybean_2022` | **YES** (ICAR-IISR Indore Soybean Production Technology) | **VALIDATED ALIAS:** Early drafting cited 2021; the production record was formally registered as `icar_iisr_soybean_2022`. Benchmark references updated to canonical ID. |
| `icar_iirb_barley_wheat_2021` | Early benchmark draft | `icar_iiwbr_wheat_2022` | **YES** (ICAR-IIWBR Karnal Peninsular Wheat Guide) | **TYPOGRAPHIC CORRECTION:** "iirb" was a typo for "iiwbr" (Indian Institute of Wheat and Barley Research). Publication registered as `icar_iiwbr_wheat_2022`. Canonical ID mapped. |
| `icar_dgr_groundnut_2022` | Early benchmark draft (`AGRI-BENCH-021`) | `mpkv_pop_2023` | **NO** (Different Issuing Organizations) | **UNREGISTERED SOURCE REJECTED:** ICAR Directorate of Groundnut Research (DGR) is not one of the 12 registered sources in Supabase. Groundnut sowing criteria (75–100 mm rainfall) in Maharashtra are officially established by MPKV Package of Practices (`mpkv_pop_2023`). Mapped to `mpkv_pop_2023`. |
| `fao_ecocrop` | Phase 4 summary text, early draft | *None (Unregistered)* | **NO** (Global Database) | **UNREGISTERED SOURCE EXCLUDED:** FAO Ecocrop was used as a global sanity-check tool in Phase 4 scoping. It is NOT present in Supabase `agricultural_knowledge_sources`. Excluded from benchmark citations. |
| `tnau_agritech_portal` | Phase 4 summary text, early draft | *None (Unregistered)* | **NO** (Tamil Nadu State University) | **UNREGISTERED SOURCE EXCLUDED:** TNAU Agritech portal is an external state portal, not registered in CropNet’s Maharashtra-first knowledge base. Excluded from benchmark citations. |
| `mpkv_research_2023` vs `mpkv_pop_2023` | `AGRI-BENCH-001`, `003` | Both exist in Supabase | **DISTINCT DOCUMENTS** | **CANONICAL DISTINCTION RESTORED:** `mpkv_research_2023` is the 13-page Joint Agresco research release (69 discrete trials). General soil testing fertility standards (Available N < 280 kg/ha = Low; SOC < 0.50% = Low) originate from the comprehensive compendium `mpkv_pop_2023` (*कृषी दैनंदिनी*). Benchmark cases 001 and 003 updated to include `mpkv_pop_2023`. |

---

## 2. Canonical Source Verification Summary

The Supabase table `agricultural_knowledge_sources` contains exactly 12 records with the following primary keys:
1. `mpkv_research_2023`
2. `mpkv_pop_2023`
3. `icrisat_chickpea_2010`
4. `icar_nrcp_manage_2022`
5. `icar_nrcp_pomegranate_2021`
6. `iisr_brochure_glance`
7. `icar_iisr_sugarcane_2022`
8. `icar_cicr_cotton_2022`
9. `icar_iiwbr_wheat_2022`
10. `icar_iisr_soybean_2022`
11. `icar_iimr_millets_2022`
12. `icar_iipr_pulses_2022`

All benchmark test cases in `benchmark_dataset.json` and mappings in `gold_standard_source_mapping.md` now strictly use these exact 12 keys. No aliases or unregistered sources remain in the evaluation dataset.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/source_discrepancy_report.md
