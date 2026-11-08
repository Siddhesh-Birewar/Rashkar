from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest

def register_pending_institutional_datasets():
    db = SessionLocal()
    try:
        # Y-10: CCE Yield Records
        y10 = DatasetRegisterRequest(
            dataset_id="Y-10-CCE-YIELD",
            dataset_name="Maharashtra Crop Cutting Experiments (CCE / DGCES) Plot Yield Records",
            publisher="Maharashtra State Department of Agriculture / DES",
            classification="institutional_request",
            format="tabular",
            temporal_coverage="Awaiting access authorization",
            spatial_coverage="Maharashtra Target AEZs",
            spatial_resolution="Plot Level / Field Cut",
            licence="Government of Maharashtra Official Data Sharing Agreement",
            provenance_metadata={
                "status": "access_pending",
                "ml_gate_policy": "Strict hard gate. Supervised farm-level yield prediction models cannot be trained until genuine CCE records are provided and verified.",
                "request_template": "Formal submission to Commissionerate of Agriculture, Pune"
            }
        )
        RegistryService.register_dataset(db, y10)

        # Y-12: CROPSAP Pest Surveillance
        y12 = DatasetRegisterRequest(
            dataset_id="Y-12-CROPSAP-OBS",
            dataset_name="CROPSAP / HORTSAP Maharashtra Pest Surveillance Records",
            publisher="ICAR-NCIPM & Maharashtra Agriculture Department",
            classification="institutional_request",
            format="tabular",
            temporal_coverage="Historical surveillance records",
            spatial_coverage="Maharashtra Multi-Crop Surveillance",
            spatial_resolution="Village / Field Scout Point",
            licence="Institutional Data Agreement",
            provenance_metadata={
                "status": "access_pending",
                "ml_gate_policy": "Supervised pest/disease outbreak prediction disabled. Weather-conducive watch warnings active in v1."
            }
        )
        RegistryService.register_dataset(db, y12)

        # H-08: Maharashtra Worker Heat Validation Dataset
        h08 = DatasetRegisterRequest(
            dataset_id="H-08-WBGT-PILOT",
            dataset_name="Maharashtra Worker Heat Validation Field Study Dataset",
            publisher="Rashkar Research & Academic Field Partner (MPKV / KVK Narayangaon)",
            classification="pilot_collection",
            format="tabular",
            temporal_coverage="Summer 2026/2027 Field Campaign",
            spatial_coverage="Pune Pilot Talukas (Baramati, Indapur, Maval, Mulshi)",
            spatial_resolution="Field Sensor Point",
            licence="Internal Research Consortium Agreement",
            provenance_metadata={
                "status": "pilot_collection_pending",
                "instrument": "QuestTemp 34 / Kestrel 5400 Heat Stress Tracker",
                "safety_restriction": "Until validation is completed, automatic prescriptive work-rest schedules and work stoppages are suppressed."
            }
        )
        RegistryService.register_dataset(db, h08)
        print("Registered pending institutional and pilot datasets (Y-10, Y-12, H-08) with explicit access-pending flags.")
    finally:
        db.close()

if __name__ == "__main__":
    register_pending_institutional_datasets()
