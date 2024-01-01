import os
import platform
import shlex
import subprocess
from enum import Enum
from pathlib import Path

if os.name == "nt":
    gs_cmd = "gswin{}c".format(platform.architecture()[0][:2])
elif os.name == "posix":
    gs_cmd = "gs"
else:
    raise AssertionError("Unsupported OS !")

kwargs = {
    "check": True,
    "capture_output": True,
    "text": True,
}


class VectorFormat(str, Enum):
    SVG = ".svg"
    PDF = ".pdf"
    EPS = ".eps"
    EMF = ".emf"


def latex2pdf(src: Path | str, dst: Path | str):
    cmd = "xelatex -halt-on-error -output-directory {} {}".format(dst.parent, src)
    cmd = shlex.split(cmd, posix=os.name == "posix")
    subprocess.run(cmd, **kwargs)


def crop_pdf(src: Path | str, dst: Path | str):
    cmd = "pdfcrop {} {}".format(src, dst)
    cmd = shlex.split(cmd, posix=os.name == "posix")
    subprocess.run(cmd, **kwargs)


def pdf2svg(src: Path | str, dst: Path | str):
    assert src.suffix == VectorFormat.PDF
    assert dst.suffix == VectorFormat.SVG
    cmd = "pdf2svg {} {}".format(src, dst)
    cmd = shlex.split(cmd, posix=os.name == "posix")
    subprocess.run(cmd, **kwargs)


def svg2vec(src: Path | str, dst: Path | str):
    assert src.suffix == VectorFormat.SVG
    cmd = "inkscape --export-filename={} {}".format(dst, src)
    cmd = shlex.split(cmd, posix=os.name == "posix")
    subprocess.run(cmd, **kwargs)


def pdf2vec_nt(src: Path | str, dst: Path | str):
    svg_tmp = src.with_suffix(VectorFormat.SVG)
    pdf2svg(src, svg_tmp)
    svg2vec(svg_tmp, dst)


def pdf2vec_posix(src: Path | str, dst: Path | str):
    cmd = "inkscape --export-filename={} {}".format(dst, src)
    cmd = shlex.split(cmd, posix=os.name == "posix")
    subprocess.run(cmd, **kwargs)


def pdf2vec(src: Path | str, dst: Path | str):
    if os.name == "nt":
        pdf2vec_nt(src, dst)
    elif os.name == "posix":
        pdf2vec_posix(src, dst)
    else:
        raise AssertionError("Unsupported OS !")


def latex2vec(src: Path | str, dst: Path | str):
    pdf_tmp = src.with_suffix(VectorFormat.PDF)
    latex2pdf(src, pdf_tmp)
    crop_pdf(pdf_tmp, pdf_tmp)
    if dst.suffix != VectorFormat.PDF:
        pdf2vec(pdf_tmp, dst)


if __name__ == "__main__":
    latex2vec(Path("example.tex"), Path("example.emf"))
