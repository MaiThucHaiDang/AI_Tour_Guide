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
        "history_text_vi": "Cửa Hòa Bình, người dân địa phương hay gọi là 'Cửa Sau', trải qua 3 lần đổi tên gắn liền với các mốc lịch sử triều Nguyễn. Năm 1804 thời Gia Long, cửa được xây dựng cùng thời điểm quy hoạch hệ thống cung điện phía trong Đại Nội với tên ban đầu là cửa Củng Thần. Năm 1821 khi lên ngôi và tái cấu trúc lại một số công trình, vua Minh Mạng đổi tên thành cửa Địa Bình. Đến năm 1833 vua Minh Mạng tiếp tục cải tổ toàn diện kiến trúc Đại Nội và đổi tên thành cửa Hòa Bình cho đến ngày nay, mang ý nghĩa biểu trưng cho sự thái bình, thịnh vượng của đất nước. Khác với các cửa Hiển Nhơn hay Chương Đức, cửa Hòa Bình có kết cấu kiến trúc độc đáo. Ban đầu cửa được xây dựng theo lối tam quan môn lầu (phía trên có tầng lầu gọi là Lầu Hòa Bình), nhưng đến năm 1839 phần lầu phía trên bị triệt giải, do đó cấu trúc hiện tại là dạng tam quan xây gạch chỉ một tầng, có vì nóc và mái lợp ngói giống hình dáng một ngôi điện cổ. Trong lịch sử từng có cầu Kim Thủy bắc ngang qua hồ Nội Kim Thủy nối từ cửa Hòa Bình đến trước cửa Tường Loan của Tử Cấm Thành, được thiết kế theo lối 'thượng gia hạ kiều' (dưới là cầu, trên có mái che lợp ngói) nhưng phần mái che này nay không còn. Cửa nằm ở mặt phía Bắc của Hoàng thành, ngay sau Điện Kiến Trung và cung Trường Sanh, là lối ngự du riêng của Hoàng đế. Cửa từng bị phá hủy nặng nề trong chiến tranh các năm 1947 và 1968, chỉ còn nền móng. Năm 1894 thời Thành Thái được trùng tu lớn lần đầu. Năm 2004 Trung tâm Bảo tồn Di tích Cố đô Huế tiến hành trùng tu toàn diện, các nghệ nhân dựa vào tư liệu ảnh cổ thời Nguyễn để phục dựng nguyên vẹn phần mái lợp ngói âm dương, chi tiết vách gạch và hệ thống cửa gỗ đúng quy chuẩn kiến trúc cung đình xưa.",
        "history_text_en": "Hoa Binh Gate, locally known as 'Back Gate', underwent three name changes through Nguyen Dynasty history. In 1804 under Emperor Gia Long, it was first built as Cung Than Gate during the initial planning of the Imperial City. In 1821 Emperor Minh Mang renamed it Dia Binh Gate. In 1833 he again comprehensively restructured the Imperial City architecture and renamed it Hoa Binh Gate (Gate of Peace), symbolizing national peace and prosperity. Unlike Hien Nhon or Chuong Duc gates, Hoa Binh Gate has a unique architectural structure. Initially built in the three-portal watchtower style with an upper floor called Hoa Binh Pavilion, the upper level was dismantled in 1839, leaving today's single-story brick structure with a tiled roof resembling an ancient palace. Historically, Kim Thuy Bridge spanned the Noi Kim Thuy pond connecting Hoa Binh Gate to Tuong Loan Gate of the Forbidden Purple City, designed in the 'bridge with covered roof' style, though the roof no longer exists. Located on the northern face of the Imperial City behind Kien Trung Palace and Truong Sanh Palace, it served as the emperor's private exit for excursions. The gate was heavily destroyed during the wars of 1947 and 1968, leaving only foundations. It underwent major restoration in 1894 under Emperor Thanh Thai. In 2004 the Hue Monuments Conservation Center conducted comprehensive restoration, with artisans using period photographs to faithfully reconstruct the yin-yang tile roof, brick walls, and wooden door system according to original court architectural standards.",
        "author": "Triều Nguyễn",
        "year": 1804,
        "latitude": 16.4721279,
        "longitude": 107.5762716
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Kiến Trung",
        "name_en": "Kien Trung Palace",
        "history_text_vi": "Điện Kiến Trung là cung điện nằm ở điểm cực Bắc của trục thần đạo xuyên qua trung tâm Tử Cấm Thành, được vua Khải Định cho xây vào năm 1921-1923 cùng thời gian với việc xây lăng để làm nơi sinh hoạt của vua trong hoàng cung. Kiểu thức điện là hợp thể phong cách Âu châu gồm kiến trúc Pháp, kiến trúc Phục hưng của Ý cùng pha thêm kiến trúc cổ truyền Việt Nam. Mặt tiền điện có trang trí những mảnh gốm sứ nhiều màu. Trước điện là vườn cảnh, có ba cầu thang đắp rồng dẫn lên thềm điện. Tầng chính trổ 13 cửa hiên, tầng trên là gác làm cùng một thể thức, trên cùng là mái ngói có hàng lan can trang trí theo phong cách Việt Nam. Dưới thời Minh Mạng nơi đây có lầu Minh Viễn (1827-1876), thời Duy Tân mang tên lầu Du Cửu (1913-1916). Năm 1921 vua Khải Định xây lại mới. Đây là nơi vua Khải Định băng hà ngày 6 tháng 11 năm 1925. Sang triều Bảo Đại, triều đình tu sửa lại tòa điện, tân trang tiện nghi theo thể cách Tây phương, xây buồng tắm. Vua và hoàng hậu Nam Phương dọn về sống tại đây, hoàng hậu hạ sinh Thái tử Bảo Long tại điện này ngày 4-1-1936. Ngày 11 tháng 3 năm 1945, vua Bảo Đại triệu cố vấn tối cao của Nhật vào điện Kiến Trung để tuyên bố nước Việt Nam độc lập, khai sinh Đế quốc Việt Nam. Điện cùng nhiều công trình khác trong hoàng thành bị phá hủy tháng 2 năm 1947 bởi Việt Minh trong chiến dịch Tiêu thổ kháng chiến, chỉ còn nền điện và hàng lan can. Từ năm 2013 Trung tâm Bảo tồn di tích cố đô Huế khởi động dự án phục hồi. Dự án khởi công ngày 16 tháng 2 năm 2019 với tổng kinh phí hơn 123 tỉ đồng và hoàn thành năm 2023.",
        "history_text_en": "Kien Trung Palace stands at the northernmost point of the sacred axis running through the Forbidden Purple City. Built by Emperor Khai Dinh from 1921-1923 concurrently with his tomb, it served as the emperor's residence within the citadel. The architectural style blends European elements including French design and Italian Renaissance with traditional Vietnamese architecture. The facade features colorful ceramic mosaic decorations. In front lies a landscape garden with three dragon-carved staircases leading to the terrace. The main floor has 13 porch doors, the upper floor follows the same pattern, and the roof features Vietnamese-style railings. During Minh Mang's reign the site housed Minh Vien Pavilion (1827-1876), and under Duy Tan it was called Du Cuu Pavilion (1913-1916). Emperor Khai Dinh rebuilt it in 1921 and died here on November 6, 1925. Under Emperor Bao Dai, the palace was renovated with Western amenities including a bathroom. The emperor and Empress Nam Phuong resided here, and she gave birth to Crown Prince Bao Long on January 4, 1936. On March 11, 1945, Emperor Bao Dai summoned the Japanese supreme advisor to Kien Trung Palace to declare Vietnam's independence, establishing the Empire of Vietnam. The palace was destroyed in February 1947 by the Viet Minh during the scorched-earth resistance campaign, leaving only the foundation and railings. In 2013 the Hue Monuments Conservation Center launched a restoration project. Construction began on February 16, 2019 with a budget of over 123 billion VND and was completed in 2023.",
        "author": "Vua Khải Định",
        "year": 1921,
        "latitude": 16.4710479,
        "longitude": 107.5765559
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Trường Sanh",
        "name_en": "Truong Sanh Palace (Palace of Longevity)",
        "history_text_vi": "Cung Trường Sanh còn có tên là Cung Trường Ninh, với tổng diện tích 11.400m2, nằm ở phía Tây Bắc Hoàng thành Huế, phía Bắc giáp hồ Nội Kim Thủy, phía Nam là cung Diên Thọ, phía Đông là Trực Phương viên thuộc Tử Cấm Thành. Vai trò ban đầu của cung là hoa viên, nơi các vua triều Nguyễn mời mẹ đến thăm thú ngoạn cảnh, về sau chuyển thành nơi ăn ở sinh hoạt của các bà Hoàng thái hậu và Thái hoàng thái hậu. Thời kỳ rực rỡ nhất, kiến trúc cảnh quan của cung được vua Thiệu Trị xếp vào hàng thứ bảy trong bài Trường Ninh Thùy Điếu thuộc tập thơ Thần kinh nhị thập cảnh. Cung được khởi công xây dựng năm Minh Mạng thứ nhất (1821), mang dáng dấp của một hoa viên với kiến trúc ban đầu hình chữ Tam gồm một điện chính, điện phía trước, lầu phía sau, nhà Huyên Đường, nhà Di Chí, lầu Vọng Hồ cùng hệ thống thành, hồ, cầu, núi. Năm Thiệu Trị thứ 6 (1846) được trùng tu lớn, nâng cấp quy mô và kiểu dáng, kiến trúc chính xếp theo hình chữ Vương gồm Thọ Khang điện đặt chính giữa, Ngũ Đại Đồng đường phía trước, Vạn Phước lâu ở phía sau. Vòng quanh cung có lạch nước Đào Nguyên nhân tạo nối qua hồ Nội Kim Thủy, ngang qua bắc những cây cầu sơn màu đỏ. Cửa chính gọi Trường An môn xây theo lối tam quan, trang trí đề tài hoa lá và ngũ sắc. Năm 1923 vua Khải Định tiếp tục tu bổ, đổi tên thành cung Trường Sanh. Năm 1990 Trung tâm Bảo tồn di tích dời các hộ dân ra khỏi phế tích. Ngày 5 tháng 1 năm 2005 khởi công dự án tu bổ với tổng kinh phí gần 30 tỷ đồng, hoàn thành năm 2007.",
        "history_text_en": "Truong Sanh Palace, also known as Truong Ninh Palace, covers 11,400 square meters in the northwest corner of the Hue Imperial City. It borders Noi Kim Thuy pond to the north, Dien Tho Palace to the south, and Truc Phuong Vien of the Forbidden Purple City to the east. Initially designed as a botanical garden where Nguyen emperors invited their mothers for outings, it later became the residence for Queen Mothers and Empress Dowagers. At its zenith, Emperor Thieu Tri ranked its landscape seventh among the Twenty Scenic Views of the Capital in his poem 'Truong Ninh Thuy Dieu'. Construction began in 1821 under Emperor Minh Mang in the shape of the Chinese character 'Three' with a main hall, front hall, rear pavilion, and systems of walls, lakes, bridges, and mountains. In 1846 Emperor Thieu Tri undertook major renovation, reorganizing the architecture in the shape of the Chinese character 'King' with Tho Khang Hall at center, Ngu Dai Dong Duong Hall in front, and Van Phuoc Pavilion behind. An artificial Peach Spring stream encircles the palace connecting to Noi Kim Thuy pond, crossed by red-painted bridges. The main gate, Truong An Mon, is built in the three-portal style decorated with floral and five-color motifs. In 1923 Emperor Khai Dinh renovated and renamed it Truong Sanh Palace. In 1990 the conservation center relocated resident families from the ruins. On January 5, 2005, a restoration project began with a budget of nearly 30 billion VND, completing in 2007.",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.469725,
        "longitude": 107.574694
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Diên Thọ",
        "name_en": "Dien Tho Palace (Palace of Longevity)",
        "history_text_vi": "Cung Diên Thọ là hệ thống kiến trúc cung điện quy mô nhất còn lại tại Cố đô Huế, nằm ở phía tây Tử Cấm Thành, phía bắc điện Phụng Tiên và phía nam cung Trường Sanh. Khuôn viên ngày nay rộng khoảng 17.500m2 với các công trình như Diên Thọ chính điện, điện Thọ Ninh, lầu Tịnh Minh, tạ Trường Du, các Khương Ninh, được nối kết bằng hệ thống hành lang có mái che. Được xây dựng tháng 4 năm 1804 làm nơi sinh sống của bà Hiếu Khang hoàng hậu - mẹ vua Gia Long, cung mang tên Trường Thọ. Sau 7 tháng thi công, ngày 20 tháng 11 năm 1804 vua thân hành đưa bà vào ở. Năm 1811 bà mất, cung Trường Thọ bị triệt giải, gỗ dùng xây điện Thanh Hòa. Năm 1820 vua Minh Mạng lên ngôi, trên khuôn viên cũ xây cung Từ Thọ cho thân mẫu là bà Thuận Thiên Cao Hoàng hậu. Năm 1848 vua Tự Đức hạ lệnh triệt giải cung Từ Thọ để xây cung Gia Thọ hoàn toàn mới. Ngày 7 tháng 5 năm 1849 bà Từ Dụ chính thức đến ở. Cung qua nhiều lần đổi tên: Từ Thọ, Gia Thọ, Ninh Thọ và cuối cùng là Diên Thọ dưới thời Khải Định. Tổng cộng 8 vị Hoàng Thái hậu, 4 vị Thái Hoàng Thái hậu đã sống tại đây. Sau 1945, bà Từ Cung - thân mẫu vua Bảo Đại - là vị Hoàng thái hậu cuối cùng ở cung Diên Thọ. Dù nhiều công trình Đại Nội bị tàn phá nặng nề trong chiến tranh, khuôn viên cung Diên Thọ hầu như còn nguyên vẹn. Năm 1993 cung nằm trong danh mục quần thể di tích Cố đô Huế được công nhận di sản thế giới. Dự án trùng tu bắt đầu năm 1997 đến nay cơ bản hoàn tất.",
        "history_text_en": "Dien Tho Palace is the largest surviving palace complex in the Hue Ancient Capital, located west of the Forbidden Purple City, north of Phung Tien Palace and south of Truong Sanh Palace. The grounds cover approximately 17,500 square meters featuring the main Dien Tho Hall, Tho Ninh Hall, Tinh Minh Pavilion, Truong Du Pavilion, and Khang Ninh structures, all connected by a covered corridor system. Built in April 1804 as the residence for Empress Dowager Hieu Khang - mother of Emperor Gia Long - it was initially named Truong Tho Palace. After seven months of construction, the emperor personally escorted her there on November 20, 1804. She died in 1811, and Truong Tho was dismantled with its timber used for Thanh Hoa Palace. In 1820 Emperor Minh Mang ascended the throne and built Tu Tho Palace on the same site for his mother, Empress Thuan Thien Cao. In 1848 Emperor Tu Duc ordered the complete demolition of Tu Tho to build Gia Tho Palace anew. On May 7, 1849, Empress Tu Du officially moved in. The palace underwent multiple name changes through history: Tu Tho, Gia Tho, Ninh Tho, and finally Dien Tho under Emperor Khai Dinh. In total, eight Queen Mothers and four Grand Queen Mothers resided here. After 1945, Tu Cung - mother of Emperor Bao Dai - was the last Queen Mother to live in Dien Tho. Although many structures in the Imperial City were heavily damaged during wartime, the Dien Tho complex remained largely intact. In 1993 it was inscribed as part of the UNESCO World Heritage Complex of Hue Monuments. A restoration project began in 1997 and is now essentially complete.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4688556,
        "longitude": 107.5753417
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Chương Đức",
        "name_en": "Chuong Duc Gate (Gate of Manifest Virtue)",
        "history_text_vi": "Cửa Chương Đức là một trong 4 cổng chính của Hoàng thành Huế, tọa lạc ở mặt phía Tây của Hoàng thành. Đây là lối ra vào chính của các bà trong cung gồm hoàng thái hậu, thái hoàng thái hậu, phi tần. Cùng với Tây Khuyết đài, cửa giúp bảo vệ triều đình và tạo sự ngăn cách giữa đời sống hoàng gia bên trong với xã hội bên ngoài. Cửa được xây dựng vào năm 1804 dưới thời vua Gia Long theo kiểu tam quan. Đến năm 1921 đời vua Khải Định, cổng được tu sửa và hoàn thiện diện mạo như ngày nay, mang nét kiến trúc khá tương đồng với cửa Hiển Nhơn ở phía Đông. Cửa có hai tầng, phần nền đài xây bằng gạch kiên cố. Thân cửa chia thành nhiều ô hộc trang trí các bức tranh đắp nổi tinh xảo, thể hiện nét nghệ thuật cung đình đặc trưng. Hoàng thành Huế có chu vi hơn 2.400 mét, mặt bằng gần vuông với 4 cửa ra vào theo 4 hướng: phía Nam là Ngọ Môn (cửa chính, nghi thức cao nhất), phía Đông là cửa Hiển Nhơn, phía Tây là cửa Chương Đức, phía Bắc là cửa Hòa Bình.",
        "history_text_en": "Chuong Duc Gate is one of the four main gates of the Hue Imperial City, located on the western side. It served as the primary entrance and exit for the royal women of the court including Queen Mothers, Empress Dowagers, and imperial concubines. Together with the Western Bastion, the gate helped protect the court and separate the royal life inside from the outside society. Built in 1804 under Emperor Gia Long in the three-portal style, it was renovated and completed to its present appearance in 1921 under Emperor Khai Dinh, featuring architecture quite similar to Hien Nhon Gate on the eastern side. The gate has two levels with a solid brick foundation. The body is divided into numerous compartments decorated with exquisite relief paintings showcasing distinctive court art. The Hue Imperial City has a perimeter of over 2,400 meters with a nearly square layout and four gates in four directions: Ngo Mon to the south (the main gate with highest ceremonial significance), Hien Nhon Gate to the east, Chuong Duc Gate to the west, and Hoa Binh Gate to the north.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4673314,
        "longitude": 107.5757295
    },
    {
        "loc_id": 1,
        "name_vi": "Hưng Miếu (Hưng Tổ Miếu)",
        "name_en": "Hung Mieu (Hung To Temple)",
        "history_text_vi": "Hưng miếu là ngôi miếu thờ Thế tử Nguyễn Phúc Luân và bà Nguyễn Thị Hoàn - song thân của vua Gia Long, vị trí ở tây nam Hoàng thành, cách Thế miếu chừng 50 mét về phía Bắc. Nguyễn Phúc Luân đáng lẽ sẽ là người lên ngôi chúa nhưng trong nội bộ chúa Nguyễn có loạn quyền thần Trương Phúc Loan nên ông bị giam vào ngục và mất tại nhà riêng khi mới 32 tuổi. Ông để lại 6 người con trai và 4 người con gái, trong đó có Nguyễn Phúc Ánh tức Gia Long - vị hoàng đế đầu tiên của triều Nguyễn. Sau khi lên ngôi năm 1802, vua Gia Long tìm lại mộ phần của cha và xây dựng miếu thờ. Việc xây dựng hoàn tất trong 4 tháng (tháng 4 đến tháng 8 năm 1804) trên địa điểm của Thế miếu ngày nay, ban đầu có tên là Hoàng Khảo miếu. Năm 1821 vua Minh Mạng cho dời Hoàng Khảo miếu lùi về phía sau 50m để lấy đất xây Thế miếu và đổi tên thành Hưng Tổ miếu. Tháng 2 năm 1947 khu miếu bị đốt cháy cùng Tử Cấm thành trong đợt tiêu thổ kháng chiến. Năm 1950 vua Bảo Đại mua lại An Khánh vương từ với giá 300.000 đồng để xây dựng lại Hưng miếu mới. Kiến trúc hiện tại có nền tảng từ An Khánh vương từ, mặt bằng gần vuông 19m x 19,20m, theo thức trùng diêm trùng lương, mái lợp ngói âm dương men vàng, nền cao 0,68m bó bằng đá Thanh. Toàn bộ dàn trò cùng các mảng trang trí đều làm bằng gỗ quý: lim, sao, kền kền, huê mộc. Năm 1995 miếu được trùng tu sơn son thiếp vàng.",
        "history_text_en": "Hung Mieu is the temple dedicated to Crown Prince Nguyen Phuc Luan and his wife Nguyen Thi Hoan, the parents of Emperor Gia Long. It is located southwest of the Imperial City, about 50 meters north of The Mieu. Nguyen Phuc Luan was destined to become lord but was imprisoned and died at age 32 due to the rebellion of powerful minister Truong Phuc Loan. He left behind six sons and four daughters, including Nguyen Phuc Anh who later became Emperor Gia Long, the first emperor of the Nguyen Dynasty. After ascending the throne in 1802, Emperor Gia Long found his father's grave and built a temple. Construction was completed in only four months (April to August 1804) on the current site of The Mieu, originally named Hoang Khao Temple. In 1821 Emperor Minh Mang relocated Hoang Khao Temple 50 meters back to make room for The Mieu and renamed it Hung To Temple. In February 1947 the temple was burned along with the Forbidden Purple City during the scorched-earth resistance campaign. In 1950 Emperor Bao Dai purchased An Khanh royal palace for 300,000 VND to rebuild Hung Mieu. The current architecture is based on An Khanh palace, with a nearly square ground plan of 19m by 19.20m, built in the double-roof style with yellow-glazed yin-yang tiles, on a 0.68m high foundation bordered by Thanh stone. The entire frame and decorative panels are crafted from precious woods: ironwood, star-apple, and rosewood. In 1995 the temple was restored with lacquering and gold gilding.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4674263,
        "longitude": 107.5764189
    },
    {
        "loc_id": 1,
        "name_vi": "Thế Miếu (Thế Tổ Miếu)",
        "name_en": "The Mieu (The To Temple)",
        "history_text_vi": "Thế Tổ miếu tọa lạc ở góc tây nam bên trong Hoàng thành Huế, là nơi thờ các vị vua triều Nguyễn và là nơi triều đình đến cúng tế các vị vua quá cố, nữ giới trong triều kể cả hoàng hậu không được đến tham dự. Nguyên ở nơi này là miếu thờ ông Nguyễn Phúc Côn (thân sinh vua Gia Long) gọi là tòa Hoàng Khảo miếu. Đến năm Minh Mạng thứ 2 (1821), Hoàng Khảo miếu được dời lùi về phía bắc khoảng 50 mét để dành vị trí xây Thế Tổ miếu thờ vua Gia Long và hoàng hậu. Miếu được xây trong 2 năm (1821-1822), ban đầu chỉ thờ Thế Tổ Cao hoàng đế, về sau trở thành nơi thờ tất cả các vị vua triều Nguyễn. Khuôn viên hình chữ nhật diện tích khoảng trên 2ha, chiếm 1/18 diện tích toàn bộ Hoàng thành và Tử Cấm thành. Đây là công trình kiến trúc gỗ rất lớn theo lối trùng thiềm điệp ốc đặt trên nền cao gần 1m, bình diện hình chữ nhật 54,60m x 27,70m, diện tích 1.500m2. Nhà chính 9 gian 2 chái kép, nhà trước 11 gian 2 chái đơn nối liền bằng vì vỏ cua chạm trổ tinh tế. Mái lợp ngói hoàng lưu ly với đỉnh nóc gắn liền thái cực bằng pháp lam rực rỡ. Bên trong miếu ngoài án thờ vua Gia Long ở gian giữa, các án thờ còn lại sắp xếp theo nguyên tắc tả chiêu hữu mục. Trước năm 1958 chỉ có 7 án thờ, đến tháng 10 năm 1958 thêm 3 vị vua chống Pháp là Hàm Nghi, Thành Thái và Duy Tân vào thờ. Bên ngoài sân đặt Cửu đỉnh - 9 chiếc đỉnh đồng to lớn đặt thẳng hàng với 9 gian thờ. Tiếp theo là Hiển Lâm các 3 tầng cao vút. Thế Miếu và Cửu Đỉnh đã được UNESCO công nhận là Di sản Văn hóa Thế giới.",
        "history_text_en": "The Mieu (The To Temple) is located in the southwestern corner of the Hue Imperial City, dedicated to the emperors of the Nguyen Dynasty. It served as the court's ceremonial site for worshipping deceased emperors, where women including empresses were not permitted to attend. Originally this site housed Hoang Khao Temple worshipping Nguyen Phuc Con (father of Emperor Gia Long). In 1821 under Emperor Minh Mang, Hoang Khao Temple was moved 50 meters north to make way for The To Temple, built to honor Emperor Gia Long and his empress. Construction took two years (1821-1822). Initially dedicated only to Emperor Gia Long, it later became the temple for all Nguyen emperors. The rectangular grounds cover over 2 hectares, occupying 1/18 of the entire Imperial and Forbidden Purple City area. It is a massive wooden architectural work built in the overlapping-roof style on a foundation nearly 1 meter high, with a rectangular plan of 54.60m by 27.70m covering 1,500 square meters. The main hall has 9 bays with double annexes, the front hall has 11 bays with single annexes, connected by exquisitely carved crab-shell trusses. The roof is covered with yellow glazed tiles topped with a brilliant enamel tai chi emblem. Inside, besides Gia Long's altar at the center, the remaining altars are arranged according to the left-right ancestral hierarchy. Before 1958 there were only 7 altars; in October 1958 three anti-French emperors - Ham Nghi, Thanh Thai, and Duy Tan - were added. Outside, the Nine Dynastic Urns (Cuu Dinh) stand in line with the nine worship bays. Beyond rises the three-tiered Hien Lam Pavilion. The Mieu and the Nine Urns are recognized by UNESCO as World Cultural Heritage.",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.4671621,
        "longitude": 107.5767333
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace (Palace of Supreme Harmony)",
        "history_text_vi": "Điện Thái Hòa là cung điện nằm trong khu vực Đại Nội của kinh thành Huế, là nơi đăng quang của 13 vua triều Nguyễn từ Gia Long đến Bảo Đại. Trong chế độ phong kiến, cung điện này được coi là trung tâm của đất nước. Vua Gia Long khởi công xây dựng ngày 21 tháng 2 năm 1805 hoàn thành tháng 10 năm 1805. Năm 1833 vua Minh Mạng quy hoạch lại kiến trúc cung đình, dời điện về vị trí ngày nay và làm lại đồ sộ lộng lẫy hơn. Năm 1923 dưới thời Khải Định, điện được đại gia trùng kiến chuẩn bị cho lễ Tứ tuần Đại khánh tiết. Điện là biểu trưng quyền lực của Hoàng triều Nguyễn, cùng với sân chầu là địa điểm dùng cho các buổi triều nghi quan trọng như lễ Đăng Quang, sinh nhật vua, đón tiếp sứ thần và đại triều ngày mồng 1 và 15 âm lịch hàng tháng. Vào những dịp này vua ngồi uy nghiêm trên ngai vàng, chỉ các quan Tứ trụ và hoàng thân mới được vào điện, các quan khác đứng xếp hàng ở sân Đại triều. Điện được xây trên nền cao 1m, diện tích 1.360m2 với 80 cột gỗ lim sơn son thếp vàng trang trí hình rồng vờn mây. Kiến trúc theo lối trùng thiềm điệp ốc, nhà trước và nhà sau nối với nhau bằng hệ thống trần vòm mai cua dưới máng nước gọi là máng thừa lưu - một sáng tạo độc đáo. Mái điện lợp ngói hoàng lưu ly chia làm 3 tầng chồng mí gọi là mái chồng diêm. Dải cổ diêm chạy quanh bốn mặt phân ô hộc trang trí hình vẽ và 197 bài thơ trên pháp lam theo lối nhất thi nhất họa. Trang trí nổi bật với con số 5 và 9 xuất hiện ở bậc thềm, trên mái và nội điện.",
        "history_text_en": "Thai Hoa Palace is located within the Imperial City of Hue and served as the coronation site for all 13 Nguyen emperors from Gia Long to Bao Dai. During the feudal period this palace was considered the center of the nation. Emperor Gia Long began construction on February 21, 1805, completing it in October 1805. In 1833 Emperor Minh Mang reorganized the court architecture, relocating the palace to its current position with grander proportions. In 1923 under Emperor Khai Dinh, the palace underwent major reconstruction for his 40th birthday celebration. The palace symbolizes the power of the Nguyen Dynasty. Together with the audience courtyard, it hosted important court ceremonies including coronations, imperial birthdays, diplomatic receptions for envoys, and grand court sessions on the 1st and 15th of each lunar month. During these occasions the emperor sat solemnly on the golden throne; only high-ranking mandarins and royalty could enter the palace while other officials stood arranged in the Great Audience Courtyard. Built on a 1-meter-high foundation covering 1,360 square meters, the palace features 80 ironwood columns lacquered red and gilded with gold, decorated with dragons amidst clouds. The architecture follows the overlapping-roof style with front and rear halls connected by a crab-shell arched ceiling system under a water channel called the overflow gutter - a unique innovation. The roof is covered with yellow glazed tiles arranged in three overlapping tiers called the layered roof. A decorative frieze band runs around all four sides divided into compartments displaying paintings and 197 poems on enamel plaques in alternating poetry-and-painting style. The number 5 and 9 feature prominently in the staircases, roof decorations, and interior design.",
        "author": "Vua Gia Long",
        "year": 1805,
        "latitude": 16.4686747,
        "longitude": 107.578412
    },
    {
        "loc_id": 1,
        "name_vi": "Nền điện Cần Chánh",
        "name_en": "Can Chanh Palace Foundation",
        "history_text_vi": "Điện Cần Chánh trong Tử Cấm thành là nơi vua thiết triều, thường tiếp sứ bộ ngoại giao, tổ chức yến tiệc của hoàng gia và triều đình nhà Nguyễn. Về tổng thể, điện được bố trí trên trục chính của Đại Nội nằm giữa điện Thái Hòa (nơi thiết triều chính) và điện Càn Thành (nơi ở của vua). Trước điện có Sân bái mạng là nơi tập hợp văn võ bá quan khi chầu vua. Điện cùng với nhà tả vu, hữu vu họp thành bố cục kiến trúc hình chữ môn. Điện có kết cấu gỗ lớn và đẹp nhất trong Tử Cấm thành. Theo Dư địa chí Thừa Thiên-Huế, điện Cần Chánh đặt trên nền cao gần 1m, bó vỉa bằng gạch vồ và đá Thanh, diện tích gần 1.000m2. Chính điện 5 gian 2 chái kép, tiền điện 7 gian 2 chái đơn, hai bên đông tây có 4 hồi lang mỗi bên 5 gian nối qua điện Văn Minh, điện Võ Hiển và qua Tả Vu, Hữu Vu. Bộ khung gồm 80 cột bằng gỗ lim, phần lớn kết cấu gỗ đều được chạm trổ tinh xảo, công phu. Trong điện, gian giữa nhà chính đặt ngự tọa, trên các hàng cột hai bên treo những bức tranh gương thể hiện cảnh đẹp kinh đô và bản đồ các tỉnh. Điện còn là nơi trưng bày nhiều báu vật của triều Nguyễn. Điện được xây dựng năm Gia Long thứ 3 (1804), tu sửa các năm 1827, 1850, 1899. Điện đã bị phá hủy hoàn toàn vào đầu năm 1947 trong chiến dịch tiêu thổ của Việt Minh. Từ năm 1994 Trung tâm Bảo tồn di tích cố đô Huế ký kết với Đại học Waseda (Nhật Bản) nghiên cứu phục dựng. Ngày 23 tháng 11 năm 2024 dự án phục hồi chính thức khởi công với kinh phí gần 200 tỷ đồng, dự kiến hoàn thành trong 4 năm. Hiện nay chỉ còn nền móng và một số dấu tích kiến trúc.",
        "history_text_en": "Can Chanh Palace within the Forbidden Purple City was where the emperor held court, received foreign diplomatic envoys, and hosted royal banquets during the Nguyen Dynasty. The palace was positioned on the main axis of the Imperial City between Thai Hoa Palace (the main audience hall) and Can Thanh Palace (the emperor's residence). In front lay the Bai Mang Courtyard where civil and military officials assembled for audiences. The palace together with the left and right auxiliary halls formed a gate-shaped architectural layout. It had the largest and most beautiful wooden structure in the Forbidden Purple City. According to regional records, Can Chanh Palace sat on a foundation nearly 1 meter high edged with large bricks and Thanh stone covering nearly 1,000 square meters. The main hall had 5 bays with double annexes, the front hall 7 bays with single annexes, with 4 corridor galleries on each side connecting to Van Minh Palace, Vo Hien Palace, and the auxiliary halls. The frame consisted of 80 ironwood columns with most wooden components intricately carved. Inside, the imperial throne stood in the central bay, while glass paintings depicting capital landscapes and provincial maps hung on the side columns. The palace also displayed numerous Nguyen Dynasty treasures. Built in 1804 under Emperor Gia Long, it was renovated in 1827, 1850, and 1899. The palace was completely destroyed in early 1947 during the Viet Minh scorched-earth campaign. Since 1994 the Hue Monuments Conservation Center has partnered with Waseda University (Japan) for restoration research. On November 23, 2024, the restoration project officially began with a budget of nearly 200 billion VND, expected to be completed within 4 years. Currently only the foundation and some architectural traces remain.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4695281,
        "longitude": 107.5777743
    },
    {
        "loc_id": 1,
        "name_vi": "Duyệt Thị Đường",
        "name_en": "Duyet Thi Duong (Royal Theater)",
        "history_text_vi": "Duyệt Thị Đường là một nhà hát dành cho vua, hoàng thân quốc thích, các quan đại thần và là nơi biểu diễn các vở tuồng cung đình cho quan khách, sứ thần thưởng thức. Đây được xem là nhà hát cổ nhất của ngành sân khấu Việt Nam. Đây còn là nơi tổ chức các buổi lễ hội đặc biệt như dịp tứ tuần các vua Minh Mạng, Tự Đức, Đồng Khánh, Khải Định. Năm 1833 triều đình tổ chức đúc tiền Minh Mạng Phi Long ngay tại địa điểm này. Vua Minh Mạng cho xây dựng Duyệt Thị Đường vào năm Minh Mạng thứ 7 (1824-1826) nằm ở góc đông nam bên trong Tử Cấm thành trên nền cũ của nhà hát Thanh Phong Đường (1805). Nhà hát hình chữ nhật rộng rãi với bộ mái có bờ quyết cong giống đình chùa Huế, chống đỡ bởi hai hàng cột lim sơn son cao 12m, vẽ rồng ẩn mây cuốn chung quanh chia làm 2 tầng. Trên cao, mặt trời, mặt trăng, tinh tú được vẽ nổi lên trần nhà màu xanh lơ. Sân khấu chính ở giữa nhà hát, vị trí tốt nhất dành cho vua ngồi ở lầu hai. Sân khấu có ba mặt, phần tường cuối trổ hai cửa, diễn viên vào ở phía phải và ra ở phía trái. Phía trên là đài cao chia hai bậc: bậc cao nhất dành cho các bà hoàng và cung tần, bậc thấp đặt ngự tọa của vua, hai bậc ngăn bởi lớp sáo trúc thưa. Nhà hát nối liền với các cung điện bằng dãy hành lang có mái. Duyệt Thị Đường được tu bổ nhiều lần, từ 1995-2002 trùng tu phục chế hoàn chỉnh, chính thức hoạt động thường xuyên từ tháng 3/2003 phục vụ biểu diễn Nhã nhạc cung đình Huế - Di sản Văn hóa phi vật thể của nhân loại.",
        "history_text_en": "Duyet Thi Duong is a theater for the emperor, royalty, high-ranking mandarins, and served as the venue for court opera performances for guests and foreign envoys. It is considered the oldest theater in Vietnamese performing arts history. It also hosted special celebrations such as the 40th birthdays of Emperors Minh Mang, Tu Duc, Dong Khanh, and Khai Dinh. In 1833 the court minted Minh Mang Phi Long coins at this very location. Emperor Minh Mang ordered its construction in the 7th year of his reign (1824-1826) in the southeastern corner of the Forbidden Purple City on the former site of Thanh Phong Theater (1805). The rectangular theater features curved roof ridges resembling Hue pagodas, supported by two rows of 12-meter-high red-lacquered ironwood columns painted with dragons hidden in swirling clouds, dividing the space into two levels. Above, the sun, moon, and stars are painted in relief on the light blue ceiling. The main stage sits at the center, with the best viewing position reserved for the emperor on the second floor. The three-sided stage has a back wall with two doors; performers enter from the right and exit from the left. Above rises a two-tiered platform: the highest reserved for empresses and court ladies, the lower for the emperor's throne, separated by a screen of bamboo blinds. The theater connects to the palaces via a covered corridor. Duyet Thi Duong underwent multiple renovations, with complete restoration from 1995-2002, officially reopening in March 2003 to host performances of Hue Royal Court Music (Nha Nhac), a UNESCO Intangible Cultural Heritage of Humanity.",
        "author": "Vua Minh Mạng",
        "year": 1826,
        "latitude": 16.470284,
        "longitude": 107.5785163
    },
    {
        "loc_id": 1,
        "name_vi": "Phủ Nội Vụ",
        "name_en": "Phu Noi Vu (Ministry of the Interior)",
        "history_text_vi": "Phủ Nội Vụ là cơ quan coi giữ tài sản, vật dụng cho Hoàng đế và hoàng gia tại nội cung, nằm về phía Đông Bắc của Hoàng thành Huế. Đây là cơ quan coi giữ kho tàng, của công và các hạng vàng ngọc châu báu, tơ lụa trong cung, đồng thời lo việc thu phát cất trữ các vật cống tiến. Vì vậy trong Nội vụ phủ có nhiều Ty và cục thợ thủ công, còn giữ trách nhiệm quản lý và sản xuất các vật dụng cho Hoàng đế và nội cung dùng. Phủ Nội Vụ thời Nguyễn bao gồm nhiều thuộc viên và kho hàng: điều hành phủ là 1 Thị lang, 2 Lang trung với các lại viên. Chuyên quản 2 kho vàng ngọc gồm kho vàng bạc và kho châu ngọc. Chuyên quản 2 kho Cẩm ngoan gồm kho gấm vóc và kho trân ngoan (đồ quý). Chuyên quản 2 kho the lụa vật hạng. Chuyên quản 2 kho văn nhạc và 2 kho tơ lụa. Nội vụ phủ có Tiết thận ty quản lý các cục thợ như may, thêu, nhuộm, dệt. Tiền thân của Nội vụ phủ vào thời Gia Long là Nội đồ gia nằm bên trong Tử Cấm Thành. Năm Minh Mạng nguyên niên (1820), vua đổi tên Nội đồ gia thành Nội vụ phủ. Năm 1837 vua Minh Mạng cho dời phủ đến vị trí hiện tại. Năm 1906 công trình được xây dựng lại theo kiến trúc Pháp, ngày nay chỉ còn lại tòa nhà chính hai tầng sót lại sau chiến tranh, vị trí gần cửa Hiển Nhơn. Từ 1936 đến 1996 khu vực liên tục thay đổi công năng từ trụ sở tuần binh, trường Cao đẳng Nghệ thuật Huế rồi Đại học Nghệ thuật Huế. Hiện nay nơi này đang có dấu hiệu xuống cấp.",
        "history_text_en": "Phu Noi Vu (Ministry of the Interior) was the agency responsible for safeguarding the emperor's and royal family's assets and belongings within the inner court, located northeast of the Hue Imperial City. It managed the treasury, public property, gold, jewels, silks within the palace, and handled the receipt and storage of tribute items. The ministry contained numerous bureaus and artisan workshops and was responsible for producing items for the emperor and the inner court. The Nguyen Dynasty's Ministry of the Interior included many officials and warehouses: one Vice Minister and two Directors oversaw the staff. It managed two gold and jewel warehouses (gold and silver, precious stones), two fine fabric warehouses (brocade and precious items), two silk and material warehouses, two literary and musical instrument warehouses, and two raw silk warehouses. The ministry also had a bureau governing craftspeople including tailors, embroiderers, dyers, and weavers. Its predecessor during Emperor Gia Long's reign was Noi Do Gia located inside the Forbidden Purple City. In 1820 Emperor Minh Mang renamed it Noi Vu Phu. In 1837 the emperor relocated it to its current position. In 1906 the building was reconstructed in French architectural style; today only the two-story main building survives post-war, near Hien Nhon Gate. From 1936 to 1996 the site underwent various transformations: guard headquarters, Hue College of Arts, then Hue University of Arts. Currently the building shows signs of deterioration.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.470755,
        "longitude": 107.5796368
    },
    {
        "loc_id": 1,
        "name_vi": "Vườn Cơ Hạ",
        "name_en": "Co Ha Garden (Imperial Garden)",
        "history_text_vi": "Vườn Cơ Hạ là một trong 5 khu vườn ngự uyển nằm bên trong Hoàng thành Huế, tọa lạc ở góc đông bắc, rộng gần 5 mẫu (2,3ha), trước giáp phủ Nội Vụ, sau giáp Hậu hồ, hai mặt đông tây giáp tường Hoàng thành và Tử cấm thành. Tên Cơ Hạ được lấy từ ý Vạn Cơ Thanh Hạ nghĩa là sự bình an, an nhàn trong mọi cơ sự. Vườn mang phong cách riêng hoàn toàn khác biệt với các khu vườn còn lại trong cung. Cổng chính xây mặt về phía nam mang tên Thượng Uyển môn. Trong cửa là điện Khâm Văn lợp ngói lưu li vàng. Sau điện là Minh Hồ, giữa hồ dựng Quang Biểu các, phía sau có Thưởng Thắng lâu. Bên trái lầu có nhà Hòa Phong tạ, bên phải có hành lang Khả Nguyệt, bao quanh có hồi lang Tứ Phương Ninh Mật. Phía đông có Minh Lý Thư Trai, phía tây có Nhật Thận hiên. Ban đầu vườn là nơi học tập của Thái tử Nguyễn Phúc Đảm (tức vua Minh Mạng sau này). Năm Minh Mạng thứ 18 (1837) khu vực được sửa sang mở rộng nối tiếp với Hậu Hồ với chức năng Ngự viên. Năm Thiệu Trị thứ 3 (1843) nhà vua cho dựng thêm các đình viện đài tạ, nâng cấp thành vườn thượng uyển. Vua Thiệu Trị đã đề vịnh về vườn với 14 cảnh khác nhau như Điện khai văn yến, Lâu thưởng Bồng doanh, Các minh tứ chiếu, Lang tập quần phương. Thời Tự Đức bổ sung thêm một số công trình. Năm 2012 sau thời gian dài hoang phế, vườn được Trung tâm Bảo tồn Di tích Cố đô Huế phục hồi nhân dịp Festival Huế. Năm 2013-2014 UBND tỉnh Thừa Thiên Huế tôn tạo mở rộng lại Cơ Hạ viên.",
        "history_text_en": "Co Ha Garden is one of five imperial gardens within the Hue Imperial City, located in the northeastern corner covering nearly 5 mau (2.3 hectares), adjacent to Phu Noi Vu to the front, Hau Ho Pond to the rear, and bordered by the Imperial City and Forbidden Purple City walls on the east and west sides. The name Co Ha derives from 'Van Co Thanh Ha,' meaning peace and leisure amidst all affairs. The garden has a distinctive style completely different from other palace gardens. The main gate faces south, named Thuong Uyen Mon. Inside stands Kham Van Hall with yellow glazed tiles. Behind lies Minh Ho Pond with Quang Bieu Pavilion at its center, and further back Thuong Thang Pavilion. To the left stands Hoa Phong Pavilion, to the right Kha Nguyet Corridor, surrounded by the Tu Phuong Ninh Mat encircling corridor. Minh Ly Thu Trai study hall lies to the east, Nhat Than Hien to the west. Originally it was the study place of Crown Prince Nguyen Phuc Dam (later Emperor Minh Mang). In 1837 the area was renovated and expanded connecting to Hau Ho Pond as an imperial garden. In 1843 Emperor Thieu Tri added more pavilions and terraces, elevating it to an imperial garden. Emperor Thieu Tri composed poems about the garden praising 14 different scenes. Under Emperor Tu Duc additional structures were added. In 2012 after a long period of abandonment, the garden was restored by the Hue Monuments Conservation Center for the Hue Festival. In 2013-2014 Thua Thien Hue province renovated and expanded Co Ha Garden.",
        "author": "Vua Thiệu Trị",
        "year": 1847,
        "latitude": 16.4717727,
        "longitude": 107.5788666
    },
    {
        "loc_id": 1,
        "name_vi": "Triệu Miếu (Triệu Tổ Miếu)",
        "name_en": "Trieu Mieu (Trieu To Temple)",
        "history_text_vi": "Triệu Tổ miếu là một công trình kiến trúc trong Hoàng thành Huế thờ Nguyễn Kim - thân sinh của chúa Tiên Nguyễn Hoàng. Nguyễn Kim bị hàng tướng nhà Mạc là Dương Chấp Nhất đầu độc chết. Ông được triều Nguyễn truy tôn miếu hiệu là Triệu Tổ. Miếu nằm ở phía bắc của Thái miếu, được xây dựng năm Gia Long thứ 3 (1804). Miếu được xây trong khuôn viên hình chữ nhật, tường phía nam gắn liền với tường Thái miếu. Về hình thức và quy mô kiến trúc, Triệu miếu tương tự như Hưng miếu, gồm 1 tòa điện chính theo lối nhà kép, chính đường 3 gian 2 chái, tiền đường 5 gian 2 chái đơn. Miếu thờ chính có diện tích 540m2, được xây theo kiểu nhà kép trùng thiềm điệp ốc. Mái lợp ngói âm dương hoàng lưu ly. Bờ mái, tường cổ diềm được đắp nổi phù điêu có gắn mảnh sành sứ. Các cấu kiện gỗ được sơn son truyền thống, hoa văn họa tiết được thếp vàng. Hai bên điện chính có Thần Khố (phía đông) và Thần Trù (phía tây). Mỗi năm tổ chức 5 lần tế tương tự như ở Thái miếu. Năm 1989 do Thái Miếu xuống cấp nặng nên Triệu miếu trở thành nơi thờ chung cho 9 chúa Nguyễn. Hơn 200 năm tồn tại, với tác động của thời tiết và chiến tranh, Triệu miếu xuống cấp nghiêm trọng. Bộ Ngoại giao Hoa Kỳ viện trợ 700.000 USD cho dự án bảo tồn tu bổ. Dự án có tổng vốn 16 tỷ đồng thực hiện từ tháng 10/2014 đến tháng 1/2017. Ngày 15 tháng 9 năm 2016 khánh thành công trình bảo tồn tu bổ sau 27 tháng thi công.",
        "history_text_en": "Trieu To Temple is an architectural monument within the Hue Imperial City dedicated to Nguyen Kim, father of Lord Nguyen Hoang, the first Nguyen lord. Nguyen Kim was poisoned by Mac dynasty defector Duong Chap Nhat. He was posthumously honored by the Nguyen Dynasty with the temple name Trieu To. The temple is located north of Thai Mieu, built in 1804 under Emperor Gia Long within a rectangular compound whose southern wall adjoins that of Thai Mieu. In form and scale Trieu Mieu resembles Hung Mieu, featuring a main double-style hall with a 3-bay 2-annex main chamber and 5-bay 2-annex front hall. The main worship hall covers 540 square meters built in the overlapping-roof double style. The roof is covered with yellow glazed yin-yang tiles. Roof edges and decorative frieze walls feature relief carvings embedded with ceramic fragments. Wooden components are traditionally lacquered red with gold-gilded decorative patterns. Flanking the main hall are the Spirit Warehouse (east) and Spirit Kitchen (west). Five annual ceremonies were held here similar to those at Thai Mieu. In 1989 due to Thai Mieu's severe deterioration, Trieu Mieu became the shared worship site for all nine Nguyen Lords. After over 200 years of existence affected by weather and war, Trieu Mieu had seriously deteriorated. The US Department of State granted $700,000 for a conservation and restoration project. The total project cost was 16 billion VND, carried out from October 2014 to January 2017. The restoration was inaugurated on September 15, 2016 after 27 months of construction.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4701907,
        "longitude": 107.5801058
    },
    {
        "loc_id": 1,
        "name_vi": "Thái Miếu (Thái Tổ Miếu)",
        "name_en": "Thai Mieu (Thai To Temple)",
        "history_text_vi": "Thái Tổ miếu là miếu thờ các vị chúa Nguyễn trong lịch sử Việt Nam, từ chúa Nguyễn Hoàng đến chúa Nguyễn Phúc Thuần. Miếu được xây dựng từ năm Gia Long thứ ba (1804) ở góc đông nam trong Hoàng thành Huế, đối xứng với Thế Tổ miếu ở hướng tây nam. Tổng thể di tích Thái Miếu là một tổ hợp kiến trúc lớn với trên 10 hạng mục công trình nằm trong khuôn viên tổng diện tích 14.904m2. Chính điện Thái Miếu là ngôi nhà bằng gỗ lớn nhất trong tất cả các cung điện được xây dựng dưới triều Nguyễn, một công trình kiến trúc gỗ gần tương tự như Thế miếu. Thái miếu theo lối nhà kép trùng thiềm điệp ốc, chính đường 13 gian 2 chái kép, tiền đường 15 gian 2 chái đơn. Phía đông chính điện là điện Long Đức, phía tây là Thổ Công tử, phía đông nam có điện Chiêu Kính, đối diện ở phía tây là điện Mục Tư, phía bắc chính điện là Triệu Tổ miếu. Trước sân Thái miếu có Tuy Thành các 3 tầng hình thức tương tự gác Hiển Lâm ở Thế miếu. Phía nam gác Tuy Thành các có nhà Tả tùng tự và Hữu tùng tự. Toàn bộ khu vực có tường gạch bao bọc, trổ 5 cửa ra các phía. Trong kháng chiến chống Pháp đầu năm 1947, khu vực Thái miếu bị Việt Minh thiêu hủy hoàn toàn trong đợt tiêu thổ kháng chiến. Năm 1971-1972, Hội đồng Nguyễn Phúc tộc và đức Từ Cung quyên góp dựng lại một tòa nhà 5 gian trên nền cũ. Tháng 10 năm 2024, Trung tâm Bảo tồn Di tích Cố đô Huế khởi công tu bổ phục hồi với kinh phí 52 tỉ đồng, dự kiến hoàn tất năm 2028.",
        "history_text_en": "Thai To Temple is dedicated to the Nguyen Lords in Vietnamese history, from Lord Nguyen Hoang to Lord Nguyen Phuc Thuan. Built in 1804 under Emperor Gia Long in the southeastern corner of the Hue Imperial City, it stands symmetrically with The To Temple in the southwest. The Thai Mieu complex is a large architectural ensemble with over 10 structures within a total area of 14,904 square meters. The main hall of Thai Mieu is the largest wooden building among all palaces built during the Nguyen Dynasty, with wooden architecture similar to The Mieu. Thai Mieu follows the double overlapping-roof style with a 13-bay double-annex main hall and a 15-bay single-annex front hall. To the east stands Long Duc Hall, to the west Tho Cong Shrine, to the southeast Chieu Kinh Hall, opposite to the west is Muc Tu Hall, and to the north of the main hall is Trieu To Temple. In front of the courtyard stands Tuy Thanh Pavilion, three tiers high resembling Hien Lam Pavilion at The Mieu. South of Tuy Thanh are the Left and Right Auxiliary Houses. The entire complex is enclosed by brick walls with five gates on various sides. During the anti-French resistance in early 1947, the Thai Mieu area was completely burned by the Viet Minh in the scorched-earth campaign. In 1971-1972, the Nguyen Phuc Clan Council and Empress Tu Cung raised funds to build a 5-bay structure on the old foundation. In October 2024 the Hue Monuments Conservation Center began restoration work with a budget of 52 billion VND, expected to be completed in 2028.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4699109,
        "longitude": 107.5803246
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Hiển Nhơn",
        "name_en": "Hien Nhon Gate (Gate of Manifest Benevolence)",
        "history_text_vi": "Cửa Hiển Nhơn là một trong bốn cửa chính của Hoàng thành Huế, nằm ở phía Đông trên trục đường Đoàn Thị Điểm. Công trình này được đánh giá là một trong những lối vào có nghệ thuật khảm sành sứ tinh xảo và đẹp mắt nhất cung đình Huế. Cửa được khởi công vào năm 1805 và hoàn thành năm 1808 dưới thời vua Gia Long. Năm 1833 thời vua Minh Mạng, cửa được đắp ghép thêm các mảnh sành sứ trang trí. Năm 1923 thời vua Khải Định, công trình được cải tạo lớn để có diện mạo như ngày nay. Cửa bị bom đạn phá hủy hoàn toàn vào năm 1968. Sau năm 1975 công trình được trùng tu và khôi phục nguyên trạng. Theo luật lệ triều Nguyễn, cửa Hiển Nhơn là lối đi dành riêng cho quan lại và nam nhân ra vào Hoàng thành, đối lập với cửa Chương Đức ở phía Tây dành cho nữ giới. Ngày nay cửa được sử dụng làm lối ra chính cho du khách sau khi kết thúc lộ trình tham quan Đại Nội Huế. Cửa được xây dựng theo lối vọng lâu tam quan với 3 lối đi thông nhau, lối giữa lớn nhất dành cho người có chức vụ cao hơn. Toàn bộ bề mặt cửa được trang trí dày đặc bằng kỹ thuật khảm sành sứ và thủy tinh màu. Các nghệ nhân đã tạo hình vô số họa tiết điển tích, hoa lá, mây trời và các linh vật cung đình rất sống động. Phía trước cửa có đôi nghê đá đen cổ uy nghiêm trấn giữ cung cấm, mang đậm bản sắc mỹ thuật thuần Việt. Vị trí: đường Đoàn Thị Điểm, phường Thuận Thành, TP. Huế.",
        "history_text_en": "Hien Nhon Gate is one of the four main gates of the Hue Imperial City, located on the eastern side along Doan Thi Diem Street. This structure is considered one of the most exquisitely decorated entrances with intricate ceramic mosaic art in Hue court architecture. Construction began in 1805 and was completed in 1808 under Emperor Gia Long. In 1833 under Emperor Minh Mang, additional ceramic shard decorations were applied. In 1923 under Emperor Khai Dinh, the gate underwent major renovation to achieve its present appearance. The gate was completely destroyed by bombs in 1968 and was fully restored after 1975. According to Nguyen Dynasty regulations, Hien Nhon Gate was the passage reserved for male officials entering and leaving the Imperial City, contrasting with Chuong Duc Gate on the western side which was reserved for women. Today it serves as the main exit for visitors after completing their tour of the Imperial City. The gate is built in the three-portal watchtower style with three interconnected passages, the central one being the largest for higher-ranking individuals. The entire surface is densely decorated with ceramic and colored glass mosaic technique. Artisans created numerous lively motifs depicting historical scenes, flowers, clouds, and court mythical creatures. In front stand a pair of majestic ancient black stone guardian lions (nghe) embodying pure Vietnamese artistic identity. Location: Doan Thi Diem Street, Thuan Thanh Ward, Hue City.",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4707473,
        "longitude": 107.5805514
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Long An (Bảo tàng Cổ vật Cung đình Huế)",
        "name_en": "Long An Palace (Hue Royal Antiquities Museum)",
        "history_text_vi": "Bảo tàng Cổ vật Cung đình Huế là viện bảo tàng trực thuộc Trung tâm bảo tồn di tích cố đô Huế. Tòa nhà chính là điện Long An xây năm 1845 dưới thời vua Thiệu Trị, bằng gỗ với 128 cây cột gỗ quý, trên các cột có hình chạm khắc tứ linh long-li-quy-phụng và hơn 1.000 bài thơ bằng chữ Hán. Điện Long An là một tòa nhà thuộc hệ thống kiến trúc cung Bảo Định, nằm ở bờ bắc sông Ngự Hà trong Kinh thành. Đây là một dạng biệt cung của vua Thiệu Trị, là nơi nghỉ của vua sau lễ Tịch điền đầu xuân. Năm 1847 vua Thiệu Trị thăng hà, hệ thống cung Bảo Định được giữ nguyên để thờ vua. Năm 1909 dưới thời vua Duy Tân, điện Long An được dựng lại làm thư viện cho trường Quốc Tử Giám với tên mới là Tân Thơ Viện. Ngày 24/8/1923 Khâm sứ Trung Kỳ Pierre Pasquier và vua Khải Định ban sắc lệnh thành lập bảo tàng, dùng tòa nhà làm nhà trưng bày hiện vật của Hội Đô Thành Hiếu Cổ. Hiện bảo tàng trưng bày hơn 300 hiện vật bằng vàng, sành, sứ, pháp lam Huế, ngự y và ngự dụng, trang phục hoàng thất. Bảo tàng lưu giữ khoảng 9.000 cổ vật cung đình triều Nguyễn, gần 100 cổ vật Champa và quản lý gần 3.000 cổ vật khác đang trưng bày tại các cung điện lăng tẩm. Có những sưu tập giá trị như sưu tập vạc đồng thời chúa Nguyễn, đồ sứ ký kiểu thời Nguyễn, pháp lam Huế, trang phục cung đình, đồ gỗ sơn son thếp vàng, nhạc cụ Nhã nhạc cung đình Huế, súng thần công. Nhiều cổ vật được công nhận là Bảo vật quốc gia.",
        "history_text_en": "The Hue Royal Antiquities Museum is under the management of the Hue Monuments Conservation Center. The main exhibition building is Long An Palace, built in 1845 under Emperor Thieu Tri, constructed of wood with 128 precious timber columns carved with the four sacred animals (dragon, unicorn, tortoise, phoenix) and over 1,000 Chinese-character poems. Long An Palace belonged to the Bao Dinh architectural complex, located on the northern bank of the Ngu Ha River within the Citadel. It served as the emperor's retreat palace after the spring plowing ceremony. After Emperor Thieu Tri's death in 1847, Bao Dinh complex was preserved for his worship. In 1909 under Emperor Duy Tan, Long An Palace was reconstructed as a library for the Quoc Tu Giam academy, renamed Tan Thu Vien. On August 24, 1923, French Resident Superior Pierre Pasquier and Emperor Khai Dinh issued a decree establishing a museum, using the building to display artifacts of the Hue Antiquarian Society. Currently the museum displays over 300 artifacts in gold, ceramic, porcelain, Hue enamelware, imperial medicine, royal utensils, and Nguyen royal costumes. The museum preserves approximately 9,000 Nguyen court artifacts, nearly 100 Champa artifacts, and manages nearly 3,000 other artifacts displayed at various palaces, tombs, and temples. Valuable collections include bronze cauldrons from the Nguyen Lord period, commissioned porcelain from the Nguyen Dynasty, Hue enamelware, court costumes, gold-lacquered wooden artifacts, Hue Royal Court musical instruments, and cannons. Many artifacts are recognized as National Treasures of Vietnam.",
        "author": "Vua Thiệu Trị",
        "year": 1845,
        "latitude": 16.4712819,
        "longitude": 107.5818602
    },
    {
        "loc_id": 1,
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate (Meridian Gate)",
        "history_text_vi": "Ngọ Môn là cổng chính phía nam của Hoàng thành Huế, có nghĩa là cổng tý ngọ hướng về phía nam. Hướng này gắn liền với quan niệm Thánh nhân Nam diện nhi thính thiên hạ (Thiên tử phải quay về hướng Nam để cai trị thiên hạ). Ngọ Môn là cổng lớn nhất trong 4 cổng chính của Hoàng thành, chỉ dành riêng cho vua đi lại hoặc dùng khi tiếp đón sứ thần. Trước kia tại vị trí này là Nam Khuyết Đài xây dựng đầu thời Gia Long, trên đài có điện Càn Nguyên, hai bên có Tả Đoan Môn và Hữu Đoan Môn. Năm Minh Mạng thứ 14 (1833) Nam Khuyết Đài giải thể hoàn toàn để xây Ngọ Môn. Ngọ Môn có hai phần chính: đài cổng và lầu Ngũ Phụng. Phần đài cổng có bình diện hình chữ U vuông góc, đáy dài 57,77m, cạnh bên dài 27,6m. Đài xây bằng gạch đá kết hợp dầm chịu lực bằng đồng thau, cao gần 5m, diện tích hơn 1.560m2. Thân đài trổ 5 lối đi: lối chính giữa là Ngọ Môn dành cho vua, hai lối bên Tả Giáp Môn và Hữu Giáp Môn dành cho quan văn, võ, hai lối ngoài cùng là Tả Dịch Môn và Hữu Dịch Môn dành cho binh lính và voi ngựa. Lầu Ngũ Phụng ở phía trên đài cổng, có hai tầng kết cấu khung gỗ lim với 100 cây cột. Mái tầng dưới nối liền nhau chạy vòng quanh che hồi lang. Mái tầng trên chia 9 bộ với nhiều hình chim phụng trang trí, bộ mái chính giữa lợp ngói lưu ly màu vàng, tám bộ còn lại lợp ngói lưu ly màu xanh. Ngọ Môn là nơi chứng kiến nhiều sự kiện lịch sử quan trọng. Ngày 30 tháng 8 năm 1945 tại cửa Ngọ Môn, vua Bảo Đại vị vua cuối cùng đọc Tuyên ngôn Thoái vị và trao chính quyền cho chính phủ lâm thời Việt Nam Dân chủ Cộng hòa. Sau trận Mậu Thân 1968 Ngọ Môn hư hỏng nặng. Năm 1970 được sửa chữa lớn. Huế đã chi 80 tỷ đồng để trùng tu hoàn thành tổng thể vào năm 2019.",
        "history_text_en": "Ngo Mon Gate is the main southern gate of the Hue Imperial City, with 'Ngo Mon' meaning the noon gate facing south. This direction embodies the Confucian concept that 'the Sage faces south to govern the realm'. Ngo Mon is the largest among the four main gates and was reserved exclusively for the emperor's passage or for receiving foreign envoys. Previously, the Southern Bastion stood here built during early Gia Long reign, topped with Can Nguyen Hall flanked by Ta Doan Mon and Huu Doan Mon gates. In 1833 under Emperor Minh Mang, the Southern Bastion was completely demolished for Ngo Mon's construction. Ngo Mon has two main parts: the gate platform and the Five Phoenix Pavilion. The gate platform has a U-shaped plan with a 57.77m long base and 27.6m side wings. Built of brick and stone with brass load-bearing beams, it stands nearly 5m high covering over 1,560 square meters. Five passageways pierce the body: the central Ngo Mon for the emperor, two side gates (Left and Right Giap Mon) for civil and military mandarins, and two outermost gates (Left and Right Dich Mon) for soldiers, elephants, and horses. The Five Phoenix Pavilion atop the platform features two levels with a frame of 100 ironwood columns. The lower roof connects in a continuous ring sheltering the surrounding corridors. The upper roof divides into nine sections decorated with phoenix figures, the central section covered with yellow glazed tiles and the remaining eight with green glazed tiles on the ancient building. Ngo Mon witnessed many important historical events. On August 30, 1945, at Ngo Mon Gate, Emperor Bao Dai - the last emperor - read the Abdication Proclamation and handed over power to the Provisional Government of the Democratic Republic of Vietnam. After the 1968 Tet Offensive Ngo Mon was severely damaged. Major repairs were carried out in 1970. Hue spent 80 billion VND on restoration, completed in 2019.",
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
