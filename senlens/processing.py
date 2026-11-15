"""Image perturbations with frozen baseline normalization for fair testing."""
from __future__ import annotations
import hashlib
import cv2
import numpy as np

CONDITIONS = [
    ('original', '원본', None),
    ('brightness_1', '밝기 감소 강', ('brightness', 0.45)),
    ('brightness_2', '밝기 감소 약', ('brightness', 0.70)),
    ('brightness_3', '밝기 증가', ('brightness', 1.30)),
    ('noise_1', '잡음 약', ('noise', 0.03)),
    ('noise_2', '잡음 중', ('noise', 0.07)),
    ('noise_3', '잡음 강', ('noise', 0.13)),
    ('blur_1', '흐림 약', ('blur', 0.8)),
    ('blur_2', '흐림 중', ('blur', 1.6)),
    ('blur_3', '흐림 강', ('blur', 2.8)),
]


def normalize_once(original):
    """Normalize intensity *once* on original image, never each variant independently.
    This does not modify spatial geometry and preserves the same GT instance mask.
    """
    x = np.asarray(original, dtype=np.float32)
    low, high = np.percentile(x, [1, 99])
    if high <= low:
        raise ValueError('원본 영상의 명암 차이가 없습니다.')
    return np.clip((x - low) / (high - low), 0, 1).astype(np.float32), (float(low), float(high))


def seed_for_image(name, seed=20261114):
    value = hashlib.sha256(f'{seed}:{name}'.encode('utf-8')).digest()
    return int.from_bytes(value[:4], byteorder='little')


def perturb(image_01, condition_id, seed=0):
    x = np.asarray(image_01, dtype=np.float32)
    if x.ndim != 2:
        raise ValueError('조건 변형은 2D 이미지 전용입니다.')
    found = next((v for key, label, v in CONDITIONS if key == condition_id), None)
    if condition_id == 'original':
        return x.copy()
    if found is None:
        raise ValueError(f'알 수 없는 조건: {condition_id}')
    kind, value = found
    if kind == 'brightness':
        return np.clip(x * value, 0, 1).astype(np.float32)
    if kind == 'noise':
        rng = np.random.default_rng(seed)
        return np.clip(x + rng.normal(0.0, value, x.shape), 0, 1).astype(np.float32)
    if kind == 'blur':
        return cv2.GaussianBlur(x, ksize=(0, 0), sigmaX=value).astype(np.float32)
    raise ValueError(kind)


def preview_gray(image_01):
    return np.round(np.clip(image_01, 0, 1) * 255).astype(np.uint8)
