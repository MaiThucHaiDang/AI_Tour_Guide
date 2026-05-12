
/* =====================================================
   AI TOUR GUIDE SYSTEM DATABASE
   ROLE: DATABASE ENGINEER
===================================================== */

CREATE DATABASE AI_Tour_Guide;
GO

USE AI_Tour_Guide;
GO



/* =====================================================
   TABLE: LOCATIONS
===================================================== */

CREATE TABLE Locations (
    loc_id INT PRIMARY KEY IDENTITY(1,1),

    name_vi NVARCHAR(255) NOT NULL,
    name_en NVARCHAR(255) NOT NULL,

    gps_coordinates NVARCHAR(100),

    open_hours NVARCHAR(100)
);



/* =====================================================
   TABLE: ARTIFACTS
===================================================== */

CREATE TABLE Artifacts (
    art_id INT PRIMARY KEY IDENTITY(1,1),

    loc_id INT NOT NULL,

    name_vi NVARCHAR(255) NOT NULL,
    name_en NVARCHAR(255) NOT NULL,

    history_text_vi NVARCHAR(MAX) NOT NULL,
    history_text_en NVARCHAR(MAX) NOT NULL,

    author NVARCHAR(255),

    year INT,

    UNIQUE(name_vi),
    FOREIGN KEY (loc_id)
    REFERENCES Locations(loc_id)
);



/* =====================================================
   TABLE: PRE_COMPUTED_AUDIO
   RESPONSE CACHE FOR FAQ
===================================================== */

CREATE TABLE Pre_computed_Audio (
    audio_id INT PRIMARY KEY IDENTITY(1,1),

    artifact_id INT NOT NULL,

    question_vi NVARCHAR(255) NOT NULL,
    question_en NVARCHAR(255) NOT NULL,

    answer_vi NVARCHAR(MAX) NOT NULL,
    answer_en NVARCHAR(MAX) NOT NULL,

    audio_vi NVARCHAR(255),
    audio_en NVARCHAR(255),

    FOREIGN KEY (artifact_id)
    REFERENCES Artifacts(art_id)
);



/* =====================================================
   TABLE: BILINGUAL_CONTENT
===================================================== */

CREATE TABLE Bilingual_Content (
    content_id INT PRIMARY KEY IDENTITY(1,1),

    artifact_id INT NOT NULL,

    lang NVARCHAR(10) NOT NULL
    CHECK (lang IN ('vi', 'en')),

    content_type NVARCHAR(50) NOT NULL
    CHECK (content_type IN ('faq', 'description', 'guide')),

    content_text NVARCHAR(MAX) NOT NULL,

    FOREIGN KEY (artifact_id)
    REFERENCES Artifacts(art_id)
);



/* =====================================================
   INDEX OPTIMIZATION
===================================================== */

CREATE INDEX idx_artifacts_loc
ON Artifacts(loc_id);

CREATE INDEX idx_audio_artifact
ON Pre_computed_Audio(artifact_id);

CREATE INDEX idx_bilingual_artifact
ON Bilingual_Content(artifact_id);

CREATE INDEX idx_artifact_name_vi
ON Artifacts(name_vi);

CREATE INDEX idx_artifact_name_en
ON Artifacts(name_en);



/* =====================================================
   INSERT DATA - LOCATIONS
===================================================== */

INSERT INTO Locations
(
    name_vi,
    name_en,
    gps_coordinates,
    open_hours
)
VALUES

(
    N'Kinh thành Huế',
    N'Hue Imperial City',
    N'16.4637,107.5909',
    N'07:00 - 17:30'
),

(
    N'Dinh Độc Lập',
    N'Independence Palace',
    N'10.7769,106.6953',
    N'08:00 - 16:30'
),

(
    N'Bảo tàng Chứng tích Chiến tranh',
    N'War Remnants Museum',
    N'10.7795,106.6920',
    N'07:30 - 17:30'
);


/* =====================================================
   INSERT DATA - ARTIFACTS
===================================================== */

/* =====================================================
   HUE IMPERIAL CITY
   loc_id = 1
===================================================== */

