import { useState, useRef, useEffect, useCallback } from 'react';

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserNodeRef = useRef(null);
  const timerRef = useRef(null);
  const mimeTypeRef = useRef('');
  const durationRef = useRef(0);
  const startTimeRef = useRef(0);
  const recordingActiveRef = useRef(false); // Guard chống race condition

  const startRecording = useCallback(async () => {
    // Nếu đang ghi rồi thì bỏ qua
    if (recordingActiveRef.current) return;
    recordingActiveRef.current = true;

    try {
      setError(null);
      durationRef.current = 0;
      startTimeRef.current = 0;

      console.log('[Recorder] Requesting microphone...');
      const audioConstraints = {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      };
      const stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });

      // Kiểm tra xem có bị hủy trong khi chờ getUserMedia không
      if (!recordingActiveRef.current) {
        stream.getTracks().forEach(t => t.stop());
        console.log('[Recorder] Cancelled during getUserMedia');
        return;
      }

      streamRef.current = stream;

      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserNodeRef.current = analyser;

      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/mp4'; 
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = ''; 
        }
      }
      mimeTypeRef.current = mimeType;

      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      mediaRecorderRef.current = mediaRecorder;

      const chunks = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const finalMime = mimeTypeRef.current || 'audio/wav';
        const blob = new Blob(chunks, { type: finalMime });
        console.log('[Recorder] Blob created, size:', blob.size, 'duration:', durationRef.current);
        setAudioBlob(blob);
      };

      mediaRecorder.start();
      startTimeRef.current = Date.now();
      setIsRecording(true);
      setDuration(0);
      console.log('[Recorder] Recording started');

      timerRef.current = setInterval(() => {
        setDuration((prev) => {
          const next = prev + 1;
          durationRef.current = next;
          if (next >= 60) {
            stopRecording();
            return 60;
          }
          return next;
        });
      }, 1000);

    } catch (err) {
      console.error('[Recorder] Error starting recording:', err);
      recordingActiveRef.current = false;
      setError(err.name === 'NotAllowedError' ? 'microphone_denied' : 'recording_error');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (!recordingActiveRef.current) return;
    recordingActiveRef.current = false;

    // Tính duration chính xác bằng Date.now
    if (startTimeRef.current > 0) {
      durationRef.current = (Date.now() - startTimeRef.current) / 1000;
      console.log('[Recorder] Actual duration:', durationRef.current, 's');
      startTimeRef.current = 0;
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsRecording(false);
  }, []);

  const resetRecording = useCallback(() => {
    setAudioBlob(null);
    setDuration(0);
    durationRef.current = 0;
    startTimeRef.current = 0;
    setError(null);
  }, []);

  useEffect(() => {
    return () => {
      recordingActiveRef.current = false;
      stopRecording();
    };
  }, [stopRecording]);

  const getFilename = () => {
    const mime = mimeTypeRef.current;
    if (mime.includes('mp4')) return 'recording.mp4';
    if (mime.includes('ogg')) return 'recording.ogg';
    return 'recording.webm';
  };

  return {
    isRecording,
    audioBlob,
    duration,
    durationRef,
    analyserNode: analyserNodeRef.current,
    startRecording,
    stopRecording,
    resetRecording,
    getFilename,
    error
  };
};
