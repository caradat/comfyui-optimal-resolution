import json

# Define file paths
file_path = 'C:/ComfyUI/frontend/custom_nodes/comfyui-optimal-resolution/models_data.json'

# Load the current data
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create new structure
new_data = {k: v for k, v in data.items() if k not in ['base_resolutions', 'multiple_of', 'mode_options']}
new_data['models_data'] = {}

# Get the data dictionaries
base_res = data.get('base_resolutions', {})
mult_of = data.get('multiple_of', {})
mode_opts = data.get('mode_options', {})

# Create a set of all model names, excluding 'default'
all_models = set(list(base_res.keys()) + list(mult_of.keys()) + list(mode_opts.keys()))
all_models.discard('default')

# Populate models_data for each model
for model in all_models:
    new_data['models_data'][model] = {
        'base_resolution': base_res.get(model, 1024),
        'multiple_of': mult_of.get(model, 16),
        'mode_options': mode_opts.get(model, mode_opts['default'])
    }

# Add the default model data
new_data['models_data']['default'] = {
    'base_resolution': 1024,
    'multiple_of': 16,
    'mode_options': mode_opts['default']
}

# Write the new data back to the file
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(new_data, f, indent=2, ensure_ascii=False)

print("Transformation completed.")