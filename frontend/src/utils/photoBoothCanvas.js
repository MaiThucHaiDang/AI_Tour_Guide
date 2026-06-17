const BLACK_THRESHOLD = 34;
const MIN_MASK_AREA_RATIO = 0.04;
const COMPONENT_SCAN_STEP = 2;
const preparedFrameCache = new Map();

const loadImage = (src) => new Promise((resolve, reject) => {
  const image = new Image();
  image.crossOrigin = 'anonymous';
  image.onload = () => resolve(image);
  image.onerror = () => reject(new Error(`Cannot load image: ${src}`));
  image.src = src;
});

const isDarkPixel = (data, index) => (
  data[index + 3] > 230
  && data[index] <= BLACK_THRESHOLD
  && data[index + 1] <= BLACK_THRESHOLD
  && data[index + 2] <= BLACK_THRESHOLD
);

const findDarkBounds = (imageData, width, height) => {
  const { data } = imageData;
  const scanWidth = Math.ceil(width / COMPONENT_SCAN_STEP);
  const scanHeight = Math.ceil(height / COMPONENT_SCAN_STEP);
  const dark = new Uint8Array(scanWidth * scanHeight);
  const visited = new Uint8Array(scanWidth * scanHeight);

  for (let sy = 0; sy < scanHeight; sy += 1) {
    for (let sx = 0; sx < scanWidth; sx += 1) {
      const x = Math.min(width - 1, sx * COMPONENT_SCAN_STEP);
      const y = Math.min(height - 1, sy * COMPONENT_SCAN_STEP);
      const index = (y * width + x) * 4;
      if (isDarkPixel(data, index)) {
        dark[sy * scanWidth + sx] = 1;
      }
    }
  }

  let best = null;
  const queueX = [];
  const queueY = [];

  for (let sy = 0; sy < scanHeight; sy += 1) {
    for (let sx = 0; sx < scanWidth; sx += 1) {
      const startIndex = sy * scanWidth + sx;
      if (!dark[startIndex] || visited[startIndex]) continue;

      let minX = sx;
      let minY = sy;
      let maxX = sx;
      let maxY = sy;
      let count = 0;
      queueX.length = 0;
      queueY.length = 0;
      queueX.push(sx);
      queueY.push(sy);
      visited[startIndex] = 1;

      for (let cursor = 0; cursor < queueX.length; cursor += 1) {
        const cx = queueX[cursor];
        const cy = queueY[cursor];
        count += 1;
        if (cx < minX) minX = cx;
        if (cx > maxX) maxX = cx;
        if (cy < minY) minY = cy;
        if (cy > maxY) maxY = cy;

        const neighbors = [
          [cx + 1, cy],
          [cx - 1, cy],
          [cx, cy + 1],
          [cx, cy - 1]
        ];
        neighbors.forEach(([nx, ny]) => {
          if (nx < 0 || ny < 0 || nx >= scanWidth || ny >= scanHeight) return;
          const nextIndex = ny * scanWidth + nx;
          if (!dark[nextIndex] || visited[nextIndex]) return;
          visited[nextIndex] = 1;
          queueX.push(nx);
          queueY.push(ny);
        });
      }

      if (!best || count > best.count) {
        best = { count, minX, minY, maxX, maxY };
      }
    }
  }

  if (!best || best.count * COMPONENT_SCAN_STEP * COMPONENT_SCAN_STEP < width * height * MIN_MASK_AREA_RATIO) {
    return null;
  }

  const x = Math.max(0, best.minX * COMPONENT_SCAN_STEP);
  const y = Math.max(0, best.minY * COMPONENT_SCAN_STEP);
  const right = Math.min(width - 1, ((best.maxX + 1) * COMPONENT_SCAN_STEP) - 1);
  const bottom = Math.min(height - 1, ((best.maxY + 1) * COMPONENT_SCAN_STEP) - 1);

  return {
    x,
    y,
    width: right - x + 1,
    height: bottom - y + 1
  };
};

const drawImageCover = (context, image, target) => {
  const sourceRatio = image.videoWidth
    ? image.videoWidth / image.videoHeight
    : image.naturalWidth / image.naturalHeight;
  const targetRatio = target.width / target.height;
  const sourceWidth = image.videoWidth || image.naturalWidth;
  const sourceHeight = image.videoHeight || image.naturalHeight;

  let cropWidth = sourceWidth;
  let cropHeight = sourceHeight;
  let cropX = 0;
  let cropY = 0;

  if (sourceRatio > targetRatio) {
    cropWidth = sourceHeight * targetRatio;
    cropX = (sourceWidth - cropWidth) / 2;
  } else {
    cropHeight = sourceWidth / targetRatio;
    cropY = (sourceHeight - cropHeight) / 2;
  }

  context.drawImage(
    image,
    cropX,
    cropY,
    cropWidth,
    cropHeight,
    target.x,
    target.y,
    target.width,
    target.height
  );
};

