"""Senescence Lens / FluoroCheck -- real Cellpose locally, honest precomputed web demo."""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import io

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DEMOS = ROOT / 'demo_results'
OUTPUTS = ROOT / 'outputs'
AVAILABLE_LOCAL = importlib.util.find_spec('cellpose') is not None

st.set_page_config(page_title='Senescence Lens | FluoroCheck', page_icon='🔬', layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.3rem;max-width:1340px}
h1,h2,h3{letter-spacing:-.035em}
[data-testid="stMetric"]{border:1px solid #dde5ef;border-radius:14px;padding:14px}
div.stButton>button[kind="primary"]{background:#295aab;border-radius:12px}
</style>''', unsafe_allow_html=True)


def heading():
    st.title('🔬 Senescence Lens')
    st.caption('AI Fluorescence Image Analysis & Reliability Lab | 교육·연구용 프로토타입')
    st.info('세포핵 형태 및 탐지 성능 분석 도구입니다. 세포 노화·질병을 진단하거나 의료적 판단을 제공하지 않습니다.', icon='ℹ️')


def get_available_pairs():
    from senlens.io_data import pair_dataset
    return [p for p in pair_dataset(DATA) if p[2] is not None]


def local_analysis():
    st.subheader('① 세포핵 실제 AI 분석')
    st.caption('이 페이지는 Cellpose 3 모델을 로컬 CPU에서 실행합니다. AI 결과를 시뮬레이션하지 않습니다.')
    if not AVAILABLE_LOCAL:
        st.error('현재 환경에 Cellpose가 없습니다. 로컬 설치 시 `pip install -r requirements-local.txt`를 실행하세요.')
        return
    pairs = get_available_pairs()
    up = st.radio('이미지 입력 방식', ['BBBC039 데이터에서 선택', '내 TIFF 이미지 업로드'], horizontal=True)
    input_name = None
    gt = None
    if up.startswith('BBBC039'):
        if not pairs:
            st.warning('공식 데이터가 없습니다. `python download_data.py --yes`를 먼저 실행하세요.')
            return
        names = [x[0] for x in pairs]
        input_name = st.selectbox('공개 데이터 이미지 선택', names)
        _, ipath, mpath = next(x for x in pairs if x[0] == input_name)
        from senlens.io_data import read_image, decode_ground_truth
        raw = read_image(ipath)
        gt = decode_ground_truth(mpath)
        st.caption(f'데이터: BBBC039v1 | 정답 있음 | 원본 {raw.shape}, {raw.dtype}')
    else:
        upload = st.file_uploader('2D TIFF 원본 이미지', type=['tif', 'tiff'])
        gtupload = st.file_uploader('정답 마스크 PNG (선택)', type=['png'])
        if upload is None:
            st.warning('분석할 TIFF 파일을 선택하세요.')
            return
        input_name = Path(upload.name).stem
        from senlens.io_data import read_image, decode_ground_truth
        try:
            raw = read_image(upload.getvalue())
            if gtupload:
                gt = decode_ground_truth(gtupload.getvalue())
        except Exception as e:
            st.error(str(e)); return
        st.caption('개인 업로드 이미지에는 촬영조건·사용 권한이 별도로 필요합니다.')
    from senlens.processing import CONDITIONS, normalize_once, perturb, seed_for_image
    keys = [x[0] for x in CONDITIONS]
    labels = {x[0]: x[1] for x in CONDITIONS}
    condition = st.selectbox('실험 조건 (원본 또는 이미지 품질 변형)', keys, format_func=lambda x: labels[x])
    st.caption('원본에서 계산한 명암 기준을 모든 변형에 고정하고 Cellpose 내부 자동 정규화를 끕니다.')
    zoom = st.slider('중앙 확대 배율', min_value=1, max_value=4, value=1)
    boundaries = st.checkbox('AI 세포핵 경계 표시', value=True)
    if st.button('실제 Cellpose 3 nuclei AI 실행', type='primary'):
        try:
            from senlens.inference import load_model, infer
            from senlens.metrics import score_instances, nuclei_statistics
            from senlens.visuals import rgb_overlay, zoom_center
            from senlens.processing import preview_gray
            import numpy as np
            from PIL import Image
            from senlens.report import save_csv, save_json
            base, (lo, hi) = normalize_once(raw)
            variant = perturb(base, condition, seed_for_image(input_name))
            with st.spinner('Cellpose nuclei 모델이 실제로 실행 중입니다. 첫 실행에는 모델 다운로드가 필요할 수 있습니다.'):
                model = load_model()
                predicted = infer(model, variant, diameter=17)
            a, b = st.columns(2)
            with a:
                st.image(zoom_center(preview_gray(variant), zoom), caption='분석 입력 이미지', clamp=True, use_container_width=True)
            with b:
                shown = rgb_overlay(variant, predicted) if boundaries else preview_gray(variant)
                st.image(zoom_center(shown, zoom), caption='AI가 찾은 핵의 경계 (황색) — 표시 전환 가능', use_container_width=True)
            nuclei = nuclei_statistics(predicted)
            count = len(nuclei)
            if gt is not None:
                result = score_instances(predicted, gt)
                c1,c2,c3,c4 = st.columns(4)
                c1.metric('AI 핵 개수', count)
                c2.metric('정답 개수', result['gt_count'])
                c3.metric('Instance F1', f"{result['f1']:.3f}")
                c4.metric('Foreground IoU', f"{result['foreground_iou']:.3f}")
                st.caption('F1은 개별 핵을 IoU≥0.5로 일대일 대응하여 계산, Foreground IoU는 모든 핵 영역의 픽셀 단위 일치도입니다.')
            else:
                result = {'pred_count': count, 'gt_count': None, 'f1': None}
                st.metric('탐지된 세포핵 수', count)
                st.warning('정답 이미지가 없어 F1·IoU는 계산할 수 없습니다. 임의 수치를 표시하지 않습니다.')
            st.dataframe(pd.DataFrame(nuclei).head(30), use_container_width=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            out = OUTPUTS / f'single_{stamp}'
            out.mkdir(parents=True, exist_ok=True)
            Image.fromarray(rgb_overlay(variant, predicted)).save(out/'overlay.png')
            save_csv(out/'metrics.csv', [{'stem': input_name, 'condition': condition, **result}])
            save_csv(out/'nuclei.csv', nuclei if nuclei else [{'nucleus_id':'','area_px2':'','circularity':''}])
            save_json(out/'manifest.json', {'real_cellpose': True, 'source': input_name,
                'condition': condition, 'baseline_p1_p99': [lo, hi], 'model':'nuclei',
                'diameter_px': 17, 'normalize_in_model': False, 'captured_utc': stamp})
            st.success(f'실제 AI 분석 기록 저장: {out.relative_to(ROOT)}')
            with (out/'metrics.csv').open('rb') as f:
                st.download_button('측정 CSV 다운로드', data=f.read(), file_name='senescence_lens_metrics.csv', mime='text/csv')
        except Exception as e:
            st.exception(e)


def choose_images():
    st.subheader('② 내가 직접 고르는 20장 — 선정 근거 기록')
    pairs = get_available_pairs()
    if not pairs:
        st.warning('BBBC039 데이터를 먼저 내려받으세요: `python download_data.py --yes`')
        return
    by_name = {p[0]: p for p in pairs}
    selection_file = DATA / 'selection.csv'
    previous = {}
    if selection_file.exists():
        with selection_file.open(encoding='utf-8-sig', newline='') as f:
            previous = {r['stem']: r.get('reason','') for r in csv.DictReader(f)}
    from senlens.io_data import read_image
    from senlens.processing import normalize_once, preview_gray

    preview_col, selection_col = st.columns(2)
    with preview_col:
        candidate = st.selectbox('미리 볼 원본 사진', sorted(by_name))
        _, image_path, _ = by_name[candidate]
        image, _ = normalize_once(read_image(image_path))
        st.image(preview_gray(image), use_container_width=True)
    with selection_col:
        st.caption('원본의 밝기, 핵 모양, 핵이 모여 있는 정도를 살펴보고 사진을 고르세요.')
        st.button(
            '이 사진을 선정 목록에 추가',
            disabled=candidate in st.session_state.get('selected_images', previous)
            or len(st.session_state.get('selected_images', previous)) >= 20,
            on_click=lambda: st.session_state.selected_images.append(candidate),
        )
    chosen = st.multiselect('실험에 사용할 이미지 20장 선택', sorted(by_name), default=list(previous),
                            max_selections=20, key='selected_images')
    st.write(f'현재 **{len(chosen)} / 20장** 선택')
    if chosen:
        with st.expander('사진을 고른 이유 (선택)'):
            editor = st.data_editor(
                pd.DataFrame([{'stem': n, 'reason': previous.get(n, '')} for n in chosen]),
                hide_index=True, disabled=['stem'], num_rows='fixed', use_container_width=True,
                column_config={'reason': '선정 이유 (선택)'},
            )
        if st.button('20장 선정 목록 저장', type='primary'):
            if len(chosen) != 20:
                st.error('정확히 20장을 선택해야 합니다.')
            else:
                selection_file.parent.mkdir(parents=True,exist_ok=True)
                editor.to_csv(selection_file, index=False, encoding='utf-8-sig')
                st.success('저장됨: data/selection.csv. 다음 명령: python run_batch.py --limit 1')
    st.caption('결과를 본 뒤 점수가 낮은 사진을 목록에서 빼지 마세요.')


def find_results():
    candidates = []
    if (DEMOS/'manifest.json').exists():
        candidates.append(DEMOS)
    if OUTPUTS.exists():
        candidates.extend(sorted((p for p in OUTPUTS.glob('run_*') if (p/'manifest.json').exists()),reverse=True))
    return candidates


def result_view():
    st.subheader('③ FluoroCheck — 실험 결과 보기')
    st.caption('실제 AI를 실행하고 저장한 결과만 표시합니다. 웹에서는 AI를 새로 실행하지 않습니다.')
    folders = find_results()
    if not folders:
        st.warning('아직 실제 분석 결과가 없습니다. 로컬에서 `python run_batch.py`로 분석한 다음 `python export_web.py 출력폴더`를 실행하세요.')
        return
    folder = st.selectbox('실험 결과 선택', folders, format_func=lambda p: str(p.relative_to(ROOT)))
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if not manifest.get('real_cellpose'):
        st.error('실제 Cellpose 실행 증빙이 없는 결과입니다.');return
    if manifest.get('state') != 'complete':
        st.warning('부분 완료 결과: 전체 200회가 성공한 결과가 아닙니다.')
    if not (folder/'records.csv').exists():
        st.error('records.csv 파일이 없습니다.'); return
    df = pd.read_csv(folder/'records.csv')
    st.caption(f"Cellpose 실제 추론: {manifest.get('completed_runs','?')} / {manifest.get('expected_runs','?')}회 · "
               f"모델 {manifest.get('installed_cellpose',manifest.get('model_version_target'))} · "
               f"선정 방식: {manifest.get('selection_method','미기록')}")
    mean_f1 = df['f1'].mean() if 'f1' in df else float('nan')
    original = df[df.condition=='original']
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('완료된 추론', len(df))
    c2.metric('분석 이미지 수', df.stem.nunique())
    c3.metric('원본 평균 F1', f"{original.f1.mean():.3f}" if not original.empty else '—')
    c4.metric('전체 조건 평균 F1', f'{mean_f1:.3f}')
    if (folder/'summary.png').exists():
        st.image(str(folder/'summary.png'), use_container_width=True)
    stems = list(df.stem.drop_duplicates())
    current = st.selectbox('이미지 선택', stems)
    options = list(df[df.stem==current].condition)
    condition = st.selectbox('조건 선택', options)
    row = df[(df.stem==current)&(df.condition==condition)].iloc[0]
    first = df[(df.stem==current)&(df.condition=='original')].iloc[0]
    zoom = st.slider('중앙 확대 배율', min_value=1, max_value=4, value=1, key='demo_zoom')
    boundaries = st.checkbox('AI 핵 경계 표시', value=True, key='demo_boundaries')
    a,b = st.columns(2)
    from PIL import Image
    import numpy as np
    def show_result(path, alt):
        from PIL import Image
        if not boundaries:
            plain = path.with_name(path.stem + '_input.png')
            if plain.exists(): path = plain
            else:
                st.caption('이전 버전에는 경계 없는 미리보기가 없습니다.')
        if path.exists():
            # Cropping via PIL avoids requiring OpenCV in the cloud demo.
            im = Image.open(path)
            if zoom > 1:
                w,h=im.size; cw,ch=max(1,w//zoom),max(1,h//zoom)
                x,y=(w-cw)//2,(h-ch)//2
                im=im.crop((x,y,x+cw,y+ch)).resize((w,h))
            st.image(im, caption=alt, use_container_width=True)
        else: st.info('이 이미지 미리보기는 저장되지 않았습니다. CSV 수치를 확인하세요.')
    with a:
        st.markdown('**원본 AI 탐지 결과**')
        fp = folder / str(first.get('overlay_file',''))
        if first.get('overlay_file') and fp.exists(): show_result(fp,'원본 분석 결과')
        else: st.info('이 이미지의 웹 미리보기는 저장되지 않았습니다. 원본 수치는 CSV에 있습니다.')
    with b:
        st.markdown('**선택 조건 AI 탐지 결과**')
        fp = folder / str(row.get('overlay_file',''))
        if row.get('overlay_file') and fp.exists(): show_result(fp,'변형 이미지 분석 결과')
        else: st.info('미리보기 없음. 다음 저장 시 --preview-count 값을 조정할 수 있습니다.')
    reason = row.get('selection_reason')
    if pd.notna(reason) and str(reason).strip():
        st.write(f'선정 이유: {reason}')
    st.dataframe(df[df.stem==current][['condition','gt_count','pred_count','tp','fp','fn','f1','foreground_iou','abs_count_error']],
                 hide_index=True, use_container_width=True)
    st.download_button('200회 전체 분석 CSV 다운로드', data=(folder/'records.csv').read_bytes(),
            file_name='senescence_lens_records.csv', mime='text/csv')
    st.info('F1은 개별 핵을 IoU≥0.50 조건으로 일대일 대응한 결과입니다. 원본·변형 모두 동일한 수작업 정답 마스크를 사용합니다.')


def guide():
    st.subheader('④ 사용 방법과 실험 기록')
    st.markdown('''
    **실제 AI 분석과 온라인 시연은 다릅니다.** 로컬 모드는 Cellpose 모델을 실행합니다. 온라인 결과 화면은 로컬에서 계산한 정답 기반 검증 기록을 보여줍니다.

    **실습 순서**
    1. Windows에 Python 3.11 설치 → `py -3.11 -m venv .venv` → `.venv\\Scripts\\activate`.
    2. `python -m pip install -r requirements-local.txt`.
    3. `python download_data.py --yes`로 BBBC039 이미지·정답 내려받기.
    4. `streamlit run app.py`에서 원본 이미지 1장으로 모델 실행.
    5. '20장 선정' 메뉴에서 사진 20장 저장. 선정 이유 입력은 선택.
    6. `python run_batch.py --limit 1`로 시험 실행.
    7. `python run_batch.py`로 20장 × 10조건 실제 실행.
    8. `python export_web.py outputs/run_실제이름`으로 웹 시연 자료 내보내기.

    **검증 기록 필수:** 학생이 설정한 밝기·잡음·흐림과 이유, 실패한 이미지, 해결한 오류, 출처, 소프트웨어 버전을 기록하세요.

    **데이터 출처:** [Broad BBBC039 공식 페이지](https://bbbc.broadinstitute.org/BBBC039). BBBC039는 Hoechst 염색 핵 분할용 데이터이며 노화 상태 정답 데이터가 아닙니다.

    **기술·연구 한계:** 20장 수동 선정 결과는 모집단 대표성이 없습니다. 이 앱은 의료기기가 아닙니다.
    ''')


def main():
    heading()
    choices = ['실제 AI 분석','20장 선정','FluoroCheck 결과','실행 안내']
    if not AVAILABLE_LOCAL:
        choices = ['FluoroCheck 결과','실행 안내']
    page = st.sidebar.radio('메뉴', choices)
    st.sidebar.divider()
    st.sidebar.caption('Senescence Lens v1.0 · 비진단 연구 도구')
    st.sidebar.caption('개발: 학생 주도 실험 기획 + AI 코딩 지원')
    if page == '실제 AI 분석': local_analysis()
    elif page == '20장 선정': choose_images()
    elif page == 'FluoroCheck 결과': result_view()
    else: guide()
    st.divider()
    st.caption('BBBC039v1 © CC0, Broad Institute · Cellpose: Stringer et al. (2021) · 실제 결과는 실험 실행 후 생성됩니다.')

if __name__ == '__main__':
    main()
