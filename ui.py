import tempfile
import uuid
from pathlib import Path

import gradio
import httpx


def get_svg_image(latex_cmd: str, is_algo: bool = False) -> str:
    url = "http://127.0.0.1:8000/latex2svg/"
    response = httpx.get(
        url,
        params={
            "latex_cmd": latex_cmd,
            "task_type": "simple" if not is_algo else "simple_with_algo",
        },
    )
    svg_code = response.text
    temp_directory = Path(tempfile.gettempdir())
    temp_svg_path = (temp_directory / str(uuid.uuid4())).with_suffix(".svg")
    with open(temp_svg_path, "w") as f:
        f.write(svg_code)
    return str(temp_svg_path)


if __name__ == "__main__":
    theme = gradio.themes.Soft()
    with gradio.Blocks(theme) as demo:
        with gradio.Row():
            output_image_box = gradio.Image(width=500, height=500, type="filepath", label="Output SVG")
            with gradio.Column():
                latex_input_box = gradio.Textbox(
                    lines=16, label="LaTeX", placeholder="Please input LaTeX equation code here"
                )
                is_algo_checkbox = gradio.Checkbox(label="Pseudocode")
                submit_btn = gradio.Button("Submit")
            submit_btn.click(fn=get_svg_image, inputs=latex_input_box, outputs=output_image_box)
    demo.launch(server_name="0.0.0.0", server_port=8001)