INSERT INTO Artifacts
(
    loc_id,
    name_vi,
    name_en,
    history_text_vi,
    history_text_en,
    author,
    year
)
VALUES
(
    1,
    N'Ngọ Môn',
    N'Ngo Mon Gate (Noon Gate)',
    N'Ngọ Môn là cổng chính phía nam của Hoàng thành Huế, được xây dựng dưới triều vua Minh Mạng vào năm 1833. Đây là công trình kiến trúc tiêu biểu của triều Nguyễn với thiết kế uy nghiêm dành riêng cho vua và các nghi lễ quan trọng của triều đình. Phía trên cổng là Lầu Ngũ Phụng, nơi diễn ra nhiều nghi lễ lớn như lễ ban sóc và duyệt binh. Ngọ Môn từng chứng kiến sự kiện vua Bảo Đại thoái vị năm 1945, đánh dấu sự kết thúc của chế độ phong kiến Việt Nam.',
    N'Ngo Mon Gate is the main southern entrance of the Hue Imperial City, constructed during Emperor Minh Mang’s reign in 1833. The structure represents the grand architecture of the Nguyen Dynasty and was reserved for emperors and important royal ceremonies. Above the gate stands the Five Phoenix Pavilion, where major imperial events such as military inspections and royal proclamations were held. Ngo Mon also witnessed Emperor Bao Dai’s abdication in 1945, marking the end of the Vietnamese feudal monarchy.',
    N'Nguyen Dynasty',
    1833
),
(
    1,
    N'Điện Thái Hòa',
    N'Thai Hoa Palace',
    N'Điện Thái Hòa là nơi thiết triều quan trọng nhất của triều Nguyễn, được xây dựng vào năm 1805 dưới thời vua Gia Long và được di dời, mở rộng dưới thời Minh Mạng. Công trình là biểu tượng quyền lực của hoàng đế với kiến trúc gỗ truyền thống cùng hệ thống cột sơn son thếp vàng tinh xảo. Đây là nơi tổ chức các buổi lễ đăng quang, tiếp đón sứ thần và những nghi thức trọng đại của triều đình Huế.',
    N'Thai Hoa Palace served as the most important ceremonial hall of the Nguyen Dynasty. Originally built in 1805 under Emperor Gia Long and later expanded during Minh Mang’s reign, the palace symbolized imperial authority through its traditional wooden architecture and gilded columns. Major royal ceremonies, coronations, diplomatic receptions, and court rituals were conducted here.',
    N'Gia Long Emperor',
    1805
),
(
    1,
    N'Tử Cấm Thành',
    N'Forbidden Purple City',
    N'Tử Cấm Thành là khu vực sinh hoạt riêng của hoàng gia Nguyễn nằm bên trong Hoàng thành Huế. Công trình được xây dựng vào đầu thế kỷ XIX và chỉ dành cho vua, hoàng hậu cùng các thành viên hoàng tộc. Khu vực này từng bao gồm nhiều cung điện, thư viện và vườn thượng uyển. Dù bị hư hại nặng trong chiến tranh, Tử Cấm Thành vẫn là biểu tượng quan trọng phản ánh đời sống cung đình Việt Nam thời phong kiến.',
    N'The Forbidden Purple City was the private residential area of the Nguyen royal family inside the Hue Imperial City. Built in the early nineteenth century, it was reserved exclusively for the emperor, queen, and royal relatives. The complex once contained numerous palaces, libraries, and royal gardens. Although heavily damaged during wars, it remains an important symbol of Vietnamese imperial life.',
    N'Nguyen Dynasty',
    1821
),
(
    1,
    N'Cửu Đỉnh',
    N'The Nine Dynastic Urns',
    N'Cửu Đỉnh là bộ chín đỉnh đồng lớn được đúc dưới thời vua Minh Mạng vào năm 1835 và đặt trước Thế Miếu trong Hoàng thành Huế. Mỗi đỉnh tượng trưng cho một vị vua Nguyễn và được chạm khắc nhiều hình ảnh về núi sông, động vật và văn hóa Việt Nam. Đây là kiệt tác nghệ thuật đúc đồng của triều Nguyễn và mang ý nghĩa về sự trường tồn của vương triều.',
    N'The Nine Dynastic Urns are a set of massive bronze urns cast during Emperor Minh Mang’s reign in 1835 and placed in front of The Mieu Temple. Each urn represents a Nguyen emperor and is decorated with detailed carvings depicting landscapes, animals, and symbols of Vietnamese culture. The urns are considered masterpieces of bronze casting and symbolize the longevity of the dynasty.',
    N'Minh Mang Emperor',
    1835
),
(
    1,
    N'Thế Miếu',
    N'The Mieu Temple',
    N'Thế Miếu là ngôi miếu thờ các vị hoàng đế triều Nguyễn, được xây dựng năm 1821 dưới thời vua Minh Mạng. Đây là nơi tổ chức các nghi lễ cúng tế hoàng gia và lưu giữ bài vị của các vị vua Nguyễn. Công trình nổi bật với kiến trúc gỗ truyền thống, mái ngói lưu ly và không gian trang nghiêm phản ánh tín ngưỡng thờ cúng tổ tiên của triều đình Huế.',
    N'The Mieu Temple is a royal ancestral temple dedicated to the emperors of the Nguyen Dynasty. Built in 1821 during Emperor Minh Mang’s reign, it served as the site for imperial worship ceremonies and houses memorial tablets of Nguyen emperors. The temple is notable for its traditional wooden architecture, glazed tile roofs, and solemn atmosphere representing royal ancestor worship.',
    N'Minh Mang Emperor',
    1821
);

