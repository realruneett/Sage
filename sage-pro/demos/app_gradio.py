import gradio as gr
import httpx
import asyncio

# Custom CSS for Premium Look
custom_css = \"\"\"
.gradio-container {
    background: radial-gradient(circle at top left, #1a1a2e, #16213e);
    color: #e94560;
}
#title-markdown {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    color: #ffffff;
}
.gr-button-primary {
    background: linear-gradient(135deg, #e94560 0%, #0f3460 100%) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3) !important;
}
.gr-box {
    border-radius: 12px !important;
    background: rgba(15, 52, 96, 0.5) !important;
    backdrop-filter: blur(10px);
}
\"\"\"

async def run_sage_pro(task):
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post("http://localhost:8000/v1/code", json={"task": task})
            if response.status_code == 200:
                data = response.json()
                # Create a Mermaid diagram for the reasoning flow
                mermaid_graph = f\"\"\"
                graph TD
                    A[Ingest] --> B[Topological Route]
                    B --> C[Parallel Debate]
                    C --> D[Lie Bracket Synthesis]
                    D --> E[Nash Crucible]
                    E --> F[Verification]
                    F --> G[Emit Solution]
                    style D fill:#e94560,stroke:#fff,stroke-width:2px
                    style E fill:#e94560,stroke:#fff,stroke-width:2px
                \"\"\"
                stats = f\"🚀 VRAM: {data['vram_peak_gb']} GB\\n🎯 δ-Index: {data['divergence_index']:.4f}\\n🔄 Nash Cycles: {data['nash_cycles']}\"
                trace = "\\n".join([f"• {t}" for t in data["xai_trace"]])
                return data["code"], data["tests"], stats, trace, mermaid_graph
            return "Error: Could not reach SAGE-PRO Engine", "", "", "", ""
        except Exception as e:
            return f"Connection Error: {str(e)}", "", "", "", ""

with gr.Blocks(title="SAGE-PRO Dashboard", css=custom_css) as demo:
    with gr.Column(elem_id="title-markdown"):
        gr.Markdown("# 🚀 SAGE-PRO: Adversarial Coding Engine")
        gr.Markdown("### Optimized for AMD Instinct MI300X (192 GB HBM3)")
    
    with gr.Row():
        with gr.Column(scale=3):
            task_input = gr.Textbox(
                label="Prompt Your Requirement", 
                placeholder="e.g. Implement a high-throughput async stream processor with zero-copy semantics...", 
                lines=4,
                elem_id="prompt-box"
            )
            with gr.Row():
                clear_btn = gr.Button("Clear", variant="secondary")
                submit_btn = gr.Button("SAGE-PRO INFER", variant="primary")
        
        with gr.Column(scale=2):
            gr.Markdown("#### Reasoning Flow Visualization")
            graph_out = gr.Markdown("Submit a task to see the AODE reasoning graph.")

    with gr.Tabs():
        with gr.TabItem("💎 Verified Solution"):
            code_out = gr.Code(label="Final Hardened Python Code", language="python", lines=20)
        with gr.TabItem("🛡️ Adversarial Suite"):
            test_out = gr.Code(label="Red-Team Generated Tests", language="python", lines=20)
        with gr.TabItem("📊 Engine Analytics"):
            with gr.Row():
                stats_out = gr.Textbox(label="Real-time Metrics", lines=5)
                trace_out = gr.Markdown(label="Deep Trace")

    submit_btn.click(
        fn=run_sage_pro, 
        inputs=[task_input], 
        outputs=[code_out, test_out, stats_out, trace_out, graph_out]
    )
    clear_btn.click(lambda: [""] * 5, None, [code_out, test_out, stats_out, trace_out, graph_out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
