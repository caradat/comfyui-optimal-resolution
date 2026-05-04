import json
import os
import math

# Determine the path to the extension directory
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(NODE_DIR, "models_data.json")

def load_models_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[OptimalResolution] Error loading models_data.json: {e}")
        return {}

class OptimalResolutionNode:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(s):
        # Load data to get all possible values for validation
        data = load_models_data()
        
        # Collect all possible models from both Image and Video
        all_models = ["Loading..."]  # Default placeholder
        if data.get("model_types"):
            all_models.extend(data["model_types"].get("Image", []))
            all_models.extend(data["model_types"].get("Video", []))
        
        # Collect all possible modes from all models
        all_modes = ["Standard"]  # Default placeholder
        if data.get("mode_options"):
            for model_name, mode_info in data["mode_options"].items():
                if isinstance(mode_info, dict) and "values" in mode_info:
                    all_modes.extend(mode_info["values"])
        
        # Remove duplicates while preserving order
        all_models = list(dict.fromkeys(all_models))
        all_modes = list(dict.fromkeys(all_modes))
        
        return {
            "required": {
                "model_type": (["Image", "Video"],),
                "model": (all_models,),
                "mode": (all_modes,),
                "aspect_ratio": (data.get("mode_aspect_ratios", {}).get("default", ["1:1", "21:9", "9:21", "16:9", "9:16", "5:4", "4:5", "4:3", "3:4", "3:2", "2:3"]),),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolution"
    CATEGORY = "image"
    
    models_data = None

    @staticmethod
    def calculate_resolution_logic(model_type, model, aspect_ratio, mode, data):
        """
        Core logic extracted for use by both the Node and the API Endpoint.
        """
        if not data:
            return 1024, 1024, "Error: No Data"

        # Get multiple_of value for the model, default to 16
        multiple_of = data.get("multiple_of", {}).get(model, 16)

        width, height = 1024, 1024
        display_text = "1024 x 1024"

        try:
            # Parse Aspect Ratio
            ar_parts = aspect_ratio.split(':')
            ar_w, ar_h = int(ar_parts[0]), int(ar_parts[1])
            ratio = ar_w / ar_h

            # 1. Handle Exact Resolutions (e.g., Qwen Fixed)
            exact_res = data.get("exact_resolutions", {}).get(model, {})
            if mode == "Fixed (exact)" and aspect_ratio in exact_res:
                w, h = exact_res[aspect_ratio]
                width = round(w / multiple_of) * multiple_of
                height = round(h / multiple_of) * multiple_of
                display_text = f"{width} x {height}"
                return width, height, display_text
            
            # Fallback for exact mode when aspect ratio is not available
            if mode == "Fixed (exact)" and model in ["Qwen Image", "Ernie Image"]:
                # Get the first available aspect ratio for this model in exact mode
                mode_aspect_ratios = data.get("mode_aspect_ratios", {})
                available_ratios = mode_aspect_ratios.get(model, {}).get("Fixed (exact)", [])
                if available_ratios:
                    fallback_ratio = available_ratios[0]
                    if fallback_ratio in exact_res:
                        w, h = exact_res[fallback_ratio]
                        width = round(w / multiple_of) * multiple_of
                        height = round(h / multiple_of) * multiple_of
                        display_text = f"{width} x {height} (using {fallback_ratio} fallback)"
                        return width, height, display_text

            # 2. Determine Base Area
            base_res = data.get("base_resolutions", {}).get(model, 1024)
            base_area = base_res * base_res

            # Handle Area mode with specific resolution selection
            if mode.startswith("Area: "):
                # Extract resolution name from mode string (e.g., "1024² (1.0MP)" from "Area: 1024² (1.0MP)")
                resolution_name = mode[6:]  # Remove "Area: " prefix
                area_resolutions = data.get("mode_resolutions", {}).get("Area", {})
                if resolution_name in area_resolutions:
                    base_area = area_resolutions[resolution_name]["area"]
            else:
                # Handle other modes (SDXL, Qwen, etc.)
                mode_resolutions = data.get("mode_resolutions", {}).get(model, {})
                if mode in mode_resolutions:
                    base_area = mode_resolutions[mode]["area"]

            # 3. Calculate Dimensions from Area and Ratio
            h_float = math.sqrt(base_area / ratio)
            w_float = h_float * ratio

            # 4. Round to multiple_of
            width = round(w_float / multiple_of) * multiple_of
            height = round(h_float / multiple_of) * multiple_of

            # Ensure minimums
            if width < multiple_of:
                width = multiple_of
            if height < multiple_of:
                height = multiple_of

            display_text = f"{width} x {height}"

        except Exception as e:
            display_text = f"Error: {str(e)}"
            width, height = 1024, 1024

        return width, height, display_text

    def get_resolution(self, model_type, model, aspect_ratio, mode):
        data = self.__class__.models_data
        if not data:
            data = load_models_data()
            self.__class__.models_data = data

        # Validate mode for model
        valid_modes = data.get("mode_options", {}).get(model, {}).get("values", [])
        if valid_modes and mode not in valid_modes:
            mode = "Standard"  # fallback

        w, h, text = self.calculate_resolution_logic(
            model_type, model, aspect_ratio, mode, data
        )

        return {
            "ui": {"resolution_text": [text]}, 
            "result": (w, h)
        }