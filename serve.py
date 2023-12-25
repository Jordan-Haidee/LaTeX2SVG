import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal

import latex2mathml.converter
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()


class TaskData(BaseModel):
    latex_cmd: str
    type: Literal["simple", "simple_with_algo"] = "simple"
    algo_name: str = ""
    download: bool = False


def crop_pdf(input_file: str, output_file: str) -> bool:
    cmd = ["pdfcrop", "--margins", "5 5 5 5", str(input_file), str(output_file)]
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
    cmd = ["xelatex", "-halt-on-error", f"-output-directory={output_file}", str(input_file)]
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
    current_time = datetime.now()
    current_timestamp = int(current_time.timestamp())
    save_dir = Path("result") / current_time.strftime(r"%Y-%m-%d-%H-%M-%S")
    save_dir.mkdir(exist_ok=True, parents=True)
    # convert pipeline
    template_path = Path(__file__).parent / "templates" / f"{task_data.type}.tex"
    with open(template_path, "r") as f:
        latex_template = f.read()
    if task_data.type == "simple":
        latex_cmd = latex_template % task_data.latex_cmd
    else:
        latex_cmd = latex_template % (task_data.algo_name, task_data.latex_cmd)
    tex_path = save_dir / f"{current_timestamp}.tex"
    pdf_path = tex_path.with_suffix(".pdf")
    with open(tex_path, "w") as f:
        f.write(latex_cmd)
    res = latex2pdf(tex_path.absolute(), tex_path.parent.absolute())
    if res is False:
        raise HTTPException(301, detail="when converting to pdf, error happened !")
    pdf_cropped_path = pdf_path.parent / (pdf_path.stem + "_cropped.pdf")
    res = crop_pdf(pdf_path, pdf_cropped_path)
    if res is False:
        raise HTTPException(302, detail="when cropping pdf, error happened !")
    svg_path = pdf_path.with_suffix(".svg")
    res = pdf2svg(pdf_cropped_path, svg_path)
    if res is False:
        raise HTTPException(303, detail="when converting to svg, error happened !")
    # return response
    response = FileResponse(svg_path)
    if task_data.download is True:
        response.headers.update({"Content-Disposition": f"attachment; filename={svg_path.name}"})
    return response


@app.post("/latex2mathml/")
def latex_to_mathml(task_data: TaskData):
    current_time = datetime.now()
    current_timestamp = int(current_time.timestamp())
    save_dir = Path("result") / current_time.strftime(r"%Y-%m-%d-%H-%M-%S")
    save_dir.mkdir(exist_ok=True, parents=True)
    output_file = save_dir / f"{current_timestamp}.xml"
    mathml_code = latex2mathml.converter.convert(task_data.latex_cmd.strip())
    with open(output_file, "w") as f:
        f.write(mathml_code)
    response = FileResponse(output_file)
    if task_data.download is True:
        response.headers.update({"Content-Disposition": f"attachment; filename={output_file.name}"})
    return response
