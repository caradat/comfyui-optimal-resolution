# comfyui-optimal-resolution

Custom node for ComfyUI helps determine the optimal resolution for image generation based on the selected model, aspect ratio, and mode. It ensures that generated images use the optimal possible dimensions for each specific model, improving quality and consistency.

## Features

- **Model-specific resolutions**: Each model has its own optimal base resolution and multiple-of value
- **Dynamic aspect ratio selection**: Aspect ratio options are filtered based on the selected mode, showing only valid combinations
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
4. Select the generation mode (if available)
5. Select your desired aspect ratio (options are filtered based on the selected mode)
6. The node will output the optimal width and height values

## Special Modes

### SDXL Base
- **Area-based (1024²)**: Uses base area of 1024² with aspect ratio adjustment
- **Fixed (exact)**: Uses pre-defined optimal resolutions for SDXL:
  - 1:1 - 1024×1024
  - 16:9 - 1360×768
  - 9:16 - 768×1360
  - 4:3 - 1152×864
  - 3:4 - 864×1152
  - 3:2 - 1248×832
  - 2:3 - 832×1248

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
- **Area: 512² (0.26MP)**: 0.26 megapixel, area = 262,144
- **Area: 640² (0.41MP)**: 0.41 megapixels, area = 409,600
- **Area: 768² (0.59MP)**: 0.59 megapixels, area = 589,824
- **Area: 896² (0.80MP)**: 0.80 megapixels, area = 802,816
- **Area: 1024² (1.0MP)**: 1.0 megapixel, area = 1,048,576
- **Area: 1152² (1.33MP)**: 1.33 megapixels, area = 1,327,104
- **Area: 1280² (1.64MP)**: 1.64 megapixels, area = 1,638,400
- **Area: 1440² (2.07MP)**: 2.07 megapixels, area = 2,073,600
- **Area: 1536² (2.36MP)**: 2.36 megapixels, area = 2,359,296
- **Area: 1664² (2.77MP)**: 2.77 megapixels, area = 2,768,896
- **Area: 1792² (3.21MP)**: 3.21 megapixels, area = 3,211,264
- **Area: 1920² (3.69MP)**: 3.69 megapixels, area = 3,686,400
- **Area: 2048² (4.19MP)**: 4.19 megapixels, area = 4,194,304

### Wan 2.2 14B
- **720p (1280x704)**: 901120 area (1280×704)
- **480p (854x480)**: 409920 area (854×480)

### Wan 2.2 5B
- **720p (1280x704)**: 901120 area (1280×704)
- **480p (854x480)**: 409920 area (854×480)

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
- `resolutions`: Custom area values for different modes (Area and model-specific like Wan 2.2 14B)
- `exact_resolutions`: Pre-defined exact resolutions for specific aspect ratios
- `aspect_ratios`: Aspect ratio options filtered by model and mode
- `models_data`: Comprehensive model configuration including base_resolution, multiple_of, and resolution_options

## Area Mode
The Area mode provides a unified set of resolution options for models that use area-based settings. This ensures consistency across different models.

Available options:
- **384² (0.15MP)**: 0.15 megapixel, area = 147,456
- **448² (0.20MP)**: 0.20 megapixels, area = 200,704
- **512² (0.26MP)**: 0.26 megapixel, area = 262,144
- **640² (0.41MP)**: 0.41 megapixels, area = 409,600
- **768² (0.59MP)**: 0.59 megapixels, area = 589,824
- **896² (0.80MP)**: 0.80 megapixels, area = 802,816
- **1024² (1.0MP)**: 1.0 megapixel, area = 1,048,576
- **1152² (1.33MP)**: 1.33 megapixels, area = 1,327,104
- **1280² (1.64MP)**: 1.64 megapixels, area = 1,638,400
- **1440² (2.07MP)**: 2.07 megapixels, area = 2,073,600
- **1536² (2.36MP)**: 2.36 megapixels, area = 2,359,296
- **1664² (2.77MP)**: 2.77 megapixels, area = 2,768,896
- **1792² (3.21MP)**: 3.21 megapixels, area = 3,211,264
- **1920² (3.69MP)**: 3.69 megapixels, area = 3,686,400
- **2048² (4.19MP)**: 4.19 megapixels, area = 4,194,304
- **2240² (5.02MP)**: 5.02 megapixels, area = 5,017,600
- **2560² (6.55MP)**: 6.55 megapixels, area = 6,553,600
- **3072² (9.44MP)**: 9.44 megapixels, area = 9,437,184
- **4096² (16.8MP)**: 16.8 megapixels, area = 16,777,216

## License

MIT License

## Credits

This node was created to optimize image generation workflows in ComfyUI by ensuring proper resolution selection based on model requirements.
