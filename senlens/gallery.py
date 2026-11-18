"""Lightweight gallery reader for the cloud, with no inference imports."""
from pathlib import Path
import json
import pandas as pd
from .saved_results import safe_asset


def read_gallery(folder):
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("state")!="complete":
        raise ValueError("사진 분석을 준비 중입니다.")
    frame=pd.read_csv(folder/"gallery.csv")
    required={"uid","dataset","image_id","condition","image_kind","height","width","f1",
              "foreground_iou","matched_mean_iou","gt_count","pred_count","tp","fp","fn",
              "thumbnail_file","input_file","overlay_file","error_file"}
    if not required.issubset(frame.columns) or frame.uid.duplicated().any():
        raise ValueError("갤러리 목록의 항목이나 고유 ID를 확인해 주세요.")
    if len(frame)!=240 or frame.dataset.value_counts().to_dict()!={"BBBC039":200,"BBBC038":40}:
        raise ValueError("240장 갤러리가 완성되지 않았습니다.")
    if not frame.condition.eq("original").all() or not frame.uid.eq(frame.dataset+":"+frame.image_id).all():
        raise ValueError("사진 출처와 분석 조건이 맞지 않습니다.")
    numeric=["height","width","f1","foreground_iou","gt_count","pred_count","tp","fp","fn"]
    frame[numeric]=frame[numeric].apply(pd.to_numeric,errors="raise")
    if frame[numeric].isna().any().any() or not frame.f1.between(0,1).all():
        raise ValueError("측정 기록에 잘못된 값이 있습니다.")
    return frame


