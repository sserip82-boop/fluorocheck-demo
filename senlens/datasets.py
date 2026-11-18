"""BBBC038 PNG instances and deterministic original-resolution preprocessing."""
from pathlib import Path
import numpy as np
from PIL import Image
from .processing import normalize_once


def read_bbbc038(path):
    with Image.open(path) as image:
        if image.mode not in ("L", "I", "I;16", "RGB", "RGBA"):
            raise ValueError(f"지원하지 않는 PNG 모드: {image.mode}")
        array = np.array(image)
    if array.ndim not in (2, 3) or min(array.shape[:2]) < 32:
        raise ValueError("이미지 크기 또는 채널을 확인해 주세요.")
    if not np.isfinite(array).all():
        raise ValueError("이미지에 잘못된 픽셀 값이 있습니다.")
    if array.ndim == 3 and array.shape[2] not in (3, 4):
        raise ValueError("RGB 또는 RGBA 이미지가 필요합니다.")
    if array.ndim == 3 and array.shape[2] == 4:
        alpha = array[..., 3].astype(np.float32) / np.iinfo(array.dtype).max
        if np.any(alpha != 1):
            raise ValueError("반투명 PNG의 배경 해석이 모호하여 분석을 중단했습니다.")
    return array


def merge_bbbc038_masks(directory, shape):
    files = sorted(p for p in Path(directory).glob("*.png") if not p.name.startswith("._"))
    if not files:
        raise ValueError("핵 정답 PNG가 없습니다.")
    output = np.zeros(shape, dtype=np.int32)
    for object_id, file in enumerate(files, 1):
        with Image.open(file) as image:
            mask = np.array(image)
        if mask.ndim == 3:
            raise ValueError(f"정답 마스크는 흑백이어야 합니다: {file.name}")
        if mask.shape != shape:
            raise ValueError(f"정답 크기가 다릅니다: {file.name}")
        region = mask > 0
        if not region.any():
            raise ValueError(f"빈 정답 마스크: {file.name}")
        if np.any(output[region]):
            raise ValueError(f"정답 마스크가 겹칩니다: {file.name}")
        output[region] = object_id
    return output


def pairs_bbbc038(root):
    root = Path(root)
    pairs = []
    for image in sorted(root.rglob("images/*.png")):
        if "__MACOSX" in image.parts or image.name.startswith("._"):
            continue
        folder = image.parent.parent
        if image.stem != folder.name:
            raise ValueError(f"이미지 ID와 폴더가 다릅니다: {image}")
        pairs.append((image.stem, image, folder / "masks"))
    if len({stem for stem, _, _ in pairs}) != len(pairs):
        raise ValueError("이미지 ID가 중복됩니다.")
    return pairs


def grayscale(array):
    if array.ndim == 2:
        return array.astype(np.float32)
    rgb = array[..., :3].astype(np.float32)
    return rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def preprocess_bbbc038(array):
    """Fixed policy chosen before inference; never adjust based on F1."""
    gray = grayscale(array)
    base, limits = normalize_once(gray)
    border = np.concatenate([base[0], base[-1], base[:, 0], base[:, -1]])
    inverted = bool(np.median(border) > 0.5)
    if inverted:
        base = 1 - base
    color = bool(array.ndim == 3 and np.mean(np.ptp(array[..., :3].astype(float), axis=2)) > 5)
    kind = ("컬러" if color else "흑백") + (" · 밝은 배경" if inverted else " · 어두운 배경")
    return base.astype(np.float32), {
        "input_channel": "luminance" if array.ndim == 3 else "grayscale",
        "preprocessing": "original_P1_P99; invert_if_border_median_above_0.5",
        "inverted": inverted, "baseline_p1": limits[0], "baseline_p99": limits[1],
        "image_kind": kind, "source_format": "RGBA PNG" if array.ndim == 3 and array.shape[2] == 4 else "RGB PNG" if array.ndim == 3 else "grayscale PNG",
        "height": int(gray.shape[0]), "width": int(gray.shape[1]),
    }
