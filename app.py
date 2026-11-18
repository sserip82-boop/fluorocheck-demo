"""Senescence Lens v2. Saved-result experience; inference stays in local tools."""
from pathlib import Path
import json
import importlib.util
import pandas as pd
from PIL import Image, UnidentifiedImageError
import streamlit as st

from senlens.saved_results import LABELS, read_results, rank_cases, explain, safe_asset, change_statement

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "demo_results_v2"
BASELINE = BUNDLE / "baseline" if BUNDLE.exists() else ROOT / "demo_results"
FOLLOWUP = BUNDLE / "followup" if BUNDLE.exists() else ROOT / "outputs/v2_followup_20261118"
GALLERY = ROOT / "gallery_results" if (ROOT / "gallery_results").exists() else ROOT / "outputs/v21_gallery"
ERROR_MAPS = BUNDLE / "errors" if BUNDLE.exists() else ROOT / "outputs/v2_errors_all_20261118"

st.set_page_config(page_title="NucleoLens AI · AI 세포핵 탐지·정확도 검증 체험 플랫폼", page_icon="🔬", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1280px;padding-top:2rem}
h1,h2,h3{letter-spacing:-.025em;overflow-wrap:anywhere;white-space:normal}
[data-testid="stMetric"]{border:1px solid #dce5ef;border-radius:12px;padding:12px}
[data-testid="stSidebar"]{background:#f1f5fb}
[data-testid="stMetricValue"]>div{white-space:normal;overflow-wrap:anywhere;font-size:1.65rem}
[data-testid="stButton"] p{white-space:normal;overflow-wrap:anywhere}
@media(max-width:700px){.block-container{padding:1rem}h1{font-size:1.9rem}}
</style>
""", unsafe_allow_html=True)


def picture(folder, relative, caption, plain=False):
    try:
        path = safe_asset(folder, relative)
        if plain:
            path = safe_asset(folder, str(Path(relative).with_name(Path(relative).stem + "_input" + Path(relative).suffix)))
        with Image.open(path) as img:
            st.image(img.copy(), caption=caption, use_container_width=True)
    except (OSError, ValueError, UnidentifiedImageError):
        st.warning("이 사진을 열 수 없습니다. 다른 사진을 골라 보거나 시연 파일을 확인해 주세요.")


def baseline_row(frame, stem):
    return frame[(frame.stem == stem) & (frame.condition == "original")].iloc[0]


def error_picture(row):
    index_path = ERROR_MAPS / "error_index.csv"
    if not index_path.exists():
        st.info("이 사진의 오류 위치 표시는 아직 준비 중입니다. 위의 놓침·오탐 수는 기존 측정 기록입니다.")
        return
    try:
        index = pd.read_csv(index_path)
        selected = index[(index.stem == row.stem) & (index.condition == row.condition)]
        if selected.empty:
            st.info("이 조건의 오류 이미지를 준비하고 있습니다. 잠시 후 다시 선택해 주세요.")
            return
        match = selected.iloc[0]
        if any(int(match[key]) != int(row[key]) for key in ["gt_count", "pred_count", "tp", "fp", "fn"]):
            st.warning("오류 이미지와 기록의 수치가 달라 표시를 보류했습니다.")
            return
        picture(ERROR_MAPS, match.error_file, "초록 · 맞게 찾은 핵 / 빨강 · 놓친 핵 / 노랑 · 잘못 찾은 핵")
        st.caption("IoU 0.50 이상인 핵을 하나씩 짝지었습니다. 경계가 달라 짝이 안 맞으면 놓침과 오탐이 함께 생길 수 있습니다. 특정 오류의 원인은 추가 확인이 필요합니다.")
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        st.warning("오류 표시 파일을 읽지 못했습니다. 기본 분석 수치는 아래에서 확인할 수 있습니다.")


def describe(row):
    st.write(explain(row))
    a, b, c = st.columns(3)
    a.metric("핵을 잘 찾은 정도 · F1", f"{row.f1:.3f}")
    b.metric("핵 영역이 겹친 정도 · IoU", f"{row.foreground_iou:.3f}")
    c.metric("놓친 핵", f"{int(row.fn)}개")
    with st.expander("점수와 정답은 어떻게 확인하나요?"):
        st.write("F1은 놓친 핵과 잘못 찾은 핵을 함께 반영합니다. 1에 가까울수록 좋습니다. 여기서 IoU는 모든 핵 영역이 정답과 겹치는 비율입니다. 사람이 핵마다 표시한 정답 마스크와 AI 예측을 비교했습니다.")


def home(frame):
    st.title("NucleoLens AI")
    st.subheader("AI 세포핵 탐지·정확도 검증 체험 플랫폼")
    st.write("AI는 세포핵을 얼마나 정확하게 찾을까?")
    from senlens.gallery import read_gallery
    try:
        gallery = read_gallery(GALLERY)
        a,b,c=st.columns(3)
        a.metric("전체 체험 사진", f"{len(gallery)}장")
        b.metric("공개 데이터셋", f"{gallery.dataset.nunique()}개")
        c.metric("AI 모델", "Cellpose 3 nuclei")
    except (OSError,ValueError,KeyError,pd.errors.ParserError):
        st.info("240장 체험 갤러리를 준비 중입니다.")
    st.write("다양한 공개 세포 사진에서 AI가 핵을 찾는 모습과 오류를 살펴보세요. BBBC039는 형광 사진이며 BBBC038에는 여러 관찰 조건의 사진이 포함됩니다.")
    st.subheader("FluoroCheck · 기존 20장의 이미지 품질 실험")
    originals = frame[frame.condition == "original"]
    noisy = frame[frame.condition == "noise_3"]
    a, b, c = st.columns(3)
    a.metric("저장된 실제 분석", f"{len(frame)}회")
    b.metric("원본 평균 F1", f"{originals.f1.mean():.3f}")
    c.metric("강한 잡음 평균 F1", f"{noisy.f1.mean():.3f}")
    picture(BASELINE, originals.iloc[0].overlay_file, "공개 형광 이미지에서 AI가 찾은 세포핵")
    st.write("왼쪽 메뉴에서 사진을 골라 체험하고, AI가 어려워한 사례와 잡음 제거 실험을 확인하세요.")
    st.caption("학생이 직접 고른 20장에 대한 탐색 실험입니다. 이 평균을 전체 데이터의 성능으로 일반화할 수 없습니다.")
    with st.expander("기존 연구 도구 · 로컬 AI 실행 / 20장 선정 / 결과 내보내기"):
        if importlib.util.find_spec("cellpose") is not None:
            from app_legacy import local_analysis, choose_images, result_view, guide
            tool = st.selectbox("연구 도구", ["사용 안내", "로컬 AI 분석", "20장 선정", "기존 결과"])
            {"사용 안내": guide, "로컬 AI 분석": local_analysis, "20장 선정": choose_images, "기존 결과": result_view}[tool]()
        else:
            st.write("웹에서는 저장된 결과를 봅니다. 새로운 AI 계산과 사진 선정은 Python과 Cellpose를 설치한 내 컴퓨터에서 할 수 있습니다.")
        st.download_button("기존 200회 측정 CSV 받기", (BASELINE / "records.csv").read_bytes(), "records.csv", "text/csv")


def experience(frame):
    st.title("AI 분석 체험")
    mode=st.radio("체험 선택", ["240장 사진 갤러리", "FluoroCheck · 밝기·잡음·흐림"], horizontal=True)
    if mode=="240장 사진 갤러리":
        from senlens.gallery import gallery_view
        gallery_view(GALLERY)
        return
    quality_experience(frame)


def quality_experience(frame):
    stems = list(frame.stem.drop_duplicates())
    stem = st.selectbox("사진 선택", stems, format_func=lambda value: f"사진 {stems.index(value)+1:02d} · {value[:13]}")
    rows = frame[frame.stem == stem]
    condition = st.selectbox("사진 조건", rows.condition.tolist(), format_func=lambda value: LABELS.get(value, value))
    row = rows[rows.condition == condition].iloc[0]
    describe(row)
    a, b = st.columns(2)
    with a:
        picture(BASELINE, row.overlay_file, "AI에 넣은 사진", plain=True)
    with b:
        picture(BASELINE, row.overlay_file, "AI가 찾은 핵의 경계")
    st.subheader("AI는 어디에서 틀렸을까요?")
    error_picture(row)
    with st.expander("사진 이름과 상세 기록"):
        st.write(stem)
        st.dataframe(rows[["condition", "tp", "fp", "fn", "f1", "foreground_iou"]], hide_index=True)


def hardest(frame):
    st.title("AI가 어려워하는 사진 TOP 5")
    criterion = st.selectbox("순위 기준", ["drop", "f1", "missed"],
                             format_func=lambda value: {"drop": "원본보다 F1이 많이 떨어진 순", "f1": "F1이 낮은 순", "missed": "놓친 핵이 많은 순"}[value])
    mode = st.radio("순위 묶기", ["사진별", "사진·조건별"], horizontal=True)
    st.caption("사진별은 사진마다 가장 어려운 조건 하나를 고릅니다. 사진·조건별은 같은 사진이 여러 번 나올 수 있습니다.")
    ranking = rank_cases(frame, criterion, mode == "사진별")
    names = list(frame.stem.drop_duplicates())
    for index, row in ranking.iterrows():
        st.write(f"**{index+1}위 · 사진 {names.index(row.stem)+1:02d} · {LABELS.get(row.condition, row.condition)}** · F1 {row.f1:.3f} · 원본 대비 {row.delta_f1:+.3f} · 놓친 핵 {int(row.fn)}개")
    choice = st.selectbox("자세히 볼 순위", list(range(len(ranking))), format_func=lambda number: f"{number+1}위")
    row = ranking.iloc[choice]
    st.caption(row.stem)
    describe(row)
    original = baseline_row(frame, row.stem)
    a, b, c = st.columns(3)
    with a:
        picture(BASELINE, original.overlay_file, "원본 사진", plain=True)
    with b:
        picture(BASELINE, row.overlay_file, "문제가 된 조건", plain=True)
    with c:
        picture(BASELINE, row.overlay_file, "이 조건의 AI 경계")
    error_picture(row)


def improvement():
    st.title("잡음을 줄이면 AI가 다시 잘 찾을까요?")
    st.write("강한 잡음에서 F1 하락이 컸던 사진 5장에 3×3 Median Filter를 적용했습니다. 주변 9개 픽셀의 가운데 값을 써서 잡음을 줄이는 방법입니다.")
    try:
        frame = read_results(FOLLOWUP)
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        st.info("추가 실험 결과를 준비 중입니다. 완료 후 이 화면에서 실제 점수를 확인할 수 있습니다.")
        return
    means = frame.groupby("condition").f1.mean().reindex(["original", "noise_3", "median_3"])
    delta = means["median_3"] - means["noise_3"]
    st.metric("잡음 제거 후 평균 F1 변화", f"{delta:+.3f}")
    st.caption("같은 5장의 원본·강한 잡음도 다시 계산했습니다. 기존 200회 결과와 비교한 재현 여부는 개발 기록에 남겼습니다.")
    st.bar_chart(pd.DataFrame({"평균 F1": means.values}, index=[LABELS[x] for x in means.index]), y_label="F1")
    stems = list(frame.stem.drop_duplicates())
    stem = st.selectbox("실험 사진", stems, format_func=lambda value: f"어려운 사진 {stems.index(value)+1}")
    rows = frame[frame.stem == stem].set_index("condition").loc[["original", "noise_3", "median_3"]]
    a, b, c = st.columns(3)
    for col, (condition, row) in zip([a, b, c], rows.iterrows()):
        with col:
            picture(FOLLOWUP, row.overlay_file, LABELS[condition], plain=True)
            st.metric("F1", f"{row.f1:.3f}")
    st.write(change_statement(rows.loc["noise_3", "f1"], rows.loc["median_3", "f1"]))
    comparison = rows[["f1", "foreground_iou"]].rename(index=LABELS, columns={"f1": "F1", "foreground_iou": "IoU · 핵 영역 겹침"})
    st.dataframe(comparison)
    with st.expander("이 실험의 AI 경계와 오류 보기"):
        condition = st.selectbox("확인할 실험 조건", list(rows.index), format_func=LABELS.get)
        row = rows.loc[condition]
        picture(FOLLOWUP, row.overlay_file, "AI가 찾은 경계")
        picture(FOLLOWUP, row.error_file, "초록 · 일치 / 빨강 · 놓침 / 노랑 · 오탐")
    paired = frame.pivot(index="stem", columns="condition", values="f1")
    improved = int((paired.median_3 > paired.noise_3).sum())
    iou_means = frame.groupby("condition").foreground_iou.mean()
    st.caption(f"{len(paired)}장 중 {improved}장의 F1이 높아졌습니다. 평균 IoU는 {iou_means['noise_3']:.3f}에서 {iou_means['median_3']:.3f}로 바뀌었습니다. 핵을 찾는 정도와 경계의 겹침을 함께 살펴보세요.")
    st.caption("성능 하락이 큰 5장만 골랐으므로 전체 이미지에서도 효과가 같다고 주장할 수 없습니다. 잡음 제거로 작은 핵의 정보도 줄어들 수 있다는 설명은 원인 추정입니다.")
    st.download_button("후속 실험 CSV 받기", (FOLLOWUP / "records.csv").read_bytes(), "median_experiment.csv", "text/csv")


def main():
    st.sidebar.title("🔬 NucleoLens AI")
    menu = st.sidebar.radio("메뉴", ["홈", "AI 분석 체험", "AI가 어려워하는 사진 TOP 5", "AI 성능 개선 실험"])
    st.sidebar.caption("v2.1 · AI 세포핵 탐지·정확도 검증 체험 플랫폼")
    st.caption("사전 계산된 실제 AI 결과를 보여줍니다. 웹에서 새 추론을 실행하지 않습니다.")
    try:
        frame = read_results(BASELINE)
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        st.error("분석 기록을 열 수 없습니다. demo_results의 records.csv와 manifest.json을 확인해 주세요.")
        return
    if menu == "홈":
        home(frame)
    elif menu == "AI 분석 체험":
        experience(frame)
    elif menu == "AI가 어려워하는 사진 TOP 5":
        hardest(frame)
    else:
        improvement()
    st.divider()
    st.caption("교육·탐구용 · 세포 노화나 질병을 판정하지 않습니다. 데이터 BBBC039v1 · BBBC038v1 / Broad Institute, CC0. 모델 Cellpose 3.1.1.3 nuclei.")


if __name__ == "__main__":
    main()
