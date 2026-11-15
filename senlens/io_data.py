"""Public BBBC039 data readers. No downloading is triggered on module import."""
from __future__ import annotations
from pathlib import Path
import hashlib
import io
import numpy as np
import tifffile
from PIL import Image
from skimage.measure import label as cc_label

IMAGE_EXTS = {'.tif', '.tiff'}


def read_image(path_or_bytes):
    """Read 2D TIFF (16-bit stays 16-bit) and reject ambiguous color/z-stacks."""
    if isinstance(path_or_bytes, (str, Path)):
        img = tifffile.imread(str(path_or_bytes))
    else:
        img = tifffile.imread(io.BytesIO(path_or_bytes))
    img = np.asarray(img)
    if img.ndim != 2:
        raise ValueError(f'단일 2D 형광 채널만 지원합니다. 현재 shape={img.shape}')
    if not np.issubdtype(img.dtype, np.number) or not np.isfinite(img).all():
        raise ValueError('이미지가 숫자형 또는 유한한 값을 포함하지 않습니다.')
    if min(img.shape) < 32:
        raise ValueError('너무 작은 이미지입니다(한 변은 32픽셀 이상).')
    return img


def decode_ground_truth(path_or_bytes):
    """Decode colored masks into integer instance IDs; separate disconnected same-color ROIs.

    BBBC039's official PNG masks use different colors for touching nuclei; using
    connected components of a binarized image can merge touching objects.
    """
    if isinstance(path_or_bytes, (str, Path)):
        with Image.open(path_or_bytes) as im:
            arr = np.array(im.convert('RGB'))
    else:
        with Image.open(io.BytesIO(path_or_bytes)) as im:
            arr = np.array(im.convert('RGB'))
    if arr.ndim != 3 or arr.shape[-1] != 3:
        raise ValueError('정답 PNG는 RGB 이미지여야 합니다.')
    # Packed RGB codes preserve distinctions even if red components coincide.
    arr = arr.astype(np.uint32)
    packed = (arr[..., 0] << 16) | (arr[..., 1] << 8) | arr[..., 2]
    out = np.zeros(packed.shape, dtype=np.int32)
    instance_id = 0
    for color in np.unique(packed):
        if color == 0:  # black background
            continue
        pieces = cc_label(packed == color, connectivity=1)
        for component in range(1, int(pieces.max()) + 1):
            instance_id += 1
            out[pieces == component] = instance_id
    return out


def pair_dataset(data_dir):
    root = Path(data_dir)
    # The official ZIPs also contain macOS resource files named ._*.tif and ._*.png.
    images = {
        p.stem: p for p in (root / 'images').rglob('*')
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith('._')
    }
    masks = {
        p.stem: p for p in (root / 'masks').rglob('*.png')
        if p.is_file() and not p.name.startswith('._')
    }
    return [(stem, img, masks.get(stem)) for stem, img in sorted(images.items())]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
