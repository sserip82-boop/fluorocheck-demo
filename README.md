# NucleoLens AI v2.1

**AI 세포핵 탐지·정확도 검증 체험 플랫폼**

“AI는 세포핵을 얼마나 정확하게 찾을까?”

프로젝트 폴더의 PowerShell에서 실행합니다.

~~~powershell
$env:CELLPOSE_LOCAL_MODELS_PATH = Join-Path (Get-Location) '.venv\cellpose-models'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
~~~

브라우저에서 http://127.0.0.1:8502 를 엽니다.

1. **홈**에서 240장 원본 사진과 기존 20장 품질 실험의 차이를 확인합니다.
2. **AI 분석 체험 → 240장 사진 갤러리**에서 데이터셋·종류·검색으로 사진을 찾고 썸네일 아래 이름을 누릅니다.
3. **AI 분석 체험 → FluoroCheck · 밝기·잡음·흐림**에서 기존 20장의 10가지 조건을 비교합니다.
4. **AI가 어려워하는 사진 TOP 5**와 **AI 성능 개선 실험**에서 기존 연구 결과를 봅니다.

BBBC038의 사진 종류는 색상과 배경을 기준으로 표시합니다. 모든 사진을 형광 영상으로 분류하지 않습니다.
F1이 낮거나 검출하지 못한 사진도 유지합니다. 정답·예측 모두 0개면 기존 F1 규칙상 1이며 화면에 설명합니다.
서로 다른 촬영 환경과 선정 방식을 가진 두 데이터셋의 평균만으로 모델 우열을 결론내릴 수 없습니다.

처리 명령은 다음과 같습니다. 데이터와 결과는 기존 파일을 보존하며 별도 폴더로 관리합니다.

~~~powershell
.\.venv\Scripts\python.exe download_bbbc038.py
.\.venv\Scripts\python.exe prepare_gallery.py
.\.venv\Scripts\python.exe run_gallery.py
.\.venv\Scripts\python.exe export_v21.py --dest outputs/nucleolens-v21-web
~~~

이미 다운로드한 공식 ZIP은 재사용하고 CRC를 검사합니다.
prepare_gallery.py의 inventory 폴더가 이미 있다면 재실행해 덮어쓰지 않습니다.
run_gallery.py는 체크포인트가 있는 사진을 재추론하지 않으며 원본·정답 해시와 프로토콜을 확인합니다.
export_v21.py의 대상 폴더가 이미 있다면 새 이름을 사용합니다.
공개 GitHub 업로드나 Streamlit 재배포는 사용자 승인 후 진행합니다.
새 패키지의 requirements.txt에는 Cellpose·PyTorch가 없습니다.

아래는 이전 버전의 사용 기록입니다.

---

# Senescence Lens v2.0 시작하기

이미 계산한 200회 결과로 사진을 즉시 비교하고, 어려운 사례 TOP 5와 실제 잡음 제거 후속 실험을 확인합니다.

프로젝트 폴더의 PowerShell에서 실행하세요.

~~~powershell
$env:CELLPOSE_LOCAL_MODELS_PATH = Join-Path (Get-Location) '.venv\cellpose-models'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
~~~

브라우저에서 http://127.0.0.1:8502 를 엽니다.

1. **홈**에서 기존 200회 요약을 확인합니다.
2. **AI 분석 체험**에서 사진과 조건을 선택합니다. 오류 표시는 20장 전체의 원본·밝기·잡음·흐림 200개 조건에 준비되어 있습니다.
3. **AI가 어려워하는 사진 TOP 5**에서 순위 기준과 자세히 볼 순위를 고릅니다.
4. **AI 성능 개선 실험**에서 같은 사진의 원본·잡음·Median Filter 결과를 비교합니다.

기존 로컬 AI 분석과 20장 선정 기능은 홈의 **기존 연구 도구**를 펼쳐 이용합니다.
개발 내역, 정확한 실험 조건, 한계와 검증은 DEVELOPMENT_LOG.md에 기록했습니다.

웹 시연 파일은 다음 명령으로 새 폴더에 준비합니다. 공개 업로드는 별도 작업입니다.

~~~powershell
.\.venv\Scripts\python.exe export_v2.py --dest outputs/v2-web-ready
~~~

