import assert from 'node:assert/strict';

const calls = [];
let currentUtterance = null;
const spokenUtterances = [];

class MockSpeechSynthesisUtterance {
  constructor(text) {
    this.text = text;
    this.lang = '';
    this.rate = 1;
    this.voice = null;
    this.onend = null;
    this.onerror = null;
  }
}

const synth = {
  speaking: false,
  paused: false,
  voices: [
    { lang: 'vi-VN', name: 'Vietnamese' },
    { lang: 'en-US', name: 'English' },
  ],
  getVoices() {
    calls.push(['getVoices']);
    return this.voices;
  },
  speak(utterance) {
    calls.push(['speak', utterance.text, utterance.lang, utterance.voice?.lang || null]);
    currentUtterance = utterance;
    spokenUtterances.push(utterance);
    this.speaking = true;
    this.paused = false;
  },
  pause() {
    calls.push(['pause']);
    if (this.speaking) this.paused = true;
  },
  resume() {
    calls.push(['resume']);
    if (this.speaking) this.paused = false;
  },
  cancel() {
    calls.push(['cancel']);
    this.speaking = false;
    this.paused = false;
    currentUtterance = null;
  },
};

globalThis.window = { speechSynthesis: synth };
globalThis.SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;

const {
  getTTSQueueInfo,
  getTTSState,
  isTTSPaused,
  isTTSPlaying,
  pauseTTS,
  playTTS,
  resumeTTS,
  stopTTS,
} = await import('../src/services/apiService.js');

const reset = () => {
  calls.length = 0;
  spokenUtterances.length = 0;
  synth.cancel();
  calls.length = 0;
  currentUtterance = null;
};

const finishCurrentUtterance = () => {
  const utterance = currentUtterance;
  assert.ok(utterance, 'expected an active utterance');
  synth.speaking = false;
  currentUtterance = null;
  utterance.onend();
};

const errorCurrentUtterance = () => {
  const utterance = currentUtterance;
  assert.ok(utterance, 'expected an active utterance');
  synth.speaking = false;
  currentUtterance = null;
  utterance.onerror();
};

const finishAllUtterances = (max = 20) => {
  for (let index = 0; index < max && currentUtterance; index += 1) {
    finishCurrentUtterance();
  }
};

const systemGeneratedSpeechText = [
  'Ngọ Môn là cổng chính phía nam của Hoàng thành Huế, được xây dựng dưới triều vua Minh Mạng vào năm 1833.',
  'Công trình gồm phần nền đài bằng gạch đá và lầu Ngũ Phụng ở phía trên, tạo nên hình ảnh rất đặc trưng của kiến trúc cung đình Nguyễn.',
  'Đây là nơi diễn ra nhiều nghi lễ quan trọng của triều đình, đồng thời gắn với sự kiện vua Bảo Đại tuyên bố thoái vị vào ngày 30 tháng 8 năm 1945.',
  'Khi tham quan, bạn nên đứng ở khoảng sân rộng phía trước để nhìn rõ bố cục năm cửa, hệ mái nhiều tầng và trục nghi lễ dẫn vào Đại Nội.',
  'Nếu muốn nghe tiếp, tôi có thể kể thêm về lầu Ngũ Phụng hoặc gợi ý điểm dừng kế tiếp trong Hoàng thành.'
].join(' ');

const longSystemGeneratedSpeechText = [
  systemGeneratedSpeechText,
  'Điện Thái Hòa nằm trên trục trung tâm của Hoàng thành, từng là nơi thiết triều và tổ chức những nghi lễ quan trọng nhất của triều Nguyễn.',
  'Không gian phía trước điện mở rộng thành sân Đại triều nghi, nơi các quan văn võ xếp hàng theo phẩm trật trong những dịp đại lễ.',
  'Đi tiếp về phía bắc, du khách có thể cảm nhận rõ sự chuyển tiếp từ khu nghi lễ công cộng sang vùng sinh hoạt riêng tư hơn của hoàng gia.',
  'Những lớp mái, hàng cột và khoảng sân nối tiếp nhau tạo thành nhịp tham quan chậm rãi, phù hợp để vừa quan sát vừa nghe thuyết minh.',
  'Nếu bạn đang đứng tại đây, hãy nhìn theo trục nam bắc để thấy cách kinh thành tổ chức quyền lực, nghi lễ và cảnh quan trong cùng một bố cục.'
].join(' ');

