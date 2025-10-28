from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image


TARGET_SIZE_DEFAULT = 1_000_000  # 约 1 MB


@dataclass
class CompressResult:
    path: Path
    original_size: int
    final_size: int
    succeeded: bool
    note: str = ""


def _iter_image_files(directory: Path, recursive: bool) -> Iterable[Path]:
    """遍历目录下的图片文件。"""
    patterns = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
    if recursive:
        for pattern in patterns:
            yield from directory.rglob(pattern)
    else:
        for pattern in patterns:
            yield from directory.glob(pattern)


def _save_to_buffer(image: Image.Image, format_hint: str, quality: int) -> BytesIO:
    """将图片按指定质量保存到内存缓冲区。"""
    buffer = BytesIO()
    save_kwargs = {"format": format_hint, "quality": quality, "optimize": True}
    # 对 JPEG 启用渐进式
    if format_hint.upper() in {"JPEG", "JPG"}:
        save_kwargs["progressive"] = True
    image.save(buffer, **save_kwargs)
    buffer.seek(0)
    return buffer


def _compress_image(
    image_path: Path,
    target_size: int,
    min_quality: int,
    quality_step: int,
    resize_step: float,
) -> CompressResult:
    original_size = image_path.stat().st_size

    with Image.open(image_path) as img:
        img_format = img.format or "JPEG"
        working_img = img.convert("RGB")

    quality = 95
    width, height = working_img.size
    last_buffer: Optional[BytesIO] = None
    note = ""

    while True:
        buffer = _save_to_buffer(working_img, "JPEG", quality)
        size = buffer.getbuffer().nbytes
        if size <= target_size:
            last_buffer = buffer
            break

        if quality > min_quality:
            quality = max(min_quality, quality - quality_step)
            continue

        new_width = max(1, int(width * resize_step))
        new_height = max(1, int(height * resize_step))
        if (new_width, new_height) == (width, height):
            note = "无法进一步压缩，已达到最小尺寸或质量。"
            last_buffer = buffer
            break

        working_img = working_img.resize((new_width, new_height), Image.LANCZOS)
        width, height = working_img.size
        # 尝试再次提高质量以平衡清晰度
        quality = min(95, max(min_quality, quality))

    if last_buffer is None:
        return CompressResult(
            path=image_path,
            original_size=original_size,
            final_size=original_size,
            succeeded=False,
            note="压缩过程中出现未知问题。",
        )

    image_path.write_bytes(last_buffer.getvalue())
    final_size = image_path.stat().st_size
    success = final_size <= target_size

    if not success and not note:
        note = "已尽力压缩，但仍超过目标大小。"

    if success and note:
        note = f"{note} (最终大小 {final_size} bytes)"

    if not note and img_format.upper() != "JPEG":
        note = f"原始格式 {img_format} 已转换为 JPEG。"

    return CompressResult(
        path=image_path,
        original_size=original_size,
        final_size=final_size,
        succeeded=success,
        note=note,
    )


def compress_directory(
    directory: str | Path,
    target_size: int = TARGET_SIZE_DEFAULT,
    recursive: bool = True,
    min_quality: int = 30,
    quality_step: int = 5,
    resize_step: float = 0.9,
) -> list[CompressResult]:
    """压缩目录中的所有图片文件，使其不超过指定大小。

    Args:
        directory: 图片所在目录。
        target_size: 目标大小（字节），默认 1 MB。
        recursive: 是否递归遍历子目录。
        min_quality: JPEG 压缩的最低质量值。
        quality_step: 每次尝试降低的质量步长。
        resize_step: 无法通过质量压缩时的缩放比例。

    Returns:
        每个文件的压缩结果列表。
    """
    dir_path = Path(directory).expanduser().resolve()
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {dir_path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {dir_path}")

    results: list[CompressResult] = []
    for image_file in _iter_image_files(dir_path, recursive):
        result = _compress_image(
            image_file,
            target_size=target_size,
            min_quality=min_quality,
            quality_step=quality_step,
            resize_step=resize_step,
        )
        results.append(result)
    return results


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}"
        size /= 1024
    return f"{size:.0f}TB"


def _print_report(results: Iterable[CompressResult], target_size: int) -> None:
    print(f"目标大小: {_format_size(target_size)}")
    for res in results:
        status = "成功" if res.succeeded else "未达标"
        note = f" | {res.note}" if res.note else ""
        print(
            f"{status}: {res.path} | 原始 {_format_size(res.original_size)} -> "
            f"最终 {_format_size(res.final_size)}{note}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="压缩目录中的图片到指定大小以下。")
    parser.add_argument("directory", help="待压缩的图片目录。")
    parser.add_argument(
        "--target",
        type=float,
        default=1.0,
        help="目标大小（MB），默认 1.0",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="仅压缩当前目录，不递归子目录。",
    )
    parser.add_argument(
        "--min-quality",
        type=int,
        default=30,
        help="JPEG 最低质量，默认 30。",
    )
    parser.add_argument(
        "--quality-step",
        type=int,
        default=5,
        help="每次调整质量的步长，默认 5。",
    )
    parser.add_argument(
        "--resize-step",
        type=float,
        default=0.9,
        help="无法通过质量压缩时的缩放比例，默认 0.9。",
    )

    args = parser.parse_args()
    target_bytes = int(args.target * 1024 * 1024)
    results = compress_directory(
        directory=args.directory,
        target_size=target_bytes,
        recursive=not args.no_recursive,
        min_quality=args.min_quality,
        quality_step=args.quality_step,
        resize_step=args.resize_step,
    )
    _print_report(results, target_bytes)
