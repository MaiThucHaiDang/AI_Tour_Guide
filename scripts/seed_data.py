"""Seed PostgreSQL database with data from the original SQL Server schema.

Run: python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import engine, Base, async_session_factory
from models.location import Location
from models.artifact import Artifact
from models.precomputed_audio import PrecomputedAudio
from models.bilingual_content import BilingualContent

LOCATIONS = [
    {
        "name_vi": "Kinh thành Huế",
        "name_en": "Hue Imperial City",
        "gps_coordinates": "16.4637,107.5909",
        "open_hours": "07:00 - 17:30"
    },
    {
        "name_vi": "Dinh Độc Lập",
        "name_en": "Independence Palace",
        "gps_coordinates": "10.7769,106.6953",
        "open_hours": "08:00 - 16:30"
    },
    {
        "name_vi": "Bảo tàng Chứng tích Chiến tranh",
        "name_en": "War Remnants Museum",
        "gps_coordinates": "10.7795,106.6920",
        "open_hours": "07:30 - 17:30"
    }
]

ARTIFACTS = [
    {
        "loc_id": 1,
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate (Noon Gate)",
        "history_text_vi": "Ngọ Môn là cổng chính phía nam của Hoàng thành Huế, được xây dựng dưới triều vua Minh Mạng vào năm 1833. Đây là công trình kiến trúc tiêu biểu của triều Nguyễn với thiết kế uy nghiêm dành riêng cho vua và các nghi lễ quan trọng của triều đình. Phía trên cổng là Lầu Ngũ Phụng, nơi diễn ra nhiều nghi lễ lớn như lễ ban sóc và duyệt binh. Ngọ Môn từng chứng kiến sự kiện vua Bảo Đại thoái vị năm 1945, đánh dấu sự kết thúc của chế độ phong kiến Việt Nam.",
        "history_text_en": "Ngo Mon Gate is the main southern entrance of the Hue Imperial City, constructed during Emperor Minh Mang’s reign in 1833. The structure represents the grand architecture of the Nguyen Dynasty and was reserved for emperors and important royal ceremonies. Above the gate stands the Five Phoenix Pavilion, where major imperial events such as military inspections and royal proclamations were held. Ngo Mon also witnessed Emperor Bao Dai’s abdication in 1945, marking the end of the Vietnamese feudal monarchy.",
        "author": "Nguyen Dynasty",
        "year": 1833
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace",
        "history_text_vi": "Điện Thái Hòa là nơi thiết triều quan trọng nhất của triều Nguyễn, được xây dựng vào năm 1805 dưới thời vua Gia Long và được di dời, mở rộng dưới thời Minh Mạng. Công trình là biểu tượng quyền lực của hoàng đế với kiến trúc gỗ truyền thống cùng hệ thống cột sơn son thếp vàng tinh xảo. Đây là nơi tổ chức các buổi lễ đăng quang, tiếp đón sứ thần và những nghi thức trọng đại của triều đình Huế.",
        "history_text_en": "Thai Hoa Palace served as the most important ceremonial hall of the Nguyen Dynasty. Originally built in 1805 under Emperor Gia Long and later expanded during Minh Mang’s reign, the palace symbolized imperial authority through its traditional wooden architecture and gilded columns. Major royal ceremonies, coronations, diplomatic receptions, and court rituals were conducted here.",
        "author": "Gia Long Emperor",
        "year": 1805
    },
    {
        "loc_id": 1,
        "name_vi": "Tử Cấm Thành",
        "name_en": "Forbidden Purple City",
        "history_text_vi": "Tử Cấm Thành là khu vực sinh hoạt riêng của hoàng gia Nguyễn nằm bên trong Hoàng thành Huế. Công trình được xây dựng vào đầu thế kỷ XIX và chỉ dành cho vua, hoàng hậu cùng các thành viên hoàng tộc. Khu vực này từng bao gồm nhiều cung điện, thư viện và vườn thượng uyển. Dù bị hư hại nặng trong chiến tranh, Tử Cấm Thành vẫn là biểu tượng quan trọng phản ánh đời sống cung đình Việt Nam thời phong kiến.",
        "history_text_en": "The Forbidden Purple City was the private residential area of the Nguyen royal family inside the Hue Imperial City. Built in the early nineteenth century, it was reserved exclusively for the emperor, queen, and royal relatives. The complex once contained numerous palaces, libraries, and royal gardens. Although heavily damaged during wars, it remains an important symbol of Vietnamese imperial life.",
        "author": "Nguyen Dynasty",
        "year": 1821
    },
    {
        "loc_id": 1,
        "name_vi": "Cửu Đỉnh",
        "name_en": "The Nine Dynastic Urns",
        "history_text_vi": "Cửu Đỉnh là bộ chín đỉnh đồng lớn được đúc dưới thời vua Minh Mạng vào năm 1835 và đặt trước Thế Miếu trong Hoàng thành Huế. Mỗi đỉnh tượng trưng cho một vị vua Nguyễn và được chạm khắc nhiều hình ảnh về núi sông, động vật và văn hóa Việt Nam. Đây là kiệt tác nghệ thuật đúc đồng của triều Nguyễn và mang ý nghĩa về sự trường tồn của vương triều.",
        "history_text_en": "The Nine Dynastic Urns are a set of massive bronze urns cast during Emperor Minh Mang’s reign in 1835 and placed in front of The Mieu Temple. Each urn represents a Nguyen emperor and is decorated with detailed carvings depicting landscapes, animals, and symbols of Vietnamese culture. The urns are considered masterpieces of bronze casting and symbolize the longevity of the dynasty.",
        "author": "Minh Mang Emperor",
        "year": 1835
    },
    {
        "loc_id": 1,
        "name_vi": "Thế Miếu",
        "name_en": "The Mieu Temple",
        "history_text_vi": "Thế Miếu là ngôi miếu thờ các vị hoàng đế triều Nguyễn, được xây dựng năm 1821 dưới thời vua Minh Mạng. Đây là nơi tổ chức các nghi lễ cúng tế hoàng gia và lưu giữ bài vị của các vị vua Nguyễn. Công trình nổi bật với kiến trúc gỗ truyền thống, mái ngói lưu ly và không gian trang nghiêm phản ánh tín ngưỡng thờ cúng tổ tiên của triều đình Huế.",
        "history_text_en": "The Mieu Temple is a royal ancestral temple dedicated to the emperors of the Nguyen Dynasty. Built in 1821 during Emperor Minh Mang’s reign, it served as the site for imperial worship ceremonies and houses memorial tablets of Nguyen emperors. The temple is notable for its traditional wooden architecture, glazed tile roofs, and solemn atmosphere representing royal ancestor worship.",
        "author": "Minh Mang Emperor",
        "year": 1821
    },
    {
        "loc_id": 2,
        "name_vi": "Phòng Nội các",
        "name_en": "Cabinet Room",
        "history_text_vi": "Phòng Nội các tại Dinh Độc Lập là nơi diễn ra các cuộc họp quan trọng của chính quyền Việt Nam Cộng hòa trước năm 1975. Căn phòng được thiết kế hiện đại với bàn họp lớn, hệ thống âm thanh và thiết bị phục vụ điều hành quốc gia. Đây là nơi nhiều quyết định chính trị và quân sự quan trọng đã được đưa ra trong giai đoạn chiến tranh Việt Nam.",
        "history_text_en": "The Cabinet Room inside Independence Palace was used for important meetings of the Republic of Vietnam government before 1975. The room featured a modern design with a large conference table, audio systems, and equipment for national administration. Many significant political and military decisions during the Vietnam War were made here.",
        "author": "Ngô Viết Thụ",
        "year": 1966
    },
    {
        "loc_id": 2,
        "name_vi": "Hầm chỉ huy",
        "name_en": "Command Bunker",
        "history_text_vi": "Hầm chỉ huy nằm dưới tầng hầm của Dinh Độc Lập, được xây dựng với kết cấu kiên cố nhằm phục vụ hoạt động quân sự và liên lạc trong thời chiến. Bên trong vẫn còn nhiều thiết bị liên lạc, bản đồ tác chiến và máy móc nguyên bản từ trước năm 1975. Đây là nơi phản ánh rõ nét bối cảnh chiến tranh và hoạt động điều hành của chính quyền miền Nam Việt Nam.",
        "history_text_en": "The Command Bunker beneath Independence Palace was built with reinforced structures for wartime military operations and communications. The bunker still preserves original communication devices, military maps, and operational equipment from before 1975. It provides valuable insight into wartime administration and military coordination in South Vietnam.",
        "author": "Ngô Viết Thụ",
        "year": 1966
    },
    {
        "loc_id": 2,
        "name_vi": "Phòng Khánh tiết",
        "name_en": "State Banquet Hall",
        "history_text_vi": "Phòng Khánh tiết là nơi tổ chức các buổi tiếp đón ngoại giao, quốc yến và sự kiện chính thức của chính quyền Việt Nam Cộng hòa. Không gian rộng lớn với sức chứa hàng trăm khách mời được thiết kế theo phong cách hiện đại kết hợp yếu tố truyền thống Việt Nam. Đây từng là nơi đón tiếp nhiều nguyên thủ và đoàn ngoại giao quốc tế.",
        "history_text_en": "The State Banquet Hall was used for diplomatic receptions, official ceremonies, and state banquets of the Republic of Vietnam government. The spacious hall, capable of hosting hundreds of guests, combines modern architecture with Vietnamese traditional elements. Many foreign dignitaries and international delegations were welcomed here.",
        "author": "Ngô Viết Thụ",
        "year": 1966
    },
    {
        "loc_id": 2,
        "name_vi": "Xe tăng 843",
        "name_en": "Tank 843",
        "history_text_vi": "Xe tăng 843 là một trong những xe tăng của Quân Giải phóng tiến vào Dinh Độc Lập ngày 30 tháng 4 năm 1975. Cùng với xe tăng 390, sự kiện này trở thành biểu tượng của ngày giải phóng miền Nam và thống nhất đất nước.",
        "history_text_en": "Tank 843 was one of the Liberation Army tanks that entered Independence Palace on April 30, 1975. Together with Tank 390, the event became a symbol of the liberation of South Vietnam and the reunification of the country.",
        "author": "People's Army of Vietnam",
        "year": 1975
    },
    {
        "loc_id": 2,
        "name_vi": "Sân thượng trực thăng",
        "name_en": "Helicopter Landing Roof",
        "history_text_vi": "Sân thượng trực thăng của Dinh Độc Lập từng được sử dụng cho hoạt động di chuyển khẩn cấp và quân sự trong thời kỳ chiến tranh. Đây cũng là địa điểm gắn liền với hình ảnh trực thăng di tản trong những ngày cuối cùng của chính quyền Sài Gòn năm 1975. Khu vực này phản ánh rõ dấu ấn của chiến tranh Việt Nam và lịch sử hiện đại của TP.HCM.",
        "history_text_en": "The helicopter landing roof of Independence Palace was used for emergency transportation and military operations during the war. It is associated with iconic evacuation helicopter images during the final days of the Saigon government in 1975. The site reflects the historical significance of the Vietnam War and modern Ho Chi Minh City history.",
        "author": "Ngô Viết Thụ",
        "year": 1966
    },
    {
        "loc_id": 3,
        "name_vi": "Máy bay F-5E Tiger",
        "name_en": "F-5E Tiger Aircraft",
        "history_text_vi": "Máy bay chiến đấu F-5E Tiger được trưng bày tại Bảo tàng Chứng tích Chiến tranh là loại máy bay từng được sử dụng trong chiến tranh Việt Nam. Hiện vật giúp khách tham quan hiểu rõ hơn về công nghệ quân sự và mức độ khốc liệt của chiến tranh trong giai đoạn từ những năm 1960 đến 1975.",
        "history_text_en": "The F-5E Tiger fighter aircraft displayed at the War Remnants Museum was used during the Vietnam War. This artifact helps visitors better understand military technology and the intensity of the conflict between the 1960s and 1975.",
        "author": "Republic of Vietnam Air Force",
        "year": 1970
    },
    {
        "loc_id": 3,
        "name_vi": "Xe tăng M48 Patton",
        "name_en": "M48 Patton Tank",
        "history_text_vi": "Xe tăng M48 Patton là phương tiện quân sự hạng nặng từng được sử dụng rộng rãi trong chiến tranh Việt Nam. Hiện vật hiện được trưng bày ngoài trời tại bảo tàng như minh chứng cho quy mô và tính chất ác liệt của chiến tranh hiện đại.",
        "history_text_en": "The M48 Patton tank was a heavy military vehicle widely used during the Vietnam War. It is now displayed outdoors at the museum as evidence of the scale and intensity of modern warfare.",
        "author": "United States Army",
        "year": 1968
    },
    {
        "loc_id": 3,
        "name_vi": "Chuồng cọp Côn Đảo",
        "name_en": "Con Dao Tiger Cages",
        "history_text_vi": "Mô hình Chuồng cọp Côn Đảo tái hiện hệ thống nhà giam nổi tiếng từng được sử dụng để giam giữ tù nhân chính trị trong thời chiến. Không gian trưng bày giúp khách tham quan hiểu thêm về điều kiện giam giữ khắc nghiệt và những câu chuyện lịch sử liên quan đến phong trào đấu tranh cách mạng Việt Nam.",
        "history_text_en": "The Con Dao Tiger Cages exhibit recreates the prison system once used to detain political prisoners during wartime. The display allows visitors to understand the harsh detention conditions and the historical stories related to Vietnam’s revolutionary struggle.",
        "author": "War Remnants Museum",
        "year": 1975
    },
    {
        "loc_id": 3,
        "name_vi": "Bộ sưu tập ảnh chiến tranh",
        "name_en": "War Photography Collection",
        "history_text_vi": "Bộ sưu tập ảnh chiến tranh tại bảo tàng bao gồm nhiều bức ảnh nổi tiếng do các phóng viên quốc tế và Việt Nam thực hiện trong chiến tranh Việt Nam. Các bức ảnh ghi lại hậu quả chiến tranh đối với con người và xã hội, góp phần truyền tải thông điệp hòa bình đến khách tham quan.",
        "history_text_en": "The museum’s war photography collection includes famous photographs taken by Vietnamese and international journalists during the Vietnam War. These images document the human and social consequences of war while promoting messages of peace to visitors.",
        "author": "Various Journalists",
        "year": 1975
    },
    {
        "loc_id": 3,
        "name_vi": "Trực thăng UH-1 Huey",
        "name_en": "UH-1 Huey Helicopter",
        "history_text_vi": "Trực thăng UH-1 Huey là một trong những biểu tượng quân sự nổi bật của chiến tranh Việt Nam. Loại trực thăng này được sử dụng cho vận chuyển quân, cứu thương và tác chiến. Hiện vật tại bảo tàng giúp tái hiện rõ nét vai trò của không quân trong chiến tranh hiện đại.",
        "history_text_en": "The UH-1 Huey helicopter is one of the most recognizable military symbols of the Vietnam War. It was used for troop transport, medical evacuation, and combat missions. The artifact at the museum illustrates the important role of air power in modern warfare.",
        "author": "Bell Helicopter Company",
        "year": 1967
    }
]

PRECOMPUTED_AUDIO = [
    {
        "artifact_id": 1,
        "question_vi": "Ngọ Môn được xây dựng khi nào?",
        "question_en": "When was Ngo Mon Gate built?",
        "answer_vi": "Ngọ Môn được xây dựng vào năm 1833 dưới triều vua Minh Mạng.",
        "answer_en": "Ngo Mon Gate was built in 1833 during Emperor Minh Mang’s reign.",
        "audio_vi": "audio/ngo_mon_vi.mp3",
        "audio_en": "audio/ngo_mon_en.mp3"
    },
    {
        "artifact_id": 2,
        "question_vi": "Điện Thái Hòa được sử dụng để làm gì?",
        "question_en": "What was Thai Hoa Palace used for?",
        "answer_vi": "Điện Thái Hòa là nơi diễn ra các buổi thiết triều và nghi lễ quan trọng của triều Nguyễn.",
        "answer_en": "Thai Hoa Palace was used for royal court meetings and important imperial ceremonies.",
        "audio_vi": "audio/thai_hoa_vi.mp3",
        "audio_en": "audio/thai_hoa_en.mp3"
    },
    {
        "artifact_id": 3,
        "question_vi": "Tử Cấm Thành có ý nghĩa gì?",
        "question_en": "What was the purpose of the Forbidden Purple City?",
        "answer_vi": "Tử Cấm Thành là nơi sinh hoạt riêng của vua và hoàng gia triều Nguyễn.",
        "answer_en": "The Forbidden Purple City was the private residence of the Nguyen royal family.",
        "audio_vi": "audio/forbidden_city_vi.mp3",
        "audio_en": "audio/forbidden_city_en.mp3"
    },
    {
        "artifact_id": 4,
        "question_vi": "Cửu Đỉnh được đúc dưới triều vua nào?",
        "question_en": "Under which emperor were the Nine Dynastic Urns cast?",
        "answer_vi": "Cửu Đỉnh được đúc dưới thời vua Minh Mạng vào năm 1835.",
        "answer_en": "The Nine Dynastic Urns were cast during Emperor Minh Mang’s reign in 1835.",
        "audio_vi": "audio/cuu_dinh_vi.mp3",
        "audio_en": "audio/cuu_dinh_en.mp3"
    },
    {
        "artifact_id": 5,
        "question_vi": "Thế Miếu dùng để làm gì?",
        "question_en": "What was The Mieu Temple used for?",
        "answer_vi": "Thế Miếu là nơi thờ các vị hoàng đế triều Nguyễn.",
        "answer_en": "The Mieu Temple was dedicated to Nguyen Dynasty emperors.",
        "audio_vi": "audio/the_mieu_vi.mp3",
        "audio_en": "audio/the_mieu_en.mp3"
    },
    {
        "artifact_id": 6,
        "question_vi": "Phòng Nội các có chức năng gì?",
        "question_en": "What was the Cabinet Room used for?",
        "answer_vi": "Phòng Nội các là nơi tổ chức các cuộc họp quan trọng của chính quyền Việt Nam Cộng hòa.",
        "answer_en": "The Cabinet Room was used for important meetings of the Republic of Vietnam government.",
        "audio_vi": "audio/cabinet_room_vi.mp3",
        "audio_en": "audio/cabinet_room_en.mp3"
    },
    {
        "artifact_id": 7,
        "question_vi": "Hầm chỉ huy được xây dựng nhằm mục đích gì?",
        "question_en": "Why was the Command Bunker built?",
        "answer_vi": "Hầm chỉ huy được xây dựng để phục vụ liên lạc và điều hành quân sự trong thời chiến.",
        "answer_en": "The Command Bunker was built for wartime communication and military operations.",
        "audio_vi": "audio/bunker_vi.mp3",
        "audio_en": "audio/bunker_en.mp3"
    },
    {
        "artifact_id": 8,
        "question_vi": "Phòng Khánh tiết được sử dụng như thế nào?",
        "question_en": "How was the State Banquet Hall used?",
        "answer_vi": "Phòng Khánh tiết được dùng để tổ chức quốc yến và tiếp đón khách quốc tế.",
        "answer_en": "The State Banquet Hall was used for diplomatic receptions and official banquets.",
        "audio_vi": "audio/banquet_hall_vi.mp3",
        "audio_en": "audio/banquet_hall_en.mp3"
    },
    {
        "artifact_id": 9,
        "question_vi": "Xe tăng 843 có ý nghĩa lịch sử gì?",
        "question_en": "What is the historical significance of Tank 843?",
        "answer_vi": "Xe tăng 843 là biểu tượng của ngày giải phóng miền Nam 30 tháng 4 năm 1975.",
        "answer_en": "Tank 843 became a symbol of the liberation of South Vietnam on April 30, 1975.",
        "audio_vi": "audio/tank_843_vi.mp3",
        "audio_en": "audio/tank_843_en.mp3"
    },
    {
        "artifact_id": 10,
        "question_vi": "Sân thượng trực thăng được dùng để làm gì?",
        "question_en": "What was the helicopter landing roof used for?",
        "answer_vi": "Sân thượng trực thăng được sử dụng cho hoạt động di chuyển khẩn cấp trong thời chiến.",
        "answer_en": "The helicopter landing roof was used for emergency transportation during wartime.",
        "audio_vi": "audio/helipad_vi.mp3",
        "audio_en": "audio/helipad_en.mp3"
    },
    {
        "artifact_id": 11,
        "question_vi": "Máy bay F-5E Tiger được sử dụng trong giai đoạn nào?",
        "question_en": "During which period was the F-5E Tiger aircraft used?",
        "answer_vi": "Máy bay F-5E Tiger được sử dụng trong chiến tranh Việt Nam trước năm 1975.",
        "answer_en": "The F-5E Tiger aircraft was used during the Vietnam War before 1975.",
        "audio_vi": "audio/f5e_vi.mp3",
        "audio_en": "audio/f5e_en.mp3"
    },
    {
        "artifact_id": 12,
        "question_vi": "Xe tăng M48 Patton là loại phương tiện gì?",
        "question_en": "What type of vehicle was the M48 Patton?",
        "answer_vi": "Xe tăng M48 Patton là xe tăng chiến đấu hạng nặng được sử dụng trong chiến tranh Việt Nam.",
        "answer_en": "The M48 Patton was a heavy combat tank used during the Vietnam War.",
        "audio_vi": "audio/m48_vi.mp3",
        "audio_en": "audio/m48_en.mp3"
    },
    {
        "artifact_id": 13,
        "question_vi": "Chuồng cọp Côn Đảo tái hiện điều gì?",
        "question_en": "What does the Con Dao Tiger Cages exhibit represent?",
        "answer_vi": "Chuồng cọp Côn Đảo tái hiện hệ thống giam giữ tù nhân chính trị trong thời chiến.",
        "answer_en": "The Con Dao Tiger Cages exhibit recreates wartime political prison conditions.",
        "audio_vi": "audio/tiger_cages_vi.mp3",
        "audio_en": "audio/tiger_cages_en.mp3"
    },
    {
        "artifact_id": 14,
        "question_vi": "Bộ sưu tập ảnh chiến tranh mang ý nghĩa gì?",
        "question_en": "What is the significance of the war photography collection?",
        "answer_vi": "Bộ sưu tập ảnh chiến tranh ghi lại hậu quả chiến tranh và truyền tải thông điệp hòa bình.",
        "answer_en": "The war photography collection documents the consequences of war and promotes peace.",
        "audio_vi": "audio/photo_collection_vi.mp3",
        "audio_en": "audio/photo_collection_en.mp3"
    },
    {
        "artifact_id": 15,
        "question_vi": "Trực thăng UH-1 Huey được sử dụng để làm gì?",
        "question_en": "What was the UH-1 Huey helicopter used for?",
        "answer_vi": "Trực thăng UH-1 Huey được sử dụng để vận chuyển quân và cứu thương trong chiến tranh.",
        "answer_en": "The UH-1 Huey helicopter was used for troop transport and medical evacuation.",
        "audio_vi": "audio/huey_vi.mp3",
        "audio_en": "audio/huey_en.mp3"
    }
]

BILINGUAL_CONTENT = [
    {
        "artifact_id": 1,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Ngọ Môn được xây dựng vào năm 1833 dưới triều vua Minh Mạng."
    },
    {
        "artifact_id": 1,
        "lang": "en",
        "content_type": "faq",
        "content_text": "Ngo Mon Gate was built in 1833 during Emperor Minh Mang’s reign."
    },
    {
        "artifact_id": 2,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Điện Thái Hòa là nơi tổ chức các nghi lễ và buổi thiết triều của vua Nguyễn."
    },
    {
        "artifact_id": 2,
        "lang": "en",
        "content_type": "faq",
        "content_text": "Thai Hoa Palace was used for imperial ceremonies and royal court meetings."
    },
    {
        "artifact_id": 3,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Tử Cấm Thành là khu vực sinh hoạt riêng của hoàng gia Nguyễn."
    },
    {
        "artifact_id": 3,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Forbidden Purple City was the private residence of the Nguyen royal family."
    },
    {
        "artifact_id": 4,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Cửu Đỉnh là biểu tượng cho sự trường tồn của triều Nguyễn."
    },
    {
        "artifact_id": 4,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Nine Dynastic Urns symbolize the longevity of the Nguyen Dynasty."
    },
    {
        "artifact_id": 5,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Thế Miếu là nơi thờ các vị hoàng đế triều Nguyễn."
    },
    {
        "artifact_id": 5,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Mieu Temple is dedicated to Nguyen Dynasty emperors."
    },
    {
        "artifact_id": 6,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Phòng Nội các là nơi họp của chính quyền Việt Nam Cộng hòa."
    },
    {
        "artifact_id": 6,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Cabinet Room was used for government meetings of the Republic of Vietnam."
    },
    {
        "artifact_id": 7,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Hầm chỉ huy phục vụ liên lạc và điều hành quân sự trong thời chiến."
    },
    {
        "artifact_id": 7,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Command Bunker supported wartime communication and military operations."
    },
    {
        "artifact_id": 8,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Phòng Khánh tiết được dùng để tổ chức quốc yến và tiếp khách quốc tế."
    },
    {
        "artifact_id": 8,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The State Banquet Hall was used for diplomatic receptions and state banquets."
    },
    {
        "artifact_id": 9,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Xe tăng 843 gắn liền với sự kiện giải phóng miền Nam năm 1975."
    },
    {
        "artifact_id": 9,
        "lang": "en",
        "content_type": "faq",
        "content_text": "Tank 843 is associated with the liberation of South Vietnam in 1975."
    },
    {
        "artifact_id": 10,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Sân thượng trực thăng được sử dụng cho các hoạt động khẩn cấp thời chiến."
    },
    {
        "artifact_id": 10,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The helicopter landing roof was used for emergency wartime operations."
    },
    {
        "artifact_id": 11,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Máy bay F-5E Tiger từng được sử dụng trong chiến tranh Việt Nam."
    },
    {
        "artifact_id": 11,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The F-5E Tiger aircraft was used during the Vietnam War."
    },
    {
        "artifact_id": 12,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Xe tăng M48 Patton là phương tiện quân sự hạng nặng."
    },
    {
        "artifact_id": 12,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The M48 Patton was a heavy military combat tank."
    },
    {
        "artifact_id": 13,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Chuồng cọp Côn Đảo tái hiện hệ thống giam giữ tù nhân chính trị."
    },
    {
        "artifact_id": 13,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The Con Dao Tiger Cages exhibit recreates political prison conditions."
    },
    {
        "artifact_id": 14,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Bộ sưu tập ảnh chiến tranh truyền tải thông điệp hòa bình."
    },
    {
        "artifact_id": 14,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The war photography collection promotes messages of peace."
    },
    {
        "artifact_id": 15,
        "lang": "vi",
        "content_type": "faq",
        "content_text": "Trực thăng UH-1 Huey được dùng cho vận chuyển quân và cứu thương."
    },
    {
        "artifact_id": 15,
        "lang": "en",
        "content_type": "faq",
        "content_text": "The UH-1 Huey helicopter was used for troop transport and medical evacuation."
    }
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if data already exists
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Location))
        if result.scalar() > 0:
            print("Database already seeded. Skipping.")
            return

        # Seed locations
        for loc_data in LOCATIONS:
            session.add(Location(**loc_data))
        await session.flush()

        # Seed artifacts
        for art_data in ARTIFACTS:
            session.add(Artifact(**art_data))
        await session.flush()
        
        # Seed precomputed audio
        for pre_data in PRECOMPUTED_AUDIO:
            session.add(PrecomputedAudio(**pre_data))
            
        # Seed bilingual content
        for bil_data in BILINGUAL_CONTENT:
            session.add(BilingualContent(**bil_data))

        await session.commit()
        print(f"Seeded {len(LOCATIONS)} locations, {len(ARTIFACTS)} artifacts, {len(PRECOMPUTED_AUDIO)} audios, {len(BILINGUAL_CONTENT)} contents.")

if __name__ == "__main__":
    asyncio.run(seed())
