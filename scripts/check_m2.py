import torch
import psutil
import os

def check_hardware():
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
    
    # Memory check
    mem = psutil.virtual_memory()
    print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    
    # Check if we can allocate a small tensor on MPS
    if torch.backends.mps.is_available():
        try:
            x = torch.ones(1, device="mps")
            print("Successfully allocated tensor on MPS.")
        except Exception as e:
            print(f"Failed to allocate on MPS: {e}")

if __name__ == "__main__":
    check_hardware()
