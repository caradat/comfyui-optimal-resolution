import json
import os
import math

from comfy_api.latest import ComfyExtension, io, ui

# Determine the path to the extension directory
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(NODE_DIR, "data")

# Cache for loaded data
_models_data_cache = None
_aspect_ratios_data = None
_resolutions_data = None


def _load_json_file(filepath):
    """Safely load a JSON file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[OptimalResolution] Error loading {filepath}: {e}")
        return {}

def _load_model_file(model_name, model_type):
    """Load a single model's configuration file."""
    # Convert model name to filename (replace spaces with underscores)
    filename = model_name.replace(' ', '_') + '.json'
    # Determine the subdirectory based on model type
    subdir = 'image' if model_type == 'Image' else 'video'
    filepath = os.path.join(DATA_DIR, subdir, filename)
    model_data = _load_json_file(filepath)
    print(f"[OptimalResolution] Loaded model '{model_name}' from {filepath}: {model_data}")
    return model_data

def load_models_data():
    """
    Load the complete models data structure from the modular files in the `data/` directory.
    This function aggregates data from:
    - `data/model_types.json` (or the model_types list in the old file)
    - `data/resolutions.json`
    - `data/aspect_ratios.json`
    - Individual model files in `data/image/` and `data/video/`
    
    Returns a dictionary with the same structure as the old `models_data.json`.
    """
    global _models_data_cache, _aspect_ratios_data, _resolutions_data
    
    # Return cached data if available
    if _models_data_cache is not None:
        return _models_data_cache
    
    # Initialize the data structure
    data = {
        "model_types": {"Image": [], "Video": []},
        "models_data": {},
        "resolutions": {},
        "aspect_ratios": {}
    }
    
    # Load the main configuration files
    _resolutions_data = _load_json_file(os.path.join(DATA_DIR, "resolutions.json"))
    _aspect_ratios_data = _load_json_file(os.path.join(DATA_DIR, "aspect_ratios.json"))
    
    data["resolutions"] = _resolutions_data
    data["aspect_ratios"] = _aspect_ratios_data
    
    # Dynamically discover models by scanning the image and video directories
    for model_type, subdir in {"Image": "image", "Video": "video"}.items():
        dir_path = os.path.join(DATA_DIR, subdir)
        if not os.path.exists(dir_path):
            print(f"[OptimalResolution] Directory not found: {dir_path}")
            continue
        
        # List all .json files in the directory
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                # Extract model name from filename (remove .json and replace underscores with spaces)
                model_name = filename[:-5].replace('_', ' ')
                
                # Add the model name to the model_types list
                data["model_types"][model_type].append(model_name)
                
                # Load the model's data
                model_data = _load_model_file(model_name, model_type)
                if model_data is None:
                    print(f"[OptimalResolution] Failed to load data for model: {model_name}")
                    continue
                # Use the model_name (from filename) as the key for consistency with the frontend
                data["models_data"][model_name] = model_data
    
    # Cache the result
    _models_data_cache = data
    return data

class OptimalResolutionNode(io.ComfyNode):
    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def define_schema(cls) -> io.Schema:
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
            if model_info is None:
                continue
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
        
        return io.Schema(
            node_id="OptimalResolutionNode",
            display_name="Optimal Resolution",
            category="image",
            inputs=[
                io.Combo.Input("model_type", options=["Image", "Video"], display_name="Model Type"),
                io.Combo.Input("model", options=all_models, display_name="Model"),
                io.Combo.Input("resolution", options=all_modes, display_name="Resolution"),
                io.Combo.Input("aspect_ratio", options=aspect_ratios, display_name="Aspect Ratio"),
            ],
            outputs=[
                io.Int.Output(display_name="width"),
                io.Int.Output(display_name="height"),
            ],
        )

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

            # Get model-specific data
            model_data = data.get("models_data", {}).get(model, {})
            if not model_data:
                print(f"[OptimalResolution] Model '{model}' not found, using default.")
                model_data = data.get("models_data", {}).get("default", {})
                if not model_data:
                    print("[OptimalResolution] Default model data is missing.")
                    model_data = {"base_resolution": 1024, "multiple_of": 16}
            
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

    @classmethod
    def execute(cls, model_type, model, aspect_ratio, resolution) -> io.NodeOutput:
        # Ensure models_data is loaded
        if not cls.models_data:
            cls.models_data = load_models_data()

        # Validate resolution for model
        model_data = cls.models_data.get("models_data", {}).get(model, cls.models_data.get("models_data", {}).get("default", {}))
        if model_data is None:
            print(f"[OptimalResolution] Model data is None for model: {model}")
            model_data = {}
        valid_modes = model_data.get("resolution_options", {}).get("values", [])
        if valid_modes and resolution not in valid_modes:
            resolution = "Standard"  # fallback

        w, h, text = cls.calculate_resolution_logic(
            model_type, model, aspect_ratio, resolution, cls.models_data
        )

        return io.NodeOutput(
            w, h,
            ui={"resolution_text": [text]}
        )