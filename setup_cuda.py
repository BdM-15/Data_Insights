"""
CUDA Configuration Script for Ollama

This script configures Ollama to use CUDA GPU acceleration for the Data_Insights platform.
Optimizes settings for NVIDIA GTX 4060 with 64GB system RAM.
"""

import subprocess
import json
import os
import logging
from config import CUDA_ENABLED, CUDA_DEVICE, GPU_MEMORY_FRACTION, OLLAMA_MODEL

logger = logging.getLogger(__name__)

def check_cuda_availability():
    """Check if CUDA is available on the system."""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected:")
            print(result.stdout.split('\n')[8:12])  # GPU info lines
            return True
        else:
            print("❌ NVIDIA GPU not detected")
            return False
    except FileNotFoundError:
        print("❌ nvidia-smi not found - NVIDIA drivers may not be installed")
        return False

def configure_ollama_for_cuda():
    """Configure Ollama to use CUDA GPU acceleration."""
    if not CUDA_ENABLED:
        print("🔄 CUDA disabled in configuration")
        return
    
    if not check_cuda_availability():
        print("⚠️ CUDA not available, falling back to CPU")
        return
    
    print("🚀 Configuring Ollama for CUDA acceleration...")
    
    # Set Ollama environment variables for GPU acceleration
    env_vars = {
        'OLLAMA_GPU_ENABLED': '1',
        'OLLAMA_GPU_DEVICE': CUDA_DEVICE,
        'OLLAMA_GPU_MEMORY_FRACTION': str(GPU_MEMORY_FRACTION),
        'OLLAMA_NUM_PARALLEL': '1',  # Single model at a time for better GPU utilization
        'OLLAMA_MAX_LOADED_MODELS': '1',  # Keep only one model in VRAM
        'OLLAMA_FLASH_ATTENTION': '1',  # Enable flash attention for efficiency
        'OLLAMA_KEEP_ALIVE': '30m',  # Keep model loaded for 30 minutes
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    print("✅ Ollama CUDA configuration applied")

def optimize_model_for_performance():
    """Download and configure the model for optimal performance."""
    print(f"🔄 Optimizing {OLLAMA_MODEL} for performance...")
    
    try:
        # Pull the model if not already available
        print(f"📥 Ensuring {OLLAMA_MODEL} is available...")
        subprocess.run(['ollama', 'pull', OLLAMA_MODEL], check=True)
        
        # Create a custom modelfile for performance optimization
        modelfile_content = f"""FROM {OLLAMA_MODEL}

# Performance optimization parameters
PARAMETER temperature 0.7
PARAMETER top_k 5
PARAMETER top_p 0.8
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048
PARAMETER num_predict 512
PARAMETER stop "Human:"
PARAMETER stop "User:"
PARAMETER stop "Assistant:"

# System prompt optimization
SYSTEM You are a concise and efficient AI consultant. Provide direct, actionable responses without unnecessary elaboration.
"""
        
        # Write modelfile
        with open('data_insights_model', 'w') as f:
            f.write(modelfile_content)
        
        # Create optimized model
        subprocess.run(['ollama', 'create', 'data_insights_optimized', '-f', 'data_insights_model'], check=True)
        
        print("✅ Optimized model 'data_insights_optimized' created")
        print("💡 Use 'data_insights_optimized' instead of the base model for better performance")
        
        # Clean up
        os.remove('data_insights_model')
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to optimize model: {e}")
    except Exception as e:
        print(f"❌ Error during model optimization: {e}")

def test_performance():
    """Test the performance of the optimized setup."""
    print("🧪 Testing performance...")
    
    try:
        import time
        start_time = time.time()
        
        result = subprocess.run([
            'ollama', 'run', 'data_insights_optimized', 
            'Hello, respond with exactly 5 words only.'
        ], capture_output=True, text=True, timeout=30)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ Response time: {response_time:.2f} seconds")
            print(f"📝 Response: {result.stdout.strip()}")
            
            if response_time < 5:
                print("🎉 Excellent performance!")
            elif response_time < 10:
                print("👍 Good performance")
            else:
                print("⚠️ Performance needs improvement")
        else:
            print(f"❌ Test failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    """Main configuration function."""
    print("🔧 Data Insights CUDA Configuration")
    print("=" * 50)
    
    configure_ollama_for_cuda()
    optimize_model_for_performance()
    test_performance()
    
    print("\n📋 Next Steps:")
    print("1. Restart the Data Insights application")
    print("2. Update OLLAMA_MODEL in config.py to 'data_insights_optimized'")
    print("3. Monitor GPU usage with: nvidia-smi -l 1")
    print("4. Expected performance: <5 seconds for simple queries")

if __name__ == "__main__":
    main()
