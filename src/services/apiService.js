/**
 * Gửi ảnh lên API Gateway thật.
 */
export const recognizeArtifactAPI = async (imageBase64, lang = 'vi') => {
  try {
    // Gọi API thật của BE đang chạy trên cổng 8000
    // LƯU Ý: Khi deploy lên server thật, cần thay đổi URL này.
    const response = await fetch('http://localhost:8000/api/v1/recognize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image_base64: imageBase64,
        lang: lang // Truyền ngôn ngữ vào BE
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "NETWORK_ERROR");
    }

    if (data.success) {
      return {
        status: "success",
        data: {
          artifact_id: data.artifact_id,
          artifact_name: data.artifact_name,
          text_response: data.response_text,
          confidence_score: data.confidence_score
        }
      };
    } else {
      return {
        status: "error",
        error_code: data.error_code,
        message: data.message,
        confidence_score: data.confidence_score
      };
    }
  } catch (error) {
    console.error("Lỗi kết nối API:", error);
    throw new Error("NETWORK_ERROR");
  }
};

/**
 * Text to Speech Service sử dụng trình duyệt để phát qua loa
 */
export const playTTS = (text, onEndCallback) => {
  if (!('speechSynthesis' in window)) {
    console.warn("Trình duyệt không hỗ trợ Web Speech API");
    if (onEndCallback) onEndCallback();
    return null;
  }

  // Hủy các speech cũ nếu có
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'vi-VN'; // Giọng tiếng Việt
  utterance.rate = 1.0;

  if (onEndCallback) {
    utterance.onend = onEndCallback;
    utterance.onerror = onEndCallback;
  }

  window.speechSynthesis.speak(utterance);
  return utterance;
};

export const stopTTS = () => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};
