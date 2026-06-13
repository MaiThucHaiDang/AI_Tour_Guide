import React from 'react';
import { ArrowRight, Bookmark, Clock, Heart, MessageCircle, PenLine } from 'lucide-react';

const formatDate = (value, language) => {
  if (!value) return language === 'vi' ? 'Đang cập nhật' : 'Updating';
  return new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }).format(new Date(value));
};

const BlogCard = ({ post, language, onOpen }) => {
  const isVi = language === 'vi';
  const sourceLabel = post.sourceType === 'user'
    ? post.authorName
    : (post.sourceType === 'external' ? post.sourceName : post.authorName);

  const handleOpen = (event) => {
    event.preventDefault();
    onOpen(post.slug);
  };

  return (
    <article className="blog-card">
      <a
        className="blog-card-link"
        href={`/blog/${post.slug}`}
        onClick={handleOpen}
        aria-label={isVi ? `Đọc bài ${post.title}` : `Read ${post.title}`}
      >
        <span className="blog-card-media">
          <img src={post.coverImage} alt={post.coverAlt} loading="lazy" decoding="async" />
          <span className="blog-card-source">
            <PenLine size={14} />
            {sourceLabel}
          </span>
        </span>

        <span className="blog-card-body">
          <span className="blog-card-meta">
            <span><Clock size={14} />{post.readingTime} {isVi ? 'phút đọc' : 'min read'}</span>
            <span>{formatDate(post.publishedAt, language)}</span>
          </span>

          <strong className="blog-card-title">{post.title}</strong>
          <span className="blog-card-excerpt">{post.excerpt}</span>

          <span className="blog-tag-row" aria-label={isVi ? 'Nhu cầu tham quan' : 'Visit needs'}>
            {post.tags.slice(0, 3).map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </span>

          <span className="blog-card-footer">
            <span className="blog-card-stats" aria-label={isVi ? 'Mức độ hữu ích của bài' : 'Note usefulness'}>
              <span><Heart size={14} />{post.likesCount}</span>
              <span><MessageCircle size={14} />{post.commentsCount}</span>
              <span><Bookmark size={14} />{post.bookmarksCount}</span>
            </span>
            <span className="blog-read-more">
              {isVi ? 'Đọc tiếp' : 'Read'}
              <ArrowRight size={16} />
            </span>
          </span>
        </span>
      </a>
    </article>
  );
};

export default BlogCard;
