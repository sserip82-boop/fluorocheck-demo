"""One-to-one nucleus matching at IoU>=0.50; no unverified metrics."""
from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment


def _all_instance_ids(mask):
    return np.unique(mask[mask > 0])


def score_instances(pred, gt, threshold=0.5):
    """Return precision, recall, F1, mean matched IoU, foreground IoU.
    If there are no matches, matched_iou is None, not a fictional zero-quality area.
    """
    pred = np.asarray(pred)
    gt = np.asarray(gt)
    if pred.shape != gt.shape or pred.ndim != 2:
        raise ValueError('예측 마스크와 정답 마스크는 같은 2D 크기여야 합니다.')
    p_ids = _all_instance_ids(pred)
    g_ids = _all_instance_ids(gt)
    npred, ngt = len(p_ids), len(g_ids)
    # Pixel-wise union/intersection of all nuclei (not the same as mean instance IoU).
    both = (pred > 0) & (gt > 0)
    either = (pred > 0) | (gt > 0)
    fg_iou = float(both.sum() / either.sum()) if either.any() else 1.0
    ious = np.zeros((ngt, npred), dtype=np.float64)
    if ngt and npred:
        # Efficient sparse pair intersections using compressed IDs.
        g = np.searchsorted(g_ids, gt[both])
        p = np.searchsorted(p_ids, pred[both])
        np.add.at(ious, (g, p), 1)
        g_areas = np.array([(gt == i).sum() for i in g_ids], dtype=np.float64)
        p_areas = np.array([(pred == i).sum() for i in p_ids], dtype=np.float64)
        unions = g_areas[:, None] + p_areas[None, :] - ious
        np.divide(ious, unions, out=ious, where=unions > 0)
        # Prefer valid matches; reject all IoU below threshold.
        valid = ious >= threshold
        costs = np.where(valid, 1.0 - ious, 1e6)
        gi, pi = linear_sum_assignment(costs)
        matched = [float(ious[g0, p0]) for g0, p0 in zip(gi, pi) if valid[g0, p0]]
    else:
        matched = []
    tp = len(matched)
    fp = npred - tp
    fn = ngt - tp
    if npred == 0 and ngt == 0:
        precision = recall = f1 = 1.0
    else:
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        'gt_count': ngt, 'pred_count': npred, 'tp': tp, 'fp': fp, 'fn': fn,
        'precision': precision, 'recall': recall, 'f1': f1,
        'matched_mean_iou': float(np.mean(matched)) if matched else None,
        'foreground_iou': fg_iou, 'abs_count_error': abs(npred - ngt),
        'rel_count_error': (abs(npred - ngt) / ngt) if ngt else None,
        'matching_iou_threshold': threshold,
    }


def nuclei_statistics(labels):
    """Return per-nucleus pixel area and circularity (4π area / perimeter²)."""
    from skimage.measure import regionprops
    out = []
    for region in regionprops(np.asarray(labels, dtype=np.int32)):
        perimeter = float(region.perimeter)
        out.append({'nucleus_id': int(region.label), 'area_px2': int(region.area),
                    'circularity': float(4 * np.pi * region.area / (perimeter ** 2)) if perimeter > 0 else None})
    return out
