import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI.OptimalResolution",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "OptimalResolutionNode") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                this.resolutionText = "Calculating...";
                this.modelsData = null;
                this.fetchTimeout = null;

                // 1. Fetch Configuration
                fetch('/optimal_resolution/models')
                    .then(res => res.json())
                    .then(data => {
                        this.modelsData = data;
                        console.log("[OptimalResolution] Fetched models data:", data);
                        // Ensure all widgets are properly initialized with correct options
                        initializeWidgets(this, data);
                        // Force update of all dependent widgets
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        if (modelWidget) {
                            console.log("[OptimalResolution] Updating mode options for model:", modelWidget.value);
                            updateModeOptions(this, modelWidget.value, data);
                            updateAspectRatioOptions(this, modelWidget.value, "Fixed (exact)", data);
                        }
                        fetchResolution(this);
                    })
                    .catch(err => {
                        console.error("[OptimalResolution] Failed to load config", err);
                        this.resolutionText = "Config Load Error";
                    });

                // 2. Setup Widget Callbacks
                setupWidgetListeners(this);

                return r;
            };

            // 3. Draw Foreground (Display Resolution)
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function(ctx, visibleRect) {
                const r = onDrawForeground ? onDrawForeground.apply(this, arguments) : undefined;
                
                if (this.resolutionText) {
                    ctx.fillStyle = "#FFFFFF";
                    ctx.font = "14px sans-serif";
                    ctx.textAlign = "center";
                    // Draw near bottom of node
                    const y = this.size[1] - 10;
                    ctx.fillText(this.resolutionText, this.size[0] / 2, y);
                }
                return r;
            };

            // 4. Handle Execution Result (Fallback)
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                if (message.resolution_text && message.resolution_text.length > 0) {
                    let text = message.resolution_text[0];
                    // Handle potential char code array from python
                    if (Array.isArray(text)) {
                        text = String.fromCharCode(...text);
                    }
                    this.resolutionText = text;
                    this.setDirtyCanvas(true, true);
                }
                return r;
            };
        }
    }
});

function initializeWidgets(node, data) {
    // Find widgets
    const typeWidget = node.widgets.find(w => w.name === "model_type");
    const modelWidget = node.widgets.find(w => w.name === "model");
    const modeWidget = node.widgets.find(w => w.name === "resolution");
    const arWidget = node.widgets.find(w => w.name === "aspect_ratio");

    if (!typeWidget || !modelWidget || !modeWidget || !arWidget) return;

    // Initial Population based on default type
    updateModelList(node, typeWidget.value, data);
    updateModeOptions(node, modelWidget.value, data);
    updateAspectRatioOptions(node, modelWidget.value, modeWidget.value, data);
}

function updateModelList(node, modelType, data) {
    const modelWidget = node.widgets.find(w => w.name === "model");
    if (!modelWidget || !data.model_types) return;

    const models = data.model_types[modelType] || [];
    modelWidget.options.values = models;
    
    // Ensure current value is valid
    if (!models.includes(modelWidget.value)) {
        modelWidget.value = models[0] || "Unknown";
    }
}

function updateModeOptions(node, modelName, data) {
    const modeWidget = node.widgets.find(w => w.name === "resolution");
    if (!modeWidget || !data.models_data) {
        console.error("[OptimalResolution] updateModeOptions: modeWidget or data.models_data is missing");
        return;
    }

    console.log("[OptimalResolution] updateModeOptions called for model:", modelName, "with data:", data.models_data[modelName]);
    
    let modelInfo = data.models_data[modelName];
    if (!modelInfo) {
        console.warn("[OptimalResolution] Model not found in data, using default:", modelName);
        modelInfo = data.models_data["default"];
    }
    
    if (!modelInfo) {
        console.error("[OptimalResolution] Default model data is also missing");
        return;
    }
    
    const options = modelInfo.resolution_options;
    if (!options || !options.values) {
        console.error("[OptimalResolution] resolution_options or values is missing for model:", modelName, modelInfo);
        return;
    }
    
    const currentMode = modeWidget.value;
    modeWidget.options.values = options.values;
    // Всегда устанавливаем значение на default из конфигурации новой модели
    modeWidget.value = options.default;
}

