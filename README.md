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

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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

## 개발 시 권장 흐름

1. `small` 모델 + CPU로 기능 검증
2. 정확도 개선이 필요하면 `medium` 또는 `large-v3` 상향
3. 운영 환경에 맞춰 CPU/GPU 설정 재조정
4. 긴 파일은 백그라운드 작업/진행률 로깅/비동기 처리 검토

## 참고

- 화자 분리(diarization)는 `faster-whisper` 단독으로는 제한적이므로 별도 도구 연동이 필요할 수 있습니다.