해당 폴더가 이미 있으면 새 이름을 지정하세요.
기존 온라인 저장소와 v1 결과는 보존됩니다. 아래는 기존 v1의 로컬 분석 사용 안내입니다.

---

# 🔬 Senescence Lens / FluoroCheck — 초보자 시작 안내

> 본 앱은 **진짜 Cellpose AI**로 BBBC039 형광 세포핵을 탐지하고, 이미지 밝기·잡음·흐림이 탐지 정확도에 미치는 영향을 분석하는 교육 프로젝트입니다. 의료·노화 진단 앱이 아닙니다.

## 0. 무엇이 들어 있나요?

- `PRD.md` — 17개 선택을 반영한 상세 최종 개발기획서
- `app.py` — 로컬 AI 분석·20장 선정·웹 결과 시연 UI
- `download_data.py` — 공식 BBBC039 TIFF, 마스크, 메타데이터 다운로드
- `run_batch.py` — 실제 Cellpose를 20장×10조건=200회 실행해 CSV/PNG/JSON 기록
- `export_web.py` — 성공한 실제 실험 결과만 온라인 시연 폴더에 반영
- `tests` — 수치 계산 및 이미지 변형 단위 테스트
- `senlens` — 실제 구현 코드

## 1. Windows 11 / VS Code 설치

