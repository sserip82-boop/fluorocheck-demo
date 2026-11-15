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
