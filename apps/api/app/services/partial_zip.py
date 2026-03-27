from __future__ import annotations

import zipfile
from pathlib import Path

from app.services.storage import list_page_images


def pack_completed_pages(result_dir: Path, zip_path: Path, *, as_cbz: bool = False) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for image in list_page_images(result_dir):
            zf.write(image, arcname=image.name)
            sidecar = result_dir / f"{image.name}.regions.json"
            if sidecar.exists():
                zf.write(sidecar, arcname=sidecar.name)
    if as_cbz and zip_path.suffix.lower() != ".cbz":
        cbz_path = zip_path.with_suffix(".cbz")
        if cbz_path.exists():
            cbz_path.unlink()
        zip_path.replace(cbz_path)
        return cbz_path
    return zip_path
