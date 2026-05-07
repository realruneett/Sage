import subprocess
import time
from loguru import logger

def launch() -> None:
    """Orchestrates the simultaneous launch of the API server and Gradio UI.
    
    This script ensures that both components are running co-residentially
    to maintain the VRAM allocation properties required by AODE.
    """
    logger.info("Launching SAGE-CODE Co-resident Engine...")
    server = None
    try:
        # Launch the FastAPI backend
        server = subprocess.Popen(["python3", "-m", "sage.api.server"])
        logger.info("API Server started. Waiting for initialization...")
        time.sleep(5)
        
        # Launch the Gradio frontend
        logger.info("Launching Gradio Dashboard...")
        subprocess.run(["python3", "demos/app_gradio.py"], check=True)
        
    except KeyboardInterrupt:
        logger.warning("Shutdown signal received.")
    finally:
        if server:
            logger.info("Terminating API Server...")
            server.terminate()
            server.wait()
            logger.info("Clean shutdown complete.")

if __name__ == "__main__":
    launch()
