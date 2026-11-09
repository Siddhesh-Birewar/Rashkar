from fastapi import FastAPI, File, UploadFile
from app.advice import PREVENTION_TIPS
from app.inference import get_prediction

app = FastAPI(title="Crop Doctor API", version="1.0")

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware  # <-- Import this
from app.advice import PREVENTION_TIPS
from app.inference import get_prediction

app = FastAPI(title="Crop Doctor API", version="1.0")

# <-- Add these lines below:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/predict")
async def predict_disease(file: UploadFile = File(...)):
  # Read the image sent by the user
  image_bytes = await file.read()

  # Get prediction from inference.py
  result = get_prediction(image_bytes)
  label = result["label"]
  confidence = result["confidence"]

  # Fetch advice (fallback to a generic message if label isn't in dictionary)
  tips = PREVENTION_TIPS.get(
      label, ["Monitor plant regularly and maintain good sanitation."]
  )
  is_healthy = "healthy" in label.lower()

  return {
      "filename": file.filename,
      "diagnosis": label,
      "confidence": f"{confidence}%",
      "is_healthy": is_healthy,
      "actionable_advice": tips,
  }