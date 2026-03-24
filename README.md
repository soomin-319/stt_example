# faster-whisper 기반 로컬 오디오/비디오 텍스트 추출

이 프로젝트는 로컬 환경에서 오디오/비디오 파일을 텍스트로 전사하기 위한 최소 CLI 도구입니다.

## 기능

- 오디오/비디오 입력 지원 (`.mp3`, `.wav`, `.m4a`, `.mp4`, `.mov` 등)
- 한국어 포함 다국어 전사 (`--language ko` 권장)
- 결과를 여러 포맷으로 저장
  - 전체 텍스트: `.txt`
  - 시간 정보 포함 텍스트: `_with_time.txt`
  - 세그먼트 JSON: `.json`
  - SRT 자막: `.srt`
- CPU/GPU 선택 실행

## 설치

운영체제별로 가상환경 활성화 명령이 다릅니다.

### macOS / Linux (bash, zsh)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

PowerShell에서 아래 오류가 나면 실행 정책 때문에 활성화 스크립트가 차단된 상태입니다.

`PSSecurityException: 이 시스템에서 스크립트를 실행할 수 없습니다`

- 1회만 우회 실행(현재 터미널 세션 한정):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

- 사용자 계정 기준으로 허용(권장, 관리자 권한 불필요):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

정책 확인:

```powershell
Get-ExecutionPolicy -List
```

### Windows CMD

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## 기본 실행

```bash
python transcribe.py sample.mp4
```

기본 출력 파일(prefix=`output`):
- `output.txt`
- `output_with_time.txt`
- `output.json`
- `output.srt`

## 옵션 예시

```bash
python transcribe.py sample.mp4 \
  --output-prefix meeting_2026_03_24 \
  --model-size small \
  --language ko \
  --device cpu \
  --compute-type int8 \
  --beam-size 5
```

GPU 예시:

```bash
python transcribe.py sample.mp4 --device cuda --compute-type float16
```

## 주요 인자

- `input_file`: 전사할 입력 파일 경로 (필수)
- `--output-prefix`: 출력 파일명 prefix (기본값: `output`)
- `--model-size`: `tiny | base | small | medium | large-v3` (기본값: `small`)
- `--language`: 언어 코드 (기본값: `ko`)
- `--device`: `cpu | cuda` (기본값: `cpu`)
- `--compute-type`: `int8 | float16 | float32` (기본값: `int8`)
- `--beam-size`: beam search 크기 (기본값: `5`)
- `--no-srt`: `.srt` 파일 생성 비활성화
- `--fallback-to-cpu`: `--device cuda` 실패 시 CPU(int8)로 자동 재시도

## 개발 시 권장 흐름

1. `small` 모델 + CPU로 기능 검증
2. 정확도 개선이 필요하면 `medium` 또는 `large-v3` 상향
3. 운영 환경에 맞춰 CPU/GPU 설정 재조정
4. 긴 파일은 백그라운드 작업/진행률 로깅/비동기 처리 검토

## 참고

- 화자 분리(diarization)는 `faster-whisper` 단독으로는 제한적이므로 별도 도구 연동이 필요할 수 있습니다.

## 문제 해결 (Windows GPU)

GPU 실행 시 아래와 같은 오류가 날 수 있습니다.

`RuntimeError: Library cublas64_12.dll is not found or cannot be loaded`

이 경우는 코드 문제라기보다 CUDA 런타임/라이브러리 로딩 문제인 경우가 대부분입니다.

### `where.exe cublas64_12.dll`, `where.exe cudnn64_9.dll` 둘 다 못 찾는 경우

아래는 가장 빠른 복구 순서입니다.

1. **GPU 드라이버 확인**

```powershell
nvidia-smi
```

- 명령이 실패하면 NVIDIA 드라이버를 먼저 설치/업데이트해야 합니다.

2. **CUDA 12.x 설치**
- `cublas64_12.dll`은 CUDA 12 계열 DLL입니다.
- 설치 후 보통 아래 경로에 DLL이 생깁니다.
  - `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin`

3. **cuDNN 9 (CUDA 12용) 설치**
- `cudnn64_9.dll`이 필요합니다.
- 설치 방식에 따라 예시 경로가 달라질 수 있습니다.
  - `C:\Program Files\NVIDIA\CUDNN\v9.x\bin`
  - 또는 CUDA `bin` 아래로 복사한 경로

4. **PATH 반영 확인 (새 PowerShell 창에서)**

```powershell
where.exe cublas64_12.dll
where.exe cudnn64_9.dll
```

- 둘 다 경로가 출력되면 DLL 탐색 문제는 해결된 상태입니다.

5. **GPU 전사 재실행**

```powershell
python transcribe.py sample.mp4 --device cuda --compute-type float16
```

> 팁: PATH를 수정했는데도 `where.exe`가 못 찾으면, 터미널을 완전히 종료 후 다시 실행하세요.

### CUDA 13을 사용 중인데 GPU가 계속 실패하는 경우

`faster-whisper`의 최신 `ctranslate2` 조합은 일반적으로 **CUDA 12 + cuDNN 9** 런타임을 요구합니다.  
즉, 시스템에 CUDA 13만 깔려 있으면 `cublas64_12.dll` / `cudnn64_9.dll`을 못 찾아 GPU 실행이 실패할 수 있습니다.

확인:

```powershell
where.exe cublas64_12.dll
where.exe cudnn64_9.dll
```

둘 중 하나라도 못 찾으면 CUDA 12/cuDNN 9 런타임을 추가 설치한 뒤 다시 실행하세요.

- 빠른 우회: CPU로 실행

```powershell
python transcribe.py sample.mp4 --device cpu --compute-type int8
```

- 자동 우회: GPU 실패 시 CPU로 자동 재시도

```powershell
python transcribe.py sample.mp4 --device cuda --compute-type float16 --fallback-to-cpu
```
