import cv2
import numpy as np
import os

def enhance_mri_image(
    input_path,
    output_dir,
    scan_id,
    clahe_clip_limit=2.5,
    clahe_grid_size=8,
    denoise_method='bilateral',
    denoise_strength=7,
    sharpen_strength=1.2,
    brightness=5,
    apply_normalization=True
):
    """
    Applies genuine OpenCV digital image processing operations to enhance MRI contrast,
    reduce acoustic/scanner noise, sharpen tissue boundaries, and normalize intensity.
    
    Returns a dict with paths to enhanced image, comparison image, and applied parameters.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Read image in BGR
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Failed to read image at {input_path}")
        
    orig_h, orig_w = img.shape[:2]
    
    # 1. Noise Reduction
    denoised = img.copy()
    if denoise_strength > 0:
        if denoise_method == 'bilateral':
            # Bilateral filter preserves sharp anatomical edges while smoothing flat noise
            d = max(3, int(denoise_strength))
            sigma_color = denoise_strength * 10
            sigma_space = denoise_strength * 10
            denoised = cv2.bilateralFilter(img, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
        elif denoise_method == 'nlm':
            # Non-local means denoising
            h_param = float(denoise_strength)
            denoised = cv2.fastNlMeansDenoisingColored(img, None, h_param, h_param, 7, 21)
        else: # Gaussian blur
            k_size = int(denoise_strength)
            if k_size % 2 == 0:
                k_size += 1
            denoised = cv2.GaussianBlur(img, (k_size, k_size), 0)

    # 2. Contrast Enhancement using CLAHE in LAB color space
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    grid_size = max(2, int(clahe_grid_size))
    clahe = cv2.createCLAHE(
        clipLimit=max(0.1, float(clahe_clip_limit)),
        tileGridSize=(grid_size, grid_size)
    )
    enhanced_l = clahe.apply(l_channel)
    
    merged_lab = cv2.merge([enhanced_l, a_channel, b_channel])
    contrast_enhanced = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)
    
    # 3. Brightness Adjustment
    if brightness != 0:
        # Scale and offset: g(x) = alpha * f(x) + beta
        contrast_enhanced = cv2.convertScaleAbs(contrast_enhanced, alpha=1.0, beta=int(brightness))
        
    # 4. Sharpening via Unsharp Masking
    if sharpen_strength > 0:
        # Gaussian blur of contrast enhanced image
        gaussian_blur = cv2.GaussianBlur(contrast_enhanced, (0, 0), sigmaX=2.0)
        # Unsharp mask formula: enhanced + amount * (enhanced - blurred)
        # using addWeighted: output = alpha * src1 + beta * src2 + gamma
        alpha = 1.0 + float(sharpen_strength)
        beta = -float(sharpen_strength)
        sharpened = cv2.addWeighted(contrast_enhanced, alpha, gaussian_blur, beta, 0)
    else:
        sharpened = contrast_enhanced
        
    # 5. Min-Max Normalization across full dynamic range
    if apply_normalization:
        normalized = np.zeros_like(sharpened)
        normalized = cv2.normalize(sharpened, normalized, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        final_enhanced = normalized
    else:
        final_enhanced = sharpened

    # Ensure valid range
    final_enhanced = np.clip(final_enhanced, 0, 255).astype(np.uint8)
    
    # Save enhanced image
    enhanced_filename = f"{scan_id}_enhanced.png"
    enhanced_filepath = os.path.join(output_dir, enhanced_filename)
    cv2.imwrite(enhanced_filepath, final_enhanced)
    
    # 6. Generate Side-by-side & Difference Comparison View
    # Compute absolute difference map between original and enhanced grayscale
    orig_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enh_gray = cv2.cvtColor(final_enhanced, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(orig_gray, enh_gray)
    # Amplify difference for clear visual comprehension
    diff_colored = cv2.applyColorMap(cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX), cv2.COLORMAP_MAGMA)
    
    # Create a 3-panel comparison: [Original | Enhanced | Enhancement Delta Map]
    h, w = img.shape[:2]
    # Resize to standard height if very large
    target_h = min(h, 450)
    target_w = int(w * (target_h / h))
    
    panel_orig = cv2.resize(img, (target_w, target_h))
    panel_enh = cv2.resize(final_enhanced, (target_w, target_h))
    panel_diff = cv2.resize(diff_colored, (target_w, target_h))
    
    # Add textual labels at top of each panel
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    cv2.putText(panel_orig, "ORIGINAL MRI", (15, 28), font, font_scale, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(panel_enh, "ENHANCED (CLAHE)", (15, 28), font, font_scale, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(panel_diff, "CONTRAST DELTA", (15, 28), font, font_scale, (255, 100, 255), 2, cv2.LINE_AA)
    
    comparison_img = np.hstack([panel_orig, panel_enh, panel_diff])
    comparison_filename = f"{scan_id}_comparison.png"
    comparison_filepath = os.path.join(output_dir, comparison_filename)
    cv2.imwrite(comparison_filepath, comparison_img)
    
    return {
        "enhanced_path": enhanced_filepath,
        "enhanced_filename": enhanced_filename,
        "comparison_path": comparison_filepath,
        "comparison_filename": comparison_filename,
        "parameters": {
            "clahe_clip_limit": clahe_clip_limit,
            "clahe_grid_size": clahe_grid_size,
            "denoise_method": denoise_method,
            "denoise_strength": denoise_strength,
            "sharpen_strength": sharpen_strength,
            "brightness": brightness,
            "apply_normalization": apply_normalization
        }
    }
