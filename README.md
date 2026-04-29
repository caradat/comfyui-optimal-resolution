# comfyui-optimal-resolution

Custom node for ComfyUI helps determine the optimal resolution for image generation based on the selected model, aspect ratio, and mode. It ensures that generated images use the optimal possible dimensions for each specific model, improving quality and consistency.

## Features

- **Model-specific resolutions**: Each model has its own optimal base resolution and multiple-of value
- **Aspect ratio support**: Supports common aspect ratios including 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9, and 9:21
- **Multiple modes**: Some models support different generation modes (Standard, Fixed resolutions, etc.)
- **Exact resolutions**: Certain models support fixed exact resolutions for optimal quality
- **Automatic calculation**: Automatically calculates optimal width and height based on model requirements

## Supported Models

### Image Models
- **SDXL Base**: Base resolution 1024, multiple of 16
- **SD 1.5**: Base resolution 512, multiple of 8
- **Flux 1**: Base resolution 1024, multiple of 16
- **Flux 2**: Base resolution 2048, multiple of 16
- **Qwen Image**: Base resolution 1328, multiple of 16
- **Ernie Image**: Base resolution 1024, multiple of 16

### Video Models
- **Wan 2.2 14B**: Base resolution 960, multiple of 16
- **Wan 2.2 5B**: Base resolution 960, multiple of 16
- **SVD XT**: Base resolution 1024, multiple of 16

## Usage

1. Add the Optimal Resolution node to your ComfyUI workflow
2. Select the model type (Image or Video)
3. Choose the specific model from the dropdown
4. Select your desired aspect ratio
5. Choose the generation mode (if available)
6. The node will output the optimal width and height values

## Special Modes

### SDXL Base
- **Area-based (1024)**: Uses base resolution of 1024² with aspect ratio adjustment
- **Fixed (exact)**: Uses pre-defined optimal resolutions for SDXL:
  - 1:1 - 1024×1024
  - 9:7 - 1152×896
  - 7:9 - 896×1152
  - 19:13 - 1216×832
  - 13:19 - 832×1216
  - 7:4 - 1344×768
  - 4:7 - 768×1344
  - 12:5 - 1536×640
  - 5:12 - 640×1536

### Qwen Image
- **Area-based (1328²)**: Uses base area of 1328² with aspect ratio adjustment
- **Fixed (exact)**: Uses pre-defined, exact resolutions based on the [model guide](https://github.com/QwenLM/Qwen-Image)
  - 1:1 - 1328×1328
  - 16:9 - 1664×928
  - 9:16 - 928×1664
  - 4:3 - 1472×1104
  - 3:4 - 1104×1472
  - 3:2 - 1584×1056
  - 2:3 - 1056×1584

### Ernie Image
- **Area-based (1024²)**: Uses base area of 1024² with aspect ratio adjustment
- **Fixed (exact)**: Uses pre-defined, exact resolutions based on the [model documentation](https://huggingface.co/baidu/ERNIE-Image)
  - 1:1 - 1024×1024
  - 16:9 - 1264×848
  - 9:16 - 848×1264
  - 21:9 - 1376×768
  - 9:21 - 768×1376
  - 9:7 - 1200×896
  - 7:9 - 896×1200

### Flux 2
- **1MP**: 1 megapixel mode
- **2MP**: 2 megapixel mode (default)
- **3MP**: 3 megapixel mode
- **4MP**: 4 megapixel mode

### Wan 2.2 14B
- **720p**: 1280×720 resolution
- **480p**: 854×480 resolution

## Installation

1. Clone this repository into your ComfyUI custom_nodes directory:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/caradat/comfyui-optimal-resolution.git
   ```
2. Restart ComfyUI
3. The Optimal Resolution node will be available in the node list under the "image" category

## Configuration

The node behavior is controlled by the `models_data.json` file, which contains:

- `model_types`: Categorization of models into Image and Video types
- `base_resolutions`: Base resolution for each model
- `multiple_of`: The value that resolutions should be multiples of for each model
- `mode_options`: Available generation modes for each model
- `mode_resolutions`: Custom area values for different modes
- `exact_resolutions`: Pre-defined exact resolutions for specific aspect ratios

## License

MIT License

## Credits

This node was created to optimize image generation workflows in ComfyUI by ensuring proper resolution selection based on model requirements.
