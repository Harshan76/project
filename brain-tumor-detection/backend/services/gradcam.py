import os
import cv2
import numpy as np

def find_last_conv_layer(model):
    """
    Intelligently discovers the last convolutional layer in any Keras model,
    including nested Functional or Sequential backbones (e.g. MobileNetV2, ResNet, custom CNN).
    """
    # 1. Search top-level layers in reverse
    for layer in reversed(model.layers):
        if 'conv' in layer.name.lower() and hasattr(layer, 'output') and len(layer.output.shape) == 4:
            return layer.name
        # If the layer is a nested Model / Functional backbone
        if hasattr(layer, 'layers'):
            for sublayer in reversed(layer.layers):
                if 'conv' in sublayer.name.lower() and hasattr(sublayer, 'output') and len(sublayer.output.shape) == 4:
                    return f"{layer.name}/{sublayer.name}"

    # Fallback to any layer with 4D output
    for layer in reversed(model.layers):
        if hasattr(layer, 'output') and len(layer.output.shape) == 4:
            return layer.name

    return None

def generate_gradcam(model, img_array, class_index=None, last_conv_layer_name=None):
    """
    Computes Gradient-weighted Class Activation Mapping (Grad-CAM).
    Uses tf.GradientTape to compute gradients of the predicted class score
    with respect to the feature activation maps of the final convolutional layer.
    """
    import tensorflow as tf

    if last_conv_layer_name is None:
        last_conv_layer_name = find_last_conv_layer(model)
        
    if last_conv_layer_name is None:
        raise ValueError("Could not find a convolutional layer in the model for Grad-CAM generation.")

    # Check if target conv layer is in a nested model
    if '/' in last_conv_layer_name:
        parent_name, sublayer_name = last_conv_layer_name.split('/')
        nested_model = model.get_layer(parent_name)
        conv_layer = nested_model.get_layer(sublayer_name)
        grad_model = tf.keras.models.Model(
            inputs=[nested_model.inputs],
            outputs=[conv_layer.output, nested_model.output]
        )
        is_nested = True
    else:
        conv_layer = model.get_layer(last_conv_layer_name)
        grad_model = tf.keras.models.Model(
            inputs=[model.inputs],
            outputs=[conv_layer.output, model.output]
        )
        is_nested = False

    img_tensor = tf.convert_to_tensor(img_array, dtype=tf.float32)

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_tensor)
        
        if class_index is None:
            class_index = tf.argmax(predictions[0])
            
        loss = predictions[:, class_index]

    # Compute gradient of the score with respect to feature maps
    grads = tape.gradient(loss, conv_outputs)
    
    if grads is None:
        # Fallback if gradient is disconnected
        return np.ones((224, 224), dtype=np.float32) * 0.5

    # Global Average Pooling of gradients across spatial dimensions
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Weight feature map activations by pooled gradients
    conv_outputs = conv_outputs[0]
    cam = tf.reduce_sum(tf.multiply(pooled_grads, conv_outputs), axis=-1)
    
    # Apply ReLU to retain features that positively contribute to the target class
    cam = tf.maximum(cam, 0)
    
    # Normalize between 0 and 1
    max_val = tf.reduce_max(cam)
    if max_val > 0:
        cam = cam / max_val
        
    return cam.numpy()

def create_gradcam_overlay(image_path, model, output_dir, scan_id, class_index=None, alpha=0.45):
    """
    End-to-end Grad-CAM pipeline:
    - Preprocesses image
    - Generates heatmap
    - Resizes to original MRI dimensions
    - Converts heatmap to JET colormap
    - Blends overlay on original image
    - Creates a 3-panel explainability visualization: [Original | Attention Heatmap | Diagnostic Overlay]
    - Saves and returns paths
    """
    from services.prediction import preprocess_mri_image
    
    os.makedirs(output_dir, exist_ok=True)
    
    batch_img, rgb_img = preprocess_mri_image(image_path)
    
    # Generate Grad-CAM heatmap
    heatmap = generate_gradcam(model, batch_img, class_index=class_index)
    
    orig_bgr = cv2.imread(image_path)
    h, w = orig_bgr.shape[:2]
    
    # Resize heatmap to match image dimensions
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    
    # Apply JET colormap (Red/Yellow = high attention, Blue = baseline)
    colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    
    # Superimpose heatmap on original image
    overlay = cv2.addWeighted(orig_bgr, 1.0 - alpha, colored_heatmap, alpha, 0)
    
    # Save standalone overlay
    overlay_filename = f"{scan_id}_gradcam.png"
    overlay_filepath = os.path.join(output_dir, overlay_filename)
    cv2.imwrite(overlay_filepath, overlay)
    
    # Generate informative 3-panel explainability chart
    target_h = min(h, 450)
    target_w = int(w * (target_h / h))
    
    panel1 = cv2.resize(orig_bgr, (target_w, target_h))
    panel2 = cv2.resize(colored_heatmap, (target_w, target_h))
    panel3 = cv2.resize(overlay, (target_w, target_h))
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    cv2.putText(panel1, "ORIGINAL MRI", (15, 28), font, font_scale, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(panel2, "GRAD-CAM ATTENTION", (15, 28), font, font_scale, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(panel3, "EXPLAINABILITY OVERLAY", (15, 28), font, font_scale, (0, 255, 0), 2, cv2.LINE_AA)
    
    # Add disclaimer banner at bottom
    tri_panel = np.hstack([panel1, panel2, panel3])
    banner = np.zeros((36, tri_panel.shape[1], 3), dtype=np.uint8)
    banner[:] = (20, 25, 35) # dark navy
    cv2.putText(
        banner,
        "ATTENTION MAP ONLY - NOT A CONFIRMED TUMOR SEGMENTATION - EXPERIMENTAL RESEARCH TOOL",
        (20, 24), font, 0.45, (200, 200, 220), 1, cv2.LINE_AA
    )
    tri_panel_with_banner = np.vstack([tri_panel, banner])
    
    panel_filename = f"{scan_id}_gradcam_panel.png"
    panel_filepath = os.path.join(output_dir, panel_filename)
    cv2.imwrite(panel_filepath, tri_panel_with_banner)
    
    return {
        "gradcam_path": overlay_filepath,
        "gradcam_filename": overlay_filename,
        "panel_path": panel_filepath,
        "panel_filename": panel_filename
    }
