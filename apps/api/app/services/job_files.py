from __future__ import annotations

import shutil
from pathlib import Path

from app.models import ChapterJob


def delete_job_files(job: ChapterJob) -> None:
    for raw in (job.upload_dir, job.result_dir, job.result_zip):
        if not raw:
            continue
        path = Path(raw)
        try:
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                # Also remove parent job folder when deleting pages/ subdir
                parent = path.parent
                if parent.name and parent.exists() and not any(parent.iterdir()):
                    shutil.rmtree(parent, ignore_errors=True)
        except OSError:
            pass
