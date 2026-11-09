# 🌱 Crop Doctor AI

> An intelligent, full-stack plant pathology assistant designed to help farmers instantly identify crop leaf diseases from photos and receive actionable treatment recommendations.

---

## 🚀 Features

* **Instant Disease Diagnostics:** Powered by a pre-trained MobileNetV2 deep learning model (`neghani/plantvillage-mobilenetv2`) fine-tuned on plant health datasets.
* **Farmer-Friendly Web Interface:** A clean, responsive, green-themed UI built with Tailwind CSS featuring a drag-and-drop image uploader and visual confidence score meters.
* **Actionable Treatment Advice:** Automatically provides step-by-step prevention and treatment guidelines based on the detected diagnosis.
* **Local & Remote Accessibility:** Runs locally on any laptop with FastAPI and can be securely exposed to remote networks or mobile clients using tools like `ngrok`.

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Uvicorn, TensorFlow / Keras
* **Inference Model:** `neghani/plantvillage-mobilenetv2` (PlantVillage dataset)
* **Frontend:** HTML5, Tailwind CSS, JavaScript (Fetch API, FontAwesome)
* **Version Control:** Git & GitHub

---

## 📁 Project Architecture

```text
crop-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point & CORS configuration
│   ├── inference.py     # MobileNetV2 image preprocessing & model prediction logic
│   └── advice.py        # Disease treatment & prevention recommendations dictionary
│
├── venv/                # Python virtual environment (ignored in git)
├── index.html           # Frontend web user interface
└── README.md            # Project documentation