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
BILINGUAL_CONTENT = []
ARTIFACT_RELATIONS = []
