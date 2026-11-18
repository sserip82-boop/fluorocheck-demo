"""Read saved results without importing inference or scientific image packages."""
from pathlib import Path
import json
import pandas as pd

LABELS = {
    "original": "원본", "brightness_1": "많이 어둡게", "brightness_2": "조금 어둡게",
    "brightness_3": "밝게", "noise_1": "잡음 약", "noise_2": "잡음 중",
    "noise_3": "잡음 강", "blur_1": "흐림 약", "blur_2": "흐림 중", "blur_3": "흐림 강",
    "median_3": "잡음 제거 후",
}


def read_results(folder):
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("state") != "complete" or not manifest.get("real_cellpose"):
        raise ValueError("분석이 끝난 실제 AI 결과를 준비해 주세요.")
    frame = pd.read_csv(folder / "records.csv")
    required = {"stem", "condition", "f1", "foreground_iou", "pred_count", "gt_count", "tp", "fp", "fn", "overlay_file"}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError("분석 기록의 필수 항목이 빠졌습니다.")
    if manifest.get("completed_runs") != len(frame) or manifest.get("expected_runs") != len(frame):
        raise ValueError("완료 횟수와 기록 수가 다릅니다.")
    if frame.duplicated(["stem", "condition"]).any():
        raise ValueError("같은 사진과 조건의 기록이 중복되었습니다.")
    numeric = list(required - {"stem", "condition", "overlay_file"})
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    if frame[numeric].isna().any().any() or not frame.f1.between(0, 1).all():
        raise ValueError("측정값에 빈 값이나 잘못된 점수가 있습니다.")
    originals = frame[frame.condition == "original"].set_index("stem").f1
    frame["baseline_f1"] = frame.stem.map(originals)
    if frame.baseline_f1.isna().any():
        raise ValueError("원본 점수가 연결되지 않은 사진이 있습니다.")
    frame["delta_f1"] = frame.f1 - frame.baseline_f1
    return frame


def rank_cases(frame, criterion="drop", unique_images=True):
    candidates = frame[frame.condition != "original"].copy() if criterion == "drop" else frame.copy()
    field, ascending = {"drop": ("delta_f1", True), "f1": ("f1", True), "missed": ("fn", False)}[criterion]
    candidates = candidates.sort_values([field, "stem", "condition"], ascending=[ascending, True, True], kind="stable")
    if unique_images:
        candidates = candidates.drop_duplicates("stem")
    return candidates.head(5).reset_index(drop=True)


def explain(row):
    text = f"AI가 핵 {int(row['pred_count'])}개를 찾았습니다. 사람의 정답은 {int(row['gt_count'])}개입니다. "
    text += f"정답과 맞은 핵은 {int(row['tp'])}개, 놓친 핵은 {int(row['fn'])}개, 잘못 찾은 핵은 {int(row['fp'])}개입니다."
    delta = row.get("delta_f1", 0)
    if row["condition"] != "original":
        text += f" 원본보다 F1이 {abs(delta):.3f} " + ("낮아졌습니다." if delta < 0 else "높아졌습니다." if delta > 0 else "만큼 달라졌으며 동일합니다.")
    return text


def safe_asset(folder, relative):
    folder = Path(folder).resolve()
    path = (folder / str(relative)).resolve()
    if folder not in path.parents or not path.is_file():
        raise ValueError("사진 파일을 찾을 수 없습니다. 시연 자료를 다시 준비해 주세요.")
    return path


def change_statement(before, after):
    delta = float(after) - float(before)
    if delta > 0:
        return f"잡음 제거 후 F1이 {delta:.3f} 높아졌습니다."
    if delta < 0:
        return f"잡음을 제거했지만 F1이 {abs(delta):.3f} 낮아졌습니다."
    return "잡음 제거 전후 F1이 같습니다."
