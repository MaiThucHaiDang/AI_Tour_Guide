"""Update seed blog post covers from icon illustrations to real photos.

Revision ID: 0007_update_blog_covers
Revises: 0006_enable_pg_trgm
Create Date: 2026-06-19

Replaces the demo /assets/icons/*.png covers of the 6 seeded blog posts with
real monument photos from /assets/images/art_<id>_1.jpg, and rewrites the
"Minh họa ..." alt text to descriptive captions.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_update_blog_covers"
down_revision = "0006_enable_pg_trgm"
branch_labels = None
depends_on = None


# (slug, new_cover_image, new_cover_alt, old_cover_image, old_cover_alt)
_UPDATES = [
    ("di-dai-noi-hue-trong-2-gio", "/assets/images/art_17_1.jpg", "Cổng Ngọ Môn, điểm bắt đầu gợi ý cho lộ trình Đại Nội Huế", "/assets/icons/ngo_mon.png", "Minh họa Ngọ Môn, điểm bắt đầu gợi ý cho lộ trình Đại Nội Huế"),
    ("gio-mo-cua-gia-ve-dai-noi-can-kiem-tra", "/assets/images/art_15_1.jpg", "Cửa Hiển Nhơn, cổng tham quan dùng cho bài về giờ mở cửa và vé Đại Nội Huế", "/assets/icons/gate.png", "Minh họa cổng tham quan dùng cho bài về giờ mở cửa và vé Đại Nội Huế"),
    ("truc-ngo-mon-dien-thai-hoa-nen-di-cham", "/assets/images/art_8_1.jpg", "Điện Thái Hòa trên trục chính Đại Nội Huế", "/assets/icons/thai_hoa.png", "Minh họa Điện Thái Hòa trên trục chính Đại Nội Huế"),
    ("an-gi-sau-buoi-tham-quan-dai-noi", "/assets/images/art_12_1.jpg", "Vườn Cơ Hạ, khoảng nghỉ xanh sau hành trình tham quan và ăn uống ở Huế", "/assets/icons/garden.png", "Minh họa khoảng nghỉ xanh sau hành trình tham quan và ăn uống ở Huế"),
    ("mot-buoi-chieu-cho-the-mieu-va-cuu-dinh", "/assets/images/art_7_1.jpg", "Thế Miếu, không gian thờ các vua triều Nguyễn", "/assets/icons/the_mieu.png", "Minh họa Thế Miếu, không gian thờ các vua triều Nguyễn"),
    ("review-di-luc-nang-gat-nen-doi-nhip-the-nao", "/assets/images/art_4_1.jpg", "Cung Diên Thọ, một điểm nghỉ trong ngày nắng ở Đại Nội", "/assets/icons/dien_tho.png", "Minh họa Cung Diên Thọ như một điểm nghỉ trong ngày nắng ở Đại Nội"),
]


def _blog_posts():
    return sa.table(
        "blog_posts",
        sa.column("slug", sa.String),
        sa.column("cover_image", sa.String),
        sa.column("cover_alt", sa.String),
    )


def upgrade() -> None:
    blog_posts = _blog_posts()
    for slug, new_img, new_alt, _old_img, _old_alt in _UPDATES:
        op.execute(
            blog_posts.update()
            .where(blog_posts.c.slug == slug)
            .values(cover_image=new_img, cover_alt=new_alt)
        )
    # Catch-all: any other post (e.g. user-created) that fell back to the old default icon cover.
    op.execute(
        blog_posts.update()
        .where(blog_posts.c.cover_image == "/assets/icons/palace.png")
        .values(cover_image="/assets/images/art_17_1.jpg")
    )


def downgrade() -> None:
    blog_posts = _blog_posts()
    # Revert user posts that used the new default cover back to the old icon default.
    op.execute(
        blog_posts.update()
        .where(blog_posts.c.cover_alt == "Ảnh bìa mặc định bài chia sẻ du lịch Huế")
        .values(cover_image="/assets/icons/palace.png")
    )
    for slug, _new_img, _new_alt, old_img, old_alt in _UPDATES:
        op.execute(
            blog_posts.update()
            .where(blog_posts.c.slug == slug)
            .values(cover_image=old_img, cover_alt=old_alt)
        )