const moderatePromptLengthSpeechText = [
  systemGeneratedSpeechText,
  'Từ vị trí phía trước Ngọ Môn, du khách có thể quan sát rõ cách công trình tạo nên một ngưỡng chuyển tiếp trang nghiêm giữa không gian bên ngoài và vùng nghi lễ của Hoàng thành.',
  'Phần nền đài vững chắc khiến cổng có dáng vẻ bề thế, còn lầu Ngũ Phụng phía trên làm mềm lại khối kiến trúc bằng hệ mái nhiều tầng và nhịp điệu cân xứng.',
  'Khi nhìn kỹ hơn, khanh sẽ thấy công trình không chỉ là lối đi, mà còn là sân khấu quyền lực, nơi nghi lễ triều đình được tổ chức trước ánh nhìn của quan lại và dân chúng trong những dịp trọng đại.',
  'Từ đây đi sâu vào Đại Nội, trục tham quan tiếp tục dẫn về Điện Thái Hòa, nơi không khí nghi lễ trở nên rõ rệt hơn qua sân rộng, hàng cột, mái điện và những khoảng chuyển tiếp trang trọng.',
  'Nếu có thời gian, hãy đi chậm qua từng lớp không gian, vì chính nhịp chuyển từ cổng, sân, điện đến các cung viện phía sau giúp người tham quan hiểu cách triều Nguyễn tổ chức quyền lực, lễ nghi và đời sống cung đình.',
  'Điểm đáng chú ý là các chi tiết kiến trúc không đứng riêng lẻ, mà cùng nhau kể một câu chuyện về trật tự, nghi lễ và mỹ cảm Huế, từ thế đứng của cổng cho đến đường nhìn mở về phía trung tâm Hoàng thành.',
  'Vì vậy, khi chụp ảnh hay nghe thuyết minh tại đây, khanh nên giữ lại một khoảnh khắc nhìn bao quát toàn cảnh trước, rồi mới tiến gần để quan sát mái, cửa, nền đài và các lớp không gian nối tiếp nhau.'
].join(' ');

const normalizeSpeech = (text) => String(text || '').replace(/\s+/g, ' ').trim();

const test = (name, fn) => {
  try {
    reset();
    fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`not ok - ${name}`);
    throw error;
  }
};

test('1 play starts speech and selects Vietnamese voice', () => {
  playTTS('Xin chao', 'vi');
  assert.equal(synth.speaking, true);
  assert.equal(getTTSState(), 'playing');
  assert.deepEqual(calls.at(-1), ['speak', 'Xin chao', 'vi-VN', 'vi-VN']);
});

test('2 pause moves active speech to paused', () => {
  playTTS('Xin chao', 'vi');
  assert.equal(pauseTTS(), true);
  assert.equal(synth.paused, true);
  assert.equal(getTTSState(), 'paused');
  assert.equal(isTTSPaused(), true);
});

test('3 resume moves paused speech back to playing', () => {
  playTTS('Xin chao', 'vi');
  pauseTTS();
  assert.equal(resumeTTS(), true);
  assert.equal(synth.paused, false);
  assert.equal(getTTSState(), 'playing');
  assert.equal(isTTSPlaying(), true);
});

test('4 stop cancels active speech', () => {
  playTTS('Xin chao', 'vi');
  stopTTS();
  assert.equal(synth.speaking, false);
  assert.equal(getTTSState(), 'idle');
  assert.equal(calls.some((call) => call[0] === 'cancel'), true);
});

test('5 stop cancels paused speech', () => {
  playTTS('Xin chao', 'vi');
  pauseTTS();
  stopTTS();
  assert.equal(synth.speaking, false);
  assert.equal(synth.paused, false);
  assert.equal(getTTSState(), 'idle');
});

test('6 playing a second message cancels the first', () => {
  playTTS('Cau mot', 'vi');
  playTTS('Cau hai', 'vi');
  const speakCalls = calls.filter((call) => call[0] === 'speak');
  const cancelCalls = calls.filter((call) => call[0] === 'cancel');
  assert.equal(speakCalls.length, 2);
  assert.equal(cancelCalls.length >= 1, true);
  assert.equal(speakCalls.at(-1)[1], 'Cau hai');
});

test('7 end callback resets state to idle', () => {
  let ended = false;
  playTTS('Xin chao', 'vi', () => {
    ended = true;
  });
  finishCurrentUtterance();
  assert.equal(ended, true);
  assert.equal(getTTSState(), 'idle');
});

test('8 stop suppresses end callback', () => {
  let ended = false;
  playTTS('Xin chao', 'vi', () => {
    ended = true;
  });
  stopTTS();
  assert.equal(ended, false);
});

