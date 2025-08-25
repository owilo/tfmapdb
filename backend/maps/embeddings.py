import numpy as np
from skimage import feature, color
from .utils import extract_map_data, xml_to_image

def embed_from_xml(xml_text):
    map_data = extract_map_data(xml_text)
    img = xml_to_image(xml_text, (map_data["length"], map_data["height"]), scale=0.16)
    img = img.resize((128, 64))
    
    img_array = np.array(img)
    
    rgb = img_array[..., :3]
    alpha = img_array[..., 3] / 255.0

    lab = color.rgb2lab(rgb)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]

    rows, cols = 4, 8
    total_cells = rows * cols
    cell_features = np.zeros(total_cells * 3, dtype=np.float32)
    
    cell_height = L.shape[0] // rows
    cell_width = L.shape[1] // cols
    
    for i in range(rows):
        y_start = i * cell_height
        y_end = (i + 1) * cell_height
        
        for j in range(cols):
            x_start = j * cell_width
            x_end = (j + 1) * cell_width
            
            cell_idx = (i * cols + j) * 3
            cell_alpha = alpha[y_start:y_end, x_start:x_end]
            
            alpha_sum = np.sum(cell_alpha)
            if alpha_sum > 1e-6:
                cell_L = L[y_start:y_end, x_start:x_end]
                cell_A = A[y_start:y_end, x_start:x_end]
                cell_B = B[y_start:y_end, x_start:x_end]
                
                cell_features[cell_idx] = np.average(cell_L, weights=cell_alpha) / 100
                cell_features[cell_idx + 1] = np.average(cell_A, weights=cell_alpha) / 128
                cell_features[cell_idx + 2] = np.average(cell_B, weights=cell_alpha) / 128

    gray = color.rgb2gray(rgb)
    hog_feat = feature.hog(gray, orientations=8, pixels_per_cell=(64, 32), cells_per_block=(1, 1), block_norm="L2")
    
    return np.concatenate([cell_features, hog_feat]).astype(np.float32)