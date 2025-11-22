import shutil
import zipfile
from pathlib import Path

from natsort import natsorted

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def extract_chapter_archive(archive_path: Path, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(dest_dir)
    return list_page_images(dest_dir)


def save_uploaded_images(files: list[tuple[str, bytes]], dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files:
        target = dest_dir / Path(name).name
        target.write_bytes(data)
    return list_page_images(dest_dir)


def list_page_images(root: Path) -> list[Path]:
    images: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and is_image(path):
            images.append(path)
    return [Path(p) for p in natsorted([str(p) for p in images])]  # 1,2,10 not 1,10,2


def pack_result_zip(result_dir: Path, zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for image in list_page_images(result_dir):
            zf.write(image, arcname=image.name)
            sidecar = result_dir / f"{image.name}.regions.json"
            if sidecar.exists():
                zf.write(sidecar, arcname=sidecar.name)
    return zip_path


def ensure_clean_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
