import gradio as gr
import httpx
import asyncio

async def run_sage_code(task):
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post("http://localhost:8000/v1/code", json={"task": task})
            if response.status_code == 200:
                data = response.json()
                return data["code"], data["tests"], f"VRAM: {data['vram_peak_gb']} GB\nDiv: {data['divergence_index']:.4f}", "\n".join(data["xai_trace"])
            return "Error", "", "", ""
        except Exception as e:
            return str(e), "", "", ""

with gr.Blocks(title="SAGE-CODE Dashboard") as demo:
    gr.Markdown("# 🛠️ SAGE-CODE: Pro Coding Engine")
    gr.Markdown("### 4-Agent Co-Resident Reasoning on AMD MI300X")
    
    with gr.Row():
        task_input = gr.Textbox(label="Coding Task", placeholder="e.g. Build an async LRU cache...", lines=3)
        submit_btn = gr.Button("Build & Verify", variant="primary")
        
    with gr.Row():
        with gr.Column(scale=2):
            code_out = gr.Code(label="Verified Code", language="python")
            test_out = gr.Code(label="Adversarial Tests", language="python")
        with gr.Column(scale=1):
            stats_out = gr.Textbox(label="Engine Stats")
            trace_out = gr.Textbox(label="Reasoning Trace", lines=10)

    submit_btn.click(fn=run_sage_code, inputs=[task_input], outputs=[code_out, test_out, stats_out, trace_out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