/* =====================================================
   INDEPENDENCE PALACE
   loc_id = 2
===================================================== */

INSERT INTO Artifacts
(
    loc_id,
    name_vi,
    name_en,
    history_text_vi,
    history_text_en,
    author,
    year
)
VALUES
(
    2,
    N'Phòng Nội các',
    N'Cabinet Room',
    N'Phòng Nội các tại Dinh Độc Lập là nơi diễn ra các cuộc họp quan trọng của chính quyền Việt Nam Cộng hòa trước năm 1975. Căn phòng được thiết kế hiện đại với bàn họp lớn, hệ thống âm thanh và thiết bị phục vụ điều hành quốc gia. Đây là nơi nhiều quyết định chính trị và quân sự quan trọng đã được đưa ra trong giai đoạn chiến tranh Việt Nam.',
    N'The Cabinet Room inside Independence Palace was used for important meetings of the Republic of Vietnam government before 1975. The room featured a modern design with a large conference table, audio systems, and equipment for national administration. Many significant political and military decisions during the Vietnam War were made here.',
    N'Ngô Viết Thụ',
    1966
),
(
    2,
    N'Hầm chỉ huy',
    N'Command Bunker',
    N'Hầm chỉ huy nằm dưới tầng hầm của Dinh Độc Lập, được xây dựng với kết cấu kiên cố nhằm phục vụ hoạt động quân sự và liên lạc trong thời chiến. Bên trong vẫn còn nhiều thiết bị liên lạc, bản đồ tác chiến và máy móc nguyên bản từ trước năm 1975. Đây là nơi phản ánh rõ nét bối cảnh chiến tranh và hoạt động điều hành của chính quyền miền Nam Việt Nam.',
    N'The Command Bunker beneath Independence Palace was built with reinforced structures for wartime military operations and communications. The bunker still preserves original communication devices, military maps, and operational equipment from before 1975. It provides valuable insight into wartime administration and military coordination in South Vietnam.',
    N'Ngô Viết Thụ',
    1966
),
(
    2,
    N'Phòng Khánh tiết',
    N'State Banquet Hall',
    N'Phòng Khánh tiết là nơi tổ chức các buổi tiếp đón ngoại giao, quốc yến và sự kiện chính thức của chính quyền Việt Nam Cộng hòa. Không gian rộng lớn với sức chứa hàng trăm khách mời được thiết kế theo phong cách hiện đại kết hợp yếu tố truyền thống Việt Nam. Đây từng là nơi đón tiếp nhiều nguyên thủ và đoàn ngoại giao quốc tế.',
    N'The State Banquet Hall was used for diplomatic receptions, official ceremonies, and state banquets of the Republic of Vietnam government. The spacious hall, capable of hosting hundreds of guests, combines modern architecture with Vietnamese traditional elements. Many foreign dignitaries and international delegations were welcomed here.',
    N'Ngô Viết Thụ',
    1966
),
(
    2,
    N'Xe tăng 843',
    N'Tank 843',
    N'Xe tăng 843 là một trong những xe tăng của Quân Giải phóng tiến vào Dinh Độc Lập ngày 30 tháng 4 năm 1975. Cùng với xe tăng 390, sự kiện này trở thành biểu tượng của ngày giải phóng miền Nam và thống nhất đất nước.',
    N'Tank 843 was one of the Liberation Army tanks that entered Independence Palace on April 30, 1975. Together with Tank 390, the event became a symbol of the liberation of South Vietnam and the reunification of the country.',
    N'People''s Army of Vietnam',
    1975
),
(
    2,
    N'Sân thượng trực thăng',
    N'Helicopter Landing Roof',
    N'Sân thượng trực thăng của Dinh Độc Lập từng được sử dụng cho hoạt động di chuyển khẩn cấp và quân sự trong thời kỳ chiến tranh. Đây cũng là địa điểm gắn liền với hình ảnh trực thăng di tản trong những ngày cuối cùng của chính quyền Sài Gòn năm 1975. Khu vực này phản ánh rõ dấu ấn của chiến tranh Việt Nam và lịch sử hiện đại của TP.HCM.',
    N'The helicopter landing roof of Independence Palace was used for emergency transportation and military operations during the war. It is associated with iconic evacuation helicopter images during the final days of the Saigon government in 1975. The site reflects the historical significance of the Vietnam War and modern Ho Chi Minh City history.',
    N'Ngô Viết Thụ',
    1966
);