function updateAspectRatioOptions(node, modelName, resolution, data) {
    const arWidget = node.widgets.find(w => w.name === "aspect_ratio");
    if (!arWidget) return;

    let validRatios = ["1:1", "21:9", "9:21", "16:9", "9:16", "5:4", "4:5", "4:3", "3:4", "3:2", "2:3"];

    // If in Fixed (exact) mode, get aspect ratios from the model's exact_resolutions
    const modelInfo = data.models_data[modelName] || {};
    if (resolution === "Fixed (exact)" && modelInfo.exact_resolutions) {
        validRatios = Object.keys(modelInfo.exact_resolutions);
    } 
    // Otherwise, check if model and resolution have specific restrictions in aspect_ratios
    else if (data.aspect_ratios?.[modelName]?.[resolution]) {
        validRatios = data.aspect_ratios[modelName][resolution];
    }
    // Use default if defined
    else if (data.aspect_ratios?.default) {
        validRatios = data.aspect_ratios.default;
    }

    arWidget.options.values = validRatios;
    
    // Ensure current value is valid
    if (!validRatios.includes(arWidget.value)) {
        arWidget.value = validRatios[0];
    }
}

function setupWidgetListeners(node) {
    const typeWidget = node.widgets.find(w => w.name === "model_type");
    const modelWidget = node.widgets.find(w => w.name === "model");
    const arWidget = node.widgets.find(w => w.name === "aspect_ratio");
    const modeWidget = node.widgets.find(w => w.name === "resolution");

    const triggerUpdate = () => {
        if (node.fetchTimeout) clearTimeout(node.fetchTimeout);
        // Debounce slightly to prevent spamming API during rapid clicks
        node.fetchTimeout = setTimeout(() => {
            fetchResolution(node);
        }, 100);
    };

    // Type Change -> Update Models and all dependent widgets
    if (typeWidget) {
        const origCallback = typeWidget.callback;
        typeWidget.callback = function(value) {
            if (origCallback) origCallback.apply(this, arguments);
            updateModelList(node, value, node.modelsData);
            
            // After updating model list, also update mode and aspect ratio options
            const modelWidget = node.widgets.find(w => w.name === "model");
            if (modelWidget) {
                updateModeOptions(node, modelWidget.value, node.modelsData);
                
                const modeWidget = node.widgets.find(w => w.name === "resolution");
                if (modeWidget) {
                    updateAspectRatioOptions(node, modelWidget.value, modeWidget.value, node.modelsData);
                }
            }
            
            triggerUpdate();
        };
    }

    // Model Change -> Update Modes and Aspect Ratios
    if (modelWidget) {
        const origCallback = modelWidget.callback;
        modelWidget.callback = function(value) {
            if (origCallback) origCallback.apply(this, arguments);
            updateModeOptions(node, value, node.modelsData);
            updateAspectRatioOptions(node, value, modeWidget.value, node.modelsData);
            triggerUpdate();
        };
    }

    // Mode Change -> Update Aspect Ratios
    if (modeWidget) {
        const origCallback = modeWidget.callback;
        modeWidget.callback = function(value) {
            if (origCallback) origCallback.apply(this, arguments);
            updateAspectRatioOptions(node, modelWidget.value, value, node.modelsData);
            triggerUpdate();
        };
    }
    
    // Others -> Just Update Resolution
    [arWidget].forEach(w => {
        if (w) {
            const origCallback = w.callback;
            w.callback = function(value) {
                if (origCallback) origCallback.apply(this, arguments);
                triggerUpdate();
            };
        }
    });
}

function fetchResolution(node) {
    if (!node.modelsData) return;

    const typeWidget = node.widgets.find(w => w.name === "model_type");
    const modelWidget = node.widgets.find(w => w.name === "model");
    const arWidget = node.widgets.find(w => w.name === "aspect_ratio");
    const modeWidget = node.widgets.find(w => w.name === "resolution");

    const payload = {
        model_type: typeWidget?.value || "Image",
        model: modelWidget?.value || "SDXL Base",
        aspect_ratio: arWidget?.value || "1:1",
        resolution: modeWidget?.value || "Standard"
    };

    fetch('/optimal_resolution/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.resolution_text) {
            node.resolutionText = data.resolution_text;
            node.setDirtyCanvas(true, true);
        }
    })
    .catch(err => {
        console.warn("[OptimalResolution] Calc API failed", err);
        // Fallback to local calculation could go here, but we rely on API for consistency
    });
}