"""Optional LaMa inpainting helper.

Install separately when ready:
  pip install simple-lama-inpainting

Then set INPAINT_PROVIDER=lama
"""

from __future__ import annotations


def lama_available() -> bool:
    try:
        import simple_lama_inpainting  # noqa: F401

        return True
    except Exception:
        return False
