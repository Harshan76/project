import os
import numpy as np
import cv2

# Define target classes in canonical alphabetical order matching standard Kaggle Brain Tumor MRI dataset
CLASS_NAMES = ['Glioma', 'Meningioma', 'No Tumor', 'Pituitary Tumor']

# Global model cache
_MODEL = None
_MODEL_PATH = None

def get_model_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keras_path = os.path.join(base_dir, 'models', 'brain_tumor_model.keras')
    h5_path = os.path.join(base_dir, 'models', 'brain_tumor_model.h5')
    if os.path.exists(keras_path):
        return keras_path
    if os.path.exists(h5_path):
        return h5_path
    return keras_path  # Default target location

def is_model_available():
    """Checks whether a valid trained model weights file is present."""
    path = get_model_path()
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return True, path
    return False, path

def load_tumor_model():
    """Loads and caches the CNN model from disk."""
    global _MODEL, _MODEL_PATH
    available, path = is_model_available()
    if not available:
        _MODEL = None
        _MODEL_PATH = None
        return None
        
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
        
    try:
        import tensorflow as tf
        print(f"Loading trained brain tumor CNN model from: {path}")
        _MODEL = tf.keras.models.load_model(path, compile=False)
        _MODEL_PATH = path
        print("Model loaded successfully.")
        return _MODEL
    except Exception as e:
        print(f"Error loading model from {path}: {e}")
        _MODEL = None
        _MODEL_PATH = None
        return None

def preprocess_mri_image(image_path, target_size=(224, 224)):
    """
    Standardized preprocessing for brain MRI scans:
    - Reads image with OpenCV
    - Converts BGR to RGB
    - Resizes to 224x224
    - Normalizes pixel intensities to [0, 1] range
    - Adds batch dimension: (1, 224, 224, 3)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
        
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Unable to decode image at {image_path}")
        
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized_img = cv2.resize(rgb_img, target_size, interpolation=cv2.INTER_AREA)
    normalized = resized_img.astype(np.float32) / 255.0
    batch_img = np.expand_dims(normalized, axis=0)
    return batch_img, rgb_img

def predict_tumor(image_path):
    """
    Performs inference on the uploaded MRI using the CNN model.
    Strictly verifies model availability without generating fake or random predictions.
    """
    available, path = is_model_available()
    if not available:
        raise RuntimeError(
            f"MODEL_NOT_TRAINED: Trained model weights were not found at '{path}'. "
            "Please run 'python train_model.py' to train or build the CNN on the brain tumor dataset."
        )
        
    model = load_tumor_model()
    if model is None:
        raise RuntimeError(
            "MODEL_LOAD_FAILED: Failed to load model weights. Ensure TensorFlow is installed and file is valid."
        )
        
    # Preprocess image
    batch_img, original_rgb = preprocess_mri_image(image_path)
    
    # Run prediction
    raw_preds = model.predict(batch_img, verbose=0)[0]
    
    # If the output layer does not have softmax activation, apply softmax
    if np.sum(raw_preds) > 1.05 or np.any(raw_preds < 0):
        exp_preds = np.exp(raw_preds - np.max(raw_preds))
        probabilities = exp_preds / np.sum(exp_preds)
    else:
        probabilities = raw_preds
        
    class_idx = int(np.argmax(probabilities))
    predicted_class = CLASS_NAMES[class_idx]
    confidence_score = float(probabilities[class_idx] * 100.0)
    
    prob_dict = {
        CLASS_NAMES[i]: round(float(probabilities[i] * 100.0), 2)
        for i in range(len(CLASS_NAMES))
    }
    
    return {
        "predicted_category": predicted_class,
        "confidence_score": round(confidence_score, 2),
        "probabilities": prob_dict,
        "class_index": class_idx,
        "model_architecture": getattr(model, 'name', 'BrainTumorCNN'),
        "input_dimensions": [224, 224, 3]
    }
