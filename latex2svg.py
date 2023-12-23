import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()


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


@app.get("/latex2svg/")
def latex2svg(
    latex_cmd: str,
    task_type: Literal["simple", "simple_with_algo"] = "simple",
    download: bool = False,
) -> str:
    # create save directory
    current_time = datetime.now()
    current_timestamp = int(current_time.timestamp())
    save_dir = Path("result") / current_time.strftime(r"%Y-%m-%d-%H-%M-%S")
    save_dir.mkdir(exist_ok=True, parents=True)
    # convert pipeline
    template_path = Path(__file__).parent / "templates" / f"{task_type}.tex"
    with open(template_path, "r") as f:
        latex_template = f.read()
    latex_cmd = latex_template % latex_cmd
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
    if download is True:
        response.headers.update({"Content-Disposition": f"attachment; filename={svg_path.name}"})
    return response


@app.get("/latex2mathml/")
def latex_to_mathml(latex_cmd: str, download: bool = False):
    try:
        import latex2mathml.converter
    except ImportError:
        print("please install latex2mathml firstly!")
        sys.exit(1)
    else:
        current_time = datetime.now()
        current_timestamp = int(current_time.timestamp())
        save_dir = Path("result") / current_time.strftime(r"%Y-%m-%d-%H-%M-%S")
        save_dir.mkdir(exist_ok=True, parents=True)
        output_file = save_dir / f"{current_timestamp}.xml"
        mathml_code = latex2mathml.converter.convert(latex_cmd.strip())
        with open(output_file, "w") as f:
            f.write(mathml_code)
        response = FileResponse(output_file)
        if download is True:
            response.headers.update({"Content-Disposition": f"attachment; filename={output_file.name}"})
        return response


if __name__ == "__main__":
    ...
    # latex_to_mathml(r"x^2+y^2=z^2", "tmp.xml")
    # latex2svg(r"L_{Q}=\frac{1}{|B|}\sum_{i=1}^{|B|}\left( y_i-Q_\phi(s_i,a_i) \right)^2")
    # latex2svg(
    # r"""\begin{aligned}
    #         y_i&=r_i+(1-d_i)\cdot \gamma\ \underset{a^\prime\in \mathcal{A}}{\max}\ Q_{\phi^\prime}(s_i^\prime,a^\prime)\\
    #         L_{Q}&=\frac{1}{|B|}\sum_{i=1}^{|B|}\left( y_i-Q_\phi(s_i,a_i) \right)^2
    #     \end{aligned}""",
    # template_path="templates/simple.tex",
    # )
    # latex2svg(
    #     r"""\STATE Randomly initialize action-value network $Q_\phi$ with parameter $\phi\gets \phi_0$.
    #     \STATE Initialize target network $Q_{\phi^\prime}$ via parameter copy: $\phi^\prime\gets\phi$.
    #     \STATE Initialize Replay Buffer $\mathcal{B}$, and collect some transitions $\{s,a,r,s^\prime,d\}$ by take random actions before training starts.
    #     \FOR{$t=1,2,\ldots,T$}
    #     \STATE Take an action $a_t$ sampled from $\epsilon-greedy$ policy:
    #     $$
    #         a_t=\left\{
    #         \begin{aligned}
    #              & random\ from\ \mathcal{A},\quad \mathrm{if}\ x< \epsilon           \\
    #              & \underset{a\in\mathcal{A}}{\arg\max}\ Q(s_t,a),\quad \mathrm{else}
    #         \end{aligned}
    #         \right.
    #     $$

    #     \STATE Observe $\{r_{t+1},s_{t+1}\}$ and store transition $\{s_t,a_t,r_{t+1},s_{t+1},d_{t+1}\}$ in $\mathcal{B}$. If episode ends, reset environment.
    #     \STATE Randomly sample a minibatch $B$ with transitions $\{s_i,a_i,r_i,s_i^\prime,d_i\}_{i=1,2,\ldots,|B|}$ from $\mathcal{B}$.
    #     \STATE Compute TD error:
    #     $$
    #         \begin{aligned}
    #             y_i&=r_i+(1-d_i)\cdot \gamma\ \underset{a^\prime\in \mathcal{A}}{\max}\ Q_{\phi^\prime}(s_i^\prime,a^\prime)\\
    #             L_{Q}&=\frac{1}{|B|}\sum_{i=1}^{|B|}\left( y_i-Q_\phi(s_i,a_i) \right)^2
    #         \end{aligned}
    #     $$
    #     \STATE Update $Q$-Network parameter $\phi$ via any gradient \textbf{descent} algorithm:
    #     $$
    #         \phi \gets \phi + \nabla_\phi L_{Q}
    #     $$

    #     \STATE Update target network parameter if $\mathcal{D}$ steps pass: $\phi^\prime\gets \phi$.

    #     \ENDFOR""",
    #     template_path="templates/simple_with_algo.tex",
    # )
