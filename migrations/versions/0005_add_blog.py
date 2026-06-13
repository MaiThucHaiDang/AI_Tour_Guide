"""Add travel blog tables and seed posts.

Revision ID: 0005_add_blog
Revises: 0004_add_knowledge_graph
Create Date: 2026-06-13
"""

from __future__ import annotations

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_add_blog"
down_revision = "0004_add_knowledge_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blog_posts",
        sa.Column("post_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("excerpt", sa.String(length=420), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image", sa.String(length=600), nullable=False),
        sa.Column("cover_alt", sa.String(length=260), nullable=False),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("author_avatar", sa.String(length=600), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=180), nullable=True),
        sa.Column("source_url", sa.String(length=700), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reading_time", sa.Integer(), server_default="1", nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("bookmarks_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="published", nullable=False),
        sa.CheckConstraint(
            "source_type IN ('seed', 'external', 'user')",
            name="ck_blog_posts_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending', 'published')",
            name="ck_blog_posts_status",
        ),
        sa.PrimaryKeyConstraint("post_id"),
    )
    op.create_index(op.f("ix_blog_posts_slug"), "blog_posts", ["slug"], unique=True)
    op.create_index(op.f("ix_blog_posts_title"), "blog_posts", ["title"], unique=False)
    op.create_index(op.f("ix_blog_posts_status"), "blog_posts", ["status"], unique=False)
    op.create_index(op.f("ix_blog_posts_published_at"), "blog_posts", ["published_at"], unique=False)

    op.create_table(
        "blog_comments",
        sa.Column("comment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["blog_posts.post_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id"),
    )
    op.create_index(op.f("ix_blog_comments_post_id"), "blog_comments", ["post_id"], unique=False)

    blog_posts = sa.table(
        "blog_posts",
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("excerpt", sa.String),
        sa.column("content", sa.Text),
        sa.column("cover_image", sa.String),
        sa.column("cover_alt", sa.String),
        sa.column("author_name", sa.String),
        sa.column("source_type", sa.String),
        sa.column("source_name", sa.String),
        sa.column("source_url", sa.String),
        sa.column("tags", postgresql.JSONB),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("reading_time", sa.Integer),
        sa.column("likes_count", sa.Integer),
        sa.column("comments_count", sa.Integer),
        sa.column("bookmarks_count", sa.Integer),
        sa.column("status", sa.String),
    )

    now = datetime(2026, 6, 13, 2, 0, tzinfo=timezone.utc)
    op.bulk_insert(
        blog_posts,
        [
            {
                "slug": "di-dai-noi-hue-trong-2-gio",
                "title": "Đi Đại Nội Huế trong 2 giờ: bắt đầu từ Ngọ Môn",
                "excerpt": "Một lộ trình ngắn cho người lần đầu vào Đại Nội: vào từ Ngọ Môn, đi theo trục chính, rồi chọn vài điểm dừng thay vì cố xem tất cả.",
                "content": "Nếu bạn chỉ có khoảng hai giờ, hãy xem Đại Nội như một hành trình có nhịp chứ không phải danh sách phải hoàn thành.\n\nBắt đầu ở Ngọ Môn để có điểm định hướng rõ ràng, sau đó đi chậm qua trục chính về Điện Thái Hòa. Đây là đoạn dễ hiểu nhất về nghi lễ, quyền lực và bố cục Hoàng thành.\n\nSau phần trục chính, chọn một nhánh theo sở thích: Thế Miếu nếu muốn đọc thêm về các vua Nguyễn, Cung Diên Thọ nếu cần khoảng nghỉ yên hơn, hoặc Điện Kiến Trung nếu thích câu chuyện phục dựng và giao thoa kiến trúc.\n\nMẹo nhỏ là giữ 10-15 phút cuối để quay lại khu trước Ngọ Môn. Ánh sáng muộn thường dễ chụp hơn, và bạn sẽ hiểu bố cục không gian tốt hơn sau khi đã đi một vòng.",
                "cover_image": "/assets/icons/ngo_mon.png",
                "cover_alt": "Minh họa Ngọ Môn, điểm bắt đầu gợi ý cho lộ trình Đại Nội Huế",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "external",
                "source_name": "Vietnam Travel",
                "source_url": "https://vietnam.travel/things-to-do/hue-itinerary",
                "tags": ["Lịch trình", "Kinh nghiệm", "Mẹo du lịch"],
                "published_at": now,
                "created_at": now,
                "updated_at": now,
                "reading_time": 2,
                "likes_count": 18,
                "comments_count": 0,
                "bookmarks_count": 7,
                "status": "published",
            },
            {
                "slug": "gio-mo-cua-gia-ve-dai-noi-can-kiem-tra",
                "title": "Giờ mở cửa và vé Đại Nội: những điều nên kiểm tra trước khi đi",
                "excerpt": "Thông tin thực dụng về mùa giờ mở cửa, giờ bán vé và cách đọc bảng giá để tránh đến sát giờ hoặc chọn nhầm tuyến tham quan.",
                "content": "Trước khi đến Đại Nội, hãy kiểm tra lại giờ mở cửa theo mùa. Trang thông tin của Trung tâm Bảo tồn Di tích Cố đô Huế ghi hai khung giờ: mùa 16/3-15/10 mở cửa sớm hơn, mùa 16/10-15/3 mở muộn và đóng sớm hơn.\n\nGiờ bán vé thường kết thúc trước giờ đóng cửa khoảng 30 phút. Vì vậy nếu muốn vào thong thả, đừng canh sát giờ cuối; hãy đến trước ít nhất một tiếng rưỡi nếu chỉ tham quan nhanh, hoặc trước nửa ngày nếu muốn đi sâu.\n\nBảng giá cũng phân biệt vé từng điểm và vé tuyến nhiều điểm. Nếu chỉ tập trung trong Đại Nội, chọn đúng vé Đại Nội sẽ dễ hơn. Nếu kết hợp lăng vua trong cùng ngày, hãy so sánh vé tuyến để tránh mua rời không cần thiết.\n\nGiờ mở cửa và giá vé có thể thay đổi theo mùa, dịp lễ hoặc chính sách mới. Trước ngày đi, hãy mở lại trang chính thức hoặc hỏi tại quầy để chắc chắn lịch của bạn không bị lệch.",
                "cover_image": "/assets/icons/gate.png",
                "cover_alt": "Minh họa cổng tham quan dùng cho bài về giờ mở cửa và vé Đại Nội Huế",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "external",
                "source_name": "Trung tâm Bảo tồn Di tích Cố đô Huế",
                "source_url": "https://www.huedisan.com.vn/thong-tin-tham-quan/",
                "tags": ["Mẹo du lịch", "Kinh nghiệm"],
                "published_at": datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc),
                "created_at": datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc),
                "reading_time": 2,
                "likes_count": 24,
                "comments_count": 0,
                "bookmarks_count": 11,
                "status": "published",
            },
            {
                "slug": "truc-ngo-mon-dien-thai-hoa-nen-di-cham",
                "title": "Vì sao trục Ngọ Môn - Điện Thái Hòa đáng đi chậm",
                "excerpt": "Không chỉ là đường vào cung điện, trục chính của Đại Nội giúp du khách đọc được ý niệm quy hoạch, nghi lễ và biểu tượng quyền lực triều Nguyễn.",
                "content": "Một sai lầm phổ biến khi vào Đại Nội là đi qua trục chính quá nhanh để kịp chụp nhiều điểm. Thực ra đoạn từ Ngọ Môn đến Điện Thái Hòa là phần dễ đọc nhất của không gian cung đình.\n\nUNESCO mô tả Quần thể di tích Huế như một kinh đô phong kiến được quy hoạch theo điều kiện tự nhiên và triết lý phương Đông. Khi đứng ở trục chính, bạn có thể cảm nhận rõ cách cổng, sân, điện và cảnh quan cùng tạo nên một thứ tự nghi lễ.\n\nHãy thử dừng lại ở ba vị trí: trước Ngọ Môn để nhìn tổng thể mặt đứng, giữa sân để thấy khoảng đệm nghi lễ, và trước Điện Thái Hòa để đọc vai trò của công trình trong các buổi thiết triều.\n\nĐi chậm không làm chuyến tham quan nghèo đi. Ngược lại, nó giúp các điểm sau như Thế Miếu, Cung Diên Thọ hay Điện Kiến Trung có ngữ cảnh rõ hơn.",
                "cover_image": "/assets/icons/thai_hoa.png",
                "cover_alt": "Minh họa Điện Thái Hòa trên trục chính Đại Nội Huế",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "external",
                "source_name": "UNESCO World Heritage Centre",
                "source_url": "https://whc.unesco.org/en/list/678/",
                "tags": ["Văn hóa - lịch sử", "Kinh nghiệm"],
                "published_at": datetime(2026, 6, 11, 2, 0, tzinfo=timezone.utc),
                "created_at": datetime(2026, 6, 11, 2, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 11, 2, 0, tzinfo=timezone.utc),
                "reading_time": 2,
                "likes_count": 31,
                "comments_count": 0,
                "bookmarks_count": 13,
                "status": "published",
            },
            {
                "slug": "an-gi-sau-buoi-tham-quan-dai-noi",
                "title": "Ăn gì sau buổi tham quan Đại Nội",
                "excerpt": "Gợi ý chuyển nhịp từ tham quan sang ẩm thực Huế: ăn nhẹ, món nước, hoặc chọn quán gần đường về thay vì cố đi quá xa khi đã mệt.",
                "content": "Sau một buổi đi bộ trong Đại Nội, lựa chọn món ăn nên phụ thuộc vào năng lượng còn lại. Nếu chỉ muốn ăn nhẹ, các món bánh Huế như bánh bèo, bánh nậm hoặc bánh khoái hợp hơn một bữa quá nặng.\n\nNếu đi vào sáng sớm, bún bò Huế là lựa chọn dễ hiểu nhưng nên tránh giờ cao điểm. Nếu đi buổi chiều, hãy chọn quán gần tuyến về khách sạn để không phải di chuyển thêm quá nhiều sau khi đã đi bộ lâu.\n\nVietnam Travel nhấn mạnh ẩm thực Huế gắn với lịch sử kinh đô và nhịp sống địa phương. Vì vậy cách ăn thú vị nhất không nhất thiết là tìm quán nổi tiếng nhất, mà là chọn một điểm vừa sức, gọi ít món, rồi để vị giác kết thúc chuyến tham quan.\n\nTrong app, bài này nên được nối với bản đồ bằng các gợi ý gần cổng ra hoặc gần trục di chuyển thực tế của người dùng.",
                "cover_image": "/assets/icons/garden.png",
                "cover_alt": "Minh họa khoảng nghỉ xanh sau hành trình tham quan và ăn uống ở Huế",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "external",
                "source_name": "Vietnam Travel",
                "source_url": "https://vietnam.travel/things-to-do/how-eat-local-hue",
                "tags": ["Ẩm thực", "Review", "Mẹo du lịch"],
                "published_at": datetime(2026, 6, 10, 2, 0, tzinfo=timezone.utc),
                "created_at": datetime(2026, 6, 10, 2, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 10, 2, 0, tzinfo=timezone.utc),
                "reading_time": 2,
                "likes_count": 15,
                "comments_count": 0,
                "bookmarks_count": 5,
                "status": "published",
            },
            {
                "slug": "mot-buoi-chieu-cho-the-mieu-va-cuu-dinh",
                "title": "Một buổi chiều cho Thế Miếu và Cửu Đỉnh",
                "excerpt": "Gợi ý dành riêng thời gian cho khu miếu thờ và biểu tượng triều đại, phù hợp với người muốn hiểu chiều sâu lịch sử hơn là chỉ chụp ảnh nhanh.",
                "content": "Thế Miếu không phải điểm nên đi vội. Không gian này cần một nhịp khác: nói nhỏ hơn, quan sát tên gọi kỹ hơn và để ý mối liên hệ giữa miếu thờ, sân, cây xanh và các biểu tượng triều đại.\n\nNếu đi buổi chiều, ánh sáng thường mềm hơn trên các mảng mái và sân gạch. Bạn có thể bắt đầu bằng việc đọc các biển giới thiệu, sau đó dành thời gian cho Cửu Đỉnh để hiểu cách triều Nguyễn biểu đạt quyền lực qua hình tượng thiên nhiên, sản vật và lãnh thổ.\n\nNguồn của Trung tâm Bảo tồn Di tích Cố đô Huế nhắc đến Huế như một điểm đến hội tụ nhiều lớp di sản. Thế Miếu là nơi rất hợp để cảm nhận điều đó vì câu chuyện không chỉ nằm ở một công trình, mà nằm trong hệ thống ký ức hoàng gia.\n\nNếu đi cùng trẻ em hoặc người ít đọc lịch sử, hãy đặt câu hỏi đơn giản: nơi này thờ ai, vì sao đặt ở đây, và chi tiết nào lặp lại nhiều nhất?",
                "cover_image": "/assets/icons/the_mieu.png",
                "cover_alt": "Minh họa Thế Miếu, không gian thờ các vua triều Nguyễn",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "external",
                "source_name": "Trung tâm Bảo tồn Di tích Cố đô Huế",
                "source_url": "https://www.huedisan.com.vn/hue-1-diem-den-5-di-san/",
                "tags": ["Văn hóa - lịch sử", "Kinh nghiệm"],
                "published_at": datetime(2026, 6, 9, 2, 0, tzinfo=timezone.utc),
                "created_at": datetime(2026, 6, 9, 2, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 9, 2, 0, tzinfo=timezone.utc),
                "reading_time": 2,
                "likes_count": 22,
                "comments_count": 0,
                "bookmarks_count": 9,
                "status": "published",
            },
            {
                "slug": "review-di-luc-nang-gat-nen-doi-nhip-the-nao",
                "title": "Review cá nhân: đi lúc nắng gắt nên đổi nhịp thế nào",
                "excerpt": "Khi nắng lên mạnh, hãy giảm số điểm, ưu tiên bóng râm, uống nước đều và chuyển phần nghe thuyết minh sang lúc nghỉ.",
                "content": "Có những ngày Đại Nội rất đẹp nhưng nắng khiến chuyến đi dễ mất sức. Khi đó, cách tốt nhất không phải là cố hoàn thành lộ trình ban đầu mà là đổi nhịp sớm.\n\nHãy gom các điểm ngoài trời vào đoạn đầu hoặc cuối ngày, còn giữa trưa ưu tiên nơi có bóng râm, mái che hoặc nhịp tham quan chậm như Cung Diên Thọ, một đoạn hành lang, hoặc khu có ghế nghỉ.\n\nNếu có phần thuyết minh trên điện thoại, hãy lưu những điểm muốn nghe kỹ rồi mở lại khi đang nghỉ. Cách này giúp mắt và chân được nghỉ nhưng mạch lịch sử không bị đứt.\n\nMột chuyến đi tốt không nhất thiết là nhiều ảnh nhất. Đôi khi chỉ cần nhớ rõ ba điểm dừng, một câu chuyện lịch sử và một góc sân có gió là đủ.",
                "cover_image": "/assets/icons/dien_tho.png",
                "cover_alt": "Minh họa Cung Diên Thọ như một điểm nghỉ trong ngày nắng ở Đại Nội",
                "author_name": "Ban biên tập AITourGuide",
                "source_type": "seed",
                "source_name": "Ban biên tập AITourGuide",
                "source_url": None,
                "tags": ["Review", "Mẹo du lịch", "Kinh nghiệm"],
                "published_at": datetime(2026, 6, 8, 2, 0, tzinfo=timezone.utc),
                "created_at": datetime(2026, 6, 8, 2, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 8, 2, 0, tzinfo=timezone.utc),
                "reading_time": 2,
                "likes_count": 12,
                "comments_count": 0,
                "bookmarks_count": 4,
                "status": "published",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_blog_comments_post_id"), table_name="blog_comments")
    op.drop_table("blog_comments")
    op.drop_index(op.f("ix_blog_posts_published_at"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_status"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_title"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_slug"), table_name="blog_posts")
    op.drop_table("blog_posts")
