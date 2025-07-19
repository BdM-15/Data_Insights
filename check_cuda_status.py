"""
Quick utility to check if CUDA (GPU) is available and being used by PyTorch and Ollama.
Run this script to verify GPU status for LLM inference.
"""

import subprocess
import sys

def check_pytorch_cuda():
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"Current device: {torch.cuda.current_device()}")
            print(f"Device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    except ImportError:
        print("PyTorch not installed.")

def check_nvidia_smi():
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("nvidia-smi output:")
            print(result.stdout)
        else:
            print("nvidia-smi not found or GPU not available.")
    except Exception as e:
        print(f"Error running nvidia-smi: {e}")

def check_ollama_gpu():
    print("\nOllama GPU status (check logs or run a model and monitor nvidia-smi):")
    print("- Ollama does not provide a direct Python API for GPU status.")
    print("- To check if Ollama is using the GPU, run a model and monitor nvidia-smi for activity.")
    print("- You can also check Ollama logs for CUDA initialization messages.")

def main():
    print("=== PyTorch CUDA Check ===")
    check_pytorch_cuda()
    print("\n=== NVIDIA-SMI Check ===")
    check_nvidia_smi()
    print("\n=== Ollama GPU Check ===")
    check_ollama_gpu()

if __name__ == "__main__":
    main()
