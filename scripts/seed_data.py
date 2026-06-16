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

from sqlalchemy import select, and_
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
        "history_text_vi": (
            "Cửa Hòa Bình là cánh cổng phía Bắc của Hoàng thành Huế, lặng lẽ nép mình bên dòng sông Hương thơ mộng. "
            "Dưới thời vua Gia Long, cửa mang tên Củng Thần — một cái tên đầy vẻ thần bí và uy nghi, gợi nhắc về chốn thâm nghiêm của hoàng cung. "
            "Nhưng đến năm 1833, vua Minh Mạng cho đại trùng tu và đổi tên thành Hòa Bình, gửi gắm khát vọng thiên hạ thái bình, quốc thái dân an. "
            "Không giống như Ngọ Môn ồn ào nơi cửa chính, Cửa Hòa Bình khoác lên mình một vẻ đẹp trầm mặc, cổ kính, như một cụ già hiền từ đang kể chuyện xưa. "
            "Cánh cổng này từng là lối đi riêng của các cung tần, mỹ nữ và thái giám trong hoàng cung — những bóng hồng khuất nẻo sau bức tường thành cao vời vợi. "
            "Những gánh hàng lương thực, nhu yếu phẩm cũng lặng lẽ qua đây để nuôi sống cuộc sống xa hoa bên trong Tử Cấm Thành. "
            "Kiến trúc cửa gồm phần nền đài vững chãi xây bằng gạch đá kết hợp với phần lầu canh hai tầng tao nhã phía trên, "
            "với những mái ngói cong cong uyển chuyển và những đường nét chạm khắc tinh xảo trên gỗ. "
            "Bước qua cửa, bạn sẽ cảm nhận ngay sự chuyển giao giữa không gian sầm uất bên ngoài và thế giới tĩnh lặng, linh thiêng bên trong. "
            "Những viên gạch rêu phong dưới chân đã chứng kiến bao cuộc chiến tranh, bao đổi thay của thời cuộc mà vẫn đứng đó, kiên cường và bền bỉ. "
            "Bạn có để ý thấy những đường nét chạm khắc trên mái không? Mỗi họa tiết hoa lá, mỗi đường cong mái ngói đều mang một triết lý phong thủy sâu xa, "
            "kể cho chúng ta nghe về quan niệm vũ trụ của người xưa. Hãy thử tưởng tượng một buổi chiều tà, ánh hoàng hôn nhuộm vàng cánh cổng, "
            "tiếng chuông chùa vọng ra từ xa — có gì đó bình yên đến lạ thường giữa chốn kinh kỳ náo nhiệt này. "
            "Cổng còn có một vẻ đẹp rất riêng vào những ngày mưa bay, khi những hạt mưa nhẹ rơi trên mái ngói rêu phong tạo nên một bản nhạc dịu dàng của quá khứ. "
            "Người Huế xưa có câu: 'Cửa Hòa Bình mở ra, gió sông Hương thổi vào mát rượi' — như một lời chào đón ân tình từ cố đô. "
            "Hãy dành chút thời gian đứng lại đây, hít hà không khí trong lành và để tâm hồn mình hòa vào nhịp điệu chậm rãi của Huế, "
            "nơi quá khứ và hiện tại cùng tồn tại trong một khoảnh khắc giao hòa kỳ diệu."
        ),
        "history_text_en": (
            "Hoa Binh Gate (Gate of Peace) is the northern entrance to the Imperial City, quietly nestled by the poetic Perfume River. "
            "Under Emperor Gia Long, it was called Cung Than Gate — a name wrapped in mystery and majesty, evoking the solemn depths of the royal citadel. "
            "But in 1833, Emperor Minh Mang undertook a major renovation and renamed it Gate of Peace, expressing his profound wish for national peace and prosperity. "
            "Unlike the grand Ngo Mon Gate in the south, Hoa Binh Gate carries a quiet, ancient beauty, like a wise old storyteller whispering tales of bygone days. "
            "This gate was once the discreet passage for palace maids, concubines, and eunuchs entering and leaving the royal court — "
            "those unseen figures whose lives unfolded behind the towering crimson walls. "
            "It was also the route for transporting daily necessities — rice, silk, firewood, and fresh produce — that sustained the luxurious life within the Forbidden Purple City. "
            "The architecture features a solid brick-and-stone foundation supporting an elegant two-story watchtower above, "
            "with gracefully curved roofs and intricate wood carvings that speak of meticulous craftsmanship. "
            "As you step through this gate, you immediately feel the transition: from the bustling city outside to the sacred, serene world within. "
            "The moss-covered bricks beneath your feet have witnessed countless wars and dynastic changes, yet they still stand, resilient and timeless. "
            "Have you noticed the intricate carvings on the roof? Each floral motif, each graceful curve of the glazed tiles carries a deep feng shui philosophy, "
            "telling stories about how the ancient Vietnamese perceived the universe. "
            "Imagine a late afternoon here, the golden sunset casting long shadows across the gate, temple bells ringing softly in the distance — "
            "there is something incredibly peaceful about this place, a serenity that feels almost out of time. "
            "On drizzly days, when raindrops gently fall upon the mossy roof tiles, the gate seems to sing its own melancholic melody of centuries past. "
            "The old Hue saying goes: 'When Hoa Binh Gate opens, the river breeze brings cool comfort' — a warm invitation from the ancient capital. "
            "Take a moment to stand here, breathe in the fresh air, and let your soul merge with Hue's gentle rhythm, "
            "where past and present coexist in a single magical moment of harmony."
        ),
        "author": "Triều Nguyễn",
        "year": 1804,
        "latitude": 16.4721279,
        "longitude": 107.5762716
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Kiến Trung",
        "name_en": "Kien Trung Palace",
        "history_text_vi": (
            "Điện Kiến Trung tọa lạc ở điểm cực Bắc của trục thần đạo xuyên suốt Tử Cấm Thành, được vua Khải Định cho xây dựng từ năm 1921 đến 1923. "
            "Trước khi có điện này, nơi đây từng là lầu Minh Viễn thời Minh Mạng (1827-1876) rồi lầu Du Cửu thời Đồng Khánh (1913-1916), "
            "nhưng vua Khải Định đã cho triệt giải hoàn toàn để xây một tòa cung điện mới, làm nơi sinh hoạt và làm việc của mình. "
            "Điện Kiến Trung là đỉnh cao của phong cách kiến trúc Đông Dương, pha trộn hài hòa giữa kiến trúc Baroque, Phục Hưng của châu Âu với nét cổ truyền Việt Nam. "
            "Mặt tiền được trang trí bằng những mảnh gốm sứ nhiều màu tinh xảo, tạo nên một vẻ đẹp sang trọng và độc đáo. "
            "Tầng chính trổ 13 cửa hiên, tầng trên là gác mái ngói có lan can trang trí theo phong cách Việt Nam. "
            "Trước điện là vườn cảnh với ba cầu thang đắp rồng uốn lượn dẫn lên thềm điện. "
            "Đây là nơi ở của hai vị vua cuối cùng triều Nguyễn: Khải Định và Bảo Đại. Chính tại đây, Hoàng hậu Nam Phương đã hạ sinh Thái tử Bảo Long vào ngày 4 tháng 1 năm 1936. "
            "Ngày 11 tháng 3 năm 1945, vua Bảo Đại triệu cố vấn tối cao Nhật Bản là đại sứ Yokoyama vào điện này để tuyên bố nước Việt Nam độc lập. "
            "Tháng 8 năm 1945, vua Bảo Đại đã tiếp phái đoàn Chính phủ Lâm thời tại điện để trao ấn kiếm thoái vị, khép lại hơn 143 năm trị vì của triều Nguyễn. "
            "Điện bị phá hủy tháng 2 năm 1947 trong chiến dịch tiêu thổ kháng chiến, và được phục dựng hoàn thành vào năm 2024 với kinh phí hơn 123 tỉ đồng. "
            "Hãy nhìn lên những mái ngói lưu ly kia — chúng đã được các nghệ nhân phục dựng tỉ mỉ dựa trên những bức ảnh tư liệu từ thập niên 1920. "
            "Quá trình phục dựng kéo dài nhiều năm với sự hợp tác của các nhà nghiên cứu lịch sử, văn hóa và mỹ thuật Huế, "
            "cùng với sự tham gia của Phân viện khoa học công nghệ xây dựng Miền Trung. "
            "Hôm nay, bạn đang đứng trước một kỳ tích phục dựng đầy cảm động — một công trình đã sống lại từ đống tro tàn."
        ),
        "history_text_en": (
            "Kien Trung Palace sits at the northernmost point of the spiritual axis running through the Forbidden Purple City, "
            "built from 1921 to 1923 under Emperor Khai Dinh. "
            "Before this palace, the site housed Minh Vien Pavilion (from Minh Mang's reign, 1827-1876) and then Du Cuu Pavilion (from Dong Khanh's reign, 1913-1916), "
            "but Emperor Khai Dinh demolished them to build an entirely new palace as his residence and workplace. "
            "Kien Trung represents the pinnacle of Indochinese architecture, blending European Baroque and Renaissance styles with traditional Vietnamese elements. "
            "Its facade is adorned with colorful ceramic mosaics, creating a uniquely elegant appearance. "
            "The main floor features 13 arched windows, while the upper level is a traditional Vietnamese tiled roof with decorative railings. "
            "In front of the palace lies a landscaped garden with three dragon-carved staircases leading up to the main hall. "
            "This palace was home to the last two Nguyen emperors: Khai Dinh and Bao Dai. It was here that Empress Nam Phuong gave birth to Crown Prince Bao Long on January 4, 1936. "
            "On March 11, 1945, Emperor Bao Dai summoned Japanese Supreme Advisor Ambassador Yokoyama to this very palace to declare Vietnam's independence. "
            "In August 1945, Emperor Bao Dai received the Provisional Government delegation at this palace to hand over the royal seal and sword, "
            "ending 143 years of Nguyen rule. "
            "The palace was destroyed in February 1947 during the scorched-earth resistance campaign and was meticulously restored, reopening in 2024 at a cost of over 123 billion VND. "
            "Look up at those glazed tiles — master craftsmen recreated them from archival photographs dating back to the 1920s. "
            "The restoration took many years with collaboration from historians, cultural researchers, and architectural experts across Vietnam, "
            "along with the Institute of Construction Science and Technology of Central Vietnam. "
            "Today, you are standing before a moving testament to cultural resurrection — a magnificent palace reborn from the ashes of war."
        ),
        "author": "Vua Khải Định",
        "year": 1921,
        "latitude": 16.4710479,
        "longitude": 107.5765559
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Trường Sanh",
        "name_en": "Truong Sanh Palace (Palace of Longevity)",
        "history_text_vi": (
            "Cung Trường Sanh tọa lạc ở phía Tây Bắc Hoàng thành, được xây dựng năm 1821 dưới triều vua Minh Mạng với tên gọi ban đầu là Cung Trường Ninh. "
            "Với tổng diện tích lên đến 11.400m², nơi đây là một quần thể kiến trúc gồm nhiều tòa nhà, hồ nước và vườn cảnh hài hòa. "
            "Ban đầu cung được xây dựng như một hoa viên, nơi các vua Nguyễn mời mẹ mình đến thăm thú, du ngoạn. "
            "Về sau, cung trở thành nơi ăn ở của các bà Hoàng thái hậu và Thái hoàng thái hậu, như bà Lệ Thiên Anh (vợ vua Tự Đức), "
            "bà Từ Minh (vợ vua Dục Đức), bà Tiên Cung (vợ vua Đồng Khánh). "
            "Vua Thiệu Trị đã từng xếp cảnh quan nơi đây là một trong 20 thắng cảnh đẹp nhất kinh đô Huế, "
            "với bài thơ 'Trường Ninh Thùy Điếu' thuộc tập 'Thần kinh nhị thập cảnh' ca ngợi vẻ đẹp nên thơ. "
            "Kiến trúc chính của cung xếp theo hình chữ Vương (王), gồm điện Thọ Khang đặt chính giữa, "
            "nhà Ngũ Đại Đồng Đường phía trước và lầu Vạn Phước phía sau, "
            "nối kết với nhau bằng hệ thống hành lang dài có mái che. "
            "Điểm nhấn đặc biệt là lạch nước Đào Nguyên nhân tạo uốn lượn quanh cung, bắc qua những cây cầu đỏ duyên dáng. "
            "Phía trước còn có những núi giả sơn mang tên Bảo Sơn, Kình Ngư, Hổ Tôn làm hậu chẩm cho toàn bộ không gian. "
            "Cung quay mặt về hướng Đông, cửa chính gọi là Trường An môn xây theo lối tam quan, trang trí đề tài hoa lá ngũ sắc. "
            "Năm 1923, vua Khải Định cho tu bổ cung và đổi tên thành Trường Sanh. "
            "Dự án phục hồi năm 2005-2007 với kinh phí gần 30 tỷ đồng đã phục dựng lạch Đào Nguyên, hồ Tân Nguyệt và các non bộ. "
            "Hãy thử tưởng tượng một buổi chiều hoàng hôn, các bà Hoàng thái hậu dạo bước bên hồ, ngắm nhìn những đóa sen nở — "
            "thật thanh bình và nên thơ biết bao giữa chốn hoàng cung lộng lẫy này."
        ),
        "history_text_en": (
            "Truong Sanh Palace is located in the northwest corner of the Imperial City, built in 1821 under Emperor Minh Mang, originally named Truong Ninh Palace. "
            "Covering an area of 11,400 square meters, it comprises multiple buildings, ponds, and gardens in perfect harmony. "
            "Initially designed as an imperial garden where Nguyen emperors invited their mothers for leisure outings, "
            "it later became the residence for Queen Mothers and Empress Dowagers such as Le Thien Anh (wife of Emperor Tu Duc), "
            "Tu Minh (wife of Emperor Duc Duc), and Tien Cung (wife of Emperor Dong Khanh). "
            "Emperor Thieu Tri ranked its landscape among the 20 most beautiful scenic spots in the capital Hue, "
            "composing the poem 'Truong Ninh Thuy Dieu' in his collection 'Than kinh nhi thap canh' to celebrate its charm. "
            "The palace's main architecture follows the shape of the Chinese character 'Vuong' (King), "
            "with Tho Khang Hall at the center, Ngu Dai Dong Duong House in front, and Van Phuoc Tower behind, "
            "all connected by long covered corridors. "
            "A special highlight is the artificial Peach Spring stream winding through the palace grounds, crossed by elegant red bridges. "
            "In front stand miniature mountains named Bao Son, Kinh Ngu, and Ho Ton, serving as the rear support in feng shui layout. "
            "The palace faces east, with its main gate called Truong An Mon built in the three-arched style, decorated with five-color floral motifs. "
            "In 1923, Emperor Khai Dinh had the palace renovated and renamed it Truong Sanh. "
            "The restoration project from 2005 to 2007 with a budget of nearly 30 billion VND restored the Peach Spring stream, Tan Nguyet Lake, and the rockeries. "
            "Just imagine an evening stroll here — the Queen Mothers walking by the lotus pond, "
            "watching the flowers bloom in the golden sunset — so peaceful and poetic, don't you think?"
        ),
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.469725,
        "longitude": 107.574694
    },
    {
        "loc_id": 1,
        "name_vi": "Cung Diên Thọ",
        "name_en": "Dien Tho Palace (Palace of Longevity)",
        "history_text_vi": (
            "Cung Diên Thọ là một trong những quần thể kiến trúc lớn nhất và còn nguyên vẹn nhất trong Hoàng thành Huế, với diện tích lên đến 17.500m². "
            "Được xây dựng vào tháng 4 năm 1804 dưới triều vua Gia Long, cung là nơi ở của các Hoàng thái hậu và Thái hoàng thái hậu qua nhiều triều đại. "
            "Tổng cộng có 8 vị Hoàng thái hậu và 4 vị Thái hoàng thái hậu đã từng sống tại nơi đây, mỗi người đều để lại những dấu ấn riêng trong lịch sử. "
            "Cung gồm khoảng 20 công trình kiến trúc lớn nhỏ, trong đó nổi bật nhất là Diên Thọ chính điện với 80 cột gỗ lim sơn đen, mái lợp ngói lưu ly vàng. "
            "Điện Thọ Ninh, tạ Trường Du, lầu Tịnh Minh và các Khương Ninh là những công trình phụ trợ tạo nên một tổng thể kiến trúc hài hòa, uyển chuyển. "
            "Điều thú vị là cung từng mang nhiều tên gọi khác nhau qua các thời kỳ: Trường Thọ (1804), Từ Thọ (1820), Gia Thọ (1849), Ninh Thọ (1901), "
            "và cuối cùng là Diên Thọ dưới thời vua Khải Định (1916). "
            "Tạ Trường Du là một trong bốn ngôi nhà tạ duy nhất còn sót lại ở Cố đô Huế, được xây trên hồ nước hình chữ nhật, "
            "với kết cấu nhà rường truyền thống Huế thanh thoát, 16 cột trụ, mái lợp ngói lưu ly men xanh. "
            "Các Khương Ninh là nơi thờ Phật, thờ Thánh và thờ cả tổ sư nghề hát bội — một sự kết hợp tín ngưỡng độc đáo hiếm thấy. "
            "Ba pho tượng Tam Thế Phật bằng gang mạ vàng được đánh giá là bộ tượng Phật đẹp nhất thời Nguyễn. "
            "Hệ thống hành lang trong cung nối thông tất cả các công trình, lợp ngói lưu ly xanh, tạo nên sự liên kết bền vững và mềm mại. "
            "Bước vào đây, bạn sẽ cảm nhận được không khí trang nghiêm nhưng ấm cúng của chốn thâm cung, "
            "nơi từng nuôi dưỡng biết bao câu chuyện buồn vui của các bậc mẫu nghi thiên hạ."
        ),
        "history_text_en": (
            "Dien Tho Palace is one of the largest and best-preserved architectural complexes within the Imperial City of Hue, spanning 17,500 square meters. "
            "Built in April 1804 under Emperor Gia Long, it served as the residence for Queen Mothers and Empress Dowagers across multiple dynasties. "
            "In total, eight Queen Mothers and four Grand Queen Mothers of the Nguyen Dynasty lived here, each leaving her own unique mark on history. "
            "The palace comprises about 20 structures, the most prominent being the main Dien Tho Hall with its 80 black-lacquered ironwood columns and yellow-glazed tile roof. "
            "Tho Ninh Hall, Truong Du Pavilion, Tinh Minh Tower, and Khuong Ninh Hall form a harmonious and elegant architectural ensemble. "
            "Interestingly, the palace bore different names throughout history: Truong Tho (1804), Tu Tho (1820), Gia Tho (1849), Ninh Tho (1901), "
            "and finally Dien Tho under Emperor Khai Dinh (1916). "
            "Truong Du Pavilion is one of only four surviving pavilions in the ancient capital of Hue, built upon a rectangular lake "
            "with the traditional Hue wooden house structure, 16 columns, and a roof covered with blue-glazed tiles. "
            "Khuong Ninh Hall uniquely blends Buddhist worship, saint veneration, and even the ancestral worship of traditional opera — a rare fusion of beliefs. "
            "Its three gilded cast-iron statues of the Buddhas of Three Times are considered the most beautiful Buddhist statues of the Nguyen era. "
            "The internal corridor system connects all buildings, covered with blue-glazed tiles, creating both structural unity and visual grace. "
            "Walking in here, you can feel the solemn yet intimate atmosphere of the deep palace — "
            "a place that once held countless joys and sorrows of the empire's foremost mothers."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4688556,
        "longitude": 107.5753417
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Chương Đức",
        "name_en": "Chuong Duc Gate (Gate of Manifest Virtue)",
        "history_text_vi": (
            "Cửa Chương Đức là cánh cổng phía Tây của Hoàng thành Huế, được xây dựng dưới thời vua Gia Long. "
            "Tên gọi 'Chương Đức' mang ý nghĩa sâu sắc: 'biểu dương đức hạnh' — như một lời nhắc nhở với tất cả những ai bước qua cánh cổng này "
            "về tầm quan trọng của đạo đức trong việc trị nước và giữ gìn nhân cách. "
            "Cổng có vọng lâu hai tầng vững chãi trên nền gạch đá kiên cố, tương tự các cổng khác trong Hoàng thành nhưng mang một vẻ đẹp riêng, trầm mặc và cổ kính. "
            "Qua cổng này, con đường dẫn vào khu vực phía Tây của thành, nơi có các cung điện dành cho Hoàng thái hậu như cung Diên Thọ và cung Trường Sanh. "
            "Đây cũng là một trong bốn cổng chính ra vào Hoàng thành, đối xứng với cửa Hiển Nhơn ở phía Đông, "
            "cùng với Ngọ Môn ở phía Nam và Hòa Bình ở phía Bắc tạo nên một hệ thống phòng thủ và giao thông hoàn chỉnh. "
            "Cửa Chương Đức không chỉ là một lối đi đơn thuần. Nó là ranh giới giữa hai thế giới: bên ngoài là cuộc sống dân dã với những khu phố cổ, "
            "những chợ búa nhộn nhịp; bên trong là không gian trang nghiêm của hoàng cung, nơi diễn ra những nghi lễ quan trọng của triều đình. "
            "Những bức tường thành nhuốm màu rêu phong, những mái ngói cong cong đã chứng kiến biết bao cuộc đổi thay của thời cuộc. "
            "Trên bờ mái, những hình rồng uốn lượn mềm mại, những họa tiết hoa lá cách điệu được chạm khắc tinh xảo trên gỗ và đá. "
            "Mỗi chi tiết đều toát lên sự trang nghiêm và tinh tế của nghệ thuật kiến trúc cung đình Huế. "
            "Hãy dừng lại một chút và ngắm nhìn kiến trúc của cổng — những đường nét chạm khắc trên mái, những họa tiết trang trí "
            "đều kể cho chúng ta nghe về một thời vàng son của văn hóa cung đình Huế. "
            "Bạn có cảm thấy sự chuyển giao kỳ diệu khi bước qua cánh cổng này không?"
        ),
        "history_text_en": (
            "Chuong Duc Gate is the western gate of the Hue Imperial City, built under Emperor Gia Long. "
            "Its name means 'Manifest Virtue' — a profound reminder to all who pass through about the importance of morality in governing the nation and preserving one's character. "
            "The gate features a solid two-story watchtower on a sturdy brick-and-stone foundation, similar to other gates in the Imperial City yet with its own quiet, ancient charm. "
            "Beyond this gate lies the road to the western quarter, where the palaces for Queen Mothers — Dien Tho and Truong Sanh — are located. "
            "It is one of four main gates of the Imperial City, symmetrical to Hien Nhon Gate in the east, "
            "together with Ngo Mon in the south and Hoa Binh in the north forming a complete defense and circulation system. "
            "Chuong Duc Gate is not merely a passageway. It marks the boundary between two worlds: outside lies the rustic life of ancient quarters and bustling markets; "
            "inside lies the solemn space of the royal court, where important ceremonies once took place. "
            "The moss-stained walls and curved tile roofs have witnessed countless changes throughout history. "
            "Along the roof ridges, gracefully curved dragon motifs and stylized floral patterns are intricately carved into wood and stone. "
            "Every detail exudes the solemnity and refinement of Hue's royal architectural art. "
            "Take a moment to admire the architecture — the carved patterns on the roof, the delicate decorative motifs — "
            "each tells a story of Hue's glorious royal cultural heritage. "
            "Don't you feel a magical transition as you step through this ancient gateway?"
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4673314,
        "longitude": 107.5757295
    },
    {
        "loc_id": 1,
        "name_vi": "Hưng Miếu (Hưng Tổ Miếu)",
        "name_en": "Hung Mieu (Hung To Temple)",
        "history_text_vi": (
            "Hưng Miếu là ngôi miếu thờ song thân của vua Gia Long — Thế tử Nguyễn Phúc Luân và bà Nguyễn Thị Hoàn, được xây dựng năm 1804. "
            "Nguyễn Phúc Luân, đáng lẽ sẽ là người lên ngôi chúa, nhưng vì nội loạn quyền thần Trương Phúc Loan nên ông bị giam vào ngục và mất khi mới 32 tuổi. "
            "Thật trớ trêu thay, ông ra đi khi còn trẻ nhưng để lại 6 người con trai và 4 người con gái, "
            "trong đó có Nguyễn Phúc Ánh — vị hoàng đế khai sáng triều Nguyễn, người sau này đã thống nhất đất nước sau hơn 200 năm chia cắt. "
            "Ngôi miếu đầu tiên được xây tại vị trí của Thế Miếu ngày nay, nhưng đến năm 1821, vua Minh Mạng cho dời về phía sau 50m để xây Thế Miếu. "
            "Năm 1947, miếu bị đốt cháy cùng với Tử Cấm Thành. Năm 1950, vua Bảo Đại đã mua lại An Khánh vương từ "
            "— vốn là nơi thờ An Khánh vương Nguyễn Phúc Quang (con vua Gia Long) với giá 300.000 đồng để xây dựng lại thành Hưng Miếu mới. "
            "Kiến trúc Hưng Miếu là một công trình gỗ tinh xảo theo lối trùng diêm trùng lương, mái lợp ngói âm dương men vàng, nền cao 0,68m bó bằng đá Thanh. "
            "Toàn bộ dàn trò với 9 hàng cột dọc, 8 hàng cột ngang đều làm bằng gỗ quý: lim, sao, kền kền, huê mộc. "
            "Các chi tiết chạm trổ hoa lá tinh xảo, mỗi đường nét đều toát lên sự trang nghiêm và lòng thành kính. "
            "Mặt dưới mặt tiền hạ doanh được trang trí dải bản gỗ hình chữ U chạm trổ tinh xảo. "
            "Sân trước lát gạch Bát Tràng hình chữ nhật, giữa sân là đường thần đạo lát đá Thanh rộng 2,15m, dẫn từ bậc thềm ra miếu môn. "
            "Hai bên sân còn có lư hương bằng đá và những chậu sứ trồng cây cảnh cổ kính. "
            "Đến nay, ngôi miếu hơn 200 năm tuổi vẫn đứng đó như một chứng nhân lịch sử, nhắc nhở chúng ta về cội nguồn của triều đại."
        ),
        "history_text_en": (
            "Hung Mieu is the temple dedicated to Emperor Gia Long's parents — Crown Prince Nguyen Phuc Luan and Mrs. Nguyen Thi Hoan, built in 1804. "
            "Nguyen Phuc Luan was destined to become lord, but he was imprisoned during a power struggle orchestrated by the usurper Truong Phuc Loan and died at just 32. "
            "Ironically, despite his early death, he left behind six sons and four daughters, "
            "including Nguyen Phuc Anh — the founding emperor of the Nguyen Dynasty, who later unified Vietnam after over 200 years of division. "
            "The original temple was built on the site where The Mieu now stands, but in 1821 Emperor Minh Mang had it relocated 50 meters north to make way for The Mieu. "
            "In 1947, the temple was burned down with the Forbidden Purple City. In 1950, Emperor Bao Dai purchased An Khanh royal shrine "
            "— originally dedicated to An Khanh Prince Nguyen Phuc Quang (son of Gia Long) for 300,000 dong to rebuild it as the new Hung Mieu. "
            "Hung Mieu is a masterwork of wooden architecture built in the traditional stacked-roof style, with a 0.68-meter-high foundation edged in Thanh stone. "
            "The entire structure rests on 9 rows of columns lengthwise and 8 rows widthwise, all made from precious woods like ironwood, sao, and mahogany. "
            "The intricate floral carvings convey both solemnity and deep filial reverence. "
            "The underside of the front facade features a U-shaped wooden decorative band with exquisite carvings. "
            "The front yard is paved with Bat Trang bricks in a rectangle, with a 2.15-meter-wide Thanh stone spirit path leading from the steps to the temple gate. "
            "Stone incense burners and antique ceramic pots with ornamental plants flank the yard. "
            "Standing for over 200 years, this temple remains a living witness to history, reminding us of the origins of a great dynasty."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4674263,
        "longitude": 107.5764189
    },
    {
        "loc_id": 1,
        "name_vi": "Thế Miếu (Thế Tổ Miếu)",
        "name_en": "The Mieu (The To Temple)",
        "history_text_vi": (
            "Thế Tổ Miếu là nơi thờ các vị vua triều Nguyễn, tọa lạc ở góc Tây Nam Hoàng thành — linh hồn của hệ thống miếu thờ triều Nguyễn. "
            "Được xây dựng từ năm 1821 đến 1822 trên nền của Hoàng Khảo miếu cũ (sau khi di dời Hưng Miếu lên phía Bắc 50m), "
            "đây là một công trình gỗ đồ sộ với diện tích lên đến 1.500m², nhà chính 9 gian 2 chái kép, nhà trước 11 gian 2 chái đơn, "
            "nối liền nhau bằng vì vỏ cua chạm trổ tinh tế. "
            "Mái được lợp ngói hoàng lưu ly với đỉnh nóc gắn liền thái cực bằng pháp lam rực rỡ. "
            "Bên trong, các án thờ vua Nguyễn được sắp xếp theo nguyên tắc 'tả chiêu, hữu mục', "
            "với án thờ vua Gia Long và hai hoàng hậu đặt ở chính giữa. "
            "Các vua Minh Mạng, Thiệu Trị, Tự Đức, Kiến Phúc, Đồng Khánh, Khải Định được thờ theo thứ tự bên trái và bên phải. "
            "Đến năm 1958, các vua Hàm Nghi, Thành Thái và Duy Tân mới được rước vào thờ. "
            "Trước sân miếu là Cửu Đỉnh — 9 chiếc đỉnh đồng lớn tượng trưng cho 9 đời vua, mỗi đỉnh nặng khoảng 2 tấn, "
            "chạm khắc 17 hình ảnh đặc trưng của đất nước như mặt trời, biển cả, núi non, hoa lá và sản vật. "
            "Hiển Lâm các cao 3 tầng sừng sững như một ngọn tháp canh, hai bên có lầu chuông, lầu trống, "
            "bên dưới trổ hai cửa: Tuấn Liệt môn và Sùng Công môn. "
            "Khuôn viên Thế Miếu rộng đến 2ha, chiếm 1/18 diện tích toàn bộ Hoàng thành. "
            "Một cây thông cổ thụ uốn lượn bên tường phía Tây, tương truyền được trồng từ ngày dựng miếu — đã hơn 200 năm tuổi. "
            "Bạn có thể nhận ra những biểu tượng trên Cửu Đỉnh không? Mỗi hình ảnh đều mang một ý nghĩa riêng, "
            "kể về văn hóa, lịch sử và con người Việt Nam dưới con mắt của các bậc đế vương."
        ),
        "history_text_en": (
            "The Mieu (The To Temple) honors the emperors of the Nguyen Dynasty, located in the southwest corner of the Imperial City — "
            "the very soul of the Nguyen worship system. "
            "Built from 1821 to 1822 on the site of the former Hoang Khao Temple (after Hung Mieu was relocated 50 meters north), "
            "it is a massive wooden structure covering 1,500 square meters, with a main hall of 9 double-side bays and a front hall of 11 single-side bays, "
            "connected by intricately carved shell-shaped roof trusses. "
            "The roof is covered with yellow-glazed tiles, topped with a brilliant enameled Taichi symbol. "
            "Inside, the imperial shrines are arranged according to the 'left deities, right ancestors' principle, "
            "with the shrine of Emperor Gia Long and his two empresses at the very center. "
            "Emperors Minh Mang, Thieu Tri, Tu Duc, Kien Phuc, Dong Khanh, and Khai Dinh are enshrined in order on the left and right. "
            "In 1958, Emperors Ham Nghi, Thanh Thai, and Duy Tan were finally admitted into the temple. "
            "In front of the temple stand the Nine Dynastic Urns (Cuu Dinh) — nine massive bronze urns symbolizing nine reigns, each weighing about 2 tons, "
            "engraved with 17 images representing Vietnam's landscapes, seas, mountains, flora, and products. "
            "The three-story Hien Lam Pavilion rises like a sentinel tower, flanked by bell and drum towers, "
            "with two gates below: Tuan Liet and Sung Cong. "
            "The temple complex covers 2 hectares, one-eighteenth of the entire Imperial City. "
            "An ancient pine tree with a gracefully twisted trunk stands by the western wall, "
            "rumored to have been planted when the temple was first built — over 200 years old. "
            "Can you spot the symbols on the Nine Urns? Each image tells a unique story about Vietnam's culture, history, and people "
            "as seen through the eyes of its emperors."
        ),
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.4671621,
        "longitude": 107.5767333
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace (Palace of Supreme Harmony)",
        "history_text_vi": (
            "Điện Thái Hòa là biểu tượng quyền lực tối cao của vương triều Nguyễn, nơi diễn ra các buổi thiết triều, "
            "lễ đăng quang của 13 vị vua và đón tiếp sứ thần ngoại giao. "
            "Được xây dựng lần đầu năm 1805 dưới triều vua Gia Long, đến năm 1833 vua Minh Mạng cho dời về vị trí hiện tại và làm lại đồ sộ hơn. "
            "Năm 1923, vua Khải Định lại cho đại gia trùng kiến chuẩn bị cho lễ Tứ tuần Đại khánh tiết. "
            "Điện được xây trên nền cao 1 mét, diện tích 1.360m², với 80 cột gỗ lim sơn son thếp vàng, "
            "mỗi cột đều được chạm khắc hình rồng vờn mây tinh xảo — biểu tượng của sự gặp gỡ giữa hoàng đế và quần thần. "
            "Mái điện lợp ngói hoàng lưu ly, được chia làm ba tầng chồng mí lên nhau gọi là mái 'chồng diêm', "
            "tạo ảo giác về chiều cao và sự uy nghiêm. Giữa hai tầng mái là dải cổ diêm chạy quanh bốn mặt, "
            "được trang trí 197 bài thơ trên pháp lam theo lối nhất thi nhất họa. "
            "Từ sân Đại triều nhìn vào, vua ngồi trên ngai vàng ở gian trong cùng, "
            "còn bá quan văn võ đứng hai bên sân theo thứ bậc từ nhất phẩm đến cửu phẩm — quan văn bên trái, quan võ bên phải. "
            "Tất cả vị trí đều được đánh dấu trên hai dãy đá trước sân chầu. "
            "Một chi tiết thú vị: con số 9 xuất hiện khắp nơi trong điện — 9 cấp thềm, 9 con rồng trên mỗi mái, "
            "vì 9 là biểu tượng của vua chúa trong văn hóa phương Đông. Con số 5 cũng xuất hiện tượng trưng cho ngũ hành. "
            "Điện được xây theo lối trùng thiềm điệp ốc — một kiến trúc sáng tạo với hệ thống trần vòm mai cua dưới máng thừa lưu, "
            "tạo ra một không gian nội thất liên tục, thống nhất mà không có cảm giác ghép nối. "
            "Hãy thử đếm xem bạn có thể tìm thấy bao nhiêu hình rồng trong điện này nhé!"
        ),
        "history_text_en": (
            "Thai Hoa Palace (Palace of Supreme Harmony) is the ultimate symbol of Nguyen imperial power, "
            "where coronations of 13 emperors, court audiences, and diplomatic ceremonies took place. "
            "First built in 1805 under Emperor Gia Long, it was relocated and greatly expanded in 1833 under Emperor Minh Mang. "
            "In 1923, Emperor Khai Dinh undertook a major renovation for his 40th birthday celebration. "
            "The palace stands on a 1-meter-high platform covering 1,360 square meters, supported by 80 red-lacquered, gold-gilded ironwood columns, "
            "each carved with dragons dancing among clouds — symbolizing the meeting between emperor and his subjects. "
            "The roof is covered with yellow-glazed tiles stacked in three overlapping tiers, creating an illusion of height and grandeur. "
            "Between the roof tiers runs a decorative band encircling all four sides, "
            "adorned with 197 poems on enamel plaques in the 'one poem, one painting' style. "
            "From the Great Court Yard, the emperor sat on his golden throne in the deepest chamber, "
            "while civil and military mandarins stood arranged by rank from first to ninth grade — civil officials on the left, military on the right. "
            "All positions were marked on two rows of stone slabs in the court yard. "
            "A fascinating detail: the number 9 appears everywhere — 9 steps, 9 dragons on each roof section — "
            "as 9 symbolizes the emperor in Eastern culture. The number 5 also appears, representing the five elements. "
            "The palace was built in the 'trung thiem diep oc' style — an innovative design with a turtle-shell vault connecting the two roof sections, "
            "creating a continuous, unified interior space without any sense of joining. "
            "Try counting how many dragons you can spot in this hall!"
        ),
        "author": "Vua Gia Long",
        "year": 1805,
        "latitude": 16.4686747,
        "longitude": 107.578412
    },
    {
        "loc_id": 1,
        "name_vi": "Nền điện Cần Chánh",
        "name_en": "Can Chanh Palace Foundation",
        "history_text_vi": (
            "Điện Cần Chánh từng là trái tim của Tử Cấm Thành, nơi vua Nguyễn thiết triều hằng ngày, tiếp đón sứ thần ngoại giao "
            "và tổ chức yến tiệc hoàng gia. Được xây dựng năm 1804 dưới triều vua Gia Long, "
            "điện nằm trên trục chính giữa Điện Thái Hòa và điện Càn Thành. "
            "Ngôi điện này có kết cấu gỗ lớn và đẹp nhất trong Tử Cấm Thành, với diện tích gần 1.000m², "
            "chính điện 5 gian 2 chái kép, tiền điện 7 gian 2 chái đơn, và 80 cột gỗ lim. "
            "Trong điện, ở gian giữa đặt ngự tọa, trên các hàng cột hai bên treo những bức tranh gương "
            "thể hiện cảnh đẹp của kinh đô và bản đồ các tỉnh trong nước. "
            "Đây từng là nơi trưng bày nhiều báu vật quý giá như đồ sứ hiếm, hòm tượng bảo ấn bằng vàng và ngọc. "
            "Hai bên điện có Tả vu và Hữu vu phục vụ việc chuẩn bị nghi lễ và chiêu đãi khách, "
            "họp thành bố cục kiến trúc hình chữ môn. "
            "Phía đông Tả vu có điện Đông Các làm từ năm 1826 — nơi làm việc của các đại thần. "
            "Về phía Nam là Tụ Khuê thơ lâu — lầu chứa sách của triều đình. "
            "Bên tả điện Cần Chánh là điện Văn Minh, bên hữu là điện Võ Hiển, đều xoay mặt hướng Nam, mái chồng, lợp ngói thanh lưu ly. "
            "Thật đáng tiếc, điện đã bị phá hủy hoàn toàn vào tháng 2 năm 1947 trong chiến dịch tiêu thổ kháng chiến. "
            "Hiện nay chỉ còn lại nền móng và một số dấu tích kiến trúc. "
            "Tin vui là dự án phục dựng điện Cần Chánh với kinh phí gần 200 tỷ đồng đã được khởi công vào tháng 11 năm 2024, "
            "dựa trên những bức ảnh tư liệu do người Pháp chụp trước khi điện sụp đổ. "
            "Hãy tưởng tượng, trong vòng 4 năm nữa, ngôi điện này sẽ sống lại, lộng lẫy như thuở nào! "
            "Bạn có thể hình dung được không khí trang nghiêm của những buổi thiết triều xưa kia không?"
        ),
        "history_text_en": (
            "Can Chanh Palace was once the heart of the Forbidden Purple City, where Nguyen emperors held daily court sessions, "
            "received foreign envoys, and hosted royal banquets. Built in 1804 under Emperor Gia Long, "
            "it stood on the main axis between Thai Hoa Palace and Can Thanh Palace. "
            "This was the largest and most beautiful wooden structure in the Forbidden City, covering nearly 1,000 square meters, "
            "with a main hall of 5 double-side bays, a front hall of 7 single-side bays, and 80 ironwood columns. "
            "Inside, the imperial throne was placed in the central bay, and mirror paintings on the surrounding columns "
            "depicted scenic views of the capital and maps of the provinces. "
            "It once displayed countless treasures including rare porcelain and gold-and-jade imperial seal boxes. "
            "Flanking the palace were the Left and Right auxiliary halls for ceremony preparation and guest reception, "
            "forming a 'gate-shaped' architectural layout. "
            "East of the Left Hall stood Dong Cac Hall (built 1826) — the working office of grand ministers. "
            "To the south was Tu Khue Poetry Tower — the imperial library. "
            "To the left of Can Chanh Palace stood Van Minh Hall, to the right Vo Hien Hall, both facing south with layered roofs of blue-glazed tiles. "
            "Sadly, the palace was completely destroyed in February 1947 during the scorched-earth resistance campaign. "
            "Only the foundation and some architectural traces remain today. "
            "The good news is that the restoration project, costing nearly 200 billion VND, began in November 2024, "
            "based on French archival photographs taken before its collapse. "
            "Imagine — within four years, this palace will come back to life in all its former glory! "
            "Can you picture the solemn atmosphere of the ancient court sessions that once took place here?"
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4695281,
        "longitude": 107.5777743
    },
    {
        "loc_id": 1,
        "name_vi": "Duyệt Thị Đường",
        "name_en": "Duyet Thi Duong (Royal Theater)",
        "history_text_vi": (
            "Duyệt Thị Đường là nhà hát hoàng gia cổ nhất còn tồn tại ở Việt Nam, được xem là viên ngọc quý của nghệ thuật sân khấu cung đình. "
            "Được xây dựng vào năm 1826 dưới triều vua Minh Mạng trên nền của nhà hát Thanh Phong Đường cũ (1805), "
            "nhà hát nằm ở góc Đông Nam bên trong Tử Cấm Thành với tổng diện tích khuôn viên 11.740m². "
            "Kiến trúc nhà hát hình chữ nhật rộng rãi, với mái cong mềm mại tựa những đình chùa Huế, "
            "được chống đỡ bởi hai hàng cột lim sơn son cao 12 mét vẽ rồng ẩn mây cuốn chung quanh. "
            "Mỗi cột còn treo thêm một bức tranh sơn thủy vẽ cảnh Huế với khung chạm rồng nổi thiếp vàng. "
            "Điều đặc biệt là sân khấu nằm ở trung tâm, với khán giả ngồi ba phía xung quanh — một thiết kế độc đáo. "
            "Vị trí đẹp nhất là lầu hai, dành riêng cho nhà vua — từ đây, vua có thể ngắm nhìn toàn bộ sân khấu. "
            "Các bà hoàng và cung tần mỹ nữ ngồi phía sau một lớp sáo trúc thưa, có thể nhìn ra mà không bị nhìn thấy — "
            "một chi tiết đầy tinh tế và kín đáo của cung đình. "
            "Hai bên vòm có treo hai câu đối bằng chữ Hán của vua Minh Mạng, "
            "nói về sức mạnh của âm nhạc trong việc nuôi dưỡng chí khí con người. "
            "Bên hữu nhà hát là Ngự y viện, nơi sao chế thuốc cho vua và hoàng gia. "
            "Ngày nay, Duyệt Thị Đường vẫn là nơi biểu diễn Nhã nhạc cung đình Huế — Di sản Văn hóa phi vật thể của UNESCO, "
            "với hai suất diễn mỗi ngày vào lúc 10 giờ sáng và 3 giờ chiều. "
            "Nhà hát đã phục dựng 8 trong số 11 điệu múa cổ và 40 bài nhã nhạc — "
            "một kho báu văn hóa đang sống động từng ngày. "
            "Nếu có dịp, bạn hãy dừng chân ở đây để thưởng thức những điệu múa cung đình và tiếng nhạc du dương — "
            "chắc chắn sẽ là một trải nghiệm khó quên!"
        ),
        "history_text_en": (
            "Duyet Thi Duong is the oldest surviving royal theater in Vietnam, considered a jewel of court performing arts. "
            "Built in 1826 under Emperor Minh Mang on the site of the older Thanh Phong Theater (1805), "
            "it is located in the southeastern corner of the Forbidden Purple City within a 11,740-square-meter compound. "
            "The rectangular theater features gracefully curved roofs reminiscent of Hue's pagodas, "
            "supported by two rows of 12-meter-high red-lacquered ironwood columns painted with dragons among clouds. "
            "Each column also bears a landscape painting of Hue framed in gold-embossed dragon carvings. "
            "What makes it unique is the central stage, surrounded by audience seating on three sides — a truly innovative design. "
            "The best seat was on the second floor, reserved for the emperor — from there, he could view the entire performance. "
            "Empresses and concubines sat behind a thin bamboo screen, able to see out without being seen — "
            "a wonderfully discreet arrangement typical of the royal court. "
            "Flanking the arches hang two couplets in Chinese characters composed by Emperor Minh Mang himself, "
            "praising music's power to nurture the human spirit. "
            "To the right of the theater stood the Imperial Medical Institute, where medicines were prepared for the king and his family. "
            "Today, Duyet Thi Duong continues to host Hue Royal Court Music (Nha Nhac), a UNESCO Intangible Cultural Heritage, "
            "with two performances daily at 10 AM and 3 PM. "
            "The theater has restored 8 of the 11 ancient court dances and 40 pieces of court music — "
            "a living cultural treasure that breathes history every single day. "
            "If you have the chance, do stop by to enjoy the court dances and melodious music — an unforgettable experience awaits!"
        ),
        "author": "Vua Minh Mạng",
        "year": 1826,
        "latitude": 16.470284,
        "longitude": 107.5785163
    },
    {
        "loc_id": 1,
        "name_vi": "Phủ Nội Vụ",
        "name_en": "Phu Noi Vu (Ministry of the Interior)",
        "history_text_vi": (
            "Phủ Nội Vụ là cơ quan đầu não quản lý tài sản, vật dụng cho Hoàng đế và hoàng gia, "
            "được ví như 'ngân khố' và 'cục hậu cần' của triều đình nhà Nguyễn. "
            "Tiền thân dưới thời Gia Long là Nội Đồ Gia nằm trong Tử Cấm Thành. Đến năm 1820, vua Minh Mạng đổi tên thành Nội Vụ Phủ. "
            "Năm 1837, phủ được dời về vị trí hiện tại ở phía Đông Bắc Hoàng thành, gần cửa Hiển Nhơn. "
            "Phủ Nội Vụ quản lý kho tàng vàng bạc, châu báu, tơ lụa, gấm vóc và các vật cống tiến, "
            "đồng thời lo việc sản xuất các vật dụng cho hoàng đế và nội cung. "
            "Cơ cấu tổ chức rất tinh vi: 1 Thị lang, 2 Lang trung điều hành, "
            "với các kho chuyên biệt: kho vàng bạc, kho châu ngọc, kho gấm vóc, kho the lụa, kho vật hạng, kho văn nhạc, kho dược phẩm. "
            "Mỗi kho đều có viên chức riêng phụ trách với các Chủ sự, Tư vụ, Thư lại các cấp. "
            "Tiết thận ty quản lý các cục thợ thủ công gồm thợ may, thêu, nhuộm, dệt và các xưởng chế tác đồ quý. "
            "Đến năm 1906, công trình được xây dựng lại theo kiến trúc Pháp, với tòa nhà chính hai tầng còn tồn tại đến ngày nay. "
            "Sau năm 1945, khu vực này trải qua nhiều lần thay đổi công năng: từ trụ sở tuần binh, "
            "trường Cao đẳng Nghệ thuật, đến Đại học Nghệ thuật Huế. "
            "Hiện tại, Phủ Nội Vụ có dấu hiệu xuống cấp, để lộ những khung sắt trên trần nhà, "
            "nhưng vẫn giữ được vẻ cổ kính, trầm mặc của một thời vàng son. "
            "Khu vực bên cạnh đã trở thành Không gian trình diễn nghề truyền thống Huế với nón lá, đèn lồng, áo dài và hoa giấy — "
            "nơi những nghề thủ công tinh hoa của cố đô vẫn đang sống động từng ngày."
        ),
        "history_text_en": (
            "Phu Noi Vu (Ministry of the Interior) was the central agency managing imperial assets and supplies, "
            "functioning as the treasury and logistics hub of the Nguyen court. "
            "Its predecessor, Noi Do Gia, was established inside the Forbidden Purple City under Emperor Gia Long. In 1820, Emperor Minh Mang renamed it Noi Vu Phu. "
            "In 1837, the ministry was relocated to its current site in the northeast of the Imperial City, near Hien Nhon Gate. "
            "It managed gold, silver, jewels, silk, brocade, and tribute items, "
            "while also overseeing production of goods for the emperor and the inner court. "
            "Its organizational structure was remarkably sophisticated: 1 Vice Minister and 2 Directors, "
            "with specialized warehouses for gold and silver, pearls and gems, brocade, silk, general goods, musical instruments, and medicines. "
            "Each warehouse had dedicated officials at various ranks. "
            "The department oversaw artisan bureaus for tailoring, embroidery, dyeing, weaving, and crafting precious items. "
            "In 1906, the building was reconstructed in French architectural style, with the two-story main building still standing today. "
            "After 1945, the site underwent many transformations: from palace guard headquarters "
            "to the College of Arts, then Hue University of Arts. "
            "Today, Phu Noi Vu shows signs of aging, with exposed iron frames on the ceiling, "
            "yet retains its ancient, solemn charm from a glorious past. "
            "The adjacent area has become a space for showcasing Hue's traditional crafts — conical hats, lanterns, ao dai, and paper flowers — "
            "where the exquisite artisan traditions of the ancient capital live on vibrantly."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.470755,
        "longitude": 107.5796368
    },
    {
        "loc_id": 1,
        "name_vi": "Vườn Cơ Hạ",
        "name_en": "Co Ha Garden (Imperial Garden)",
        "history_text_vi": (
            "Vườn Cơ Hạ hay Cơ Hạ Viên là một trong năm khu vườn thượng uyển nằm trong Hoàng thành Huế, "
            "được ví như 'ốc đảo bình yên' giữa chốn cung đình. "
            "Tên gọi 'Cơ Hạ' được lấy từ ý 'Vạn Cơ Thanh Hạ', nghĩa là sự bình an trong mọi cơ sự — "
            "một nơi để vua nghỉ ngơi, thư giãn sau những giờ triều chính căng thẳng. "
            "Vườn tọa lạc ở góc Đông Bắc Hoàng thành, rộng gần 2,3 ha, trước giáp Phủ Nội Vụ, sau giáp Hậu Hồ. "
            "Ban đầu đây là nơi học tập của Thái tử Nguyễn Phúc Đảm (vua Minh Mạng sau này). "
            "Đến năm 1837, khu vực được sửa sang và mở rộng thành ngự uyển. "
            "Vua Thiệu Trị đã từng đề vịnh về vườn với 14 cảnh đẹp khác nhau, như 'Điện khai văn yến', "
            "'Lâu thưởng Bồng doanh', 'Các minh tứ chiếu'..., mỗi cảnh đều được vẽ tranh minh họa và khắc thơ vào bia đá. "
            "Trong vườn có điện Khâm Văn — công trình chính nằm trên trục trung tâm, hồ Minh Hồ với gác Quang Biểu giữa hồ, "
            "lầu Thưởng Thắng, cầu Kim Nghê có mái che, và hệ thống hành lang Tứ Phương Ninh Mật hình chữ khẩu chạy vòng quanh. "
            "Có cả hồ sen, núi giả, hang động, sông nhỏ nhân tạo — một bức tranh thu nhỏ của non sông đất nước. "
            "Phía đông vườn có Minh Lý Thư Trai, phía tây có Nhật Thận hiên, "
            "cùng các ngọn núi giả Thọ Yên, Trùng Đình và ao Thụy Liên. "
            "Vườn Cơ Hạ đã được phục hồi vào năm 2012 và trở thành một điểm nhấn đặc biệt trong các kỳ Festival Huế. "
            "Năm 2013-2014, tỉnh Thừa Thiên Huế tiếp tục tôn tạo và mở rộng vườn. "
            "Ngồi đây, bạn có thể cảm nhận được sự thanh tịnh mà các vua Nguyễn từng tìm kiếm giữa bộn bề việc nước."
        ),
        "history_text_en": (
            "Co Ha Garden (Co Ha Vien) is one of five imperial gardens within the Hue Imperial City, "
            "a peaceful oasis amidst the royal court. "
            "Its name comes from 'Van Co Thanh Ha', meaning 'peace in all matters' — "
            "a place for the emperor to rest and unwind after intense court sessions. "
            "Located in the northeast corner of the Imperial City, it covers nearly 2.3 hectares, bordering Phu Noi Vu to the front and Hau Ho Lake to the rear. "
            "Originally, this was the study place of Crown Prince Nguyen Phuc Dam (later Emperor Minh Mang). "
            "In 1837, the area was renovated and expanded into an imperial garden. "
            "Emperor Thieu Tri celebrated its beauty in poetry, describing 14 distinct scenic spots "
            "such as 'Hall of Literary Banquets', 'Tower Overlooking Paradise', and 'Pavilion of Radiant Reflections' — "
            "each illustrated in paintings and inscribed on stone stelae. "
            "The garden features Kham Van Hall — the main structure on the central axis, Minh Ho Lake with Quang Bieu Pavilion in its center, "
            "Thuong Thang Tower, the covered Kim Nghi Bridge, "
            "and the Four Directions Covered Corridor running around in a rectangular shape. "
            "With lotus ponds, artificial mountains, caves, and miniature streams, it's a microcosm of Vietnam's landscapes. "
            "To the east lies Minh Ly Thu Trai study room, to the west is Nhat Than Hien pavilion, "
            "along with artificial mountains Tho Yen, Trung Dinh, and Thuy Lien pond. "
            "Co Ha Garden was restored in 2012 and has since become a highlight of the Hue Festival. "
            "From 2013 to 2014, Thua Thien Hue province further renovated and expanded the garden. "
            "Sitting here, you can truly feel the tranquility the Nguyen emperors once sought amidst their heavy state affairs."
        ),
        "author": "Vua Thiệu Trị",
        "year": 1847,
        "latitude": 16.4717727,
        "longitude": 107.5788666
    },
    {
        "loc_id": 1,
        "name_vi": "Triệu Miếu (Triệu Tổ Miếu)",
        "name_en": "Trieu Mieu (Trieu To Temple)",
        "history_text_vi": (
            "Triệu Tổ Miếu là nơi thờ Nguyễn Kim — vị chúa Nguyễn đầu tiên, người đặt nền móng cho sự nghiệp của dòng họ Nguyễn kéo dài hơn 400 năm. "
            "Nguyễn Kim là thân sinh của chúa Tiên Nguyễn Hoàng, người khai phá vùng đất Đàng Trong, mở mang bờ cõi về phương Nam. "
            "Ông bị hàng tướng nhà Mạc là Dương Chấp Nhất đầu độc chết, "
            "nhưng đã được các đời vua Nguyễn truy tôn miếu hiệu là Triệu Tổ. "
            "Miếu được xây dựng năm 1804 dưới triều vua Gia Long, nằm ở phía Bắc Thái Miếu, "
            "tạo thành một quần thể kiến trúc thờ tự trang nghiêm trong góc Đông Nam Hoàng thành. "
            "Về quy mô và hình thức, Triệu Miếu tương tự Hưng Miếu, gồm chính đường 3 gian 2 chái, tiền đường 5 gian 2 chái đơn, với diện tích 540m². "
            "Mái lợp ngói âm dương hoàng lưu ly, các cấu kiện gỗ được sơn son thếp vàng tinh xảo. "
            "Bờ mái và tường cổ diềm được đắp nổi phù điêu có gắn mảnh sành sứ — một kỹ thuật trang trí đặc trưng thời Nguyễn. "
            "Hai bên điện chính có Thần Khố (phía đông) và Thần Trù (phía tây) để phục vụ việc tế lễ. "
            "Năm 1989, do Thái Miếu xuống cấp nặng, Triệu Miếu trở thành nơi thờ chung cho 9 chúa Nguyễn. "
            "Từ năm 2014 đến 2017, Bộ Ngoại giao Hoa Kỳ đã tài trợ 700.000 USD để bảo tồn, tu bổ di tích này, "
            "với tổng vốn đầu tư 16 tỷ đồng, khánh thành vào tháng 9 năm 2016 sau 27 tháng thi công. "
            "Ngôi miếu hơn 200 năm tuổi vẫn đứng đó, như một chứng nhân lịch sử, "
            "nhắc nhở chúng ta về cội nguồn của dòng tộc Nguyễn và những trang sử hào hùng của dân tộc."
        ),
        "history_text_en": (
            "Trieu Mieu (Trieu To Temple) honors Nguyen Kim — the first Nguyen Lord who laid the foundation for the Nguyen clan's 400-year legacy. "
            "Nguyen Kim was the father of Lord Nguyen Hoang, the pioneer who opened up the southern region of Vietnam (Dang Trong), expanding the nation's territory. "
            "He was poisoned by a Mac dynasty defector general named Duong Chap Nhat, "
            "but was posthumously honored with the temple name Trieu To by later Nguyen emperors. "
            "The temple was built in 1804 under Emperor Gia Long, located north of Thai Mieu, "
            "forming a solemn ancestral worship complex in the southeast corner of the Imperial City. "
            "In scale and form, Trieu Mieu resembles Hung Mieu, with a main hall of 3 bays, front hall of 5 bays, covering 540 square meters. "
            "The roof is covered with yin-yang yellow-glazed tiles, with wooden components lacquered in red and gilded in gold. "
            "The roof ridges and decorative borders feature raised reliefs embedded with ceramic shards — a signature Nguyen decorative technique. "
            "Flanking the main hall are the God's Treasury (east) and God's Kitchen (west) for ceremonial preparations. "
            "In 1989, due to Thai Mieu's severe deterioration, Trieu Mieu became the shared shrine for all 9 Nguyen Lords. "
            "From 2014 to 2017, the US State Department funded $700,000 for its preservation, "
            "with a total investment of 16 billion VND, inaugurated in September 2016 after 27 months of construction. "
            "This 200-year-old temple still stands as a living witness to history, "
            "reminding us of the Nguyen clan's deep roots and the nation's glorious past."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4701907,
        "longitude": 107.5801058
    },
    {
        "loc_id": 1,
        "name_vi": "Thái Miếu (Thái Tổ Miếu)",
        "name_en": "Thai Mieu (Thai To Temple)",
        "history_text_vi": (
            "Thái Tổ Miếu là ngôi miếu lớn nhất thờ các vị chúa Nguyễn, được xây dựng năm 1804 ở góc Đông Nam Hoàng thành, "
            "đối xứng với Thế Tổ Miếu ở hướng Tây Nam. "
            "Đây là một tổ hợp kiến trúc đồ sộ với trên 10 hạng mục công trình trong khuôn viên rộng đến 14.904m². "
            "Chính điện Thái Miếu là ngôi nhà gỗ lớn nhất trong tất cả các cung điện thời Nguyễn, "
            "với chính đường 13 gian 2 chái kép và tiền đường 15 gian 2 chái đơn — "
            "một quy mô chưa từng có, vượt qua cả Thế Miếu về kích thước. "
            "Thái Miếu thờ các chúa Nguyễn từ Nguyễn Hoàng (chúa Tiên) đến Nguyễn Phúc Thuần, "
            "mỗi năm tổ chức 5 lần tế lễ lớn vào các tháng mạnh xuân, mạnh hạ, mạnh thu, mạnh đông và quý đông. "
            "Trước sân Thái Miếu có Tuy Thành các cao 3 tầng, hình thức tương tự Hiển Lâm các ở Thế Miếu, "
            "hai bên có lầu chuông, lầu trống và tường ngắn nối liền. "
            "Phía nam Tuy Thành các là Tả Tùng tự và Hữu Tùng tự — nơi thờ các công thần có công với triều Nguyễn. "
            "Phía đông chính điện là điện Long Đức, phía tây là Thổ Công từ, "
            "phía đông nam có điện Chiêu Kính, đối diện là điện Mục Tư. "
            "Toàn bộ khu vực có tường gạch bao bọc, trổ 5 cửa ra các phía. "
            "Không may thay, đầu năm 1947, khu vực Thái Miếu bị thiêu hủy hoàn toàn trong chiến dịch tiêu thổ kháng chiến. "
            "Năm 1971-1972, Hội đồng Nguyễn Phúc tộc và Đức Từ Cung đã quyên góp dựng lại một tòa nhà 5 gian trên nền cũ. "
            "Vào tháng 10 năm 2024, dự án tu bổ, phục hồi Thái Miếu với kinh phí 52 tỉ đồng đã được khởi công, dự kiến hoàn tất vào năm 2028. "
            "Một công trình đang dần được hồi sinh để thế hệ mai sau biết đến và tự hào về lịch sử."
        ),
        "history_text_en": (
            "Thai Mieu (Thai To Temple) is the largest temple dedicated to the Nguyen Lords, built in 1804 in the southeast corner of the Imperial City, "
            "symmetrical to The Mieu in the southwest. "
            "This massive architectural complex features over 10 structures within a 14,904-square-meter compound. "
            "Its main hall is the largest wooden building ever constructed under the Nguyen Dynasty, "
            "with a 13-bay main hall featuring double side wings and a 15-bay front hall with single side wings — "
            "a scale unprecedented even by the standards of The Mieu. "
            "Thai Mieu honors the Nguyen Lords from Nguyen Hoang (the first lord) to Nguyen Phuc Thuan, "
            "with five major annual ceremonies held during the first months of each season and the winter solstice. "
            "In front stands the three-story Tuy Thanh Pavilion, resembling The Mieu's Hien Lam Pavilion, "
            "flanked by bell and drum towers connected by short walls. "
            "South of Tuy Thanh Pavilion stand Ta Tung Tu and Huu Tung Tu — shrines for meritorious officials of the Nguyen court. "
            "East of the main hall stands Long Duc Hall, west is Tho Cong Shrine, "
            "southeast is Chieu Kinh Hall, opposite it is Muc Tu Hall. "
            "The entire complex is enclosed by brick walls with five gates opening to all directions. "
            "Tragically, in early 1947, the entire complex was burned down during the scorched-earth campaign. "
            "In 1971-1972, the Nguyen Phuc clan council and Empress Tu Cung raised funds to rebuild a 5-bay hall on the original foundation. "
            "In October 2024, a 52-billion-VND restoration project began, expected to complete by 2028. "
            "A monument slowly being revived so future generations can know and take pride in their heritage."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4699109,
        "longitude": 107.5803246
    },
    {
        "loc_id": 1,
        "name_vi": "Cửa Hiển Nhơn",
        "name_en": "Hien Nhon Gate (Gate of Manifest Benevolence)",
        "history_text_vi": (
            "Cửa Hiển Nhơn là cánh cổng phía Đông của Hoàng thành Huế, được xây dựng dưới thời vua Gia Long "
            "với kiến trúc tương tự Cửa Chương Đức ở phía Tây. "
            "Tên gọi 'Hiển Nhơn' mang một ý nghĩa nhân văn sâu sắc: 'biểu lộ lòng nhân ái' — "
            "một lời nhắc nhở về đức tính quan trọng nhất của người cầm quyền. "
            "Cổng có vọng lâu hai tầng trên nền gạch đá vững chãi, với kiến trúc thanh thoát nhưng không kém phần uy nghiêm. "
            "Đây là một trong bốn cổng chính để ra vào Hoàng thành, dẫn đến khu vực phía Đông "
            "nơi có các miếu thờ tổ tiên hoàng gia như Thái Miếu và Triệu Miếu. "
            "Cổng được xây dựng kiên cố với phần nền đài cao bằng gạch vồ và đá thanh, "
            "phần lầu canh hai tầng lợp ngói lưu ly xanh, bờ mái trang trí hình rồng uốn lượn mềm mại. "
            "Cửa Hiển Nhơn không chỉ là một lối đi, mà còn là một tác phẩm nghệ thuật kiến trúc, "
            "với những đường nét chạm khắc tinh xảo trên gỗ và những họa tiết trang trí mang đậm phong cách cung đình Huế. "
            "Ngày nay, Cửa Hiển Nhơn là một trong những lối ra phổ biến cho du khách sau khi tham quan Đại Nội, "
            "dẫn ra khu vực phố thị nhộn nhịp bên ngoài. "
            "Khi bước qua cánh cổng này, bạn rời khỏi không gian tĩnh lặng của hoàng cung để bước vào cuộc sống sôi động của phố phường Huế — "
            "những hàng quán cà phê, những tiệm bánh nón, tiếng cười nói rộn ràng của người dân địa phương. "
            "Hãy dừng lại một lát trước khi rời đi, ngắm nhìn kiến trúc của cổng và cảm nhận sự chuyển giao "
            "giữa không gian hoàng cung linh thiêng và cuộc sống đời thường sôi động bên ngoài — "
            "một ranh giới mỏng manh giữa hai thế giới mà bạn có thể cảm nhận rõ ràng ngay tại đây."
        ),
        "history_text_en": (
            "Hien Nhon Gate is the eastern gate of the Hue Imperial City, built under Emperor Gia Long "
            "with architecture similar to Chuong Duc Gate on the west. "
            "Its name bears a profound humanistic meaning: 'Manifest Benevolence' — "
            "a reminder of the most important virtue for those who rule. "
            "The gate features a two-story watchtower on a solid brick-and-stone foundation, with elegant yet dignified architecture. "
            "It is one of four main gates of the Imperial City, leading to the eastern quarter "
            "where royal ancestral temples such as Thai Mieu and Trieu Mieu are located. "
            "The gate was solidly constructed with a high platform made of large baked bricks and Thanh stone, "
            "with a two-story watchtower roofed with blue-glazed tiles and adorned with gracefully curved dragon motifs. "
            "Hien Nhon Gate is not merely a passageway but a masterpiece of architectural art, "
            "with intricate wood carvings and ornamental motifs imbued with the distinctive Hue court style. "
            "Today, Hien Nhon Gate is a common exit for visitors leaving the Imperial City, "
            "leading out to the bustling streets beyond. "
            "As you step through this gate, you leave the serene space of the royal court and enter the vibrant life of Hue's streets — "
            "coffee shops, conical hat stalls, the lively chatter of local people going about their daily lives. "
            "Pause for a moment before leaving, admire the gate's architecture and feel the transition "
            "between the sacred royal court space and the vibrant everyday life outside — "
            "a delicate boundary between two worlds that you can feel distinctly right here."
        ),
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4707473,
        "longitude": 107.5805514
    },
    {
        "loc_id": 1,
        "name_vi": "Điện Long An (Bảo tàng Cổ vật Cung đình Huế)",
        "name_en": "Long An Palace (Hue Royal Antiquities Museum)",
        "history_text_vi": (
            "Điện Long An là một kiệt tác kiến trúc gỗ thời Nguyễn, được vua Thiệu Trị xây dựng vào năm 1845 "
            "trong khuôn viên cung Bảo Định làm nơi nghỉ ngơi sau lễ Tịch điền mỗi đầu xuân. "
            "Vua Thiệu Trị thường lui tới đây để đọc sách, làm thơ, ngâm vịnh. "
            "Sau khi vua qua đời, điện từng là nơi quàn thi hài của vua trong tám tháng trước khi làm lễ an táng. "
            "Năm 1885, sau biến cố thất thủ kinh đô, điện bị quân Pháp triệt hạ và đồ thờ bị cướp phá. "
            "Năm 1909, điện được chuyển về vị trí hiện nay và trở thành Tân Thơ Viện, "
            "nơi lưu giữ hàng ngàn tư liệu chữ Hán, Pháp, Anh. "
            "Điện hình chữ nhật dài 35,7m, rộng 28m, diện tích mái lên đến 1.750m², nằm trên 128 cột gỗ lim vững chãi. "
            "Điểm đặc biệt là các chi tiết gỗ không sơn son thếp vàng mà để mộc, "
            "được chạm trổ tinh xảo với các đồ án 'lưỡng long triều nguyệt', 'long, lân, quy, phượng' — "
            "một phong cách trang trí độc đáo hiếm thấy trong các cung điện Huế. "
            "Trong điện còn có hai bài thơ chữ Hán đặc biệt của vua Thiệu Trị được làm theo thể 'hồi văn kiêm liên hoàn' gồm 56 chữ, "
            "có thể đọc xuôi ngược thành 64 bài thơ khác nhau mà các nhà thơ đến nay vẫn chưa giải mã hết. "
            "Năm 1923, điện trở thành Bảo tàng Khải Định, nay là Bảo tàng Cổ vật Cung đình Huế, "
            "lưu giữ hơn 10.000 hiện vật quý giá gồm đồ vàng, đồ sứ, trang phục hoàng gia, nhạc khí cung đình và các cổ vật Chăm pa. "
            "Bộ sưu tập đầu hồ — một trò chơi cung đình xưa — và các bức tranh gương hơn 150 năm tuổi là những hiện vật vô giá. "
            "Đây là bảo tàng duy nhất ở Việt Nam có số lượng hiện vật khổng lồ của một triều đại phong kiến — "
            "một kho báu vô giá của văn hóa dân tộc đang chờ bạn khám phá."
        ),
        "history_text_en": (
            "Long An Palace is a masterpiece of Nguyen wooden architecture, built in 1845 by Emperor Thieu Tri "
            "within the Bao Dinh Palace grounds as his retreat after the annual Plowing Ceremony each early spring. "
            "Emperor Thieu Tri often came here to read, compose poetry, and relax. "
            "After his death, his body lay in state here for eight months before the funeral. "
            "In 1885, after the fall of the capital, the palace was ransacked by French forces and stripped of its ceremonial objects. "
            "In 1909, it was relocated to its current site and became the Tan Thu Vien library, "
            "housing thousands of documents in Chinese, French, and English. "
            "The rectangular building measures 35.7m by 28m, with a roof spanning 1,750 square meters, resting on 128 ironwood columns. "
            "A unique feature: the wooden details are left unpainted instead of the usual red-and-gold lacquer, "
            "with exquisite carvings of 'two dragons facing the moon', and the 'dragon, unicorn, turtle, phoenix' motifs — "
            "a rare decorative style among Hue's palaces. "
            "Inside are two special Chinese poems by Emperor Thieu Tri composed in the 'palindrome chain' style using 56 characters, "
            "which can be read forwards and backwards to form 64 different poems — a mystery that poets still haven't fully solved. "
            "In 1923, it became the Khai Dinh Museum, now the Hue Royal Antiquities Museum, "
            "preserving over 10,000 precious artifacts including gold, porcelain, royal costumes, court musical instruments, and Cham antiquities. "
            "The collection of Dau Ho — an ancient court game — and mirror paintings over 150 years old are among its priceless treasures. "
            "It is the only museum in Vietnam with such a vast collection from a single feudal dynasty — "
            "a priceless national cultural treasure waiting for you to discover."
        ),
        "author": "Vua Thiệu Trị",
        "year": 1845,
        "latitude": 16.4712819,
        "longitude": 107.5818602
    },
    {
        "loc_id": 1,
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate (Meridian Gate)",
        "history_text_vi": (
            "Ngọ Môn là cổng chính phía Nam của Hoàng thành Huế — bộ mặt của cả một triều đại và là cổng lớn nhất trong bốn cổng chính. "
            "Được xây dựng vào năm 1833 dưới triều vua Minh Mạng, Ngọ Môn thay thế cho Nam Khuyết Đài thời Gia Long. "
            "Tên gọi 'Ngọ Môn' có nghĩa là 'cổng hướng về phương Ngọ' — tức phương Nam, "
            "hướng mà bậc thiên tử quay mặt để cai trị thiên hạ theo quan niệm 'Thánh nhân Nam diện nhi thính thiên hạ'. "
            "Kiến trúc Ngọ Môn gồm hai phần chính: phần đài cổng hình chữ U vững chãi và phần lầu Ngũ Phụng thanh thoát phía trên. "
            "Đài cao gần 5m, diện tích hơn 1.560m², đáy dài 57,77m, trổ 5 lối đi. "
            "Lối chính giữa (Ngọ Môn) dành riêng cho vua, hai lối bên (Tả Giáp Môn và Hữu Giáp Môn) cho quan văn võ, "
            "hai lối ngoài cùng (Tả Dịch Môn và Hữu Dịch Môn) cho binh lính và voi ngựa. "
            "Lầu Ngũ Phụng có hai tầng, kết cấu hoàn toàn bằng gỗ lim với chẵn 100 cây cột, "
            "mái chính giữa lợp ngói lưu ly vàng, tám mái còn lại lợp ngói xanh, "
            "với nhiều hình chim phụng trang trí ở bờ nóc và bờ quyết. "
            "Ngoài ra còn có 4 tòa nhà nhỏ phụ trợ hai bên Đông, Tây dực lâu. "
            "Ngọ Môn chứng kiến nhiều sự kiện lịch sử trọng đại: lễ Ban Sóc (ban lịch mới), lễ Truyền Lô (tuyên đọc tên tiến sĩ), "
            "và đặc biệt là ngày 30 tháng 8 năm 1945, vua Bảo Đại đọc Tuyên ngôn Thoái vị, "
            "trao chính quyền lại cho Chính phủ Lâm thời, khép lại chế độ quân chủ hơn 143 năm. "
            "Năm 1968, Ngọ Môn bị hư hại nặng trong trận Mậu Thân và được trùng tu với kinh phí 80 tỷ đồng, hoàn thành năm 2019. "
            "Câu ca dao xưa nhắc: 'Ngọ Môn 5 cửa 9 lầu, 1 lầu vàng 8 lầu xanh, 3 cửa thẳng 2 cửa quanh' — "
            "hãy tự mình kiểm tra xem có đúng không nhé!"
        ),
        "history_text_en": (
            "Ngo Mon Gate (Meridian Gate) is the main southern entrance of the Hue Imperial City — "
            "the very face of an entire dynasty and the grandest of the four main gates. "
            "Built in 1833 under Emperor Minh Mang, it replaced the Nam Khuyet Dai platform from Gia Long's reign. "
            "The name 'Ngo Mon' means 'gate facing the Meridian direction' — the south, "
            "the direction the Son of Heaven faces to rule the empire, based on the ancient concept that 'the sage king faces south to hear the world'. "
            "The gate consists of two main parts: a solid U-shaped stone platform and the graceful Five Phoenix Pavilion above. "
            "The platform stands nearly 5m tall, covering over 1,560 square meters, 57.77m long at the base, with five passageways. "
            "The central passage (Ngo Mon) was reserved for the emperor, "
            "the two side passages (Ta Giap Mon and Huu Giap Mon) for civil and military mandarins, "
            "and the outermost two (Ta Dich Mon and Huu Dich Mon) for soldiers, elephants, and horses. "
            "The Five Phoenix Pavilion has two levels, entirely built from ironwood with exactly 100 columns, "
            "with a yellow-glazed central roof and eight surrounding blue-glazed ones, "
            "adorned with numerous phoenix figures along the roof ridges and edges. "
            "There were also four auxiliary buildings on the east and west sides. "
            "Ngo Mon witnessed many historic events: the Ban Soc calendar ceremony, the Truyen Lo doctorate announcement, "
            "and most notably on August 30, 1945, Emperor Bao Dai's Abdication Proclamation, "
            "handing over power to the Provisional Government and ending over 143 years of monarchy. "
            "In 1968, Ngo Mon was severely damaged during the Tet Offensive and was restored at a cost of 80 billion VND, completed in 2019. "
            "An old folk rhyme describes: 'Ngo Mon has 5 gates and 9 towers, 1 golden tower and 8 blue towers, "
            "3 straight gates and 2 angled gates' — see if you can verify this yourself!"
        ),
        "author": "Triều Nguyễn / Vua Minh Mạng",
        "year": 1833,
        "latitude": 16.468083,
        "longitude": 107.578667
    }
]

PRECOMPUTED_AUDIO = []

# ─── Bilingual Content ─────────────────────────────────────────────────────────
# Each entry references artifact by name_vi (resolved at seed time) and provides
# language-specific blocks for: visit_highlights, visit_route, nearby_context,
# notable_objects, photo_spots.
# Schema: (artifact_name_vi, lang, content_type, content_text)
BILINGUAL_CONTENT_RAW = [

    # ── 1. Cửa Hòa Bình ──────────────────────────────────────────────────────
    ("Cửa Hòa Bình", "vi", "visit_highlights",
        "Phần đài bên dưới: nền gạch đá hình thang vững chãi, bốn bức tường phủ rêu phong cổ kính. "
        "Lầu canh hai tầng bên trên: mái ngói cong uyển chuyển, đường chạm khắc hoa lá trên gỗ. "
        "Hướng Bắc nhìn ra dòng sông Hương thơ mộng qua cổng. "
        "Khoảng sân nhỏ trong lòng cổng: không gian chuyển giao giữa nội và ngoại thành."
    ),
    ("Cửa Hòa Bình", "vi", "visit_route",
        "Bắt đầu từ phía ngoài, quan sát tổng thể phần đài bằng gạch đá và hai cánh cổng gỗ. "
        "Bước qua ngưỡng cửa, chú ý tấm đá lát bên dưới đã mòn sau hàng thế kỷ. "
        "Đứng trong lòng cổng nhìn lên hệ thống mái lầu hai tầng — quan sát đầu đao và hoa văn trên nóc. "
        "Ra phía trong, quay lại nhìn toàn bộ mặt Nam cổng — bố cục đối xứng hoàn hảo. "
        "Từ đây có thể đi về phía Đông tới Điện Kiến Trung hoặc phía Tây tới Cung Trường Sanh."
    ),
    ("Cửa Hòa Bình", "vi", "nearby_context",
        "Ngay phía Nam cổng: đường lớn nội thành dẫn về Điện Thái Hòa và Ngọ Môn. "
        "Phía Tây: Cung Trường Sanh — nơi nghỉ ngơi của các Hoàng thái hậu. "
        "Phía Đông: Điện Kiến Trung — cung điện cuối cùng thời Nguyễn, vừa được phục dựng năm 2024."
    ),
    ("Cửa Hòa Bình", "en", "visit_highlights",
        "The lower platform: solid trapezoidal brick-and-stone base with moss-covered walls. "
        "The two-story watchtower above: gracefully curved tiled roofs, intricate wood carvings of floral motifs. "
        "Northward view toward the poetic Perfume River through the gate. "
        "The small courtyard inside the gate: a transitional space between the inner and outer city."
    ),
    ("Cửa Hòa Bình", "en", "visit_route",
        "Start from outside: take in the full view of the brick platform and wooden gate panels. "
        "Step through the threshold — notice the worn stone pavement, polished by centuries of feet. "
        "Stand inside the gate and look up at the two-tier roof structure — observe the upturned eaves and ridge carvings. "
        "Step inside the city, then turn back to admire the symmetrical south-facing facade of the gate. "
        "From here you can head east to Kien Trung Palace or west to Truong Sanh Palace."
    ),
    ("Cửa Hòa Bình", "en", "nearby_context",
        "Just south of the gate: the main inner-city road leading to Thai Hoa Palace and Ngo Mon. "
        "To the west: Truong Sanh Palace — the Queen Mothers' retreat. "
        "To the east: Kien Trung Palace — the last Nguyen-era palace, just restored in 2024."
    ),

    # ── 2. Điện Kiến Trung ────────────────────────────────────────────────────
    ("Điện Kiến Trung", "vi", "visit_highlights",
        "Mặt tiền Đông – Tây khảm gốm sứ đa màu sắc — điểm nhấn kiến trúc Đông Dương độc đáo. "
        "Ba cầu thang rồng đắp nổi uốn lượn dẫn lên thềm điện. "
        "Tầng một: 13 cửa hiên vòm Baroque, ban công tầng hai lan can trang trí Việt Nam. "
        "Nội thất: bàn làm việc phòng của vua Bảo Đại được phục dựng, bản đồ toàn quốc treo tường. "
        "Sân thượng tầng hai: view nhìn xuống toàn bộ Tử Cấm Thành về phía Nam."
    ),
    ("Điện Kiến Trung", "vi", "visit_route",
        "Tiếp cận từ phía Nam qua sân vườn với ba cầu thang rồng. "
        "Chiêm ngưỡng toàn bộ mặt tiền trước khi bước lên — chú ý mảnh sứ khảm và cột đèn kiểu Pháp. "
        "Bước vào tầng một: quan sát khu vực phòng khách, không gian làm việc và cầu thang rộng giữa nhà. "
        "Lên tầng hai: phòng ngủ hoàng gia và ban công nhìn ra vườn phía trước. "
        "Ra phía sân thượng để ngắm tổng thể Tử Cấm Thành từ trên cao — hướng về Điện Thái Hòa ở phía Nam."
    ),
    ("Điện Kiến Trung", "vi", "nearby_context",
        "Phía Nam: Điện Thái Hòa và sân Đại triều nghi nổi tiếng. "
        "Phía Bắc: Cửa Hòa Bình và hướng ra sông Hương. "
        "Gần đó: Duyệt Thị Đường — nhà hát cung đình còn nguyên vẹn nhất Việt Nam."
    ),
    ("Điện Kiến Trung", "vi", "notable_objects",
        "Bộ gốm sứ khảm mặt tiền: hàng trăm mảnh ghép tạo thành những bức tranh phong cảnh. "
        "Cầu thang rồng: đá đắp nổi hình rồng uốn lượn — biểu tượng quyền uy. "
        "Đèn chùm pha lê phòng đón khách: di vật thời Khải Định — Bảo Đại. "
        "Bản đồ Đông Dương và phòng làm việc của vua Bảo Đại: tái hiện chính xác theo tư liệu lịch sử."
    ),
    ("Điện Kiến Trung", "en", "visit_highlights",
        "East-West facade inlaid with multi-colored ceramic mosaics — the hallmark of Indochinese architecture. "
        "Three dragon-carved staircases with raised relief sweeping up to the main hall. "
        "Ground floor: 13 arched Baroque-style windows; second-floor balcony with Vietnamese-style railings. "
        "Interior: Emperor Bao Dai's restored office and a full map of Indochina on the wall. "
        "Second-floor terrace: panoramic view over the entire Forbidden Purple City to the south."
    ),
    ("Điện Kiến Trung", "en", "visit_route",
        "Approach from the south through the garden with the three dragon staircases. "
        "Admire the full facade before ascending — note the ceramic inlays and French-style lampposts. "
        "Enter the ground floor: observe the reception room, workspace, and the wide central staircase. "
        "Head to the second floor: the royal bedroom and balcony overlooking the front garden. "
        "Step onto the terrace to see the full sweep of the Forbidden Purple City — facing Thai Hoa Palace to the south."
    ),
    ("Điện Kiến Trung", "en", "nearby_context",
        "To the south: Thai Hoa Palace and the famous Great Court Yard. "
        "To the north: Hoa Binh Gate and the road toward the Perfume River. "
        "Nearby: Duyet Thi Duong Theater — Vietnam's best-preserved royal theater."
    ),
    ("Điện Kiến Trung", "en", "notable_objects",
        "The ceramic mosaic facade: hundreds of shards forming landscape paintings. "
        "Dragon staircases: raised-relief stone carvings symbolizing imperial power. "
        "Crystal chandeliers in the reception room: artifacts from the Khai Dinh – Bao Dai era. "
        "Map of Indochina and Bao Dai's office: historically accurate recreation."
    ),

    # ── 3. Cung Trường Sanh ───────────────────────────────────────────────────
    ("Cung Trường Sanh", "vi", "visit_highlights",
        "Cổng Trường An môn kiểu tam quan, trang trí hoa lá ngũ sắc rực rỡ. "
        "Lạch Đào Nguyên nhân tạo uốn lượn quanh cung — bắc qua những cây cầu đỏ duyên dáng. "
        "Hồ Tân Nguyệt và các non bộ giả sơn mang tên Bảo Sơn, Kình Ngư, Hổ Tôn. "
        "Điện Thọ Khang ở trung tâm: nơi Hoàng thái hậu tiếp khách và sống thường nhật. "
        "Lầu Vạn Phước phía sau: tầm nhìn ra khu vườn và khoảng trời phía Bắc."
    ),
    ("Cung Trường Sanh", "vi", "visit_route",
        "Vào từ cổng Trường An môn phía Đông — quan sát hoa văn ngũ sắc trên mặt tiền cổng. "
        "Đi vòng theo lạch Đào Nguyên, dừng lại trên cây cầu đỏ để nhìn xuống lạch nước. "
        "Ghé thăm các non bộ giả sơn — từ đây nhìn lại Điện Thọ Khang sẽ thấy rõ bố cục chữ Vương. "
        "Vào Điện Thọ Khang xem nội thất và hệ thống hành lang có mái che kết nối các khu. "
        "Ra phía sau thăm lầu Vạn Phước và hồ Tân Nguyệt trước khi rời cung."
    ),
    ("Cung Trường Sanh", "vi", "nearby_context",
        "Phía Đông: Cung Diên Thọ — không gian thâm cung của các bà Hoàng thái hậu lớn hơn. "
        "Phía Bắc: Cửa Hòa Bình và khu vực Điện Kiến Trung. "
        "Phía Nam: Cửa Chương Đức dẫn ra phố thị phía Tây."
    ),
    ("Cung Trường Sanh", "en", "visit_highlights",
        "Truong An Mon triple-arched gate, decorated with vibrant five-color floral motifs. "
        "The artificial Peach Spring stream winding through the grounds — crossed by elegant red bridges. "
        "Tan Nguyet Lake and the rockery mountains named Bao Son, Kinh Ngu, and Ho Ton. "
        "Tho Khang Hall at the center: the Queen Mother's reception and daily living quarters. "
        "Van Phuoc Tower at the rear: views over the garden and the northern sky."
    ),
    ("Cung Trường Sanh", "en", "visit_route",
        "Enter through Truong An Mon gate on the east — observe the five-color floral patterns on the facade. "
        "Walk along the Peach Spring stream and pause on the red bridge to look down at the water. "
        "Visit the rockery mountains — from here, looking back at Tho Khang Hall reveals the King-character layout. "
        "Enter Tho Khang Hall to see the interior and the covered corridor system connecting all sections. "
        "Head to the rear to visit Van Phuoc Tower and Tan Nguyet Lake before leaving."
    ),
    ("Cung Trường Sanh", "en", "nearby_context",
        "To the east: Dien Tho Palace — the larger inner sanctum of the Queen Mothers. "
        "To the north: Hoa Binh Gate and the Kien Trung Palace area. "
        "To the south: Chuong Duc Gate leading out to the western streets."
    ),

    # ── 4. Cung Diên Thọ ──────────────────────────────────────────────────────
    ("Cung Diên Thọ", "vi", "visit_highlights",
        "Chính điện Diên Thọ: 80 cột gỗ lim sơn đen, mái lưu ly vàng — uy nghiêm mà ấm áp. "
        "Tạ Trường Du: ngôi nhà tạ xây trên hồ, 16 cột, mái ngói men xanh thanh thoát. "
        "Lầu Tịnh Minh: tầng cao nhất trong cụm, nhìn bao quát toàn khu. "
        "Các Khương Ninh: không gian thờ Phật và nghệ thuật hát bội duy nhất còn sót lại. "
        "Hệ thống hành lang mái men xanh kết nối tất cả công trình — dài nhất Hoàng thành Huế."
    ),
    ("Cung Diên Thọ", "vi", "visit_route",
        "Vào từ cửa chính phía Nam — quan sát bình phong khắc hình long phụng trước sân. "
        "Bước vào chính điện Diên Thọ: đếm 80 cột lim sơn đen, ngắm ngai Hoàng thái hậu. "
        "Đi qua hành lang men xanh sang tạ Trường Du — đứng trên tạ nhìn xuống mặt hồ. "
        "Thăm lầu Tịnh Minh từ hành lang phía Tây — leo cầu thang gỗ lên tầng trên. "
        "Kết thúc ở các Khương Ninh phía Đông — chiêm ngưỡng ba pho tượng Tam Thế Phật bằng gang mạ vàng."
    ),
    ("Cung Diên Thọ", "vi", "nearby_context",
        "Ngay phía Tây: Cung Trường Sanh — cung điện khác của Hoàng thái hậu. "
        "Phía Nam: Cửa Chương Đức dẫn ra phố. "
        "Phía Đông: Hưng Miếu và Thế Miếu — hệ thống miếu thờ triều Nguyễn."
    ),
    ("Cung Diên Thọ", "vi", "notable_objects",
        "Ngai Hoàng thái hậu: sơn son thếp vàng, đặt trong hậu cung chính điện. "
        "Bộ tượng Tam Thế Phật gang mạ vàng: được đánh giá đẹp nhất thời Nguyễn. "
        "Binh phong trước cửa: chạm khắc long phụng, bảo vệ phong thủy cho chính điện. "
        "Giếng vuông cổ kính trong sân: nguồn nước sinh hoạt của cung xưa."
    ),
    ("Cung Diên Thọ", "en", "visit_highlights",
        "Dien Tho Main Hall: 80 black-lacquered ironwood columns, yellow-glazed roof — majestic yet warm. "
        "Truong Du Pavilion: a pavilion built on a lake, 16 columns, graceful blue-glazed tile roof. "
        "Tinh Minh Tower: the tallest structure in the complex, with panoramic views. "
        "Khuong Ninh Hall: the only surviving space for Buddhist worship and royal opera tradition. "
        "Blue-glazed corridor system connecting all structures — the longest in the Imperial City."
    ),
    ("Cung Diên Thọ", "en", "visit_route",
        "Enter through the south gate — observe the screen wall carved with dragon-phoenix motifs. "
        "Step into the Dien Tho Main Hall: count the 80 black columns, admire the Queen Mother's throne. "
        "Walk through the blue-glazed corridor to Truong Du Pavilion — stand on the pavilion and look down at the lake. "
        "Visit Tinh Minh Tower from the west corridor — climb the wooden staircase to the upper level. "
        "Finish at Khuong Ninh Hall to the east — admire the three gilded cast-iron Buddha statues."
    ),
    ("Cung Diên Thọ", "en", "nearby_context",
        "Immediately to the west: Truong Sanh Palace — another Queen Mother's palace. "
        "To the south: Chuong Duc Gate leading to the streets. "
        "To the east: Hung Mieu and The Mieu — the Nguyen ancestral temple complex."
    ),
    ("Cung Diên Thọ", "en", "notable_objects",
        "Queen Mother's throne: red-lacquered and gold-gilded, placed in the main hall's inner chamber. "
        "Three gilded cast-iron Buddhas: considered the most beautiful Buddhist statues of the Nguyen era. "
        "Screen wall at the gate: carved with dragons and phoenixes to protect feng shui. "
        "Ancient square well in the courtyard: the palace's historic water source."
    ),

    # ── 5. Cửa Chương Đức ────────────────────────────────────────────────────
    ("Cửa Chương Đức", "vi", "visit_highlights",
        "Lầu canh hai tầng: mái ngói cong cong, gờ mái đắp rồng uốn lượn mềm mại. "
        "Nền đài cao bằng gạch vồ và đá thanh: biểu tượng sức mạnh phòng thủ của Hoàng thành. "
        "Trục đường Tây: nhìn từ cổng thấy thẳng vào khu vực cung Diên Thọ và Trường Sanh."
    ),
    ("Cửa Chương Đức", "vi", "visit_route",
        "Quan sát mặt Tây ngoài thành trước — nhìn bốn bức tường rêu phong và hào nước. "
        "Bước qua cổng vào trong, chú ý lối đi chính giữa rộng hơn hai lối phụ hai bên. "
        "Nhìn lên phía lầu canh để thấy hoa văn chạm khắc trên gỗ và gờ mái. "
        "Từ trong cổng, theo trục đường chính đi thẳng vào khu Cung Diên Thọ."
    ),
    ("Cửa Chương Đức", "vi", "nearby_context",
        "Phía Đông: Cung Diên Thọ và Cung Trường Sanh. "
        "Đối xứng phía Đông thành: Cửa Hiển Nhơn — đối xứng với cổng này theo trục Đông-Tây."
    ),
    ("Cửa Chương Đức", "en", "visit_highlights",
        "Two-story watchtower: curved tiled roofs, roof ridges adorned with gracefully curved dragon motifs. "
        "High platform made of large baked bricks and Thanh stone: a symbol of the Imperial City's defensive strength. "
        "Western road axis: looking from the gate you can see straight to Dien Tho and Truong Sanh Palaces."
    ),
    ("Cửa Chương Đức", "en", "visit_route",
        "Observe the exterior west face first — the moss-covered walls and moat. "
        "Pass through the gate: notice the wider central passage versus the two narrower side passages. "
        "Look up at the watchtower to see the carved wood carvings and roof ridges. "
        "From inside the gate, follow the main road straight into the Dien Tho Palace area."
    ),
    ("Cửa Chương Đức", "en", "nearby_context",
        "To the east: Dien Tho Palace and Truong Sanh Palace. "
        "Symmetrically on the east wall: Hien Nhon Gate — its mirror counterpart on the east-west axis."
    ),

    # ── 6. Hưng Miếu ─────────────────────────────────────────────────────────
    ("Hưng Miếu (Hưng Tổ Miếu)", "vi", "visit_highlights",
        "Chính điện gỗ lim trùng diêm: mái lợp ngói âm dương men vàng, các chi tiết chạm trổ hoa lá tinh xảo. "
        "Đường thần đạo: đá Thanh rộng 2,15m dẫn từ bậc thềm ra miếu môn thẳng tắp. "
        "Thần Khố phía Đông và Thần Trù phía Tây: hai nhà phụ trợ cho nghi lễ tế tự. "
        "Sân lát gạch Bát Tràng: hình chữ nhật, hai bên có lư hương đá và chậu sứ cổ kính."
    ),
    ("Hưng Miếu (Hưng Tổ Miếu)", "vi", "visit_route",
        "Vào từ miếu môn phía Nam — đi theo đường thần đạo đá Thanh lên thềm. "
        "Dừng trước bậc thềm quan sát toàn bộ mặt tiền chính điện — kiến trúc gỗ trùng diêm 3 gian 2 chái. "
        "Vào bên trong chiêm ngưỡng bàn thờ và các hiện vật thờ phụng. "
        "Ghé Thần Khố bên Đông và Thần Trù bên Tây — hiểu rõ quy trình tổ chức lễ tế. "
        "Bước ra sân, quan sát kỹ các lư hương đá và hệ thống cổng rào bằng đá."
    ),
    ("Hưng Miếu (Hưng Tổ Miếu)", "vi", "nearby_context",
        "Ngay phía Bắc: Thế Miếu — nơi thờ các vua Nguyễn với Cửu Đỉnh đồng nổi tiếng. "
        "Phía Đông: Triệu Miếu và Thái Miếu. "
        "Cả khu này tạo thành tổ hợp miếu thờ triều Nguyễn ở góc Tây Nam Hoàng thành."
    ),
    ("Hưng Miếu (Hưng Tổ Miếu)", "en", "visit_highlights",
        "Double-eaved ironwood main hall: yellow-glazed yin-yang tiles, exquisitely carved floral details. "
        "Spirit path: 2.15-meter-wide Thanh stone walkway leading straight from the steps to the gate. "
        "God's Treasury on the east and God's Kitchen on the west: two ritual support buildings. "
        "Bat Trang brick courtyard: rectangular layout, flanked by stone incense burners and antique ceramic pots."
    ),
    ("Hưng Miếu (Hưng Tổ Miếu)", "en", "visit_route",
        "Enter through the south gate — walk along the Thanh stone spirit path up to the steps. "
        "Pause before the steps to take in the full facade — a 3-bay double-eaved wooden hall. "
        "Step inside to view the altar and ceremonial objects. "
        "Visit the God's Treasury (east) and God's Kitchen (west) to understand ceremonial preparation. "
        "Return to the courtyard to examine the stone incense burners and stone fence system."
    ),
    ("Hưng Miếu (Hưng Tổ Miếu)", "en", "nearby_context",
        "Just to the north: The Mieu — where Nguyen emperors are enshrined with the famous Nine Dynastic Urns. "
        "To the east: Trieu Mieu and Thai Mieu. "
        "Together these temples form the Nguyen ancestral worship complex in the southwest corner of the Imperial City."
    ),

    # ── 7. Thế Miếu ──────────────────────────────────────────────────────────
    ("Thế Miếu (Thế Tổ Miếu)", "vi", "visit_highlights",
        "Cửu Đỉnh (9 đỉnh đồng): mỗi đỉnh khoảng 2 tấn, chạm 17 hình ảnh đặc trưng Việt Nam — bảo vật quốc gia. "
        "Hiển Lâm các 3 tầng: ngọn tháp gỗ cao nhất Hoàng thành, nhìn thấy từ xa. "
        "Chính điện 9 gian 2 chái kép: bên trong 10 bàn thờ vua Nguyễn xếp theo lối tả chiêu hữu mục. "
        "Cây thông cổ thụ hơn 200 năm phía Tây tường — tương truyền trồng từ ngày dựng miếu. "
        "Lầu chuông, lầu trống hai bên Hiển Lâm các: âm thanh lễ tế xưa còn vang vọng."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "vi", "visit_route",
        "Vào từ phía Nam qua Tuấn Liệt môn hoặc Sùng Công môn — hai cổng hai bên Hiển Lâm các. "
        "Dừng trước Cửu Đỉnh: đi dọc theo hàng 9 đỉnh, tìm những hình ảnh quen thuộc như mặt trời, biển cả. "
        "Ngước nhìn Hiển Lâm các từ phía trước — ba tầng mái ngói chồng lên nhau tạo cảm giác kỳ vĩ. "
        "Vào chính điện để chiêm bái 10 bàn thờ vua Nguyễn — không khí trang nghiêm và u tịch. "
        "Trước khi ra, ghé cây thông cổ thụ phía Tây — đặt tay lên thân cây cảm nhận chiều dài lịch sử."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "vi", "nearby_context",
        "Ngay phía Nam: Hưng Miếu — thờ thân phụ vua Gia Long. "
        "Phía Đông: Triệu Miếu và Thái Miếu. "
        "Cả khu tạo thành tổ hợp miếu lớn nhất Hoàng thành, nên dành ít nhất 45 phút để tham quan đầy đủ."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "vi", "notable_objects",
        "Cửu Đỉnh: 9 đỉnh đồng đúc năm 1836 thời Minh Mạng, bảo vật quốc gia Việt Nam. "
        "Ngai thờ và long vị: sơn son thếp vàng, ghi danh hiệu từng vua Nguyễn. "
        "Lầu Chuông và Lầu Trống: chuông đồng và trống lớn dùng trong lễ tế hàng năm."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "en", "visit_highlights",
        "Nine Dynastic Urns (Cuu Dinh): each about 2 tons, engraved with 17 images of Vietnam — national treasures. "
        "Three-story Hien Lam Pavilion: the tallest wooden tower in the Imperial City, visible from afar. "
        "Main hall with 9 double-side bays: inside, 10 imperial shrines arranged by the ancient 'left-right' principle. "
        "Ancient pine tree over 200 years old by the west wall — said to have been planted when the temple was founded. "
        "Bell and drum towers flanking Hien Lam: echoes of centuries of ceremonial sound."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "en", "visit_route",
        "Enter from the south through Tuan Liet Mon or Sung Cong Mon — the two gates flanking Hien Lam. "
        "Stop at the Nine Dynastic Urns: walk along the row of 9 urns, seek out familiar images like the sun, sea, mountains. "
        "Look up at Hien Lam Pavilion from the front — three stacked roof tiers create a sense of grandeur. "
        "Enter the main hall to pay respects at the 10 imperial shrines — the atmosphere is solemn and still. "
        "Before leaving, visit the ancient pine to the west — place your hand on the trunk and feel centuries of history."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "en", "nearby_context",
        "Just to the south: Hung Mieu — honoring Emperor Gia Long's father. "
        "To the east: Trieu Mieu and Thai Mieu. "
        "Together they form the largest temple complex in the Imperial City — allow at least 45 minutes."
    ),
    ("Thế Miếu (Thế Tổ Miếu)", "en", "notable_objects",
        "Nine Dynastic Urns: cast in 1836 under Emperor Minh Mang, designated as Vietnamese national treasures. "
        "Shrines and spirit tablets: red-lacquered and gold-gilded, inscribed with each emperor's reign name. "
        "Bell Tower and Drum Tower: bronze bell and large drum used in annual ceremonial rites."
    ),

    # ── 8. Điện Thái Hòa ─────────────────────────────────────────────────────
    ("Điện Thái Hòa", "vi", "visit_highlights",
        "Mái chồng diêm ba tầng: ngói hoàng lưu ly chất thành tầng tầng lớp lớp — nhìn từ sân lên thấy rõ hiệu ứng. "
        "Dải cổ diêm quanh bốn mặt: 197 bài thơ trên pháp lam theo lối nhất thi nhất họa. "
        "80 cột gỗ lim sơn son thếp vàng: mỗi cột đều chạm hình rồng vờn mây. "
        "Ngai vàng trong cùng: sơn son thếp vàng, đặt trên bệ cao, nhìn ra cửa Ngọ Môn. "
        "Hai hàng đá đánh dấu vị trí bá quan văn võ trên sân Đại triều nghi."
    ),
    ("Điện Thái Hòa", "vi", "visit_route",
        "Đứng ở sân Đại triều nghi — tưởng tượng hàng trăm quan văn võ đứng hai bên theo phẩm trật. "
        "Bước dần lên 9 bậc thềm trước cửa — chú ý từng bậc đều bằng đá nguyên khối. "
        "Vào bên trong nhìn lên trần nhà: hệ thống xà gỗ chạm khắc tinh vi và màu sắc rực rỡ. "
        "Chiêm ngưỡng ngai vàng từ khoảng cách vừa phải — hướng mắt từ ngai ra cửa chính nhìn về Ngọ Môn. "
        "Đi ra hai bên hành lang để xem chi tiết cổ diêm và pháp lam ở tầm gần."
    ),
    ("Điện Thái Hòa", "vi", "nearby_context",
        "Phía Nam: sân Đại triều nghi và Ngọ Môn — đây là trục thần đạo chính của Hoàng thành. "
        "Phía Bắc: Nền điện Cần Chánh — nơi vua làm việc hàng ngày (trung tâm hành chính). "
        "Hai bên: Tả Vu và Hữu Vu — nơi quan chờ thiết triều."
    ),
    ("Điện Thái Hòa", "vi", "notable_objects",
        "Ngai vàng: sơn son thếp vàng, bảo vật quốc gia, đặt trên bệ đá cao 3 cấp. "
        "Bảo tán vàng: lọng vàng treo trên ngai, biểu tượng quyền lực tối cao. "
        "Long đèn: đèn chùm hình rồng treo trên trần điện, thắp sáng trong các buổi thiết triều. "
        "Pháp lam: 197 bài thơ trên men màu — kỹ thuật điêu luyện thời Nguyễn."
    ),
    ("Điện Thái Hòa", "en", "visit_highlights",
        "Three-tier stacked roof: yellow-glazed tiles in ascending layers — most striking when viewed from the courtyard. "
        "Decorative frieze encircling all four sides: 197 enamel poems in the 'one poem, one painting' style. "
        "80 gold-gilded red-lacquered ironwood columns: each carved with dragons dancing among clouds. "
        "Golden throne in the innermost chamber: elevated on a three-step stone base, facing Ngo Mon. "
        "Two rows of stone markers in the Great Court Yard: the positions of civil and military mandarins."
    ),
    ("Điện Thái Hòa", "en", "visit_route",
        "Stand in the Great Court Yard — imagine hundreds of ranked mandarins standing on either side. "
        "Ascend the 9 stone steps to the main entrance — each step is carved from a single stone block. "
        "Step inside and look up: the intricately carved and vibrantly colored wooden beam system. "
        "View the golden throne from a respectful distance — trace the sight line from throne to Ngo Mon Gate. "
        "Walk along the side galleries to examine the enamel frieze and patterned carvings up close."
    ),
    ("Điện Thái Hòa", "en", "nearby_context",
        "To the south: the Great Court Yard and Ngo Mon Gate — the main spirit axis of the Imperial City. "
        "To the north: the Can Chanh Palace Foundation — the emperor's daily workspace. "
        "On both sides: Ta Vu and Huu Vu halls — where officials waited for court audiences."
    ),
    ("Điện Thái Hòa", "en", "notable_objects",
        "Golden throne: red-lacquered and gold-gilded national treasure, on a three-step stone pedestal. "
        "Royal canopy: a gilded ceremonial parasol above the throne, symbol of supreme power. "
        "Dragon lanterns: dragon-shaped chandeliers hanging from the ceiling, lit during court audiences. "
        "Enamel plaques: 197 poems in polychrome enamel — a pinnacle of Nguyen craftsmanship."
    ),
    ("Điện Thái Hòa", "en", "photo_spots",
        "Best shot: stand at the south edge of the Great Court Yard, align the two rows of stone markers with the palace entrance. "
        "Close-up: the golden throne through the main doorframe. "
        "Wide view: from the top of the 9 steps looking back down the court yard toward Ngo Mon."
    ),
    ("Điện Thái Hòa", "vi", "photo_spots",
        "Góc chụp đẹp nhất: đứng cuối sân Đại triều nghi, căn hai hàng đá đánh dấu bá quan với cửa điện làm trung tâm. "
        "Chụp cận: ngai vàng qua khung cửa chính. "
        "Góc rộng: từ đỉnh 9 bậc thềm nhìn ngược lại sân về phía Ngọ Môn."
    ),

    # ── 9. Nền điện Cần Chánh ─────────────────────────────────────────────────
    ("Nền điện Cần Chánh", "vi", "visit_highlights",
        "Nền móng đá Thanh: hệ thống bệ đá và móng tường phác thảo rõ bố cục nguyên bản điện 9 gian 2 chái. "
        "Cột đá chân tảng: các viên đá kê cột còn nguyên vị trí, cho thấy quy mô của điện xưa. "
        "Bảng thuyết minh phục dựng 3D: hình ảnh mô phỏng điện khi còn nguyên vẹn trước năm 1947."
    ),
    ("Nền điện Cần Chánh", "vi", "visit_route",
        "Từ Điện Thái Hòa đi thẳng về hướng Bắc — Nền điện Cần Chánh nằm ngay trên trục thần đạo chính. "
        "Đứng ở rìa phía Nam nền nhìn vào trong để nhận ra bố cục gian và chái qua hệ thống chân cột. "
        "Di chuyển dọc theo rìa nền để quan sát toàn bộ chu vi — chu vi rộng hơn nhiều so với tưởng tượng. "
        "Đọc các biển giải thích về chức năng từng khu vực: hậu đường nơi vua nghỉ, tiền đường nơi thiết triều nhỏ."
    ),
    ("Nền điện Cần Chánh", "vi", "nearby_context",
        "Ngay phía Nam: Điện Thái Hòa — biểu tượng quyền lực nghi lễ. "
        "Phía Bắc trên trục thần đạo: Điện Kiến Trung — nơi ở của vua. "
        "Hai bên: Tả Vu Hữu Vu và các công trình Tử Cấm Thành."
    ),
    ("Nền điện Cần Chánh", "en", "visit_highlights",
        "Thanh stone foundation: the system of stone bases and wall footings outlines the original 9-bay 2-wing layout. "
        "Column base stones: the original stone column pads still in place, showing the scale of the former palace. "
        "3D restoration panels: visual reconstructions of how the palace looked before its destruction in 1947."
    ),
    ("Nền điện Cần Chánh", "en", "visit_route",
        "From Thai Hoa Palace, walk straight north — Can Chanh Foundation lies directly on the main spirit axis. "
        "Stand at the south edge of the foundation and look inward to trace the bay-and-wing layout from the column bases. "
        "Walk around the perimeter to understand the full scale — it is much larger than expected. "
        "Read the interpretation panels for each zone: the rear hall where the emperor rested, the front hall for small audiences."
    ),
    ("Nền điện Cần Chánh", "en", "nearby_context",
        "Just to the south: Thai Hoa Palace — the ceremonial power center. "
        "To the north on the spirit axis: Kien Trung Palace — the emperor's residence. "
        "On both sides: Ta Vu, Huu Vu, and the other Forbidden Purple City structures."
    ),

    # ── 10. Duyệt Thị Đường ───────────────────────────────────────────────────
    ("Duyệt Thị Đường", "vi", "visit_highlights",
        "Sân khấu Nhã nhạc cung đình: khu biểu diễn chính với rèm nhung và đèn chùm cổ điển. "
        "Nội thất sơn son thếp vàng tầng một: hệ thống cột gỗ lim chạm rồng phượng. "
        "Khu ngồi dành cho hoàng gia tầng hai: ban công gỗ nhìn xuống sân khấu — chỉ vua và hoàng gia được ngồi đây. "
        "Hành lang và tiền sảnh tầng một: nơi quan lại chờ đợi và chuẩn bị."
    ),
    ("Duyệt Thị Đường", "vi", "visit_route",
        "Vào từ cổng chính phía Nam — quan sát tổng thể mặt tiền nhà hát với mái ngói và trụ cột. "
        "Bước vào tiền sảnh: chiêm ngưỡng bộ cột gỗ lim sơn son và hệ thống vì kèo. "
        "Tiến vào khu khán phòng: quan sát sân khấu từ dưới lên, nhìn lên khu ngồi hoàng gia tầng hai. "
        "Leo cầu thang lên tầng hai — ngồi vào vị trí hoàng gia nhìn xuống sân khấu. "
        "Sau đó thăm phòng trưng bày về Nhã nhạc UNESCO và các hiện vật nhạc cụ cung đình."
    ),
    ("Duyệt Thị Đường", "vi", "nearby_context",
        "Ngay phía Tây: Điện Kiến Trung. "
        "Phía Nam trên trục thần đạo: Điện Thái Hòa. "
        "Phía Đông Bắc: Phủ Nội Vụ — kho lưu trữ vật phẩm hoàng gia."
    ),
    ("Duyệt Thị Đường", "vi", "notable_objects",
        "Đàn Nguyệt và Đàn Tranh: nhạc cụ dây cung đình trưng bày trong nhà hát. "
        "Trống Nhã nhạc: bộ trống lớn dùng trong các buổi biểu diễn Nhã nhạc hoàng cung. "
        "Trang phục biểu diễn: áo dài cung đình thêu rồng phượng tái hiện tại phòng trưng bày."
    ),
    ("Duyệt Thị Đường", "en", "visit_highlights",
        "Royal music performance stage: the main performance area with classical curtains and chandeliers. "
        "Ground-floor interior with red-lacquered and gold-gilded finish: ironwood columns carved with dragon and phoenix. "
        "Royal seating on the second floor: wooden balcony overlooking the stage — reserved for the emperor and royal family only. "
        "Ground-floor corridor and foyer: where officials waited and performers prepared."
    ),
    ("Duyệt Thị Đường", "en", "visit_route",
        "Enter through the south gate — take in the full facade with its tiled roofs and columns. "
        "Step into the foyer: admire the red-lacquered ironwood columns and the roof truss system. "
        "Move into the main hall: view the stage from the floor, look up at the royal balcony. "
        "Climb to the second floor — sit in the royal viewing position and look down at the stage. "
        "Then visit the UNESCO Nha Nhac exhibition room and the court instrument collection."
    ),
    ("Duyệt Thị Đường", "en", "nearby_context",
        "Immediately to the west: Kien Trung Palace. "
        "To the south on the spirit axis: Thai Hoa Palace. "
        "To the northeast: Phu Noi Vu — the Imperial Household Department storehouse."
    ),
    ("Duyệt Thị Đường", "en", "notable_objects",
        "Dan Nguyet and Dan Tranh: string instruments on display in the theater. "
        "Nha Nhac drums: large drums used in royal Nha Nhac performances. "
        "Performance costumes: embroidered court robes with dragon and phoenix motifs on display."
    ),

    # ── 11. Phủ Nội Vụ ───────────────────────────────────────────────────────
    ("Phủ Nội Vụ", "vi", "visit_highlights",
        "Khuôn viên rộng lớn: tổ hợp nhiều kho và công trình lưu trữ — trung tâm hậu cần hoàng cung. "
        "Cổng Phủ Nội Vụ: kiến trúc cổng lầu kiểu Nguyễn, mái lưu ly xanh. "
        "Các kho đồ nội thất và hiện vật triều đình còn được trưng bày một phần."
    ),
    ("Phủ Nội Vụ", "vi", "visit_route",
        "Tiếp cận từ phía Nam — nhìn tổng thể cổng trước khi vào. "
        "Tham quan khu nhà kho chính, quan sát cách bố trí không gian lưu trữ xưa. "
        "Đọc biển thuyết minh về vai trò quản lý tài sản hoàng gia của Phủ Nội Vụ."
    ),
    ("Phủ Nội Vụ", "vi", "nearby_context",
        "Phía Tây: Duyệt Thị Đường — nhà hát cung đình. "
        "Phía Nam: Điện Kiến Trung và trục thần đạo chính. "
        "Đây là khu vực Đông Bắc Tử Cấm Thành — ít du khách lui tới nhất nhưng giá trị lịch sử cao."
    ),
    ("Phủ Nội Vụ", "en", "visit_highlights",
        "Expansive compound: a complex of storehouses and archives — the logistics hub of the royal court. "
        "Main gate: Nguyen-style gatehouse with blue-glazed tile roof. "
        "Partial display of court furniture and imperial objects."
    ),
    ("Phủ Nội Vụ", "en", "visit_route",
        "Approach from the south — observe the gatehouse before entering. "
        "Tour the main storehouse block, noting the spatial arrangement of historic storage areas. "
        "Read the interpretation panels about the Phu Noi Vu's role managing imperial assets."
    ),
    ("Phủ Nội Vụ", "en", "nearby_context",
        "To the west: Duyet Thi Duong Theater — the royal theater. "
        "To the south: Kien Trung Palace and the main spirit axis. "
        "This northeast zone of the Forbidden City is the least visited but historically very rich."
    ),

    # ── 12. Vườn Cơ Hạ ───────────────────────────────────────────────────────
    ("Vườn Cơ Hạ", "vi", "visit_highlights",
        "Minh Hồ: hồ bán nguyệt trung tâm có đình Quang Biểu nổi trên mặt nước. "
        "Lầu Thưởng Thắng: nhìn bao quát toàn khu vườn — từng là nơi vua và hoàng gia ngắm cảnh. "
        "Cầu Kim Nghi: cây cầu có mái che dẫn qua hồ — kiến trúc thủy đình độc đáo. "
        "Điện Kham Văn: công trình chính trên trục trung tâm, nơi vua đọc sách và thưởng thơ."
    ),
    ("Vườn Cơ Hạ", "vi", "visit_route",
        "Vào từ cổng phía Nam — tổng thể vườn theo bố cục 'tiền thủy hậu sơn'. "
        "Đi theo đường dọc bờ hồ Minh Hồ, dừng nhìn đình Quang Biểu phản chiếu trên mặt nước. "
        "Đi qua cầu Kim Nghi có mái che — chiêm ngưỡng cầu từ phía hồ. "
        "Leo lên lầu Thưởng Thắng để nhìn tổng thể vườn từ trên cao. "
        "Kết thúc tại Điện Kham Văn — không gian yên tĩnh và thanh cao nhất trong vườn."
    ),
    ("Vườn Cơ Hạ", "vi", "nearby_context",
        "Phía Tây Nam: khu vực Duyệt Thị Đường và Điện Kiến Trung. "
        "Phía Đông: khu vực Phủ Nội Vụ. "
        "Khu vườn là nơi lý tưởng để nghỉ ngơi và chiêm ngưỡng bố cục phong thủy trước khi tiếp tục tham quan."
    ),
    ("Vườn Cơ Hạ", "vi", "photo_spots",
        "Góc đẹp: đứng trên cầu Kim Nghi nhìn về phía đình Quang Biểu giữa hồ Minh Hồ. "
        "Góc hoàng hôn: lầu Thưởng Thắng nhìn về hướng Tây khi mặt trời lặn."
    ),
    ("Vườn Cơ Hạ", "en", "visit_highlights",
        "Minh Ho Lake: the central crescent-shaped lake with Quang Bieu Pavilion floating on it. "
        "Thuong Thang Tower: overlooks the entire garden — once where the emperor and royals watched the scenery. "
        "Kim Nghi Bridge: a covered bridge crossing the lake — a unique waterfront architectural feature. "
        "Kham Van Hall: the main structure on the central axis, where the emperor read and composed poetry."
    ),
    ("Vườn Cơ Hạ", "en", "visit_route",
        "Enter from the south gate — the garden follows the 'front water, rear mountain' feng shui layout. "
        "Walk along the shore of Minh Ho Lake, pausing to see Quang Bieu Pavilion reflected in the water. "
        "Cross the covered Kim Nghi Bridge — admire it from the lakeside perspective. "
        "Climb Thuong Thang Tower for a bird's-eye view of the full garden layout. "
        "Finish at Kham Van Hall — the quietest and most refined space in the garden."
    ),
    ("Vườn Cơ Hạ", "en", "nearby_context",
        "To the southwest: Duyet Thi Duong Theater and Kien Trung Palace area. "
        "To the east: Phu Noi Vu zone. "
        "This garden is an ideal rest stop to enjoy feng shui scenery before continuing your tour."
    ),
    ("Vườn Cơ Hạ", "en", "photo_spots",
        "Best shot: stand on Kim Nghi Bridge looking toward Quang Bieu Pavilion on Minh Ho Lake. "
        "Sunset angle: Thuong Thang Tower facing west at dusk."
    ),

    # ── 13. Triệu Miếu ────────────────────────────────────────────────────────
    ("Triệu Miếu (Triệu Tổ Miếu)", "vi", "visit_highlights",
        "Chính đường 3 gian 2 chái: mái ngói âm dương hoàng lưu ly, cấu kiện gỗ sơn son thếp vàng. "
        "Phù điêu mảnh sành sứ trên bờ mái và cổ diêm: kỹ thuật trang trí đặc trưng thời Nguyễn. "
        "Thần Khố phía Đông và Thần Trù phía Tây: công trình phụ trợ lễ tế. "
        "Sân và đường thần đạo: không gian trang nghiêm, trầm lắng."
    ),
    ("Triệu Miếu (Triệu Tổ Miếu)", "vi", "visit_route",
        "Vào từ cổng phía Nam — quan sát cổng tam quan và tường bao kiên cố. "
        "Đi theo đường thần đạo vào sân trước, nhìn toàn bộ mặt tiền chính đường. "
        "Vào chính đường thắp hương và chiêm bái bàn thờ Nguyễn Kim. "
        "Ghé thăm Thần Khố và Thần Trù hai bên để hiểu quy trình lễ tế ngày xưa."
    ),
    ("Triệu Miếu (Triệu Tổ Miếu)", "vi", "nearby_context",
        "Ngay phía Nam: Thái Miếu — thờ 9 chúa Nguyễn cùng chỗ từ năm 1989. "
        "Phía Tây: Hưng Miếu và Thế Miếu. "
        "Cả khu phía Đông Nam này là vùng miếu thờ ít du khách ghé nhất — thích hợp để chiêm nghiệm yên tĩnh."
    ),
    ("Triệu Miếu (Triệu Tổ Miếu)", "en", "visit_highlights",
        "3-bay main hall: yellow-glazed yin-yang tiles, red-lacquered gold-gilded wooden components. "
        "Ceramic shard relief on roof ridges and frieze: a signature decorative technique of the Nguyen era. "
        "God's Treasury (east) and God's Kitchen (west): ritual support structures. "
        "Courtyard and spirit path: a solemn, contemplative space."
    ),
    ("Triệu Miếu (Triệu Tổ Miếu)", "en", "visit_route",
        "Enter through the south triple-arch gate — observe the gate and surrounding enclosure wall. "
        "Walk the spirit path into the front yard, taking in the full main hall facade. "
        "Step inside to light incense and pay respects at Nguyen Kim's altar. "
        "Visit the God's Treasury and Kitchen on each side to understand the ceremonial preparation process."
    ),
    ("Triệu Miếu (Triệu Tổ Miếu)", "en", "nearby_context",
        "Just to the south: Thai Mieu — also housing the 9 Nguyen Lords' shrines since 1989. "
        "To the west: Hung Mieu and The Mieu. "
        "This southeast temple zone is the least visited — perfect for quiet reflection."
    ),

    # ── 14. Thái Miếu ─────────────────────────────────────────────────────────
    ("Thái Miếu (Thái Tổ Miếu)", "vi", "visit_highlights",
        "Tuy Thành Các 3 tầng: điểm nhấn trục trung tâm, tương tự Hiển Lâm Các ở Thế Miếu. "
        "Chính điện lớn nhất thời Nguyễn: 13 gian 2 chái kép, quy mô vượt cả Thế Miếu. "
        "Tả Tùng Tự và Hữu Tùng Tự: nơi thờ công thần triều Nguyễn, hai bên phía Nam. "
        "Hệ thống tường gạch bao bọc 5 cổng: không gian thành quách kín đáo."
    ),
    ("Thái Miếu (Thái Tổ Miếu)", "vi", "visit_route",
        "Vào từ cổng phía Nam — nhìn thẳng vào Tuy Thành Các nổi bật trên trục chính. "
        "Dừng trước Tuy Thành Các — ngắm nhìn kiến trúc ba tầng trước khi tiếp tục. "
        "Vào chính điện đang trong quá trình phục dựng — đọc các biển về lịch sử và dự án trùng tu 2024-2028. "
        "Ghé thăm Tả Tùng Tự và Hữu Tùng Tự phía Nam để tìm hiểu về các công thần được thờ."
    ),
    ("Thái Miếu (Thái Tổ Miếu)", "vi", "nearby_context",
        "Ngay phía Bắc: Triệu Miếu. "
        "Phía Tây: Hưng Miếu và Thế Miếu. "
        "Đây là khu Đông Nam Hoàng thành — khu miếu thờ lớn nhất, đang được đầu tư phục hồi."
    ),
    ("Thái Miếu (Thái Tổ Miếu)", "en", "visit_highlights",
        "Three-story Tuy Thanh Pavilion: the focal point of the central axis, similar to Hien Lam at The Mieu. "
        "The largest main hall of the Nguyen era: 13 double-side bays, exceeding even The Mieu in scale. "
        "Ta Tung Tu and Huu Tung Tu: shrines for meritorious Nguyen officials, on either side to the south. "
        "Brick enclosure walls with 5 gates: a self-contained sacred precinct."
    ),
    ("Thái Miếu (Thái Tổ Miếu)", "en", "visit_route",
        "Enter from the south gate — look straight toward Tuy Thanh Pavilion on the central axis. "
        "Pause before Tuy Thanh Pavilion — admire the three-tier architecture before continuing. "
        "Visit the main hall currently under restoration — read the panels about the 2024-2028 renovation project. "
        "Visit Ta Tung Tu and Huu Tung Tu to the south to learn about the meritorious officials enshrined here."
    ),
    ("Thái Miếu (Thái Tổ Miếu)", "en", "nearby_context",
        "Just to the north: Trieu Mieu. "
        "To the west: Hung Mieu and The Mieu. "
        "This southeast zone is the Imperial City's largest ancestral complex, currently being actively restored."
    ),

    # ── 15. Cửa Hiển Nhơn ─────────────────────────────────────────────────────
    ("Cửa Hiển Nhơn", "vi", "visit_highlights",
        "Lầu canh hai tầng: mái ngói lưu ly xanh, gờ mái đắp rồng uốn lượn mềm mại. "
        "Phần đài cao bằng gạch vồ và đá Thanh: kiến trúc phòng thủ kiên cố. "
        "Hướng Đông mở ra khu phố cổ Huế — đây là ranh giới giữa nội và ngoại thành."
    ),
    ("Cửa Hiển Nhơn", "vi", "visit_route",
        "Quan sát mặt Đông ngoài thành — tường rêu phong và phố thị bên ngoài. "
        "Bước qua cổng vào trong — nhìn lên lầu canh, quan sát hoa văn chạm khắc. "
        "Từ trong nhìn ngược ra Đông — cảm nhận sự chuyển giao giữa không gian cung đình và phố thị. "
        "Từ cổng này có thể đi bộ về phía Tây tới khu Thái Miếu và Triệu Miếu."
    ),
    ("Cửa Hiển Nhơn", "vi", "nearby_context",
        "Phía Tây bên trong thành: khu Thái Miếu và Triệu Miếu. "
        "Đối xứng phía Tây thành: Cửa Chương Đức. "
        "Phía Bắc ngoài thành: khu phố cổ Gia Hội và sông Hương."
    ),
    ("Cửa Hiển Nhơn", "en", "visit_highlights",
        "Two-story watchtower: blue-glazed tile roof, roof ridges with graceful dragon motifs. "
        "High platform of large baked bricks and Thanh stone: solid defensive architecture. "
        "Eastward opening onto Hue's ancient quarter — the boundary between inner palace and outer city."
    ),
    ("Cửa Hiển Nhơn", "en", "visit_route",
        "Observe the east exterior — moss-covered walls and the bustling streets beyond. "
        "Step through the gate inward — look up at the watchtower and examine the carved patterns. "
        "Looking east from inside — feel the threshold between royal court and city life. "
        "From this gate you can walk west to the Thai Mieu and Trieu Mieu temple complex."
    ),
    ("Cửa Hiển Nhơn", "en", "nearby_context",
        "To the west inside the wall: Thai Mieu and Trieu Mieu temple complex. "
        "Symmetrical to the west wall: Chuong Duc Gate. "
        "North outside the wall: Gia Hoi old quarter and the Perfume River."
    ),

    # ── 16. Điện Long An ──────────────────────────────────────────────────────
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "vi", "visit_highlights",
        "Hệ thống 128 cột gỗ lim để mộc: không sơn son thếp vàng — kỹ thuật chạm trổ tinh hoa thay cho màu sắc. "
        "Hai bài thơ hồi văn kiêm liên hoàn 56 chữ của vua Thiệu Trị: đọc xuôi ngược thành 64 bài khác nhau. "
        "Bộ sưu tập đầu hồ — trò chơi cung đình xưa — và tranh gương hơn 150 năm tuổi. "
        "Hơn 10.000 hiện vật: vàng, sứ, trang phục hoàng gia, nhạc khí, cổ vật Chăm."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "vi", "visit_route",
        "Vào từ cổng phía Nam — quan sát tổng thể nhà chữ nhật 35,7m × 28m. "
        "Đứng trước hiên điện, nhìn lên hệ thống vì kèo và cột gỗ để mộc — khác hẳn các điện khác trong Hoàng thành. "
        "Vào bên trong: tham quan phòng trưng bày đồ vàng và sứ Hoàng gia tầng một. "
        "Tìm hai bài thơ hồi văn trên vách điện — đọc thử theo hướng dẫn. "
        "Tầng hai (nếu mở): khu trưng bày nhạc khí cung đình và trang phục."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "vi", "nearby_context",
        "Phía Bắc: Cửa Hiển Nhơn — cổng phía Đông Hoàng thành. "
        "Phía Tây: Thái Miếu và Triệu Miếu. "
        "Đây là bảo tàng cổ vật lớn nhất Việt Nam về triều đại phong kiến — nên dành ít nhất 1 giờ."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "vi", "notable_objects",
        "Bộ ấn vàng triều Nguyễn: ấn vàng hoàng đế được trưng bày trong tủ kính an ninh cao. "
        "Tranh gương: bộ tranh trên kính hơn 150 năm tuổi — kỹ thuật hiếm của thời Nguyễn. "
        "Bộ đầu hồ: gồm bình đồng và tên bằng gỗ — trò chơi phong lưu của quý tộc hoàng gia. "
        "Nhạc cụ Nhã nhạc: đàn bầu, đàn tranh, sáo trúc, trống cung đình nguyên bản."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "en", "visit_highlights",
        "128 unpainted ironwood columns: no lacquer or gilt — intricate carving replaces color as the art form. "
        "Two palindrome-chain poems of 56 characters by Emperor Thieu Tri: readable in any direction to form 64 distinct poems. "
        "Dau Ho collection — an ancient court game — and mirror paintings over 150 years old. "
        "Over 10,000 artifacts: gold, porcelain, royal costumes, court instruments, Cham antiquities."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "en", "visit_route",
        "Enter from the south gate — observe the full rectangular structure (35.7m × 28m). "
        "Stand before the portico and look up at the unpainted woodwork system — notably different from other palaces. "
        "Go inside: tour the ground-floor display of imperial gold and porcelain. "
        "Find the two palindrome poems on the interior walls — try reading them as guided. "
        "Upper floor (if open): court musical instrument and royal costume exhibition."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "en", "nearby_context",
        "To the north: Hien Nhon Gate — the eastern gate of the Imperial City. "
        "To the west: Thai Mieu and Trieu Mieu. "
        "This is Vietnam's largest museum of a single feudal dynasty — allow at least 1 hour."
    ),
    ("Điện Long An (Bảo tàng Cổ vật Cung đình Huế)", "en", "notable_objects",
        "Nguyen imperial gold seals: displayed in high-security glass cases. "
        "Mirror paintings: glass artworks over 150 years old — a rare Nguyen-era technique. "
        "Dau Ho set: bronze vase and wooden darts — the refined game of the Nguyen nobility. "
        "Nha Nhac instruments: original dan bau, dan tranh, bamboo flute, and court drums."
    ),

    # ── 17. Ngọ Môn ───────────────────────────────────────────────────────────
    ("Ngọ Môn", "vi", "visit_highlights",
        "Đài nền hình chữ U: cao gần 5m, dài 57,77m, trổ 5 lối đi — mỗi lối dành cho một tầng lớp khác nhau. "
        "Lầu Ngũ Phụng: 100 cột gỗ lim, mái vàng trung tâm và 8 mái xanh xung quanh — biểu tượng phượng hoàng. "
        "Bốn tòa nhà phụ Đông, Tây dực lâu hai bên: tạo thành quần thể hoàn chỉnh nhìn từ sân. "
        "Sân Đại triều nghi phía Bắc: chứng kiến lễ thoái vị của vua Bảo Đại ngày 30/8/1945."
    ),
    ("Ngọ Môn", "vi", "visit_route",
        "Đứng ở phía Nam Ngọ Môn — quan sát tổng thể đài hình chữ U và 5 lối đi, đếm thử số cửa. "
        "Tiếp cận gần: nhìn kỹ vật liệu xây dựng đài — gạch vồ, đá Thanh, và những lớp rêu phong. "
        "Bước qua cửa chính giữa (cửa Ngọ Môn) vào sân — đây là lối dành cho vua xưa. "
        "Đứng dưới chân lầu Ngũ Phụng nhìn lên — đếm hoa văn phụng trang trí trên bờ nóc. "
        "Leo lên lầu Ngũ Phụng (nếu mở): nhìn xuống sân Ngọ Môn và toàn cảnh phía Nam Hoàng thành. "
        "Nhìn ra phía Bắc để thấy trục thần đạo chính dẫn thẳng vào Điện Thái Hòa."
    ),
    ("Ngọ Môn", "vi", "nearby_context",
        "Phía Bắc ngay sau cổng: sân Đại triều nghi và Điện Thái Hòa. "
        "Phía Nam: Hồ Thái Dịch và quảng trường trước Ngọ Môn — nơi du khách thường chụp ảnh. "
        "Đây là điểm bắt đầu lý tưởng cho hành trình khám phá Hoàng thành theo trục Bắc-Nam."
    ),
    ("Ngọ Môn", "vi", "notable_objects",
        "5 lối đi đài Ngọ Môn: Cửa Ngọ, Tả Giáp, Hữu Giáp, Tả Dịch, Hữu Dịch — phân tầng theo phẩm trật. "
        "Lầu Ngũ Phụng: 100 cột gỗ lim, biểu tượng 5 con phụng — đặc trưng kiến trúc quan trọng nhất. "
        "Mái ngói hoàng lưu ly và thanh lưu ly: màu vàng tượng trưng cho đế vương, màu xanh cho quan lại."
    ),
    ("Ngọ Môn", "vi", "photo_spots",
        "Góc kinh điển: đứng phía Nam hồ Thái Dịch nhìn vào Ngọ Môn với hồ làm tiền cảnh phản chiếu. "
        "Góc từ lầu Ngũ Phụng: nhìn xuống sân Đại triều nghi — thấy cả Điện Thái Hòa ở phía Bắc. "
        "Góc hoàng hôn: mặt Tây của Ngọ Môn khi ánh chiều tà nhuộm vàng các mái ngói."
    ),
    ("Ngọ Môn", "en", "visit_highlights",
        "U-shaped stone platform: nearly 5m high, 57.77m long, with 5 passageways — each reserved for a different rank. "
        "Five Phoenix Pavilion: 100 ironwood columns, yellow-glazed central roof and 8 blue-glazed roofs — the phoenix motif. "
        "Four auxiliary buildings on the east and west wings: completing the ensemble viewed from the court. "
        "The Great Court to the north: witnessed Emperor Bao Dai's abdication on August 30, 1945."
    ),
    ("Ngọ Môn", "en", "visit_route",
        "Stand south of Ngo Mon — take in the full U-shaped platform with 5 passageways; try to count the gates. "
        "Approach closely: examine the construction materials — large baked bricks, Thanh stone, moss-covered with age. "
        "Walk through the central passage (Ngo Mon proper) into the court — the path once reserved for the emperor. "
        "Stand beneath the Five Phoenix Pavilion and look up — count the phoenix carvings along the ridge. "
        "Climb the Five Phoenix Pavilion (if open): look down at the Ngo Mon courtyard and the southern panorama. "
        "Look north to see the main spirit axis running straight to Thai Hoa Palace."
    ),
    ("Ngọ Môn", "en", "nearby_context",
        "Directly north: the Great Court Yard and Thai Hoa Palace. "
        "To the south: Thai Dich Lake and the plaza in front of Ngo Mon — the most popular photo spot. "
        "This is the ideal starting point for exploring the Imperial City along the north-south spirit axis."
    ),
    ("Ngọ Môn", "en", "notable_objects",
        "The 5 passageways: Ngo Mon (emperor), Ta Giap, Huu Giap (mandarins), Ta Dich, Huu Dich (soldiers) — ranked hierarchy in stone. "
        "Five Phoenix Pavilion: 100 ironwood columns, the phoenix symbol of imperial grace — the most important architectural feature. "
        "Yellow and blue-glazed roof tiles: yellow symbolizing the emperor, blue symbolizing the mandarins."
    ),
    ("Ngọ Môn", "en", "photo_spots",
        "Classic shot: stand south of Thai Dich Lake looking toward Ngo Mon with the lake as a reflecting foreground. "
        "From the Five Phoenix Pavilion: look down at the Great Court Yard — Thai Hoa Palace visible to the north. "
        "Sunset angle: the west face of Ngo Mon when the late afternoon light gilds the tile roofs."
    ),
]

ARTIFACT_RELATIONS = []


# ─── Seeding Functions ─────────────────────────────────────────────────────────

async def seed_locations(session):
    """Upsert all locations."""
    for loc_data in LOCATIONS:
        existing = await session.execute(
            select(Location).where(Location.name_vi == loc_data["name_vi"])
        )
        obj = existing.scalar_one_or_none()
        if not obj:
            obj = Location(**loc_data)
            session.add(obj)
            logger.info("  [+] Location: %s", loc_data["name_vi"])
        else:
            for k, v in loc_data.items():
                setattr(obj, k, v)
            logger.info("  [~] Updated location: %s", loc_data["name_vi"])
    await session.flush()


async def seed_artifacts(session) -> dict[str, int]:
    """Upsert all artifacts. Returns {name_vi: art_id} mapping."""
    name_to_id: dict[str, int] = {}
    for art_data in ARTIFACTS:
        existing = await session.execute(
            select(Artifact).where(Artifact.name_vi == art_data["name_vi"])
        )
        obj = existing.scalar_one_or_none()
        if not obj:
            obj = Artifact(**art_data)
            session.add(obj)
            await session.flush()
            logger.info("  [+] Artifact: %s (id=%s)", art_data["name_vi"], obj.art_id)
        else:
            for k, v in art_data.items():
                setattr(obj, k, v)
            await session.flush()
            logger.info("  [~] Updated artifact: %s (id=%s)", art_data["name_vi"], obj.art_id)
        name_to_id[art_data["name_vi"]] = obj.art_id
    return name_to_id


async def seed_bilingual_content(session, name_to_id: dict[str, int]):
    """Upsert bilingual_content rows from BILINGUAL_CONTENT_RAW."""
    inserted = 0
    updated = 0
    skipped = 0
    for (artifact_name_vi, lang, content_type, content_text) in BILINGUAL_CONTENT_RAW:
        art_id = name_to_id.get(artifact_name_vi)
        if art_id is None:
            logger.warning("  [!] Skipped bilingual for unknown artifact: %s", artifact_name_vi)
            skipped += 1
            continue

        existing = await session.execute(
            select(BilingualContent).where(
                and_(
                    BilingualContent.artifact_id == art_id,
                    BilingualContent.lang == lang,
                    BilingualContent.content_type == content_type,
                )
            )
        )
        obj = existing.scalar_one_or_none()
        if not obj:
            obj = BilingualContent(
                artifact_id=art_id,
                lang=lang,
                content_type=content_type,
                content_text=content_text,
            )
            session.add(obj)
            inserted += 1
        else:
            obj.content_text = content_text
            updated += 1
    logger.info(
        "  Bilingual content: %d inserted, %d updated, %d skipped.",
        inserted, updated, skipped
    )


async def main():
    """Run all seeding steps."""
    logger.info("=== Starting AI Tour Guide Database Seed ===")

    async with async_session_factory() as session:
        async with session.begin():
            logger.info("[1/3] Seeding Locations...")
            await seed_locations(session)

            logger.info("[2/3] Seeding Artifacts...")
            name_to_id = await seed_artifacts(session)

            logger.info("[3/3] Seeding Bilingual Content...")
            await seed_bilingual_content(session, name_to_id)

    logger.info("=== Seed complete! ===")
    logger.info("Artifacts seeded: %d", len(ARTIFACTS))
    logger.info("Bilingual content rows: %d", len(BILINGUAL_CONTENT_RAW))


if __name__ == "__main__":
    asyncio.run(main())

