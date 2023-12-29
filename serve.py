import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
from latex2mathml import converter
from pydantic import BaseModel

app = FastAPI()
template_env = Environment(
    variable_start_string=r"{{{",
    variable_end_string=r"}}}",
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
)


class TaskData(BaseModel):
    latex_cmd: str
    type: Literal["simple", "simple_with_algo"] = "simple"
    algo_name: str = ""
    download: bool = False


def crop_pdf(input_file: str, output_file: str) -> bool:
    cmd = ["pdfcrop", str(input_file), str(output_file)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Exit Code: {e.returncode}")
        print(f"Output: {e.output}")
        return False
    else:
        return True


def pdf2svg(input_file: str, output_file: str):
    cmd = ["pdf2svg", str(input_file), str(output_file)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Exit Code: {e.returncode}")
        print(f"Output: {e.output}")
        return False
    else:
        return True


def latex2pdf(input_file: str, output_file: str) -> bool:
    cmd = ["xelatex", "-halt-on-error", "-output-directory", str(output_file), str(input_file)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", "\n", "--" * 20)
        print(f"Exit Code: {e.returncode}", "\n", "--" * 20)
        print(f"Output: {e.output}", "\n", "--" * 20)
        return False
    else:
        return True


@app.post("/latex2svg/")
def latex2svg(task_data: TaskData) -> str:
    # create save directory
    task_id = str(uuid.uuid4())
    task_dir = Path(tempfile.gettempdir()) / task_id
    task_dir.mkdir()
    # convert pipeline
    if task_data.type == "simple":
        latex_cmd = template_env.get_template("simple.jinja2").render(latex_math_equation_code=task_data.latex_cmd)
    else:
        latex_cmd = template_env.get_template("simple_with_algo.jinja2").render(
            algo_name=task_data.algo_name,
            algo_code=task_data.latex_cmd,
        )
    tex_path = task_dir / "{}.tex".format(task_id)
    pdf_path = tex_path.with_suffix(".pdf")
    with open(tex_path, "w") as f:
        f.write(latex_cmd)
    res = latex2pdf(tex_path.absolute(), tex_path.parent.absolute())
    if res is False:
        raise HTTPException(351, detail="when converting to pdf, error happened !")
    pdf_cropped_path = pdf_path.parent / (pdf_path.stem + "_cropped.pdf")
    res = crop_pdf(pdf_path, pdf_cropped_path)
    if res is False:
        raise HTTPException(352, detail="when cropping pdf, error happened !")
    svg_path = pdf_path.with_suffix(".svg")
    res = pdf2svg(pdf_cropped_path, svg_path)
    if res is False:
        raise HTTPException(353, detail="when converting to svg, error happened !")
    # return response
    response = FileResponse(svg_path)
    if task_data.download is True:
        response.headers.update({"Content-Disposition": f"attachment; filename={svg_path.name}"})
    return response


@app.post("/latex2mathml/")
def latex_to_mathml(task_data: TaskData):
    task_id = str(uuid.uuid4())
    task_dir = Path(tempfile.gettempdir()) / task_id
    task_dir.mkdir()
    output_file = task_dir / "{}.xml".format(task_id)
    mathml_code = converter.convert(task_data.latex_cmd.strip())
    with open(output_file, "w") as f:
        f.write(mathml_code)
    response = FileResponse(output_file)
    if task_data.download is True:
        response.headers.update({"Content-Disposition": f"attachment; filename={output_file.name}"})
    return response
