#!/bin/bash

echo "🔍 Checking GPU/CUDA availability..."
echo ""

# Check if nvidia-smi is available
if command -v nvidia-smi &> /dev/null; then
    echo "✅ nvidia-smi found"
    echo ""
    nvidia-smi
    echo ""
else
    echo "❌ nvidia-smi not found"
    echo "NVIDIA drivers may not be installed"
    echo ""
fi

# Check Python CUDA availability
if [ -f "venv/bin/python" ]; then
    echo "Checking PyTorch CUDA availability..."
    venv/bin/python -c "
import sys
try:
    import torch
    print(f'PyTorch version: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA version: {torch.version.cuda}')
        print(f'GPU count: {torch.cuda.device_count()}')
        for i in range(torch.cuda.device_count()):
            print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
    else:
        print('⚠️  CUDA not available in PyTorch')
except ImportError:
    print('⚠️  PyTorch not installed')
    print('Run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121')
"
else
    echo "⚠️  Virtual environment not found"
    echo "Run: python3 -m venv venv && source venv/bin/activate"
fi
