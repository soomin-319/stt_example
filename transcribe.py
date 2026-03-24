import argparse
import json
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3_600_000
    total_ms %= 3_600_000
    minutes = total_ms // 60_000
    total_ms %= 60_000
    secs = total_ms // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="오디오/비디오 파일을 faster-whisper로 텍스트 전사합니다."
    )
    parser.add_argument("input_file", help="입력 오디오/비디오 파일 경로")
    parser.add_argument(
        "--output-prefix",
        default="output",
        help="출력 파일 prefix (예: output -> output.txt, output.json)",
    )
    parser.add_argument(
        "--model-size",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper 모델 크기",
    )
    parser.add_argument("--language", default="ko", help="언어 코드 (예: ko, en)")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="연산 장치 선택",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        choices=["int8", "float16", "float32"],
        help="연산 정밀도",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="beam search 크기",
    )
    parser.add_argument(
        "--no-srt",
        action="store_true",
        help="SRT 파일을 생성하지 않습니다.",
    )
    parser.add_argument(
        "--fallback-to-cpu",
        action="store_true",
        help="GPU(CUDA) 실패 시 CPU(int8)로 자동 재시도합니다.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

    from faster_whisper import WhisperModel

    model = WhisperModel(
        args.model_size,
        device=args.device,
        compute_type=args.compute_type,
    )

    print(f"[INFO] 전사 시작: {input_path}")
    try:
        segments, info = model.transcribe(
            str(input_path),
            beam_size=args.beam_size,
            language=args.language,
        )
        segment_list = list(segments)
    except RuntimeError as exc:
        message = str(exc)
        cuda_lib_error = any(
            keyword in message.lower()
            for keyword in ["cublas", "cudnn", "cuda", "dll is not found", "cannot be loaded"]
        )
        if args.device == "cuda" and args.fallback_to_cpu and cuda_lib_error:
            print(
                "[WARN] CUDA 라이브러리를 찾지 못해 GPU 전사에 실패했습니다. "
                "CPU(int8)로 자동 재시도합니다."
            )
            model = WhisperModel(
                args.model_size,
                device="cpu",
                compute_type="int8",
            )
            segments, info = model.transcribe(
                str(input_path),
                beam_size=args.beam_size,
                language=args.language,
            )
            segment_list = list(segments)
        else:
            raise RuntimeError(
                f"{message}\n\n"
                "GPU 실행 실패로 보입니다. 아래를 확인하세요:\n"
                "1) NVIDIA 드라이버 및 CUDA 런타임 설치 상태\n"
                "2) Python/패키지와 CUDA 버전 호환성\n"
                "3) 빠른 우회: --device cpu --compute-type int8\n"
                "4) 자동 우회: --fallback-to-cpu"
            ) from exc

    output_prefix = Path(args.output_prefix)
    txt_path = output_prefix.with_suffix(".txt")
    timed_txt_path = output_prefix.with_name(f"{output_prefix.name}_with_time").with_suffix(".txt")
    json_path = output_prefix.with_suffix(".json")
    srt_path = output_prefix.with_suffix(".srt")

    with txt_path.open("w", encoding="utf-8") as f:
        for segment in segment_list:
            f.write(segment.text.strip() + "\n")

    with timed_txt_path.open("w", encoding="utf-8") as f:
        for segment in segment_list:
            start = round(segment.start, 2)
            end = round(segment.end, 2)
            f.write(f"[{start}s ~ {end}s] {segment.text.strip()}\n")

    json_data = {
        "meta": {
            "input_file": str(input_path),
            "model_size": args.model_size,
            "device": args.device,
            "compute_type": args.compute_type,
            "beam_size": args.beam_size,
            "language": info.language,
            "language_probability": info.language_probability,
        },
        "segments": [
            {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
            for segment in segment_list
        ],
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    if not args.no_srt:
        with srt_path.open("w", encoding="utf-8") as f:
            for idx, segment in enumerate(segment_list, start=1):
                start_srt = format_timestamp(segment.start)
                end_srt = format_timestamp(segment.end)
                f.write(f"{idx}\n")
                f.write(f"{start_srt} --> {end_srt}\n")
                f.write(f"{segment.text.strip()}\n\n")

    print("[DONE] 전사 완료")
    print(f" - TXT: {txt_path}")
    print(f" - TIMED TXT: {timed_txt_path}")
    print(f" - JSON: {json_path}")
    if not args.no_srt:
        print(f" - SRT: {srt_path}")
    print(f"[INFO] 감지 언어: {info.language} (확률: {info.language_probability:.4f})")


if __name__ == "__main__":
    main()
