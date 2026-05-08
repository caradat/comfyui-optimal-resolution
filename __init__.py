from .nodes import OptimalResolutionNode, load_models_data, NODE_DIR
from server import PromptServer
import json
import os
import aiohttp

NODE_CLASS_MAPPINGS = {
    "OptimalResolutionNode": OptimalResolutionNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OptimalResolutionNode": "Optimal Resolution"
}

WEB_DIRECTORY = "./js"

# Load data immediately at module import time
OptimalResolutionNode.models_data = load_models_data()

# Setup API Routes
server = PromptServer.instance

@server.routes.get("/optimal_resolution/models")
async def get_models_data(request):
    """Returns the configuration JSON to the frontend."""
    data = OptimalResolutionNode.models_data
    if not data:
        data = load_models_data()
    return aiohttp.web.json_response(data, status=200)

@server.routes.post("/optimal_resolution/calculate")
async def calculate_resolution_api(request):
    """Calculates resolution without executing the workflow."""
    try:
        body = await request.json()
        model_type = body.get("model_type", "Image")
        model = body.get("model", "SDXL Base")
        aspect_ratio = body.get("aspect_ratio", "1:1")
        multiple_of = body.get("multiple_of", 16)
        resolution = body.get("resolution", "Standard")
        
        data = OptimalResolutionNode.models_data
        if not data:
            data = load_models_data()

        w, h, text = OptimalResolutionNode.calculate_resolution_logic(
            model_type, model, aspect_ratio, resolution, data
        )

        return aiohttp.web.json_response({
            "width": w,
            "height": h,
            "resolution_text": text
        }, status=200)
    except Exception as e:
        print(f"[OptimalResolution] API Error: {e}")
        return aiohttp.web.json_response({"error": str(e)}, status=500)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']