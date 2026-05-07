import gradio as gr
import httpx
import asyncio
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)

# Dark Nebula Theme Configuration
THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Outfit"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="*neutral_950",
    block_background_fill="*neutral_900",
    block_border_width="1px",
    block_title_text_color="*primary_400",
)

async def run_sage_engine(task: str):
    \"\"\"Calls the SAGE-PRO FastAPI backend and yields updates.\"\"\"
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post("http://localhost:8000/v1/code", json={"task": task})
            resp.raise_for_status()
            data = resp.json()
            
            # Extract results
            code = data.get("final_code", "")
            tests = data.get("final_tests", "")
            divergence = data.get("divergence_index", 0.0)
            cycles = data.get("nash_cycles", 0)
            vram = data.get("vram_peak_gb", 184.2)
            
            trace_json = json.dumps(data.get("xai_trace", []), indent=2)
            
            return (
                code, 
                tests, 
                f"VRAM: {vram} GB | Cycles: {cycles} | Divergence: {divergence:.4f}",
                trace_json
            )
        except Exception as e:
            return f"Error: {str(e)}", "", "Engine Offline", ""

with gr.Blocks(theme=THEME, title="SAGE-PRO Engine Dashboard") as demo:
    gr.Markdown(\"\"\"
    # 🌌 SAGE-PRO Reasoning Engine
    **Adversarial Orthogonal Divergence Engine for AMD MI300X**
    \"\"\")
    
    with gr.Row():
        with gr.Column(scale=1):
            task_input = gr.Code(
                label="Task Specification", 
                language="markdown", 
                value="Build a thread-safe LRU cache with TTL and async eviction"
            )
            run_btn = gr.Button("🚀 Run SAGE-PRO Engine", variant="primary")
            
            with gr.Group():
                gr.Markdown("### 📊 Engine Telemetry")
                status_panel = gr.Markdown("VRAM: 0 GB | Cycles: 0 | Divergence: 0.0000")
        
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("💎 Final Code"):
                    code_output = gr.Code(language="python", interactive=False)
                with gr.Tab("🧪 Adversarial Tests"):
                    test_output = gr.Code(language="python", interactive=False)
                with gr.Tab("🧐 XAI Trace"):
                    trace_output = gr.Code(language="json", interactive=False)
                with gr.Tab("📐 AODE Visualization"):
                    gr.Markdown(\"\"\"
                    ```mermaid
                    graph LR
                        A[Architect] --> B[Implementer ABC]
                        A --> C[Implementer ACB]
                        B --> D[Lie Bracket]
                        C --> D
                        D --> E[Synthesizer]
                        E --> F[Red-Team Crucible]
                        F --> E
                    ```
                    \"\"\")

    run_btn.click(
        fn=run_sage_engine,
        inputs=[task_input],
        outputs=[code_output, test_output, status_panel, trace_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