test('9 English playback selects English locale', () => {
  playTTS('Hello', 'en');
  assert.deepEqual(calls.at(-1), ['speak', 'Hello', 'en-US', 'en-US']);
});

test('10 unsupported browser returns unsupported state without crashing', () => {
  const originalWindow = globalThis.window;
  globalThis.window = {};
  assert.equal(getTTSState(), 'unsupported');
  assert.equal(playTTS('Hello', 'en'), null);
  globalThis.window = originalWindow;
});

test('11 long system speech is split into multiple utterances', () => {
  playTTS(systemGeneratedSpeechText, 'vi');
  const info = getTTSQueueInfo();
  assert.equal(info.total > 1, true);
  assert.equal(spokenUtterances.length, 1);
  assert.equal(spokenUtterances[0].text.length <= 220, true);
});

test('12 long system speech does not call final callback halfway', () => {
  let ended = false;
  playTTS(systemGeneratedSpeechText, 'vi', () => {
    ended = true;
  });
  finishCurrentUtterance();
  assert.equal(ended, false);
  assert.equal(getTTSState(), 'playing');
  assert.equal(spokenUtterances.length >= 2, true);
});

test('13 long system speech calls final callback only after all chunks', () => {
  let ended = false;
  playTTS(systemGeneratedSpeechText, 'vi', () => {
    ended = true;
  });
  finishAllUtterances();
  assert.equal(ended, true);
  assert.equal(getTTSState(), 'idle');
  assert.equal(currentUtterance, null);
});

test('13b long system speech reads the full generated text', () => {
  playTTS(systemGeneratedSpeechText, 'vi');
  finishAllUtterances();
  const spokenText = spokenUtterances.map((utterance) => utterance.text).join(' ');
  assert.equal(normalizeSpeech(spokenText), normalizeSpeech(systemGeneratedSpeechText));
});

test('14 pause and resume work while a long queue is active', () => {
  playTTS(systemGeneratedSpeechText, 'vi');
  assert.equal(pauseTTS(), true);
  assert.equal(getTTSState(), 'paused');
  assert.equal(resumeTTS(), true);
  assert.equal(getTTSState(), 'playing');
});

test('15 pause ignores browser end event and play resumes the queue', () => {
  let ended = false;
  playTTS(systemGeneratedSpeechText, 'vi', () => {
    ended = true;
  });
  assert.equal(pauseTTS(), true);
  const pausedUtterance = currentUtterance;
  synth.speaking = false;
  currentUtterance = null;
  pausedUtterance.onend();
  assert.equal(ended, false);
  assert.equal(getTTSState(), 'paused');
  assert.equal(spokenUtterances.length, 1);
  assert.equal(resumeTTS(), true);
  assert.equal(getTTSState(), 'playing');
  assert.equal(spokenUtterances.length, 2);
  finishAllUtterances();
  assert.equal(ended, true);
  assert.equal(getTTSState(), 'idle');
});

test('16 stop cancels a long queue and suppresses final callback', () => {
  let ended = false;
  playTTS(systemGeneratedSpeechText, 'vi', () => {
    ended = true;
  });
  finishCurrentUtterance();
  stopTTS();
  assert.equal(getTTSState(), 'idle');
  assert.equal(ended, false);
  assert.equal(getTTSQueueInfo().total, 0);
});

test('17 an utterance error continues with the remaining queue', () => {
  let ended = false;
  playTTS(systemGeneratedSpeechText, 'vi', () => {
    ended = true;
  });
  errorCurrentUtterance();
  assert.equal(ended, false);
  assert.equal(getTTSState(), 'playing');
  assert.equal(spokenUtterances.length >= 2, true);
});

test('18 long narration survives 5 pause/play cycles and reads full text', () => {
  let endedCount = 0;
  let pauseSuccessCount = 0;
  let resumeSuccessCount = 0;

  playTTS(longSystemGeneratedSpeechText, 'vi', () => {
    endedCount += 1;
  });

  for (let cycle = 0; cycle < 5; cycle += 1) {
    assert.equal(pauseTTS(), true);
    pauseSuccessCount += 1;
    assert.equal(getTTSState(), 'paused');
    assert.equal(endedCount, 0);

    const pausedUtterance = currentUtterance;
    assert.ok(pausedUtterance, 'expected active utterance during pause cycle');
    synth.speaking = false;
    currentUtterance = null;
    pausedUtterance.onend();

    assert.equal(endedCount, 0);
    assert.equal(getTTSState(), 'paused');
    assert.equal(resumeTTS(), true);
    resumeSuccessCount += 1;
    assert.equal(getTTSState(), 'playing');
  }

  finishAllUtterances();

  const spokenText = spokenUtterances.map((utterance) => utterance.text).join(' ');
  assert.equal(pauseSuccessCount, 5);
  assert.equal(resumeSuccessCount, 5);
  assert.equal(endedCount, 1);
  assert.equal(getTTSState(), 'idle');
  assert.equal(normalizeSpeech(spokenText).includes(normalizeSpeech(longSystemGeneratedSpeechText)), true);
});

