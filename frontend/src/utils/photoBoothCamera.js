let sharedStream = null;
let releaseTimer = null;
let pendingStreamPromise = null;

const stopStream = (stream) => {
  stream?.getTracks().forEach((track) => track.stop());
};

export const getPhotoBoothCameraStream = async () => {
  window.clearTimeout(releaseTimer);
  releaseTimer = null;

  const hasLiveTrack = sharedStream?.getVideoTracks().some((track) => track.readyState === 'live');
  if (sharedStream && hasLiveTrack) {
    return sharedStream;
  }

  if (pendingStreamPromise) {
    return pendingStreamPromise;
  }

  pendingStreamPromise = navigator.mediaDevices.getUserMedia({
    video: {
      facingMode: 'user',
      width: { ideal: 1920 },
      height: { ideal: 1440 }
    },
    audio: false
  }).then((stream) => {
    stopStream(sharedStream);
    sharedStream = stream;
    return stream;
  }).finally(() => {
    pendingStreamPromise = null;
  });

  return pendingStreamPromise;
};

export const schedulePhotoBoothCameraRelease = (delayMs = 180000) => {
  window.clearTimeout(releaseTimer);
  releaseTimer = window.setTimeout(() => {
    stopStream(sharedStream);
    sharedStream = null;
    releaseTimer = null;
  }, delayMs);
};

export const releasePhotoBoothCameraStream = () => {
  window.clearTimeout(releaseTimer);
  releaseTimer = null;
  stopStream(sharedStream);
  sharedStream = null;
};
