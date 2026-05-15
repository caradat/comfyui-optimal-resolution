from .nodes import OptimalResolutionNode, load_models_data, NODE_DIR
from .nodes import ComfyExtension, io
from server import PromptServer
import json
import os
import aiohttp


WEB_DIRECTORY = "./js"

# Load data immediately at module import time
OptimalResolutionNode.models_data = load_models_data()

class OptimalResolutionExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [OptimalResolutionNode]

async def comfy_entrypoint() -> ComfyExtension:
    return OptimalResolutionExtension()

# Setup API Routes
prompt_server = PromptServer.instance

@prompt_server.routes.get("/optimal_resolution/models")
async def get_models_data(request):
    """Returns the configuration JSON to the frontend."""
    data = OptimalResolutionNode.models_data
    if not data:
        data = load_models_data()
    return aiohttp.web.json_response(data, status=200)

@prompt_server.routes.post("/optimal_resolution/calculate")
async def calculate_resolution_api(request):
    """Calculates resolution without executing the workflow."""
    try:
        body = await request.json()
        model_type = body.get("model_type", "Image")
        model = body.get("model", "Flux 1")
        aspect_ratio = body.get("aspect_ratio", "1:1")
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

__all__ = ['WEB_DIRECTORY']