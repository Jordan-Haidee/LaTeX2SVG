import tempfile
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from core import VectorFormat, latex2vec

app = FastAPI()
temp_dir = Path(tempfile.gettempdir())
template_env = Environment(
    variable_start_string=r"{{{",
    variable_end_string=r"}}}",
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
)


class TaskData(BaseModel):
    tex_code: str
    algo_name: str = ""
    vec_type: VectorFormat


@app.post("/latex2vector/")
def api_convert(task_data: TaskData):
    task_id = str(uuid.uuid4())
    task_dir = temp_dir / task_id
    task_dir.mkdir()
    if bool(task_data.algo_name):
        tex_f_str = template_env.get_template("algo.jinja2").render(code=task_data.tex_code, name=task_data.algo_name)
    else:
        tex_f_str = template_env.get_template("simple.jinja2").render(code=task_data.tex_code)
    tex_path = task_dir / "{}.tex".format(task_id)
    vec_path = tex_path.with_suffix(task_data.vec_type)
    with open(tex_path, "w") as f:
        f.write(tex_f_str)
    latex2vec(tex_path, vec_path)
    return FileResponse(vec_path)
