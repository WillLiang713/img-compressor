# img-compressor

批量图片压缩工具，可以将目录中的图片压缩到指定大小以下。

## 功能特性

- 支持多种图片格式：JPEG、PNG、WebP、BMP
- 自动将图片转换为 JPEG 格式以获得更好的压缩率
- 智能压缩：先降低质量，再缩小尺寸
- 支持递归处理子目录
- 可自定义目标大小、最低质量等参数

## 安装

### 依赖要求

- Python 3.7+
- Pillow 12.0.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装 Pillow：

```bash
pip install Pillow==12.0.0
```

## 使用方法

### 命令行使用

#### 基本用法

压缩指定目录下的所有图片（包括子目录）：

```bash
python compress.py /path/to/images
```

#### 指定目标大小

将图片压缩到 500 KB 以下：

```bash
python compress.py /path/to/images --target 0.5
```

将图片压缩到 2 MB 以下：

```bash
python compress.py /path/to/images --target 2.0
```

#### 仅处理当前目录（不递归子目录）

```bash
python compress.py /path/to/images --no-recursive
```

#### 自定义压缩参数

```bash
python compress.py /path/to/images \
  --target 1.0 \
  --min-quality 40 \
  --quality-step 10 \
  --resize-step 0.85
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `directory` | 待压缩的图片目录（必需） | - |
| `--target` | 目标大小（MB） | 1.0 |
| `--no-recursive` | 仅压缩当前目录，不递归子目录 | False |
| `--min-quality` | JPEG 最低质量（0-100） | 30 |
| `--quality-step` | 每次调整质量的步长 | 5 |
| `--resize-step` | 无法通过质量压缩时的缩放比例 | 0.9 |

### 作为 Python 模块使用

#### 基本示例

```python
from compress import compress_directory

# 压缩目录中的所有图片
results = compress_directory("/path/to/images")

# 查看压缩结果
for result in results:
    print(f"文件: {result.path}")
    print(f"原始大小: {result.original_size} bytes")
    print(f"压缩后大小: {result.final_size} bytes")
    print(f"是否成功: {result.succeeded}")
    if result.note:
        print(f"备注: {result.note}")
    print("-" * 50)
```

#### 自定义参数

```python
from compress import compress_directory

results = compress_directory(
    directory="/path/to/images",
    target_size=500_000,  # 500 KB（以字节为单位）
    recursive=True,       # 递归处理子目录
    min_quality=40,       # 最低质量 40
    quality_step=10,      # 质量步长 10
    resize_step=0.85      # 缩放比例 0.85
)
```

#### 输出压缩报告

```python
from compress import compress_directory

target_size = 1_000_000  # 1 MB
results = compress_directory("/path/to/images", target_size=target_size)

# 自定义输出格式
for result in results:
    status = "成功" if result.succeeded else "未达标"
    original_mb = result.original_size / 1024 / 1024
    final_mb = result.final_size / 1024 / 1024
    print(f"{status}: {result.path.name}")
    print(f"  原始: {original_mb:.2f}MB -> 最终: {final_mb:.2f}MB")
    if result.note:
        print(f"  备注: {result.note}")
```

## 压缩策略

工具采用两阶段压缩策略：

1. **质量压缩**：从质量 95 开始，按照 `quality_step` 逐步降低质量，直到达到 `min_quality`
2. **尺寸缩放**：如果降低质量仍无法达到目标大小，则按照 `resize_step` 缩小图片尺寸

这种策略可以在保证图片质量的同时，尽可能满足目标文件大小。

## 示例输出

```
目标大小: 1MB
成功: /path/to/images/photo1.jpg | 原始 3MB -> 最终 980KB | 原始格式 PNG 已转换为 JPEG。
成功: /path/to/images/photo2.jpg | 原始 1MB -> 最终 850KB
未达标: /path/to/images/photo3.jpg | 原始 5MB -> 最终 1MB | 已尽力压缩，但仍超过目标大小。
成功: /path/to/images/photo4.png | 原始 2MB -> 最终 750KB | 原始格式 PNG 已转换为 JPEG。
```

## 注意事项

- **原文件会被覆盖**：压缩操作会直接修改原始文件，建议提前备份重要图片
- **格式转换**：所有图片都会被转换为 JPEG 格式以获得更好的压缩效果
- **RGB 模式**：图片会被转换为 RGB 模式，可能会丢失透明通道（alpha channel）
- **不可逆操作**：压缩是有损的，且会覆盖原文件，无法恢复

## 许可证

本项目采用开源许可证，具体请查看项目仓库。

## 贡献

欢迎提交 Issue 和 Pull Request！
