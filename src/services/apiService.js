/**
 * Giả lập gửi request lên API Gateway.
 * Thời gian phản hồi giả lập: 1.5 giây.
 */
export const recognizeArtifactAPI = async (imageBase64, forceError = null) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 1. Giả lập mất kết nối mạng
      if (forceError === 'network' || !navigator.onLine) {
        return reject(new Error("NETWORK_ERROR"));
      }

      // 2. Giả lập ảnh mờ / không nhận diện được (edge case)
      if (forceError === 'blur') {
        return resolve({
          status: "error",
          error_code: "LOW_CONFIDENCE",
          message: "Ảnh quá tối hoặc không chứa hiện vật trong hệ thống.",
          confidence_score: 0.3
        });
      }

      // 3. Giả lập thành công
      resolve({
        status: "success",
        data: {
          artifact_id: "HUE_001",
          artifact_name: "Ngọ Môn",
          text_response: "Đây là cổng chính phía Nam của Hoàng thành Huế, được xây dựng năm 1833 dưới triều vua Minh Mạng. Cổng có 5 lối đi, lối chính giữa dành riêng cho vua. Kiến trúc phần trên gọi là lầu Ngũ Phụng.",
          audio_url: "mock_audio", // Will be handled by Web Speech API in our mock
          confidence_score: 0.95
        }
      });
    }, 1500); // delay 1.5s
  });
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