def gallery_view(folder):
    import streamlit as st
    from PIL import Image, UnidentifiedImageError
    try:
        frame=read_gallery(folder)
    except (OSError,ValueError,KeyError,pd.errors.ParserError):
        st.info("새 사진 갤러리를 준비하고 있습니다. 아래에서 기존 FluoroCheck 실험을 선택할 수 있습니다.")
        return
    total_col, datasets_col, model_col=st.columns(3)
    total_col.metric("전체 체험 사진", f"{len(frame)}장")
    datasets_col.metric("공개 데이터셋", f"{frame.dataset.nunique()}개")
    model_col.metric("AI 모델", "Cellpose 3 nuclei")
    st.caption("사진 종류는 눈에 보이는 색상과 배경으로 분류했습니다. BBBC038에는 여러 촬영 방식이 섞여 있습니다.")
    a,b,c=st.columns(3)
    with a:
        dataset=st.selectbox("공개 데이터",["전체","BBBC039","BBBC038"])
    filtered=frame if dataset=="전체" else frame[frame.dataset==dataset]
    with b:
        kind=st.selectbox("사진 종류",["전체"]+sorted(filtered.image_kind.unique()))
    if kind!="전체": filtered=filtered[filtered.image_kind==kind]
    with c:
        query=st.text_input("사진 이름 검색",placeholder="이미지 ID 일부 입력")
    if query.strip():
        filtered=filtered[filtered.image_id.str.contains(query.strip(),case=False,regex=False)]
    if filtered.empty:
        st.info("조건에 맞는 사진이 없습니다. 검색어나 필터를 바꿔 보세요.")
        return
    page=st.selectbox("사진 목록 페이지",list(range((len(filtered)+11)//12)),
                       format_func=lambda index:f"{index+1} / {(len(filtered)+11)//12} 페이지",
                       key=f"gallery_page_{dataset}_{kind}_{query}")
    visible=filtered.iloc[page*12:(page+1)*12]
    available=set(filtered.uid)
    if st.session_state.get("gallery_selected") not in available:
        st.session_state.gallery_selected=visible.iloc[0].uid
    st.caption("사진 목록을 아래로 스크롤해 고르세요. 선택 결과는 목록 바로 아래에 나옵니다.")
    with st.container(height=460, border=False):
        for start in range(0,len(visible),3):
            columns=st.columns(3)
            for column,(_,row) in zip(columns,visible.iloc[start:start+3].iterrows()):
                with column:
                    try:
                        with Image.open(safe_asset(folder,row.thumbnail_file)) as image:
                            st.image(image.copy(),use_container_width=True)
                    except (OSError,ValueError,UnidentifiedImageError):
                        st.warning("미리보기를 열 수 없습니다.")
                    label=f"{row.dataset} · {row.image_id[:18]}"
                    st.button(label,key=f"select_{row.uid}",on_click=select_gallery,args=(row.uid,),
                              use_container_width=True)
    row=filtered[filtered.uid==st.session_state.gallery_selected].iloc[0]
    st.subheader(f"{row.dataset} · {row.image_id[:16]}")
    st.caption(f"{row.image_kind} · 원본 {int(row.width)}×{int(row.height)} 픽셀 · {row.source_format}")
    st.write(f"AI가 핵 {int(row.pred_count)}개를 찾았습니다. 사람이 표시한 정답은 {int(row.gt_count)}개입니다. "
             f"정답과 맞은 핵 {int(row.tp)}개, 놓친 핵 {int(row.fn)}개, 잘못 찾은 핵 {int(row.fp)}개입니다.")
    a,b,c,d=st.columns(4)
    a.metric("AI 핵 수",int(row.pred_count))
    b.metric("정답 핵 수",int(row.gt_count))
    c.metric("핵 탐지 F1",f"{row.f1:.3f}")
    d.metric("영역 IoU",f"{row.foreground_iou:.3f}")
    if row.gt_count==0 and row.pred_count==0:
        st.caption("정답과 AI 예측이 모두 0개인 사진입니다. 기존 평가 규칙에 따라 F1은 1로 계산됩니다.")
    from PIL import Image
    def show(relative,caption):
        try:
            with Image.open(safe_asset(folder,relative)) as image:
                st.image(image.copy(),caption=caption,use_container_width=True)
        except (OSError,ValueError,UnidentifiedImageError):
            st.warning("사진을 읽지 못했습니다. 다른 사진을 선택해 주세요.")
    a,b=st.columns(2)
    with a: show(row.input_file,"AI에 넣은 사진")
    with b: show(row.overlay_file,"AI가 찾은 핵 경계")
    st.subheader("AI는 어디에서 틀렸을까요?")
    show(row.error_file,"초록 · 일치 / 빨강 · 놓침 / 노랑 · 오탐")
    with st.expander("점수·정답·전처리 자세히 보기"):
        st.write("사람이 미리 표시한 정답과 예측 핵을 IoU 0.50 이상에서 일대일로 짝짓습니다. F1은 놓침과 오탐을 반영하며 1에 가까울수록 좋습니다. 영역 IoU는 전체 핵 영역의 겹침 비율입니다.")
        value=row.matched_mean_iou
        st.write("짝이 맞은 핵의 평균 IoU · "+(f"{value:.3f}" if pd.notna(value) else "짝이 맞은 핵 없음"))
        channel="RGB의 밝기 채널" if row.input_channel=="luminance" else "흑백 채널"
        inversion="적용" if row.inverted else "미적용"
        st.write(f"입력 · {channel} / 명암 반전 · {inversion} / 핵 지름 · {int(row.diameter_px)} px")
        st.caption(row.uid)
        st.caption("같은 Cellpose 3 nuclei와 고정 지름 17px를 사용했습니다. 촬영 방식과 선정 기준이 달라 두 데이터셋의 점수를 단순 비교해 우열을 판단할 수 없습니다.")
    with st.expander("데이터셋별 원본 요약"):
        table=frame.groupby("dataset").agg(사진수=("uid","size"),평균F1=("f1","mean"),평균영역IoU=("foreground_iou","mean"))
        st.dataframe(table)
    st.download_button("240장 원본 분석 CSV",(Path(folder)/"gallery.csv").read_bytes(),"nucleolens_gallery.csv","text/csv")


def select_gallery(uid):
    import streamlit as st
    st.session_state.gallery_selected=uid
