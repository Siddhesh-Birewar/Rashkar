from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.registry import DatasetRegisterRequest, DatasetRegistryResponse
from backend.app.services.registry_service import RegistryService

router = APIRouter()

@router.get("/", response_model=List[DatasetRegistryResponse])
def list_registered_datasets(db: Session = Depends(get_db)):
    """List all registered datasets with provenance and status."""
    return RegistryService.list_datasets(db)

@router.get("/{dataset_id}", response_model=DatasetRegistryResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = RegistryService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return dataset

@router.post("/", response_model=DatasetRegistryResponse)
def register_dataset(request: DatasetRegisterRequest, db: Session = Depends(get_db)):
    return RegistryService.register_dataset(db, request)