/* =====================================================
   WAR REMNANTS MUSEUM
   loc_id = 3
===================================================== */

INSERT INTO Artifacts
(
    loc_id,
    name_vi,
    name_en,
    history_text_vi,
    history_text_en,
    author,
    year
)
VALUES
(
    3,
    N'Máy bay F-5E Tiger',
    N'F-5E Tiger Aircraft',
    N'Máy bay chiến đấu F-5E Tiger được trưng bày tại Bảo tàng Chứng tích Chiến tranh là loại máy bay từng được sử dụng trong chiến tranh Việt Nam. Hiện vật giúp khách tham quan hiểu rõ hơn về công nghệ quân sự và mức độ khốc liệt của chiến tranh trong giai đoạn từ những năm 1960 đến 1975.',
    N'The F-5E Tiger fighter aircraft displayed at the War Remnants Museum was used during the Vietnam War. This artifact helps visitors better understand military technology and the intensity of the conflict between the 1960s and 1975.',
    N'Republic of Vietnam Air Force',
    1970
),
(
    3,
    N'Xe tăng M48 Patton',
    N'M48 Patton Tank',
    N'Xe tăng M48 Patton là phương tiện quân sự hạng nặng từng được sử dụng rộng rãi trong chiến tranh Việt Nam. Hiện vật hiện được trưng bày ngoài trời tại bảo tàng như minh chứng cho quy mô và tính chất ác liệt của chiến tranh hiện đại.',
    N'The M48 Patton tank was a heavy military vehicle widely used during the Vietnam War. It is now displayed outdoors at the museum as evidence of the scale and intensity of modern warfare.',
    N'United States Army',
    1968
),
(
    3,
    N'Chuồng cọp Côn Đảo',
    N'Con Dao Tiger Cages',
    N'Mô hình Chuồng cọp Côn Đảo tái hiện hệ thống nhà giam nổi tiếng từng được sử dụng để giam giữ tù nhân chính trị trong thời chiến. Không gian trưng bày giúp khách tham quan hiểu thêm về điều kiện giam giữ khắc nghiệt và những câu chuyện lịch sử liên quan đến phong trào đấu tranh cách mạng Việt Nam.',
    N'The Con Dao Tiger Cages exhibit recreates the prison system once used to detain political prisoners during wartime. The display allows visitors to understand the harsh detention conditions and the historical stories related to Vietnam’s revolutionary struggle.',
    N'War Remnants Museum',
    1975
),
(
    3,
    N'Bộ sưu tập ảnh chiến tranh',
    N'War Photography Collection',
    N'Bộ sưu tập ảnh chiến tranh tại bảo tàng bao gồm nhiều bức ảnh nổi tiếng do các phóng viên quốc tế và Việt Nam thực hiện trong chiến tranh Việt Nam. Các bức ảnh ghi lại hậu quả chiến tranh đối với con người và xã hội, góp phần truyền tải thông điệp hòa bình đến khách tham quan.',
    N'The museum’s war photography collection includes famous photographs taken by Vietnamese and international journalists during the Vietnam War. These images document the human and social consequences of war while promoting messages of peace to visitors.',
    N'Various Journalists',
    1975
),
(
    3,
    N'Trực thăng UH-1 Huey',
    N'UH-1 Huey Helicopter',
    N'Trực thăng UH-1 Huey là một trong những biểu tượng quân sự nổi bật của chiến tranh Việt Nam. Loại trực thăng này được sử dụng cho vận chuyển quân, cứu thương và tác chiến. Hiện vật tại bảo tàng giúp tái hiện rõ nét vai trò của không quân trong chiến tranh hiện đại.',
    N'The UH-1 Huey helicopter is one of the most recognizable military symbols of the Vietnam War. It was used for troop transport, medical evacuation, and combat missions. The artifact at the museum illustrates the important role of air power in modern warfare.',
    N'Bell Helicopter Company',
    1967
);


