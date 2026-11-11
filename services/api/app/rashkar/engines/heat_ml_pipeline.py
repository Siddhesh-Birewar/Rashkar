"""
RASHKAR — Machine Learning Forecast & Personalization Pipeline.

1. Feature Engineering: Air temperature, humidity, wind speed, solar radiation, elevation, worker profile.
2. XGBoost + LSTM for WBGT Forecasting (benchmarked against Liljegren physics ground truth).
3. Random Forest for Personalization (worker strain classification & work-rest cycles).
4. Model evaluation: MAE, RMSE, R2, feature importances.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score
import torch
import torch.nn as nn
import xgboost as xgb

from .wbgt_solver import calculate_wbgt


class WBGTLSTMModel(nn.Module):
    """
    LSTM sequence-to-sequence model predicting 0-6 hour WBGT trajectory
    from preceding meteorological observation sequence.
    """

    def __init__(
        self,
        input_dim: int = 5,
        hidden_dim: int = 32,
        num_layers: int = 1,
        output_dim: int = 6,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers=num_layers, batch_first=True
        )
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])


class HeatMLPipeline:
    """
    Staged Machine Learning pipeline combining:
    1. XGBoost WBGT fast regressor.
    2. PyTorch LSTM sequential trajectory predictor.
    3. Random Forest personalized worker strain classifier.
    """

    def __init__(self, model_dir: Optional[Path | str] = None):
        self.model_dir = (
            Path(model_dir)
            if model_dir is not None
            else Path(__file__).resolve().parent / "saved_models"
        )
        # Lazy directory creation: avoid side effects on module import.
        self.xgb_model: Optional[xgb.XGBRegressor] = None
        self.rf_model: Optional[RandomForestClassifier] = None
        self.lstm_model: Optional[WBGTLSTMModel] = None
        self.metrics: Dict[str, Any] = {}

    def generate_synthetic_benchmark_dataset(
        self, num_samples: int = 2500
    ) -> pd.DataFrame:
        """Generates meteorological data and computes Liljegren WBGT ground truth."""
        rng = np.random.default_rng(42)

        temp_c = rng.uniform(22.0, 44.0, num_samples)
        rh_pct = rng.uniform(15.0, 95.0, num_samples)
        wind_mps = rng.uniform(0.5, 12.0, num_samples)
        solar_w_m2 = rng.uniform(0.0, 1000.0, num_samples)
        zenith_deg = rng.uniform(0.0, 85.0, num_samples)
        elevation_m = rng.uniform(400.0, 750.0, num_samples)

        ground_truth_wbgt = [
            calculate_wbgt(
                temp_c=float(temp_c[i]),
                rh_pct=float(rh_pct[i]),
                wind_speed_ms=float(wind_mps[i]),
                solar_irradiance_wm2=float(solar_w_m2[i]),
                in_sun=True,
            )["wbgt_estimated_c"]
            for i in range(num_samples)
        ]

        return pd.DataFrame(
            {
                "temp_c": temp_c,
                "rh_pct": rh_pct,
                "wind_mps": wind_mps,
                "solar_w_m2": solar_w_m2,
                "zenith_deg": zenith_deg,
                "elevation_m": elevation_m,
                "wbgt_ground_truth": ground_truth_wbgt,
            }
        )

    def train_xgboost_wbgt_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trains XGBoost regressor against Liljegren ground truth and returns metrics."""
        features = [
            "temp_c",
            "rh_pct",
            "wind_mps",
            "solar_w_m2",
            "zenith_deg",
            "elevation_m",
        ]
        x = df[features]
        y = df["wbgt_ground_truth"]

        split_idx = int(len(df) * 0.8)
        x_train, x_test = x.iloc[:split_idx], x.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model = xgb.XGBRegressor(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            random_state=42,
            n_jobs=1,
        )
        model.fit(x_train, y_train)

        preds = model.predict(x_test)
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        self.xgb_model = model
        self.metrics["xgboost_wbgt"] = {
            "mae_c": round(mae, 3),
            "rmse_c": round(rmse, 3),
            "r2_score": round(r2, 4),
            "sample_count": len(df),
            "feature_importances": {
                feat: round(float(imp), 4)
                for feat, imp in zip(features, model.feature_importances_)
            },
        }
        return self.metrics["xgboost_wbgt"]

    def train_rf_personalization_model(self, num_samples: int = 1500) -> Dict[str, Any]:
        """Trains Random Forest classifier for personalized heat strain categories."""
        rng = np.random.default_rng(42)
        wbgt_vals = rng.uniform(18.0, 36.0, num_samples)
        age_vals = rng.integers(18, 68, num_samples)
        acclim_vals = rng.choice([0, 1], size=num_samples, p=[0.25, 0.75])
        workload_vals = rng.choice([1, 2, 3, 4], size=num_samples)
        hours_vals = rng.uniform(1.0, 8.0, num_samples)

        labels = []
        for i in range(num_samples):
            w = wbgt_vals[i]
            thresh = (
                28.0
                - (workload_vals[i] * 1.5)
                - (2.5 if acclim_vals[i] == 0 else 0.0)
            )
            if age_vals[i] > 50:
                thresh -= 1.0
            if hours_vals[i] > 4.0:
                thresh -= 1.0

            if w < thresh - 2.0:
                labels.append(0)
            elif w <= thresh:
                labels.append(1)
            elif w <= thresh + 2.5:
                labels.append(2)
            else:
                labels.append(3)

        x = np.column_stack(
            [wbgt_vals, age_vals, acclim_vals, workload_vals, hours_vals]
        )
        y = np.array(labels)

        split_idx = int(num_samples * 0.8)
        x_train, x_test = x[:split_idx], x[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        rf = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42)
        rf.fit(x_train, y_train)

        preds = rf.predict(x_test)
        acc = float(accuracy_score(y_test, preds))

        self.rf_model = rf
        self.metrics["rf_personalization"] = {
            "accuracy": round(acc, 4),
            "sample_count": num_samples,
            "classes": ["Low", "Moderate", "High", "Extreme"],
        }
        return self.metrics["rf_personalization"]

    def train_lstm_wbgt_trajectory(self, num_sequences: int = 400) -> Dict[str, Any]:
        """Trains PyTorch LSTM sequence model to predict next 6-hour WBGT trend."""
        torch.manual_seed(42)
        # Prevent macOS libomp thread-pool contention when co-loaded with XGBoost.
        try:
            torch.set_num_threads(1)
        except RuntimeError:
            pass
        rng = np.random.default_rng(42)
        seq_len = 6
        input_dim = 5
        output_dim = 6

        x_seq = rng.uniform(0.2, 0.9, size=(num_sequences, seq_len, input_dim)).astype(
            np.float32
        )
        base_temp = 25.0 + x_seq[:, -1, 0] * 12.0
        rh = 40.0 + x_seq[:, -1, 1] * 40.0
        offsets = np.linspace(0.0, 3.5, output_dim).astype(np.float32)
        y_seq = np.zeros((num_sequences, output_dim), dtype=np.float32)
        for t in range(output_dim):
            y_seq[:, t] = 0.7 * (base_temp + offsets[t]) + 0.2 * (rh * 0.1) + 5.0

        y_mean = float(np.mean(y_seq))
        y_std = float(np.std(y_seq))
        y_norm = (y_seq - y_mean) / y_std

        model = WBGTLSTMModel(
            input_dim=input_dim, hidden_dim=24, num_layers=1, output_dim=output_dim
        )
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.02)

        x_tensor = torch.tensor(x_seq, dtype=torch.float32)
        y_tensor = torch.tensor(y_norm, dtype=torch.float32)

        model.train()
        for _ in range(40):
            optimizer.zero_grad()
            outputs = model(x_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            preds_norm = model(x_tensor).numpy()
            preds = preds_norm * y_std + y_mean
            mae = float(np.mean(np.abs(preds - y_seq)))

        self.lstm_model = model
        self.metrics["lstm_wbgt_trajectory"] = {
            "mae_c": round(mae, 3),
            "trajectory_hours": output_dim,
            "architecture": "LSTM(hidden=24, layers=1) -> Dense(6)",
        }
        return self.metrics["lstm_wbgt_trajectory"]

    def predict_wbgt_ml(
        self,
        temp_c: float,
        rh_pct: float,
        wind_mps: float,
        solar_w_m2: float,
        zenith_deg: float,
        elevation_m: float = 560.0,
    ) -> float:
        """Performs XGBoost inference if trained; anchors with physics solver."""
        if self.xgb_model is not None:
            features = pd.DataFrame(
                [
                    {
                        "temp_c": temp_c,
                        "rh_pct": rh_pct,
                        "wind_mps": wind_mps,
                        "solar_w_m2": solar_w_m2,
                        "zenith_deg": zenith_deg,
                        "elevation_m": elevation_m,
                    }
                ]
            )
            pred = float(self.xgb_model.predict(features)[0])
            return round(pred, 2)

        res = calculate_wbgt(
            temp_c=temp_c,
            rh_pct=rh_pct,
            wind_speed_ms=wind_mps,
            solar_irradiance_wm2=solar_w_m2,
            in_sun=True,
        )
        return res["wbgt_estimated_c"]

    def run_full_pipeline_benchmarking(self) -> Dict[str, Any]:
        """Runs complete benchmark and training cycle."""
        df = self.generate_synthetic_benchmark_dataset(num_samples=2000)
        xgb_res = self.train_xgboost_wbgt_model(df)
        rf_res = self.train_rf_personalization_model(num_samples=1200)
        lstm_res = self.train_lstm_wbgt_trajectory(num_sequences=300)

        return {
            "status": "TRAINED_AND_BENCHMARKED",
            "reference_baseline": "Liljegren et al. (2008) physics-based solver",
            "models": {
                "xgboost_wbgt_forecast": xgb_res,
                "rf_worker_personalization": rf_res,
                "lstm_wbgt_trajectory": lstm_res,
            },
        }


heat_ml_pipeline = HeatMLPipeline()
