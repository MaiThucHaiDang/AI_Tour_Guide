const PHOTO_BOOTH_BASE = '/assets/photo-booth';

export const PHOTO_BOOTH_COVER_FRAME = {
  key: 'bia_tongthe',
  type: 'cover',
  artifactId: null,
  nameVi: 'Ảnh bìa tổng thể',
  nameEn: 'Trip cover photo',
  src: `${PHOTO_BOOTH_BASE}/bia_tongthe.png`
};

export const PHOTO_BOOTH_FRAMES = {
  1: {
    key: 'cuahoabinh',
    artifactId: 1,
    nameVi: 'Cửa Hòa Bình',
    nameEn: 'Hoa Binh Gate',
    src: `${PHOTO_BOOTH_BASE}/cuahoabinh.png`
  },
  2: {
    key: 'dienkientrung',
    artifactId: 2,
    nameVi: 'Điện Kiến Trung',
    nameEn: 'Kien Trung Palace',
    src: `${PHOTO_BOOTH_BASE}/dienkientrung.png`
  },
  3: {
    key: 'cungtruongsanh',
    artifactId: 3,
    nameVi: 'Cung Trường Sanh',
    nameEn: 'Truong Sanh Palace',
    src: `${PHOTO_BOOTH_BASE}/cungtruongsanh.png`
  },
  4: {
    key: 'cungdientho',
    artifactId: 4,
    nameVi: 'Cung Diên Thọ',
    nameEn: 'Dien Tho Palace',
    src: `${PHOTO_BOOTH_BASE}/cungdientho.png`
  },
  5: {
    key: 'cuachuongduc',
    artifactId: 5,
    nameVi: 'Cửa Chương Đức',
    nameEn: 'Chuong Duc Gate',
    src: `${PHOTO_BOOTH_BASE}/cuachuongduc.png`
  },
  6: {
    key: 'hungmieu',
    artifactId: 6,
    nameVi: 'Hưng Miếu',
    nameEn: 'Hung Mieu Temple',
    src: `${PHOTO_BOOTH_BASE}/hungmieu.png`
  },
  7: {
    key: 'themieu',
    artifactId: 7,
    nameVi: 'Thế Miếu',
    nameEn: 'The Mieu Temple',
    src: `${PHOTO_BOOTH_BASE}/themieu.png`
  },
  8: {
    key: 'dienthaihoa',
    artifactId: 8,
    nameVi: 'Điện Thái Hòa',
    nameEn: 'Thai Hoa Palace',
    src: `${PHOTO_BOOTH_BASE}/dienthaihoa.png`
  },
  9: {
    key: 'nendiencanchanh',
    artifactId: 9,
    nameVi: 'Nền điện Cần Chánh',
    nameEn: 'Can Chanh Palace Foundation',
    src: `${PHOTO_BOOTH_BASE}/nendiencanchanh.png`
  },
  10: {
    key: 'duyetthiduong',
    artifactId: 10,
    nameVi: 'Duyệt Thị Đường',
    nameEn: 'Duyet Thi Duong Theater',
    src: `${PHOTO_BOOTH_BASE}/duyetthiduong.png`
  },
  11: {
    key: 'phunoivu',
    artifactId: 11,
    nameVi: 'Phủ Nội Vụ',
    nameEn: 'Phu Noi Vu',
    src: `${PHOTO_BOOTH_BASE}/phunoivu.png`
  },
  12: {
    key: 'vuoncoha',
    artifactId: 12,
    nameVi: 'Vườn Cơ Hạ',
    nameEn: 'Co Ha Garden',
    src: `${PHOTO_BOOTH_BASE}/vuoncoha.png`
  },
  13: {
    key: 'trieumieu',
    artifactId: 13,
    nameVi: 'Triệu Miếu',
    nameEn: 'Trieu Mieu Temple',
    src: `${PHOTO_BOOTH_BASE}/trieumieu.png`
  },
  14: {
    key: 'thaimieu',
    artifactId: 14,
    nameVi: 'Thái Miếu',
    nameEn: 'Thai Mieu Temple',
    src: `${PHOTO_BOOTH_BASE}/thaimieu.png`
  },
  15: {
    key: 'cuahiennhon',
    artifactId: 15,
    nameVi: 'Cửa Hiển Nhơn',
    nameEn: 'Hien Nhon Gate',
    src: `${PHOTO_BOOTH_BASE}/cuahiennhon.png`
  },
  16: {
    key: 'dienlongan',
    artifactId: 16,
    nameVi: 'Điện Long An',
    nameEn: 'Long An Palace',
    src: `${PHOTO_BOOTH_BASE}/dienlongan.png`
  },
  17: {
    key: 'cuangomon',
    artifactId: 17,
    nameVi: 'Ngọ Môn',
    nameEn: 'Ngo Mon Gate',
    src: `${PHOTO_BOOTH_BASE}/cuangomon.png`
  }
};

export const getPhotoBoothFrame = (artifactId) => {
  const numericId = Number(artifactId);
  return Number.isFinite(numericId) ? PHOTO_BOOTH_FRAMES[numericId] || null : null;
};

export const hasPhotoBoothFrame = (artifactId) => Boolean(getPhotoBoothFrame(artifactId));

export const getAllPhotoBoothFrames = () => [
  PHOTO_BOOTH_COVER_FRAME,
  ...Object.values(PHOTO_BOOTH_FRAMES)
];
