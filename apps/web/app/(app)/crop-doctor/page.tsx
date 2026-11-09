import { AlertTriangle, Camera, Gauge, Image, Microscope, ShieldAlert } from "lucide-react";
import { UploadWorkflow } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function CropDoctorPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Image assessment"
      title="Crop Doctor"
      description="Photograph a visible symptom and receive a result only when the diagnosis service can process it."
      icon={Microscope}
      steps={[
        "Add a clear crop image",
        "Confirm crop and symptom context",
        "Review result, confidence and limits",
      ]}
      sections={[
        {
          title: "Image quality",
          description: "The leaf or affected area should be clear, close and well lit.",
          icon: Image,
          status: "Not checked",
        },
        {
          title: "Disease prediction",
          description: "No disease label is shown before the model returns a valid response.",
          icon: Microscope,
          status: "Unavailable",
        },
        {
          title: "Confidence",
          description: "Confidence is displayed with model scope and limitations.",
          icon: Gauge,
          status: "Unavailable",
        },
        {
          title: "Model unavailable",
          description: "You will see a clear retry state if the diagnosis model cannot respond.",
          icon: ShieldAlert,
          status: "Protected",
        },
        {
          title: "Unclear image",
          description: "Retake guidance appears instead of an artificial prediction.",
          icon: AlertTriangle,
          status: "Protected",
        },
        {
          title: "Camera guidance",
          description: "Include one close photo and one wider crop-context photo when possible.",
          icon: Camera,
          status: "Ready",
        },
      ]}
    >
      <UploadWorkflow />
    </IntelligenceWorkspace>
  );
}