const clearDarkPixels = (context, frameImage, maskBounds) => {
  const frameCanvas = document.createElement('canvas');
  frameCanvas.width = frameImage.naturalWidth;
  frameCanvas.height = frameImage.naturalHeight;
  const frameContext = frameCanvas.getContext('2d');
  frameContext.drawImage(frameImage, 0, 0);

  const imageData = frameContext.getImageData(
    maskBounds.x,
    maskBounds.y,
    maskBounds.width,
    maskBounds.height
  );
  const { data } = imageData;
  for (let index = 0; index < data.length; index += 4) {
    if (
      data[index] <= BLACK_THRESHOLD
      && data[index + 1] <= BLACK_THRESHOLD
      && data[index + 2] <= BLACK_THRESHOLD
    ) {
      data[index + 3] = 0;
    }
  }

  frameContext.putImageData(imageData, maskBounds.x, maskBounds.y);
  context.drawImage(frameCanvas, 0, 0);
};

export const getPhotoFrameMaskBounds = async (frameSrc) => {
  const frameImage = await loadImage(frameSrc);
  const canvas = document.createElement('canvas');
  canvas.width = frameImage.naturalWidth;
  canvas.height = frameImage.naturalHeight;
  const context = canvas.getContext('2d');
  context.drawImage(frameImage, 0, 0);
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  const maskBounds = findDarkBounds(imageData, canvas.width, canvas.height);
  if (!maskBounds) {
    throw new Error('Không tìm thấy vùng đen trong khung ảnh.');
  }
  return {
    frameImage,
    maskBounds,
    width: canvas.width,
    height: canvas.height
  };
};

export const preparePhotoBoothFrame = async (frameSrc) => {
  if (preparedFrameCache.has(frameSrc)) {
    return preparedFrameCache.get(frameSrc);
  }

  const preparedPromise = (async () => {
  const { frameImage, maskBounds, width, height } = await getPhotoFrameMaskBounds(frameSrc);
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  clearDarkPixels(context, frameImage, maskBounds);
  return {
    frameImage,
    overlaySrc: canvas.toDataURL('image/png'),
    maskBounds,
    width,
    height
  };
  })();

  preparedFrameCache.set(frameSrc, preparedPromise);
  try {
    return await preparedPromise;
  } catch (error) {
    preparedFrameCache.delete(frameSrc);
    throw error;
  }
};

export const composePhotoBoothImage = async ({
  frameSrc,
  cameraSource,
  mimeType = 'image/png',
  quality
}) => {
  const { frameImage, maskBounds, width, height } = await preparePhotoBoothFrame(frameSrc);
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');

  drawImageCover(context, cameraSource, maskBounds);
  clearDarkPixels(context, frameImage, maskBounds);

  return quality === undefined ? canvas.toDataURL(mimeType) : canvas.toDataURL(mimeType, quality);
};

export const optimizePhotoBoothImage = async (
  imageBase64,
  {
    maxWidth = 1400,
    maxHeight = 1400,
    mimeType = 'image/jpeg',
    quality = 0.9
  } = {}
) => {
  if (!imageBase64) return '';

  const image = await loadImage(imageBase64);
  const sourceWidth = image.naturalWidth;
  const sourceHeight = image.naturalHeight;
  const scale = Math.min(1, maxWidth / sourceWidth, maxHeight / sourceHeight);
  const targetWidth = Math.max(1, Math.round(sourceWidth * scale));
  const targetHeight = Math.max(1, Math.round(sourceHeight * scale));
  const canvas = document.createElement('canvas');
  canvas.width = targetWidth;
  canvas.height = targetHeight;
  const context = canvas.getContext('2d');

  context.drawImage(image, 0, 0, targetWidth, targetHeight);
  return canvas.toDataURL(mimeType, quality);
};

export const preloadPhotoBoothFrames = async (frames = []) => {
  const uniqueSources = Array.from(new Set(
    frames
      .map((frame) => frame?.src)
      .filter(Boolean)
  ));

  const results = await Promise.allSettled(
    uniqueSources.map((src) => preparePhotoBoothFrame(src))
  );

  return {
    total: uniqueSources.length,
    ready: results.filter((result) => result.status === 'fulfilled').length,
    failed: results
      .map((result, index) => ({ result, src: uniqueSources[index] }))
      .filter(({ result }) => result.status === 'rejected')
      .map(({ src, result }) => ({ src, error: result.reason }))
  };
};
