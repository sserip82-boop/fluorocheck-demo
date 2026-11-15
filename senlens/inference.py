"""Lazy import so cloud demo never downloads Cellpose weights."""
from __future__ import annotations
import numpy as np

MODEL_VERSION = 'cellpose==3.1.1.3'
MODEL_ID = 'nuclei'


def load_model():
    try:
        from cellpose import models
    except ImportError as exc:
        raise RuntimeError('Cellpose가 설치되지 않았습니다. requirements-local.txt를 설치하세요.') from exc
    return models.Cellpose(gpu=False, model_type='nuclei')


def infer(model, image, diameter=17.0):
    """Keep normalization off: per-variant normalization erases brightness experiment."""
    arr = np.asarray(image, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError('Cellpose 입력은 단일 채널 2D 이미지여야 합니다.')
    masks, flows, styles, diams = model.eval(
        arr, diameter=float(diameter), channels=[0, 0], normalize=False,
        flow_threshold=0.4, cellprob_threshold=0.0,
    )
    return np.asarray(masks, dtype=np.int32)