/* =====================================================
   INSERT DATA - PRE COMPUTED AUDIO
===================================================== */

INSERT INTO Pre_computed_Audio
(
    artifact_id,
    question_vi,
    question_en,
    answer_vi,
    answer_en,
    audio_vi,
    audio_en
)
VALUES

/* =====================================================
   HUE IMPERIAL CITY
===================================================== */

(
    1,
    N'Ngọ Môn được xây dựng khi nào?',
    N'When was Ngo Mon Gate built?',

    N'Ngọ Môn được xây dựng vào năm 1833 dưới triều vua Minh Mạng.',
    N'Ngo Mon Gate was built in 1833 during Emperor Minh Mang’s reign.',

    N'audio/ngo_mon_vi.mp3',
    N'audio/ngo_mon_en.mp3'
),

(
    2,
    N'Điện Thái Hòa được sử dụng để làm gì?',
    N'What was Thai Hoa Palace used for?',

    N'Điện Thái Hòa là nơi diễn ra các buổi thiết triều và nghi lễ quan trọng của triều Nguyễn.',
    N'Thai Hoa Palace was used for royal court meetings and important imperial ceremonies.',

    N'audio/thai_hoa_vi.mp3',
    N'audio/thai_hoa_en.mp3'
),

(
    3,
    N'Tử Cấm Thành có ý nghĩa gì?',
    N'What was the purpose of the Forbidden Purple City?',

    N'Tử Cấm Thành là nơi sinh hoạt riêng của vua và hoàng gia triều Nguyễn.',
    N'The Forbidden Purple City was the private residence of the Nguyen royal family.',

    N'audio/forbidden_city_vi.mp3',
    N'audio/forbidden_city_en.mp3'
),

(
    4,
    N'Cửu Đỉnh được đúc dưới triều vua nào?',
    N'Under which emperor were the Nine Dynastic Urns cast?',

    N'Cửu Đỉnh được đúc dưới thời vua Minh Mạng vào năm 1835.',
    N'The Nine Dynastic Urns were cast during Emperor Minh Mang’s reign in 1835.',

    N'audio/cuu_dinh_vi.mp3',
    N'audio/cuu_dinh_en.mp3'
),

(
    5,
    N'Thế Miếu dùng để làm gì?',
    N'What was The Mieu Temple used for?',

    N'Thế Miếu là nơi thờ các vị hoàng đế triều Nguyễn.',
    N'The Mieu Temple was dedicated to Nguyen Dynasty emperors.',

    N'audio/the_mieu_vi.mp3',
    N'audio/the_mieu_en.mp3'
),

/* =====================================================
   INDEPENDENCE PALACE
===================================================== */

(
    6,
    N'Phòng Nội các có chức năng gì?',
    N'What was the Cabinet Room used for?',

    N'Phòng Nội các là nơi tổ chức các cuộc họp quan trọng của chính quyền Việt Nam Cộng hòa.',
    N'The Cabinet Room was used for important meetings of the Republic of Vietnam government.',

    N'audio/cabinet_room_vi.mp3',
    N'audio/cabinet_room_en.mp3'
),

(
    7,
    N'Hầm chỉ huy được xây dựng nhằm mục đích gì?',
    N'Why was the Command Bunker built?',

    N'Hầm chỉ huy được xây dựng để phục vụ liên lạc và điều hành quân sự trong thời chiến.',
    N'The Command Bunker was built for wartime communication and military operations.',

    N'audio/bunker_vi.mp3',
    N'audio/bunker_en.mp3'
),

(
    8,
    N'Phòng Khánh tiết được sử dụng như thế nào?',
    N'How was the State Banquet Hall used?',

    N'Phòng Khánh tiết được dùng để tổ chức quốc yến và tiếp đón khách quốc tế.',
    N'The State Banquet Hall was used for diplomatic receptions and official banquets.',

    N'audio/banquet_hall_vi.mp3',
    N'audio/banquet_hall_en.mp3'
),

