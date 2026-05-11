import pytest
import os
import base64
from pathlib import Path
from services.image_recognition import recognize_image
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_vision_accuracy():
    """
    Unit Test 1: Kiểm thử độ chính xác nhận diện hình ảnh (Mục tiêu >= 80%).
    """
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    image_files = list(test_dir.glob("*.*"))
    
    if not image_files:
        pytest.skip("Chưa có ảnh trong thư mục 'test_images'.")
    
    total_images = len(image_files)
    correct_predictions = 0

    print(f"\n--- Đang test {total_images} ảnh ---")

    for img_path in image_files:
        # Lấy tên file để làm ID mong đợi
        expected_id = img_path.stem 
        
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        result = await recognize_image(encoded_string)
        
        # So khớp linh hoạt: tên file khớp với ID trong DB
        if result.recognized and (expected_id in result.artifact_id or result.artifact_id in expected_id):
            correct_predictions += 1
            print(f"  [ĐÚNG] {img_path.name} -> {result.artifact_id}")
        else:
            print(f"  [SAI] {img_path.name} | AI: {result.artifact_id} | Mong đợi: {expected_id}")

    accuracy = correct_predictions / total_images
    print(f"\n=> Tổng kết: {accuracy * 100:.2f}% ({correct_predictions}/{total_images})")
    
    assert accuracy >= 0.8, f"Độ chính xác {accuracy*100}% không đạt tiêu chuẩn 80%."