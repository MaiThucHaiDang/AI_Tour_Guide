"""Seed PostgreSQL database with Hue Imperial City data.

Run after migrations: alembic upgrade head && python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import async_session_factory
from models.location import Location
from models.artifact import Artifact
from models.precomputed_audio import PrecomputedAudio
from models.bilingual_content import BilingualContent
from models.graph import ArtifactFAQ, ArtifactRelation, KnowledgeFact
from services.ai.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = [
    {
        "name_vi": "Kinh thành Huế (Đại Nội)",
        "name_en": "Hue Imperial City (The Citadel)",
        "gps_coordinates": "16.4695,107.5780",
        "open_hours": "07:00 - 17:30",
        "latitude": 16.4695,
        "longitude": 107.5780
    }
]

ARTIFACTS = [
    {
        "loc_id": 1,
        "name_vi": "Cửa Hòa Bình",
        "name_en": "Hoa Binh Gate (Gate of Peace)",
        "history_text_vi": "Cửa Hòa Bình là cổng phía Bắc của Hoàng thành Huế, nằm đối diện với Ngọ Môn ở phía Nam. Cổng được xây dựng dưới thời vua Gia Long và hoàn thiện dưới triều Minh Mạng. Đây là một trong bốn cổng chính dẫn vào Hoàng thành, mang ý nghĩa cầu chúc hòa bình và thái bình cho đất nước. Kiến trúc cổng gồm vọng lâu hai tầng trên nền đá vững chãi.",
        "history_text_en": "Hoa Binh Gate (Gate of Peace) is the northern gate of the Imperial City of Hue, directly opposite the Ngo Mon Gate to the south. Built during the reign of Emperor Gia Long and completed under Emperor Minh Mang, it is one of four main gates leading into the Imperial Citadel. The gate symbolizes wishes for peace and prosperity. Its architecture features a two-story watchtower on a solid stone foundation.",
        "author": "Triều Nguyễn",
        "year": 1804,
        "latitude": 16.4721279,
        "longitude": 107.5762716
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Kiến Trung",
        "name_en": "Kien Trung Palace",
        "history_text_vi": "Điện Kiến Trung là cung điện nằm trong Tử Cấm Thành, được xây dựng năm 1921 dưới thời vua Khải Định theo phong cách kiến trúc Đông Tây kết hợp. Đây là nơi ở và làm việc của hai vị vua cuối cùng triều Nguyễn là Khải Định và Bảo Đại. Năm 1945, vua Bảo Đại đã đọc chiếu thoái vị tại đây, đánh dấu sự kết thúc của chế độ phong kiến Việt Nam. Điện bị hư hại nặng trong chiến tranh và được phục dựng hoàn thành vào năm 2019.",
        "history_text_en": "Kien Trung Palace is located within the Forbidden Purple City and was built in 1921 under Emperor Khai Dinh in a blend of Eastern and Western architectural styles. It served as the residence and workplace of the last two Nguyen Dynasty emperors, Khai Dinh and Bao Dai. In 1945, Emperor Bao Dai read his abdication proclamation here, marking the end of feudal monarchy in Vietnam. The palace was severely damaged during wartime and was fully restored in 2019.",
        "author": "Vua Khải Định",
        "year": 1921,
        "latitude": 16.4710479,
        "longitude": 107.5765559
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Trường Sanh",
        "name_en": "Truong Sanh Palace (Palace of Longevity)",
        "history_text_vi": "Cung Trường Sanh được xây dựng năm 1821 dưới triều vua Minh Mạng, ban đầu có tên là cung Trường Ninh, là nơi nghỉ dưỡng của các Thái hậu và Hoàng Thái hậu triều Nguyễn. Cung nằm ở góc Tây Bắc của Hoàng thành, bao gồm nhiều tòa nhà, hồ nước và vườn cảnh tạo thành một quần thể kiến trúc hài hòa. Nơi đây nổi tiếng với nghệ thuật ghép sành sứ tinh xảo trang trí trên các bức tường và mái.",
        "history_text_en": "Truong Sanh Palace was built in 1821 under Emperor Minh Mang, originally named Truong Ninh Palace. It served as a retreat for Queen Mothers and Empress Dowagers of the Nguyen Dynasty. Located in the northwest corner of the Imperial City, the complex includes multiple buildings, ponds, and gardens forming a harmonious architectural ensemble. The palace is renowned for its exquisite mosaic art made from broken ceramics adorning the walls and roofs.",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.469725,
        "longitude": 107.574694
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Diên Thọ",
        "name_en": "Dien Tho Palace (Palace of Longevity)",
        "history_text_vi": "Cung Diên Thọ được xây dựng năm 1804 dưới triều vua Gia Long, là nơi sinh sống của các Hoàng Thái hậu và Thái hoàng Thái hậu triều Nguyễn. Đây là một trong những quần thể kiến trúc lớn nhất và còn nguyên vẹn nhất trong Hoàng thành. Cung gồm khoảng 20 công trình bao gồm điện chính, nhà kho, nhà bếp và vườn hoa. Kiến trúc mang đậm phong cách cung đình Huế với mái ngói hoàng lưu ly và hệ thống cột gỗ lim chạm trổ tinh xảo.",
        "history_text_en": "Dien Tho Palace was built in 1804 under Emperor Gia Long as the residence for Queen Mothers and Grand Queen Mothers of the Nguyen Dynasty. It is one of the largest and best-preserved architectural complexes within the Imperial City. The palace comprises about 20 structures including the main hall, storehouses, kitchens, and gardens. Its architecture features the distinctive Hue court style with yellow-glazed tile roofs and intricately carved ironwood columns.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4688556,
        "longitude": 107.5753417
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Chương Đức",
        "name_en": "Chuong Duc Gate (Gate of Manifest Virtue)",
        "history_text_vi": "Cửa Chương Đức là cổng phía Tây của Hoàng thành Huế, được xây dựng dưới thời vua Gia Long. Cổng có kiến trúc vọng lâu hai tầng, tương tự các cổng khác của Hoàng thành. Tên gọi 'Chương Đức' mang ý nghĩa 'biểu dương đức hạnh'. Qua cổng này là con đường dẫn đến khu vực Tây của thành, nơi có các cung điện dành cho Thái hậu.",
        "history_text_en": "Chuong Duc Gate is the western gate of the Hue Imperial City, built during the reign of Emperor Gia Long. The gate features a two-story watchtower architecture, similar to the other gates of the Imperial City. The name 'Chuong Duc' means 'Manifest Virtue'. Beyond this gate lies the road to the western quarter of the citadel, where palaces for the Queen Mothers are located.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4673314,
        "longitude": 107.5757295
    },
    {
        "loc_id": 1,
        "name_vi": "Hưng Miếu (Hưng Tổ Miếu)",
        "name_en": "Hung Mieu (Hung To Temple)",
        "history_text_vi": "Hưng Miếu được xây dựng năm 1804 dưới triều vua Gia Long để thờ phụng thân phụ của ông là Nguyễn Phúc Luân (được truy tôn là Hưng Tổ). Miếu nằm ở phía Tây Nam của Hoàng thành, gần Thế Miếu. Kiến trúc gồm 5 gian 2 chái với mái ngói lưu ly, bên trong có long ngai và bài vị thờ. Hưng Miếu là biểu tượng của lòng hiếu thảo và sự tôn kính tổ tiên trong văn hóa cung đình Huế.",
        "history_text_en": "Hung Mieu was built in 1804 under Emperor Gia Long to worship his father Nguyen Phuc Luan (posthumously honored as Hung To). The temple is located in the southwestern area of the Imperial City, near The Mieu. Its architecture features five bays with two annexes and a glazed tile roof. Inside are the royal throne and ancestral tablets. Hung Mieu symbolizes filial piety and ancestral reverence in Hue court culture.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4674263,
        "longitude": 107.5764189
    },
    {
        "loc_id": 1,
        "name_vi": "Thế Miếu (Thế Tổ Miếu)",
        "name_en": "The Mieu (The To Temple)",
        "history_text_vi": "Thế Miếu là miếu thờ các vị vua triều Nguyễn, được xây dựng năm 1821 dưới triều vua Minh Mạng. Đây là công trình kiến trúc quan trọng bậc nhất trong hệ thống miếu thờ của Hoàng thành. Miếu gồm 9 gian, mỗi gian thờ một vị vua, hiện thờ 7 vị vua Nguyễn. Phía trước Thế Miếu là hàng Cửu Đỉnh nổi tiếng - 9 chiếc đỉnh đồng lớn tượng trưng cho 9 đời vua. Thế Miếu và Cửu Đỉnh đã được UNESCO công nhận là Di sản Văn hóa Thế giới.",
        "history_text_en": "The Mieu is the temple dedicated to the emperors of the Nguyen Dynasty, built in 1821 under Emperor Minh Mang. It is the most important architectural monument in the Imperial City's temple complex. The temple has nine bays, each dedicated to one emperor, currently enshrining seven Nguyen emperors. In front of The Mieu stand the famous Nine Dynastic Urns (Cuu Dinh) - nine large bronze urns symbolizing nine imperial reigns. The Mieu and the Cuu Dinh are recognized by UNESCO as World Cultural Heritage.",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.4671621,
        "longitude": 107.5767333
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace (Palace of Supreme Harmony)",
        "history_text_vi": "Điện Thái Hòa là cung điện quan trọng nhất của triều Nguyễn, nơi diễn ra các buổi thiết triều và lễ nghi trọng đại. Được xây dựng lần đầu năm 1805 dưới triều vua Gia Long và trùng tu nhiều lần, điện nằm ngay sau Ngọ Môn trên trục chính của Hoàng thành. Điện có 80 cột gỗ lim sơn son thếp vàng, mái lợp ngói hoàng lưu ly. Nội thất trang trí rồng, mây và các biểu tượng hoàng gia. Đây là biểu tượng quyền lực tối cao của vương triều Nguyễn.",
        "history_text_en": "Thai Hoa Palace (Palace of Supreme Harmony) is the most important palace of the Nguyen Dynasty, where court audiences and grand ceremonies took place. First built in 1805 under Emperor Gia Long and renovated multiple times, the palace sits directly behind the Ngo Mon Gate on the main axis of the Imperial City. It features 80 ironwood columns lacquered in red and gilded in gold, with a roof of yellow-glazed tiles. The interior is decorated with dragons, clouds, and royal symbols. It stands as the supreme symbol of Nguyen imperial power.",
        "author": "Vua Gia Long",
        "year": 1805,
        "latitude": 16.4686747,
        "longitude": 107.578412
    },
    {
        "loc_id": 1,
        "name_vi": "Nền điện Cần Chánh",
        "name_en": "Can Chanh Palace Foundation",
        "history_text_vi": "Điện Cần Chánh từng là nơi vua Nguyễn tiếp kiến các quan đại thần và sứ thần nước ngoài trong các buổi thường triều. Được xây dựng năm 1804 dưới triều vua Gia Long, điện nằm ngay sau Điện Thái Hòa trong Tử Cấm Thành. Đây từng là một trong những công trình kiến trúc đẹp nhất Hoàng thành với quy mô lớn và trang trí cầu kỳ. Điện đã bị phá hủy trong chiến tranh năm 1947, hiện chỉ còn lại nền móng và một số dấu tích kiến trúc.",
        "history_text_en": "Can Chanh Palace was where Nguyen emperors held daily audiences with mandarins and received foreign envoys. Built in 1804 under Emperor Gia Long, the palace stood directly behind Thai Hoa Palace within the Forbidden Purple City. It was once one of the most beautiful structures in the Imperial City, with grand proportions and elaborate decorations. The palace was destroyed during the war in 1947; only its foundation and some architectural remains survive today.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4695281,
        "longitude": 107.5777743
    },
    {
        "loc_id": 1,
        "name_vi": "Duyệt Thị Đường",
        "name_en": "Duyet Thi Duong (Royal Theater)",
        "history_text_vi": "Duyệt Thị Đường là nhà hát hoàng gia cổ nhất còn tồn tại ở Việt Nam, được xây dựng năm 1826 dưới triều vua Minh Mạng. Nằm trong Tử Cấm Thành, đây là nơi biểu diễn tuồng, múa và âm nhạc cung đình phục vụ hoàng gia. Nhà hát có kiến trúc đặc biệt với sân khấu nằm giữa, khán giả ngồi xung quanh ba phía. Ngày nay, Duyệt Thị Đường vẫn được sử dụng để biểu diễn Nhã nhạc cung đình Huế - Di sản Văn hóa phi vật thể của nhân loại.",
        "history_text_en": "Duyet Thi Duong is the oldest surviving royal theater in Vietnam, built in 1826 under Emperor Minh Mang. Located within the Forbidden Purple City, it hosted performances of classical opera, dance, and court music for the royal family. The theater has a unique architecture with a central stage surrounded by audience seating on three sides. Today, Duyet Thi Duong continues to host performances of Hue Royal Court Music (Nha Nhac), a UNESCO Intangible Cultural Heritage of Humanity.",
        "author": "Vua Minh Mạng",
        "year": 1826,
        "latitude": 16.470284,
        "longitude": 107.5785163
    },
    {
        "loc_id": 1,
        "name_vi": "Phủ Nội Vụ",
        "name_en": "Phu Noi Vu (Ministry of the Interior)",
        "history_text_vi": "Phủ Nội Vụ là cơ quan quản lý các công việc nội bộ của cung đình triều Nguyễn, được xây dựng dưới thời vua Gia Long. Phủ chịu trách nhiệm quản lý kho bạc, đồ dùng hoàng gia, cung cấp vật tư và giám sát các xưởng thủ công trong Hoàng thành. Khu vực này từng có nhiều nhà kho, xưởng chế tác và văn phòng hành chính. Phủ Nội Vụ phản ánh hệ thống hành chính phức tạp và tinh vi của triều đình Nguyễn.",
        "history_text_en": "Phu Noi Vu (Ministry of the Interior) managed internal affairs of the Nguyen Dynasty court, built under Emperor Gia Long. The ministry was responsible for managing the treasury, royal possessions, supplies, and overseeing craft workshops within the Imperial City. The area once housed numerous storehouses, workshops, and administrative offices. Phu Noi Vu reflects the complex and sophisticated administrative system of the Nguyen court.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.470755,
        "longitude": 107.5796368
    },
    {
        "loc_id": 1,
        "name_vi": "Vườn Cơ Hạ",
        "name_en": "Co Ha Garden (Imperial Garden)",
        "history_text_vi": "Vườn Cơ Hạ là vườn ngự uyển nằm trong Tử Cấm Thành, được xây dựng năm 1847 dưới triều vua Thiệu Trị. Đây là khu vườn riêng của nhà vua để nghỉ ngơi, thưởng ngoạn và sáng tác thơ văn. Vườn có hồ sen, đình các, cây cổ thụ và các tiểu cảnh nghệ thuật. Vua Thiệu Trị đã viết nhiều bài thơ ca ngợi cảnh đẹp nơi đây. Vườn Cơ Hạ là minh chứng cho tình yêu thiên nhiên và nghệ thuật vườn cảnh tinh tế của các vua Nguyễn.",
        "history_text_en": "Co Ha Garden is an imperial garden within the Forbidden Purple City, built in 1847 under Emperor Thieu Tri. It served as the emperor's private retreat for relaxation, contemplation, and literary composition. The garden features lotus ponds, pavilions, ancient trees, and artistic miniature landscapes. Emperor Thieu Tri wrote many poems praising its beauty. Co Ha Garden testifies to the Nguyen emperors' love for nature and their refined art of garden design.",
        "author": "Vua Thiệu Trị",
        "year": 1847,
        "latitude": 16.4717727,
        "longitude": 107.5788666
    },
    {
        "loc_id": 1,
        "name_vi": "Triệu Miếu (Triệu Tổ Miếu)",
        "name_en": "Trieu Mieu (Trieu To Temple)",
        "history_text_vi": "Triệu Miếu được xây dựng năm 1804 dưới triều vua Gia Long để thờ Nguyễn Kim (Triệu Tổ), vị chúa Nguyễn đầu tiên, người đã đặt nền móng cho sự nghiệp của dòng họ Nguyễn. Miếu nằm ở phía Đông Nam của Hoàng thành, đối xứng với Thái Miếu. Kiến trúc gồm 5 gian, bên trong có long ngai và bài vị thờ. Triệu Miếu thể hiện tinh thần uống nước nhớ nguồn của triều đình Nguyễn.",
        "history_text_en": "Trieu Mieu was built in 1804 under Emperor Gia Long to worship Nguyen Kim (Trieu To), the first Nguyen Lord who laid the foundation for the Nguyen clan's legacy. The temple is located in the southeastern area of the Imperial City, symmetrical to Thai Mieu. Its architecture features five bays with royal thrones and ancestral tablets inside. Trieu Mieu embodies the Nguyen court's spirit of honoring their origins.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4701907,
        "longitude": 107.5801058
    },
    {
        "loc_id": 1,
        "name_vi": "Thái Miếu (Thái Tổ Miếu)",
        "name_en": "Thai Mieu (Thai To Temple)",
        "history_text_vi": "Thái Miếu được xây dựng năm 1804 dưới triều vua Gia Long để thờ các vị chúa Nguyễn tiền triều và các vị tổ tiên xa hơn của dòng họ Nguyễn. Đây là miếu thờ có quy mô lớn nhất trong hệ thống miếu thờ tổ tiên của triều Nguyễn, gồm 11 gian thờ. Miếu nằm ở phía Đông Nam Hoàng thành, gần cổng Hiển Nhơn. Kiến trúc trang nghiêm với hệ thống cột gỗ lim và mái ngói lưu ly, phản ánh quy cách thờ cúng hoàng gia đầy trang trọng.",
        "history_text_en": "Thai Mieu was built in 1804 under Emperor Gia Long to worship the Nguyen Lords of the preceding era and more distant ancestors of the Nguyen clan. It is the largest temple in the Nguyen Dynasty's ancestral worship system, featuring 11 worship bays. Located in the southeastern part of the Imperial City near Hien Nhon Gate, its solemn architecture includes ironwood columns and glazed tile roofs, reflecting the formal and dignified protocols of royal ancestor worship.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4699109,
        "longitude": 107.5803246
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Hiển Nhơn",
        "name_en": "Hien Nhon Gate (Gate of Manifest Benevolence)",
        "history_text_vi": "Cửa Hiển Nhơn là cổng phía Đông của Hoàng thành Huế, được xây dựng dưới thời vua Gia Long. Cổng có kiến trúc tương tự Cửa Chương Đức ở phía Tây, với vọng lâu hai tầng trên nền gạch đá. Tên 'Hiển Nhơn' nghĩa là 'biểu lộ lòng nhân ái'. Đây là một trong bốn cổng chính để ra vào Hoàng thành, dẫn đến khu vực phía Đông nơi có các miếu thờ tổ tiên hoàng gia.",
        "history_text_en": "Hien Nhon Gate is the eastern gate of the Hue Imperial City, built under Emperor Gia Long. The gate has architecture similar to Chuong Duc Gate on the western side, with a two-story watchtower on a brick and stone base. The name 'Hien Nhon' means 'Manifest Benevolence'. It is one of four main gates for entering the Imperial City, leading to the eastern quarter where royal ancestral temples are located.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4707473,
        "longitude": 107.5805514
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Long An (Bảo tàng Cổ vật Cung đình Huế)",
        "name_en": "Long An Palace (Hue Royal Antiquities Museum)",
        "history_text_vi": "Điện Long An được xây dựng năm 1845 dưới triều vua Thiệu Trị, ban đầu là cung điện trong Tử Cấm Thành. Năm 1909, dưới thời vua Duy Tân, điện được dời ra vị trí hiện tại để phục vụ làm bảo tàng. Từ năm 1923, đây là Bảo tàng Cổ vật Cung đình Huế, lưu giữ hơn 10.000 hiện vật quý giá bao gồm đồ vàng, bạc, đồng, sứ, gỗ, vải và nhiều tác phẩm nghệ thuật cung đình. Kiến trúc điện là một trong những công trình gỗ đẹp nhất còn lại của triều Nguyễn.",
        "history_text_en": "Long An Palace was built in 1845 under Emperor Thieu Tri, originally serving as a palace within the Forbidden Purple City. In 1909, under Emperor Duy Tan, it was relocated to its current position to serve as a museum. Since 1923, it has housed the Hue Royal Antiquities Museum, preserving over 10,000 precious artifacts including gold, silver, bronze, porcelain, wood, and textile items along with many royal artworks. The palace architecture is one of the finest surviving wooden structures of the Nguyen Dynasty.",
        "author": "Vua Thiệu Trị",
        "year": 1845,
        "latitude": 16.4712819,
        "longitude": 107.5818602
    },
    {
        "loc_id": 1,
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate (Meridian Gate)",
        "history_text_vi": "Ngọ Môn là cổng chính phía Nam của Hoàng thành Huế, được xây dựng vào năm 1833 dưới triều vua Minh Mạng. Cổng có kiến trúc đồ sộ, nguy nga với lầu Ngũ Phụng ở phía trên, nơi diễn ra nhiều sự kiện trọng đại của triều đình nhà Nguyễn như lễ Ban Sóc, lễ Truyền Lô và cũng là nơi vua Bảo Đại tuyên bố thoái vị năm 1945.",
        "history_text_en": "Ngo Mon Gate (Meridian Gate) is the main southern entrance of the Imperial City of Hue, built in 1833 under Emperor Minh Mang. It is a grand and magnificent structure topped with the Five Phoenix Pavilion (Lau Ngu Phung). The gate hosted major royal events such as the Ban Soc calendar decree ceremony, the Truyen Lo doctor laureate ceremony, and was also where Emperor Bao Dai declared his abdication in 1945.",
        "author": "Triều Nguyễn / Vua Minh Mạng",
        "year": 1833,
        "latitude": 16.468083,
        "longitude": 107.578667
    }
]

PRECOMPUTED_AUDIO = []
BILINGUAL_CONTENT = []
ARTIFACT_RELATIONS = []


async def main():
    """Seed the database."""
    from sqlalchemy import select, text

    async with async_session_factory() as session:
        # Clear existing data in reverse FK order
        logger.info("Clearing existing data...")
        await session.execute(text("DELETE FROM artifact_relations"))
        await session.execute(text("UPDATE artifact_faqs SET fact_id = NULL"))
        await session.execute(text("DELETE FROM knowledge_facts"))
        await session.execute(text("DELETE FROM artifact_faqs"))
        await session.execute(text("DELETE FROM precomputed_audio"))
        await session.execute(text("DELETE FROM bilingual_content"))
        await session.execute(text("DELETE FROM artifacts"))
        await session.execute(text("DELETE FROM locations"))
        await session.execute(text("ALTER SEQUENCE locations_loc_id_seq RESTART WITH 1"))
        await session.execute(text("ALTER SEQUENCE artifacts_art_id_seq RESTART WITH 1"))
        await session.commit()

        # Check if calibrated file exists
        calibrated_file = Path(__file__).resolve().parents[1] / "backend" / "data" / "map_calibrated.json"
        seeded_bounds = None
        seeded_artifacts_coords = {}
        
        if calibrated_file.exists():
            try:
                import json
                with open(calibrated_file, "r", encoding="utf-8") as f:
                    cal_data = json.load(f)
                    seeded_bounds = cal_data.get("map_bounds")
                    for art_cfg in cal_data.get("artifacts", []):
                        seeded_artifacts_coords[art_cfg["name_vi"]] = (art_cfg["lat"], art_cfg["lng"])
                logger.info(f"Loaded calibrated coordinates and bounds from {calibrated_file}")
            except Exception as exc:
                logger.warning(f"Failed to load calibrated config from file: {exc}")

        # Seed locations
        location_objs = []
        for loc_data in LOCATIONS:
            data = loc_data.copy()
            if seeded_bounds:
                sw = seeded_bounds[0]
                ne = seeded_bounds[1]
                data["gps_coordinates"] = f"16.4695,107.5780|{sw[0]},{sw[1]};{ne[0]},{ne[1]}"
            loc = Location(**data)
            session.add(loc)
            location_objs.append(loc)
        await session.flush()
        logger.info(f"Seeded {len(LOCATIONS)} location(s)")

        hue_loc_id = location_objs[0].loc_id

        # Seed artifacts
        for art_data in ARTIFACTS:
            data = art_data.copy()
            data["loc_id"] = hue_loc_id
            if data["name_vi"] in seeded_artifacts_coords:
                lat, lng = seeded_artifacts_coords[data["name_vi"]]
                data["latitude"] = lat
                data["longitude"] = lng
            art = Artifact(**data)
            session.add(art)
        await session.flush()
        logger.info(f"Seeded {len(ARTIFACTS)} artifact(s)")

        await session.commit()
        logger.info("Database seeded successfully for Hue Imperial City!")


if __name__ == "__main__":
    asyncio.run(main())