(
    9,
    N'Xe tăng 843 có ý nghĩa lịch sử gì?',
    N'What is the historical significance of Tank 843?',

    N'Xe tăng 843 là biểu tượng của ngày giải phóng miền Nam 30 tháng 4 năm 1975.',
    N'Tank 843 became a symbol of the liberation of South Vietnam on April 30, 1975.',

    N'audio/tank_843_vi.mp3',
    N'audio/tank_843_en.mp3'
),

(
    10,
    N'Sân thượng trực thăng được dùng để làm gì?',
    N'What was the helicopter landing roof used for?',

    N'Sân thượng trực thăng được sử dụng cho hoạt động di chuyển khẩn cấp trong thời chiến.',
    N'The helicopter landing roof was used for emergency transportation during wartime.',

    N'audio/helipad_vi.mp3',
    N'audio/helipad_en.mp3'
),

/* =====================================================
   WAR REMNANTS MUSEUM
===================================================== */

(
    11,
    N'Máy bay F-5E Tiger được sử dụng trong giai đoạn nào?',
    N'During which period was the F-5E Tiger aircraft used?',

    N'Máy bay F-5E Tiger được sử dụng trong chiến tranh Việt Nam trước năm 1975.',
    N'The F-5E Tiger aircraft was used during the Vietnam War before 1975.',

    N'audio/f5e_vi.mp3',
    N'audio/f5e_en.mp3'
),

(
    12,
    N'Xe tăng M48 Patton là loại phương tiện gì?',
    N'What type of vehicle was the M48 Patton?',

    N'Xe tăng M48 Patton là xe tăng chiến đấu hạng nặng được sử dụng trong chiến tranh Việt Nam.',
    N'The M48 Patton was a heavy combat tank used during the Vietnam War.',

    N'audio/m48_vi.mp3',
    N'audio/m48_en.mp3'
),

(
    13,
    N'Chuồng cọp Côn Đảo tái hiện điều gì?',
    N'What does the Con Dao Tiger Cages exhibit represent?',

    N'Chuồng cọp Côn Đảo tái hiện hệ thống giam giữ tù nhân chính trị trong thời chiến.',
    N'The Con Dao Tiger Cages exhibit recreates wartime political prison conditions.',

    N'audio/tiger_cages_vi.mp3',
    N'audio/tiger_cages_en.mp3'
),

(
    14,
    N'Bộ sưu tập ảnh chiến tranh mang ý nghĩa gì?',
    N'What is the significance of the war photography collection?',

    N'Bộ sưu tập ảnh chiến tranh ghi lại hậu quả chiến tranh và truyền tải thông điệp hòa bình.',
    N'The war photography collection documents the consequences of war and promotes peace.',

    N'audio/photo_collection_vi.mp3',
    N'audio/photo_collection_en.mp3'
),

(
    15,
    N'Trực thăng UH-1 Huey được sử dụng để làm gì?',
    N'What was the UH-1 Huey helicopter used for?',

    N'Trực thăng UH-1 Huey được sử dụng để vận chuyển quân và cứu thương trong chiến tranh.',
    N'The UH-1 Huey helicopter was used for troop transport and medical evacuation.',

    N'audio/huey_vi.mp3',
    N'audio/huey_en.mp3'
);



/* =====================================================
   INSERT DATA - BILINGUAL CONTENT
===================================================== */

INSERT INTO Bilingual_Content
(
    artifact_id,
    lang,
    content_type,
    content_text
)
VALUES

/* =====================================================
   HUE IMPERIAL CITY
===================================================== */

(
    1,
    'vi',
    'faq',
    N'Ngọ Môn được xây dựng vào năm 1833 dưới triều vua Minh Mạng.'
),

(
    1,
    'en',
    'faq',
    N'Ngo Mon Gate was built in 1833 during Emperor Minh Mang’s reign.'
),

(
    2,
    'vi',
    'faq',
    N'Điện Thái Hòa là nơi tổ chức các nghi lễ và buổi thiết triều của vua Nguyễn.'
),

(
    2,
    'en',
    'faq',
    N'Thai Hoa Palace was used for imperial ceremonies and royal court meetings.'
),

(
    3,
    'vi',
    'faq',
    N'Tử Cấm Thành là khu vực sinh hoạt riêng của hoàng gia Nguyễn.'
),

(
    3,
    'en',
    'faq',
    N'The Forbidden Purple City was the private residence of the Nguyen royal family.'
),

