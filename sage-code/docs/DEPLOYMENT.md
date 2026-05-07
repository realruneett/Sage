# SAGE-CODE Deployment Guide

## AMD Instinct MI300X

1.  **Host Setup**:
    - ROCm 6.2+
    - Docker + Docker Compose
    - `firejail` (for sandboxing)

2.  **Clone and Launch**:
    ```bash
    git clone https://github.com/user/sage-code
    cd sage-code
    docker compose up -d
    ```

3.  **Environment Variables**:
    Create a `.env` file:
    ```env
    HF_TOKEN=your_token_here
    SAGE_MODE=deep
    VLLM_ENFORCE_EAGER=True
    ```

4.  **Verification**:
    Run `make test` to verify the tool oracle and agent communication.
