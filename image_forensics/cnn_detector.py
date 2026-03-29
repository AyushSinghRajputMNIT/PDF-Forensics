import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image

print("[INIT] Loading CNN model...")

model = resnet18(weights=ResNet18_Weights.DEFAULT)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

def predict_tampering(image_path):
    print(f"      → Running CNN on {image_path}")

    try:
        img = Image.open(image_path).convert("RGB")
        img = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(img)

        score = torch.softmax(output, dim=1)[0]
        confidence = float(torch.max(score).item())
        uncertainty = 1 - confidence

        # Scale down impact (VERY IMPORTANT)
        tamper_signal = uncertainty * 0.3

        return tamper_signal

    except Exception as e:
        print(f"      ⚠ CNN failed: {e}")
        return 0.0