(
    4,
    'vi',
    'faq',
    N'Cửu Đỉnh là biểu tượng cho sự trường tồn của triều Nguyễn.'
),

(
    4,
    'en',
    'faq',
    N'The Nine Dynastic Urns symbolize the longevity of the Nguyen Dynasty.'
),

(
    5,
    'vi',
    'faq',
    N'Thế Miếu là nơi thờ các vị hoàng đế triều Nguyễn.'
),

(
    5,
    'en',
    'faq',
    N'The Mieu Temple is dedicated to Nguyen Dynasty emperors.'
),

/* =====================================================
   INDEPENDENCE PALACE
===================================================== */

(
    6,
    'vi',
    'faq',
    N'Phòng Nội các là nơi họp của chính quyền Việt Nam Cộng hòa.'
),

(
    6,
    'en',
    'faq',
    N'The Cabinet Room was used for government meetings of the Republic of Vietnam.'
),

(
    7,
    'vi',
    'faq',
    N'Hầm chỉ huy phục vụ liên lạc và điều hành quân sự trong thời chiến.'
),

(
    7,
    'en',
    'faq',
    N'The Command Bunker supported wartime communication and military operations.'
),

(
    8,
    'vi',
    'faq',
    N'Phòng Khánh tiết được dùng để tổ chức quốc yến và tiếp khách quốc tế.'
),

(
    8,
    'en',
    'faq',
    N'The State Banquet Hall was used for diplomatic receptions and state banquets.'
),

(
    9,
    'vi',
    'faq',
    N'Xe tăng 843 gắn liền với sự kiện giải phóng miền Nam năm 1975.'
),

(
    9,
    'en',
    'faq',
    N'Tank 843 is associated with the liberation of South Vietnam in 1975.'
),

(
    10,
    'vi',
    'faq',
    N'Sân thượng trực thăng được sử dụng cho các hoạt động khẩn cấp thời chiến.'
),

(
    10,
    'en',
    'faq',
    N'The helicopter landing roof was used for emergency wartime operations.'
),

/* =====================================================
   WAR REMNANTS MUSEUM
===================================================== */

(
    11,
    'vi',
    'faq',
    N'Máy bay F-5E Tiger từng được sử dụng trong chiến tranh Việt Nam.'
),

(
    11,
    'en',
    'faq',
    N'The F-5E Tiger aircraft was used during the Vietnam War.'
),

(
    12,
    'vi',
    'faq',
    N'Xe tăng M48 Patton là phương tiện quân sự hạng nặng.'
),

(
    12,
    'en',
    'faq',
    N'The M48 Patton was a heavy military combat tank.'
),

(
    13,
    'vi',
    'faq',
    N'Chuồng cọp Côn Đảo tái hiện hệ thống giam giữ tù nhân chính trị.'
),

(
    13,
    'en',
    'faq',
    N'The Con Dao Tiger Cages exhibit recreates political prison conditions.'
),

(
    14,
    'vi',
    'faq',
    N'Bộ sưu tập ảnh chiến tranh truyền tải thông điệp hòa bình.'
),

(
    14,
    'en',
    'faq',
    N'The war photography collection promotes messages of peace.'
),

(
    15,
    'vi',
    'faq',
    N'Trực thăng UH-1 Huey được dùng cho vận chuyển quân và cứu thương.'
),

(
    15,
    'en',
    'faq',
    N'The UH-1 Huey helicopter was used for troop transport and medical evacuation.'
);


/* =====================================================
   UNIT TEST 2
   QUERY PERFORMANCE TEST
   TARGET: SELECT QUERY < 50ms
===================================================== */

-- Unit Test 2: 
-- Result checked using SET STATISTICS TIME ON
-- Query execution time satisfied requirement (< 50ms)

SET STATISTICS TIME ON;

SELECT *
FROM Artifacts
WHERE loc_id = 1;

SELECT *
FROM Artifacts
WHERE name_vi = N'Ngọ Môn';

SET STATISTICS TIME OFF;



/* =====================================================
   SAMPLE JOIN QUERY
===================================================== */

SELECT
    A.name_vi,
    A.name_en,
    L.name_vi AS location_name,
    L.open_hours
FROM Artifacts A
JOIN Locations L
ON A.loc_id = L.loc_id;



/* =====================================================
   SAMPLE FAQ CACHE QUERY
===================================================== */

SELECT
    question_vi,
    answer_vi,
    audio_vi
FROM Pre_computed_Audio
WHERE artifact_id = 8;