test('19 pause near later chunk boundary resumes next chunk and finishes full text', () => {
  let endedCount = 0;
  playTTS(longSystemGeneratedSpeechText, 'vi', () => {
    endedCount += 1;
  });

  finishCurrentUtterance();
  finishCurrentUtterance();
  assert.equal(spokenUtterances.length >= 3, true);
  const activeBeforePause = currentUtterance;
  const activeText = activeBeforePause.text;

  assert.equal(pauseTTS(), true);
  assert.equal(getTTSState(), 'paused');

  synth.paused = true;
  synth.speaking = true;
  currentUtterance = null;
  activeBeforePause.onend();

  const infoAfterPausedEnd = getTTSQueueInfo();
  assert.equal(infoAfterPausedEnd.state, 'paused');
  assert.equal(infoAfterPausedEnd.pausedEndedChunk >= 0, true);
  assert.equal(endedCount, 0);

  assert.equal(resumeTTS(), true);
  assert.equal(getTTSState(), 'playing');
  assert.notEqual(currentUtterance?.text, activeText);

  finishAllUtterances();
  assert.equal(endedCount, 1);
  assert.equal(getTTSState(), 'idle');
});

test('20 pause/play across later chunks succeeds 5 times and reaches the end', () => {
  let endedCount = 0;
  let pauseSuccessCount = 0;
  let resumeSuccessCount = 0;

  playTTS(longSystemGeneratedSpeechText, 'vi', () => {
    endedCount += 1;
  });

  for (let cycle = 0; cycle < 5; cycle += 1) {
    if (cycle > 0 && currentUtterance) {
      finishCurrentUtterance();
    }

    assert.equal(pauseTTS(), true);
    pauseSuccessCount += 1;

    const pausedUtterance = currentUtterance;
    assert.ok(pausedUtterance, 'expected active utterance in later-chunk stress cycle');
    synth.paused = true;
    synth.speaking = true;
    currentUtterance = null;
    pausedUtterance.onend();

    assert.equal(endedCount, 0);
    assert.equal(getTTSState(), 'paused');
    assert.equal(resumeTTS(), true);
    resumeSuccessCount += 1;
    assert.equal(getTTSState(), 'playing');
  }

  finishAllUtterances();
  assert.equal(pauseSuccessCount, 5);
  assert.equal(resumeSuccessCount, 5);
  assert.equal(endedCount, 1);
  assert.equal(getTTSState(), 'idle');
});

test('21 moderate-length generated narration survives pause/play at many text positions', () => {
  let endedCount = 0;
  let pauseSuccessCount = 0;
  let resumeSuccessCount = 0;

  playTTS(moderatePromptLengthSpeechText, 'vi', () => {
    endedCount += 1;
  });

  const queueInfo = getTTSQueueInfo();
  assert.equal(queueInfo.total >= 8, true);

  for (let targetChunk = 0; targetChunk < queueInfo.total && currentUtterance; targetChunk += 2) {
    while (getTTSQueueInfo().currentChunk < targetChunk && currentUtterance) {
      finishCurrentUtterance();
    }

    if (!currentUtterance) break;

    assert.equal(pauseTTS(), true);
    pauseSuccessCount += 1;
    assert.equal(getTTSState(), 'paused');
    assert.equal(endedCount, 0);

    const pausedUtterance = currentUtterance;
    synth.paused = true;
    synth.speaking = true;
    currentUtterance = null;
    pausedUtterance.onend();

    assert.equal(getTTSState(), 'paused');
    assert.equal(endedCount, 0);
    assert.equal(resumeTTS(), true);
    resumeSuccessCount += 1;
    assert.equal(getTTSState(), 'playing');
  }

  finishAllUtterances(60);

  const spokenText = spokenUtterances.map((utterance) => utterance.text).join(' ');
  assert.equal(pauseSuccessCount >= 4, true);
  assert.equal(resumeSuccessCount, pauseSuccessCount);
  assert.equal(endedCount, 1);
  assert.equal(getTTSState(), 'idle');
  assert.equal(normalizeSpeech(spokenText).includes(normalizeSpeech(moderatePromptLengthSpeechText)), true);
});
