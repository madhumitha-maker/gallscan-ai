from typing import Dict, Any, List
import numpy as np
import onnxruntime as ort
from app.config import settings, CLASS_NAMES, IDX_TO_LABEL, DISPLAY_NAMES
from app.models.schemas import ClassProbabilityItem

class ONNXPredictor:
    def __init__(self, model_path: str = None):
        path = model_path or str(settings.ONNX_MODEL_PATH)
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(path, sess_options, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict(self, input_batch: np.ndarray) -> Dict[str, Any]:
        """
        Runs inference on input batch of shape (1, 3, 224, 224).
        Returns top-1 class, confidence, top-3 classes, and all class probabilities.
        """
        ort_inputs = {self.input_name: input_batch}
        ort_outs = self.session.run([self.output_name], ort_inputs)
        logits = ort_outs[0][0]  # shape (9,)

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / np.sum(exp_logits)

        # Build probabilities mapping and top-3 items
        prob_dict: Dict[str, float] = {}
        all_items: List[ClassProbabilityItem] = []

        for idx, prob in enumerate(probabilities):
            raw_name = IDX_TO_LABEL.get(idx, f"Class_{idx}")
            display_name = DISPLAY_NAMES.get(raw_name, raw_name)
            prob_float = float(prob)
            prob_dict[raw_name] = prob_float
            all_items.append(
                ClassProbabilityItem(
                    class_id=idx,
                    raw_name=raw_name,
                    display_name=display_name,
                    probability=round(prob_float, 4),
                    percentage=round(prob_float * 100.0, 2)
                )
            )

        # Sort descending
        all_items_sorted = sorted(all_items, key=lambda x: x.probability, reverse=True)
        top_1 = all_items_sorted[0]
        top_3 = all_items_sorted[:3]

        return {
            "predicted_class": top_1.raw_name,
            "predicted_display_name": top_1.display_name,
            "confidence": top_1.probability,
            "top_1_item": top_1,
            "top_3_items": top_3,
            "class_probabilities": prob_dict
        }

# Global singleton predictor instance
onnx_predictor: ONNXPredictor = None

def get_onnx_predictor() -> ONNXPredictor:
    global onnx_predictor
    if onnx_predictor is None:
        onnx_predictor = ONNXPredictor()
    return onnx_predictor
