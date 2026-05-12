/**
 * Gửi ảnh lên API Gateway thật.
 */
// Dùng path tương đối để Vite Proxy tự forward sang đúng backend port
// Proxy config trong vite.config.js: /api/v1 → :8000, /api/voice → :8001
const RECOGNIZE_API_URL = '';
const VOICE_API_URL = '';

export const recognizeArtifactAPI = async (imageBase64, lang = 'vi') => {
  try {
    // Gọi API thật của BE đang chạy trên cổng 8000
    // LƯU Ý: Khi deploy lên server thật, cần thay đổi URL này.
    const response = await fetch(`${RECOGNIZE_API_URL}/api/v1/recognize`, {
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

/**
 * Gửi ghi âm lên API Voice Chat
 */
const USE_MOCK = false; // Đã đổi thành false để dùng Backend thật

export const voiceChatAPI = async (audioBlob, lang = 'vi', signal = null, filename = 'recording.webm') => {
  // --- CHẾ ĐỘ MOCK (Test không cần Backend) ---
  if (USE_MOCK) {
    console.log("🎙️ [MOCK] Đang gửi audio blob:", audioBlob.size, "bytes", "Ngôn ngữ:", lang);
    return new Promise((resolve, reject) => {
      const controller = new AbortController();
      if (signal) {
        signal.addEventListener('abort', () => controller.abort());
      }

      const timeoutId = setTimeout(() => {
        if (controller.signal.aborted) {
          reject(new Error('TIMEOUT'));
          return;
        }

        // Tạo một blob mpeg giả hoặc gọi Web Speech API đọc văn bản giả để có trải nghiệm
        const text = lang === 'vi' 
          ? 'Đây là kết quả giả lập từ Frontend. Ngọ Môn được xây dựng năm 1833 dưới triều vua Minh Mạng.'
          : 'This is a mock result from Frontend. Ngo Mon Gate was built in 1833 during Emperor Minh Mang reign.';
        
        // Phát âm thanh giả lập
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === 'vi' ? 'vi-VN' : 'en-US';
        window.speechSynthesis.speak(utterance);

        // Trả về một blob rỗng đại diện cho audio (UI sẽ không phát lỗi nhưng dựa vào audio tag)
        // Lưu ý: với blob rỗng thì audio HTML player sẽ không phát, nhưng Web Speech ở trên sẽ nói.
        const mockBlob = new Blob(['mock audio data'], { type: 'audio/mpeg' });
        resolve(mockBlob);
      }, 2000); // Giả lập độ trễ 2 giây của mạng
    });
  }
  // --- KẾT THÚC MOCK ---

  const formData = new FormData();
  formData.append('audio', audioBlob, filename);
  formData.append('lang', lang);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  if (signal) {
    signal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch(`${VOICE_API_URL}/api/voice/chat`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.blob();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('TIMEOUT');
    }
    throw error;
  }
};
