import tempfile
import uuid
from pathlib import Path

import gradio
import httpx


def pipeline(latex_cmd: str, algo_name: str = None) -> str:
    url = "http://127.0.0.1:8000/latex2svg/"
    data = {
        "latex_cmd": latex_cmd,
        "type": "simple" if not bool(algo_name) else "simple_with_algo",
        "algo_name": algo_name,
    }
    response = httpx.post(url, json=data)
    svg_code = response.text
    temp_directory = Path(tempfile.gettempdir())
    temp_svg_path = (temp_directory / str(uuid.uuid4())).with_suffix(".svg")
    with open(temp_svg_path, "w") as f:
        f.write(svg_code)
    return str(temp_svg_path)


if __name__ == "__main__":
    with gradio.Blocks(theme=gradio.themes.Soft(), title="LaTeX2SVG") as demo:
        with gradio.Row():
            output_image_box = gradio.Image(
                width=500,
                height=500,
                type="filepath",
                label="SVG Output",
            )
            with gradio.Column():
                latex_input_box = gradio.Textbox(
                    lines=14,
                    max_lines=14,
                    label="LaTeX",
                    placeholder="Please input LaTeX code here ...",
                    show_copy_button=True,
                )
                with gradio.Row():
                    algo_name_box = gradio.Textbox(
                        show_label=False,
                        placeholder="Algorithm name of pseudocode ...\nblank means it's a normal LaTeX math equation",
                        show_copy_button=True,
                    )
                submit_btn = gradio.Button("Submit")
            submit_btn.click(
                fn=pipeline,
                inputs=[latex_input_box, algo_name_box],
                outputs=output_image_box,
            )
    demo.launch(server_name="0.0.0.0", server_port=8001)
