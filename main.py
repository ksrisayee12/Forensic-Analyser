import cv2
import numpy as np

# ------------------------------
# 1. Load Image Function
# ------------------------------
def load_image(path):
    """Loads an image from file."""
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Image not found. Check file path.")
    return img

# ------------------------------
# 2. Preprocessing Function
# ------------------------------
def preprocess_image(img):
    """
    Applies noise reduction, contrast enhancement, and color correction
    to improve underwater image visibility.
    """
    
    # Convert to LAB color space for contrast enhancement
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L-channel to improve contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)

    # Merge and convert back to BGR
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # Noise reduction using bilateral filter (preserves edges)
    denoised = cv2.bilateralFilter(enhanced_img, d=9, sigmaColor=75, sigmaSpace=75)

    return denoised

# ------------------------------
# 3. Edge Detection Function
# ------------------------------
def detect_edges(img):
    """
    Apply Canny edge detection after converting to grayscale.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Use Gaussian blur before Canny for smooth edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    edges = cv2.Canny(blurred, 50, 150)
    return edges

# ------------------------------
# 4. Contour Extraction Function
# ------------------------------
def extract_contours(edge_img):
    """
    Finds contours from edge-detected image.
    """
    contours, hierarchy = cv2.findContours(edge_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# ------------------------------
# 5. Draw Fish Outline Function
# ------------------------------
def draw_fish_outline(original_img, contours):
    """
    Draws detected fish boundaries using contours.
    """
    outlined = original_img.copy()

    # Draw contours (you can adjust thickness and color)
    cv2.drawContours(outlined, contours, -1, (0, 255, 0), 2)

    return outlined

# ------------------------------
# MAIN EXECUTION BLOCK
# ------------------------------
if __name__ == "__main__":
    path = r"C:\Users\prana\OneDrive\Desktop\cv\Dorey.jpg"  # Change path here to test multiple images

    # Step 1: Load Image
    original = load_image(path)

    # Step 2: Preprocess for underwater enhancement
    processed = preprocess_image(original)

    # Step 3: Edge Detection
    edges = detect_edges(processed)

    # Step 4: Extract Contours
    contours = extract_contours(edges)

    # Step 5: Draw Final Fish Outlines
    outlined_img = draw_fish_outline(processed, contours)

    # ------------------------------
    # 6. Display all images
    # ------------------------------
    cv2.imshow("Original Image", original)
    cv2.imshow("Processed Image", processed)
    cv2.imshow("Detected Edges", edges)
    cv2.imshow("Fish Outlined Image", outlined_img)

    print(f"Contours Detected: {len(contours)} (Possible fish shapes detected)")

    cv2.waitKey(0)
    cv2.destroyAllWindows()
