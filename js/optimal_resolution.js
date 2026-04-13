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
                        initializeWidgets(this, data);
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
    const modeWidget = node.widgets.find(w => w.name === "mode");

    if (!typeWidget || !modelWidget || !modeWidget) return;

    // Initial Population based on default type
    updateModelList(node, typeWidget.value, data);
    updateModeOptions(node, modelWidget.value, data);
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
    const modeWidget = node.widgets.find(w => w.name === "mode");
    if (!modeWidget || !data.mode_options) return;

    let options = data.mode_options["default"];
    if (data.mode_options[modelName]) {
        options = data.mode_options[modelName];
    }

    modeWidget.options.values = options.values;
    modeWidget.value = options.default;
}

function setupWidgetListeners(node) {
    const typeWidget = node.widgets.find(w => w.name === "model_type");
    const modelWidget = node.widgets.find(w => w.name === "model");
    const arWidget = node.widgets.find(w => w.name === "aspect_ratio");
    const multWidget = node.widgets.find(w => w.name === "multiple_of");
    const modeWidget = node.widgets.find(w => w.name === "mode");

    const triggerUpdate = () => {
        if (node.fetchTimeout) clearTimeout(node.fetchTimeout);
        // Debounce slightly to prevent spamming API during rapid clicks
        node.fetchTimeout = setTimeout(() => {
            fetchResolution(node);
        }, 100);
    };

    // Type Change -> Update Models
    if (typeWidget) {
        const origCallback = typeWidget.callback;
        typeWidget.callback = function(value) {
            if (origCallback) origCallback.apply(this, arguments);
            updateModelList(node, value, node.modelsData);
            triggerUpdate();
        };
    }

    // Model Change -> Update Modes
    if (modelWidget) {
        const origCallback = modelWidget.callback;
        modelWidget.callback = function(value) {
            if (origCallback) origCallback.apply(this, arguments);
            updateModeOptions(node, value, node.modelsData);
            triggerUpdate();
        };
    }

    // Others -> Just Update Resolution
    [arWidget, multWidget, modeWidget].forEach(w => {
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
    const multWidget = node.widgets.find(w => w.name === "multiple_of");
    const modeWidget = node.widgets.find(w => w.name === "mode");

    const payload = {
        model_type: typeWidget?.value || "Image",
        model: modelWidget?.value || "SDXL Base",
        aspect_ratio: arWidget?.value || "1:1",
        multiple_of: multWidget?.value || 16,
        mode: modeWidget?.value || "Standard"
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