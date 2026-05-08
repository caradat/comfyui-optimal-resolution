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
        models_data = data.get("models_data", {})
        for model_name, model_info in models_data.items():
            mode_info = model_info.get("resolution_options", {})
            if isinstance(mode_info, dict) and "values" in mode_info:
                all_modes.extend(mode_info["values"])
        
        # Remove duplicates while preserving order
        all_models = list(dict.fromkeys(all_models))
        all_modes = list(dict.fromkeys(all_modes))
        
        # Build aspect_ratio options
        # Start with default if available
        aspect_ratios = data.get("aspect_ratios", {}).get("default", ["1:1", "21:9", "9:21", "16:9", "9:16", "5:4", "4:5", "4:3", "3:4", "3:2", "2:3"])
        
        # If model is specified and uses 'Fixed (exact)', get aspect ratios from exact_resolutions
        # Since we can't access model value here at class level, we return the default
        # The actual dynamic selection will be handled in the widget frontend
        
        return {
            "required": {
                "model_type": (["Image", "Video"],),
                "model": (all_models,),
                "resolution": (all_modes,),
                "aspect_ratio": (aspect_ratios,),
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

        width, height = 1024, 1024
        display_text = "1024 x 1024"

        try:
            # Parse Aspect Ratio - extract numeric parts before any parentheses
            # Handle cases like "16:9 (720p)" by taking only the part before parentheses
            base_aspect = aspect_ratio.split(' (')[0] if ' (' in aspect_ratio else aspect_ratio
            ar_parts = base_aspect.split(':')
            ar_w, ar_h = int(ar_parts[0]), int(ar_parts[1])
            ratio = ar_w / ar_h

            # Get model-specific data, falling back to defaults
            model_data = data.get("models_data", {}).get(model, data.get("models_data", {}).get("default", {}))
            
            # Get multiple_of value for the model, default to 16
            multiple_of = model_data.get("multiple_of", 16)
            
            # 1. Handle Exact Resolutions (e.g., Qwen Fixed)
            model_info = data.get("models_data", {}).get(model, {})
            exact_res = model_info.get("exact_resolutions", {})
            if mode == "Fixed (exact)" and aspect_ratio in exact_res:
                w, h = exact_res[aspect_ratio]
                width = round(w / multiple_of) * multiple_of
                height = round(h / multiple_of) * multiple_of
                display_text = f"{width} x {height}"
                return width, height, display_text
            
            # Fallback for exact mode when aspect ratio is not available
            if mode == "Fixed (exact)" and "exact_resolutions" in model_info:
                # Get the first available aspect ratio for this model in exact mode
                available_ratios = list(exact_res.keys())
                if available_ratios:
                    fallback_ratio = available_ratios[0]
                    w, h = exact_res[fallback_ratio]
                    width = round(w / multiple_of) * multiple_of
                    height = round(h / multiple_of) * multiple_of
                    display_text = f"{width} x {height} (using {fallback_ratio} fallback)"
                    return width, height, display_text

            # 2. Determine Base Area
            base_res = model_data.get("base_resolution", 1024)
            base_area = base_res * base_res

            # Handle Area mode with specific resolution selection
            if mode.startswith("Area: "):
                # Extract resolution name from mode string (e.g., "1024² (1.0MP)" from "Area: 1024² (1.0MP)")
                resolution_name = mode[6:]  # Remove "Area: " prefix
                area_resolutions = data.get("resolutions", {})
                if resolution_name in area_resolutions:
                    base_area = area_resolutions[resolution_name]["area"]

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

    def get_resolution(self, model_type, model, aspect_ratio, resolution):
        data = self.__class__.models_data
        if not data:
            data = load_models_data()
            self.__class__.models_data = data

        # Validate resolution for model
        model_data = data.get("models_data", {}).get(model, data.get("models_data", {}).get("default", {}))
        valid_modes = model_data.get("resolution_options", {}).get("values", [])
        if valid_modes and resolution not in valid_modes:
            resolution = "Standard"  # fallback

        w, h, text = self.calculate_resolution_logic(
            model_type, model, aspect_ratio, resolution, data
        )

        return {
            "ui": {"resolution_text": [text]}, 
            "result": (w, h)
        }