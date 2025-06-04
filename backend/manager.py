import os
import torch
from ultralytics import YOLO
import logging
from .Models.models_model import Model as ModelDB


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.loaded_models = {}
        logger.info("Central ModelManager is initialized.")

    def get_model(self, model_id):
        try:
            model_id = int(model_id)
        except (ValueError, TypeError):
            return None

        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        model_record = ModelDB.query.get(model_id)
        if not model_record or not model_record.model_path:
            return None

        absolute_path = os.path.join(PROJECT_ROOT, model_record.model_path)
        if not os.path.exists(absolute_path):
            logger.error(f"Model file not found at: '{absolute_path}'")
            return None

        try:
            model = YOLO(absolute_path)
            if torch.cuda.is_available():
                model.to('cuda')
            self.loaded_models[model_id] = model
            logger.info(f"Loaded and cached model ID {model_id} from {absolute_path}.")
            return model
        except Exception as e:
            logger.error(f"Failed to load model from '{absolute_path}': {e}")
            return None


model_manager = ModelManager()