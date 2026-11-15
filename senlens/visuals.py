"""Dependable static outputs for portfolio and cloud demo."""
import cv2
import numpy as np
from PIL import Image
from .processing import preview_gray


def rgb_overlay(image_01, labels):
    gray = preview_gray(image_01)
    rgb = np.stack((gray // 3, gray // 2, gray), axis=-1)
    labels = np.asarray(labels, dtype=np.int32)
    # Draw each instance independently: touching nuclei need separate boundary lines.
    for obj_id in np.unique(labels):
        if obj_id == 0: continue
        mask = (labels == obj_id).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(rgb, contours, -1, (255, 202, 73), 1)
    return rgb


def zoom_center(image, factor=1):
    """Centrally crop and enlarge for microscopy detail inspection."""
    x = np.asarray(image)
    if factor <= 1:
        return x
    height, width = x.shape[:2]
    h = max(1, int(round(height / factor)))
    w = max(1, int(round(width / factor)))
    top = (height - h)//2
    left = (width - w)//2
    crop = x[top:top+h, left:left+w]
    method = cv2.INTER_NEAREST if x.dtype == np.uint8 else cv2.INTER_LINEAR
    return cv2.resize(crop, (width, height), interpolation=method)


def save_preview(image_01, labels, path):
    p = __import__('pathlib').Path(path)
    Image.fromarray(rgb_overlay(image_01, labels)).save(p, optimize=True)
    # Also save the unannotated input to support real overlay on/off controls.
    gray = preview_gray(image_01)
    Image.fromarray(gray).save(p.with_name(p.stem + '_input.png'), optimize=True)


def save_summary_plot(rows, output_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from collections import defaultdict
    groups = defaultdict(list)
    for row in rows:
        if row.get('f1') is not None:
            groups[row['condition']].append(float(row['f1']))
    if not groups:
        return False
    order = ['original', 'brightness_1', 'brightness_2', 'brightness_3',
             'noise_1', 'noise_2', 'noise_3', 'blur_1', 'blur_2', 'blur_3']
    xs = [k for k in order if k in groups]
    means = [float(np.mean(groups[k])) for k in xs]
    fig, ax = plt.subplots(figsize=(11.5, 4.5))
    ax.bar(xs, means)
    ax.set_ylim(0, 1)
    ax.set_ylabel('Instance F1 @ IoU >= 0.5')
    ax.set_xlabel('Condition')
    ax.set_title('Senescence Lens - AI nucleus detection reliability')
    ax.tick_params(axis='x', labelrotation=40)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return True