**Python 3.11 64비트** 설치 후 VS Code에서 프로젝트 폴더를 엽니다. VS Code 메뉴 `터미널 > 새 터미널`을 선택하고 아래를 순서대로 실행합니다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
```

> PowerShell 정책 때문에 `Activate.ps1`가 실행되지 않아도 위처럼 `.venv\\Scripts\\python.exe`를 직접 실행하면 됩니다.

**중요:** `requirements.txt`는 온라인 결과 시연 전용입니다. 실제 Cellpose 분석을 하려면 **`requirements-local.txt`**를 설치해야 합니다.

## 2. 공개 데이터 내려받기

```powershell
.\.venv\Scripts\python.exe download_data.py --yes
```

공식 파일은 이미지 약 **77.9MB**, 정답 약 2.8MB, 메타데이터 약 18KB입니다. 최초 다운로드에는 인터넷 접속이 필요합니다. `data/images`, `data/masks`, `data/metadata` 폴더에 안전하게 압축을 풉니다.

공식 데이터 링크: https://bbbc.broadinstitute.org/BBBC039

**공식 데이터는 Hoechst 염색 세포핵 이미지**이며, 특정 세포의 노화 상태 라벨은 없습니다.

## 3. 앱에서 세포핵 1장 실제 분석하기

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

1. 브라우저에서 앱을 열고 **`실제 AI 분석`** 메뉴를 선택합니다.
2. 공식 TIFF 이미지 하나를 선택합니다.
3. `원본`을 고르고 **`실제 Cellpose 3 nuclei AI 실행`** 버튼을 누릅니다.
4. 첫 실행에서 AI 가중치를 다운로드해야 하므로 인터넷이 필요할 수 있습니다.
5. 왼쪽 입력 사진과 오른쪽 핵 경계, 핵 개수, F1, IoU를 확인합니다.
6. 다른 조건(밝기/잡음/흐림)을 선택해 달라지는 모습을 살펴봅니다.
7. 저장 결과는 `outputs/single_...`에 있습니다.

**F1 / IoU가 보이지 않는다면?** 정답 PNG가 없거나 파일이 맞지 않는 경우입니다. 이때는 임의 점수를 만들지 않고 `N/A`로 표시합니다.

## 4. 직접 분석할 20장과 이유 선택

앱 사이드바에서 **`20장 선정`**을 선택합니다.

1. 이미지 목록에서 직접 20장을 선택합니다.
2. 이유를 남기고 싶으면 **사진을 고른 이유 (선택)**을 열어 적습니다.
3. `20장 선정 목록 저장`을 누릅니다.
4. `data/selection.csv` 파일이 생성되었는지 확인합니다.

> 20장 수동 선정은 계획된 선택(Q14=B)입니다. **결과를 본 뒤 높은 점수만 남기는 방식은 하지 않습니다.**

## 5. 실제 AI 200회 실험

한 장을 10가지 조건으로 먼저 테스트합니다.

```powershell
.\.venv\Scripts\python.exe run_batch.py --limit 1
```

정상이라면 10개 기록이 생깁니다. 이후 전체 20장을 실행합니다.

```powershell
.\.venv\Scripts\python.exe run_batch.py
```

`outputs/run_날짜시간/` 아래에 `records.csv`, `summary.csv`, `summary.png`, `manifest.json`, 미리보기 이미지가 생성됩니다. 원본 20개 + 변형 180개 = **200개의 실제 추론 기록**이어야 합니다.

**AI가 잘못 탐지한 이미지도 삭제하지 마세요.** 실패 원인을 조사하는 것이 연구의 핵심입니다.

## 6. 웹 시연 준비

완료된 `outputs/run_...` 폴더 경로를 확인합니다. 실제 완료 결과만 다음 명령으로 내보냅니다.

```powershell
.\.venv\Scripts\python.exe export_web.py outputs/run_20261114T000000Z
```

> 위 폴더명은 예시입니다. **실제로 생성된 폴더 이름**으로 바꾸세요.

`demo_results/`가 생성된 후 GitHub에 코드와 해당 폴더를 올리고, Streamlit Community Cloud에서 `app.py`를 선택해 배포합니다. 배포에는 `requirements.txt`만 사용하며 **웹에서는 가중치를 다운로드하거나 새 이미지를 분석하지 않습니다.**

Community Cloud: https://share.streamlit.io/

**중요:** 이 프로젝트 파일을 받았다고 해서 웹 주소가 자동 생성되는 것은 아닙니다. GitHub 업로드와 배포는 직접 완료해야 합니다.

## 7. 테스트 및 오류 확인

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**핵심 용어**

- **Cellpose**: 사전 학습된 세포/세포핵 경계 탐지 AI 모델.
- **Ground truth(정답 마스크)**: 사람이 핵의 영역을 색상으로 표시한 기준 데이터.
- **F1**: AI가 실제 핵을 얼마나 잘 찾는지(놓침·오탐) 측정하는 점수.
- **IoU**: AI가 표시한 영역과 정답 영역이 겹치는 정도.
- **TP/FP/FN**: 맞힌 핵 / 잘못 찾은 핵 / 놓친 핵.
- **CSV**: 엑셀로 열어볼 수 있는 표 형태의 파일.
- **PRD**: 만들 앱의 목표·기능·검증 기준을 상세히 정리한 문서.

## 8. 포트폴리오에서 학생이 직접 보여줄 것

1. “AI도 관찰 환경 때문에 잘못 판단할까?” 연구 질문을 정한 이유.
2. 이미지 선정 기준과 비교하고 싶은 특징.
3. Codex에 어떤 기능을 지시했는지와 실제 오류 해결 기록.
4. Cellpose가 핵을 놓치거나 2개를 합친 사례의 스크린샷.
5. 조건별 F1 그래프에서 해석한 사실, 예외 사례와 불확실성.
6. 내가 직접 한 일과 AI 코딩 도움·보호자 지원을 나누어 적은 기록.

## 9. 현재 검증 상태와 제한

- 코드에는 **실제 Cellpose 호출**이 있습니다. 가짜 AI 성능 수치를 만들지 않습니다.
- 소스 작성 환경에서는 단위 테스트를 실행했으나, 외부 데이터와 AI 가중치 다운로드가 제한되어 실제 Cellpose 추론과 온라인 배포는 완료하지 못했습니다.
- Windows 사용자의 컴퓨터에서 **1장 실제 추론 → 20장 선정 → 200회 검증 → 웹 배포**를 수행해 주세요.
- 프로젝트 자체는 의료기기가 아니며, 세포 노화 여부를 진단하지 않습니다.
- Cellpose 사전 학습 가중치의 학습 데이터에는 비상업적 사용 조건이 관련될 수 있으므로 상업적 이용 전에 별도 확인이 필요합니다.

### 출처

- Broad BBBC039v1: https://bbbc.broadinstitute.org/BBBC039
- Cellpose v3 모델 문서: https://cellpose.readthedocs.io/en/v3.1.1.1/models.html
- Cellpose 논문: Stringer et al., Nature Methods (2021).
- Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
