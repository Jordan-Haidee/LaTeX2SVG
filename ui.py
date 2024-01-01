import tempfile
import uuid
from pathlib import Path
from core import VectorFormat
import gradio
import httpx


def pipeline(
    tex_code: str,
    algo_name: str = "",
    vec_type: VectorFormat = VectorFormat.SVG,
) -> str:
    url = "http://127.0.0.1:8000/latex2vector/"
    data = {
        "tex_code": tex_code,
        "algo_name": algo_name,
        "vec_type": vec_type,
    }
    response = httpx.post(url, json=data, verify=False, timeout=10)
    task_id = str(uuid.uuid4())
    temp_directory = Path(tempfile.gettempdir())
    temp_vec_path = (temp_directory / task_id).with_suffix(vec_type)
    with open(temp_vec_path, "wb") as f:
        f.write(response.content)
    return str(temp_vec_path)


if __name__ == "__main__":
    with gradio.Blocks(theme=gradio.themes.Soft(), title="LaTeX2Vector") as demo:
        with gradio.Row():
            output_file_box = gradio.File(
                type="filepath",
                label="Vector Output",
            )
            with gradio.Column():
                latex_input_box = gradio.Textbox(
                    lines=10,
                    max_lines=10,
                    label="LaTeX",
                    placeholder="Input LaTeX code here ...",
                    show_copy_button=True,
                )
                algo_name_box = gradio.Textbox(label="Algorithm Name")
                vec_type_dropdown = gradio.Dropdown(
                    choices=map(lambda x: x.value, VectorFormat),
                    label="Vector Type",
                )
                submit_btn = gradio.Button("Submit")

            submit_btn.click(
                fn=pipeline,
                inputs=[latex_input_box, algo_name_box, vec_type_dropdown],
                outputs=output_file_box,
            )
    demo.launch(server_name="0.0.0.0", server_port=8001)
