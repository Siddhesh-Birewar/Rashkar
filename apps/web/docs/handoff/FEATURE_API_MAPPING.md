# CropNet AI — Feature ↔ API Mapping

Every current Flutter screen and its real backend endpoint(s). “Auth” = Bearer
token required.

| Screen / workflow | Current Flutter file | Endpoint(s) |
|---|---|---|
| Login | `features/auth/presentation/login_screen.dart` | Supabase Auth (client SDK) |
| Register | `features/auth/presentation/register_screen.dart` | Supabase Auth (client SDK) |
| Farms dashboard | `main.dart` → `MyFarmsDashboard` | `GET /api/v1/farms` |
| Add/Edit farm + boundary | `main.dart` → `AddEditFarmScreen` | `POST /api/v1/farms`, `PUT /api/v1/farms/{id}` |
| Farm detail | `main.dart` → `FarmDetailScreen` | `GET /api/v1/farms/{id}`, `DELETE /api/v1/farms/{id}` |
| Soil Intelligence | `main.dart` → `SoilIntelligenceReportScreen` | `POST /api/v1/farms/{id}/soil/analyse`, `GET /api/v1/farms/{id}/soil`, `GET .../soil/history` |
| Soil Lab upload | `features/soil/presentation/screens/soil_report_upload_screen.dart` | `POST /api/v1/farms/{id}/soil-reports/upload` |
| Soil Lab review | `.../soil_report_review_screen.dart` | `GET .../soil-reports/{rid}`, `PATCH .../measurements/{mid}`, `POST .../confirm` |
| Soil Lab history | `.../soil_report_history_screen.dart` | `GET .../soil-reports` |
| Lab vs SoilGrids comparison | `.../widgets/lab_vs_soilgrids_comparison_widget.dart` | derived from the soil profile + confirmed report (no extra call) |
| Weather | `main.dart` → `WeatherClimateReportScreen` | `GET .../weather/current`, `.../forecast`, `.../climate-summary` |
| Crop catalogue | `main.dart` → `CropCatalogScreen` | `GET /api/v1/crops` |
| Crop detail | `main.dart` → `CropDetailScreen` | `GET /api/v1/crops/{id}`, `.../requirements`, `.../sources` |
| Advisory | `core/router/advisory_screen.dart` | `POST /api/v1/agriculture/evaluate-farm`, `.../explain-decision`, `.../follow-up`, `.../conversation`, `GET .../decision/{id}` |
| History | `core/router/history_screen.dart` | local session history + `GET /api/v1/farms` |
| Farm Health dashboard | `features/farm_health/presentation/screens/farm_health_dashboard_screen.dart` | `GET /api/v1/farms/{id}/health-snapshot`, `POST .../invalidate` |
| Water workspace | `features/water/presentation/screens/water_workspace_screen.dart` | `.../water/sources`, `.../water/evaluation`, `.../water/reports/*` |
| Satellite vegetation | `features/satellite/presentation/screens/satellite_vegetation_screen.dart` | `POST .../satellite/sync`, `GET .../satellite/latest`, `.../timeseries` |
| Government Schemes list | `features/schemes/presentation/screens/schemes_list_screen.dart` | `GET /api/v1/schemes`, `.../filters` |
| Scheme detail | `.../scheme_detail_screen.dart` | `GET /api/v1/schemes/{id}` |
| Schemes admin | `.../scheme_admin_screen.dart`, `.../scheme_editor_screen.dart` | `GET .../admin/status`, `POST/PUT/PATCH/DELETE /api/v1/schemes...`, `POST .../seed` |
| Crop Doctor | `features/agri_intelligence/.../agri_intelligence_screen.dart` (tab 0) | `POST /api/v1/crop-doctor/predict`, `GET .../status` |
| Heat Risk (manual) | same screen (tab 1) | `GET /api/v1/heat-risk/crops`, `POST .../crop`, `POST .../worker` |
| Heat Risk (farm) | same screen (farm section) | `POST /api/v1/heat-risk/farm/{id}` |
| Income (no UI yet) | — | `GET /api/v1/income/opportunities`, `POST .../match-opportunities`, `.../calculate-scenario`, `.../compare-opportunities` |

## Screens with no backend call

- Login/Register (Supabase SDK only).
- History (client session store).
- Static About/disclaimer screens.

## Backend features with no current screen

- `POST /api/v1/agriculture/follow-up` (used indirectly via conversation).
- `GET /api/v1/farms/decision/{decision_id}`.
- `GET /api/v1/soil/providers`, `.../layers`, `.../pilot-coverage`, `.../report-status`.
- Income endpoints (backend-only).
- `POST /api/v1/crops/seed` (ops).
- PMFBY module (no endpoint exposed).
