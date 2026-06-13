import React, { useCallback, useEffect, useState } from 'react';
import {
  ArrowLeft,
  Bookmark,
  Clock,
  ExternalLink,
  Heart,
  Link as LinkIcon,
  MessageCircle,
  RefreshCw,
  Send
} from 'lucide-react';
import {
  addBlogCommentAPI,
  getBlogPostAPI,
  updateBlogInteractionAPI
} from '../../services/apiService';
import { getBlogInteraction, setBlogInteraction } from './blogLocalStorage';

const UNSAFE_TEXT_PATTERN = /(<\s*\/?\s*script\b|javascript\s*:|on[a-z]+\s*=)/i;

const formatDate = (value, language) => {
  if (!value) return language === 'vi' ? 'Đang cập nhật' : 'Updating';
  return new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  }).format(new Date(value));
};

const renderPlainText = (content) => (
  (content || '')
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => <p key={paragraph}>{paragraph}</p>)
);

const BlogDetailPage = ({ slug, language, onBackList }) => {
  const isVi = language === 'vi';
  const [post, setPost] = useState(null);
  const [interaction, setInteraction] = useState({ liked: false, bookmarked: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [commentAuthor, setCommentAuthor] = useState('');
  const [commentContent, setCommentContent] = useState('');
  const [commentError, setCommentError] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  const copy = {
    back: isVi ? 'Quay lại cẩm nang' : 'Back to guide',
    loading: isVi ? 'Đang tải bài viết...' : 'Loading post...',
    retry: isVi ? 'Thử lại' : 'Retry',
    readOriginal: isVi ? 'Đọc bài gốc' : 'Read original',
    sourceLabel: isVi ? 'Nguồn tham khảo' : 'Reference source',
    like: isVi ? 'Thích' : 'Like',
    liked: isVi ? 'Đã thích' : 'Liked',
    bookmark: isVi ? 'Lưu bài' : 'Bookmark',
    bookmarked: isVi ? 'Đã lưu' : 'Saved',
    share: isVi ? 'Chia sẻ' : 'Share',
    copied: isVi ? 'Đã copy link bài viết.' : 'Post link copied.',
    comments: isVi ? 'Bình luận' : 'Comments',
    noComments: isVi ? 'Chưa có kinh nghiệm bổ sung. Bạn có thể mở đầu bằng điều mình vừa trải qua.' : 'No added tips yet.',
    authorLabel: isVi ? 'Tên hiển thị' : 'Display name',
    authorPlaceholder: isVi ? 'Khách' : 'Guest',
    commentLabel: isVi ? 'Kinh nghiệm muốn bổ sung' : 'Tip to add',
    commentPlaceholder: isVi ? 'Ví dụ: nên đến sớm hơn, góc chụp đẹp, đoạn nào dễ nắng...' : 'Example: arrive earlier, best photo angle, hot section...',
    send: isVi ? 'Gửi kinh nghiệm' : 'Add tip',
    emptyComment: isVi ? 'Hãy nhập kinh nghiệm hoặc ghi chú bạn muốn chia sẻ.' : 'Add a tip or note before posting.',
    unsafeComment: isVi ? 'Vui lòng nhập chữ thường, không dán mã HTML hoặc script.' : 'Please enter plain text, not HTML or scripts.',
    savedHint: isVi
      ? 'Lưu trên thiết bị này để mở lại trước cổng hoặc trong lúc nghỉ chân.'
      : 'Saved on this device for quick access during your visit.'
  };

  const loadPost = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getBlogPostAPI(slug);
      setPost(data);
      setInteraction(getBlogInteraction(data.slug));
    } catch (err) {
      setError(err.message || (isVi ? 'Không thể tải bài viết.' : 'Unable to load post.'));
    } finally {
      setLoading(false);
    }
  }, [isVi, slug]);

  useEffect(() => {
    loadPost();
  }, [loadPost]);

  const toggleInteraction = async (action) => {
    if (!post) return;
    const key = action === 'like' ? 'liked' : 'bookmarked';
    const countKey = action === 'like' ? 'likesCount' : 'bookmarksCount';
    const previousInteraction = interaction;
    const nextActive = !interaction[key];
    const nextInteraction = { ...interaction, [key]: nextActive };
    const delta = nextActive ? 1 : -1;

    setNotice('');
    setInteraction(nextInteraction);
    setBlogInteraction(post.slug, nextInteraction);
    setPost((current) => ({
      ...current,
      [countKey]: Math.max(0, current[countKey] + delta)
    }));

    try {
      const response = await updateBlogInteractionAPI(post.slug, { action, active: nextActive });
      setPost((current) => ({
        ...current,
        likesCount: response.likes_count ?? current.likesCount,
        bookmarksCount: response.bookmarks_count ?? current.bookmarksCount
      }));
    } catch (err) {
      setInteraction(previousInteraction);
      setBlogInteraction(post.slug, previousInteraction);
      setPost((current) => ({
        ...current,
        [countKey]: Math.max(0, current[countKey] - delta)
      }));
      setNotice(err.message || (isVi ? 'Không thể cập nhật tương tác.' : 'Unable to update interaction.'));
    }
  };

  const copyLink = async () => {
    const url = new URL(`/blog/${post.slug}`, window.location.origin).toString();
    try {
      await navigator.clipboard.writeText(url);
      setNotice(copy.copied);
    } catch {
      setNotice(url);
    }
  };

  const submitComment = async (event) => {
    event.preventDefault();
    const content = commentContent.trim();
    const authorName = commentAuthor.trim() || 'Khách';
    setCommentError('');

    if (!content) {
      setCommentError(copy.emptyComment);
      return;
    }
    if (UNSAFE_TEXT_PATTERN.test(content) || UNSAFE_TEXT_PATTERN.test(authorName)) {
      setCommentError(copy.unsafeComment);
      return;
    }

    setSubmittingComment(true);
    try {
      const comment = await addBlogCommentAPI(post.slug, { authorName, content });
      setPost((current) => ({
        ...current,
        comments: [...current.comments, comment],
        commentsCount: current.commentsCount + 1
      }));
      setCommentContent('');
    } catch (err) {
      setCommentError(err.message || (isVi ? 'Không thể gửi bình luận.' : 'Unable to post comment.'));
    } finally {
      setSubmittingComment(false);
    }
  };

  if (loading) {
    return (
      <div className="blog-page">
        <header className="blog-topbar">
          <button type="button" className="blog-back-button" onClick={onBackList}>
            <ArrowLeft size={18} />
            {copy.back}
          </button>
        </header>
        <section className="blog-state">
          <RefreshCw size={22} className="spin" />
          <p>{copy.loading}</p>
        </section>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="blog-page">
        <header className="blog-topbar">
          <button type="button" className="blog-back-button" onClick={onBackList}>
            <ArrowLeft size={18} />
            {copy.back}
          </button>
        </header>
        <section className="blog-state error">
          <p>{error}</p>
          <button type="button" onClick={loadPost}>
            <RefreshCw size={17} />
            {copy.retry}
          </button>
        </section>
      </div>
    );
  }

  const sourceLabel = post.sourceType === 'external'
    ? (post.sourceName || 'Nguồn tham khảo')
    : post.authorName;

  return (
    <div className="blog-page">
      <header className="blog-topbar">
        <button type="button" className="blog-back-button" onClick={onBackList}>
          <ArrowLeft size={18} />
          {copy.back}
        </button>
      </header>

      <main className="blog-detail-main">
        <article className="blog-detail-article">
          <div className="blog-detail-cover">
            <img src={post.coverImage} alt={post.coverAlt} decoding="async" />
          </div>

          <div className="blog-detail-heading">
            <div className="blog-tag-row">
              {post.tags.map((tag) => <span key={tag}>{tag}</span>)}
            </div>
            <h1>{post.title}</h1>
            <div className="blog-detail-meta">
              <span>{sourceLabel || post.authorName}</span>
              <span>{formatDate(post.publishedAt, language)}</span>
              <span><Clock size={15} />{post.readingTime} {isVi ? 'phút đọc' : 'min read'}</span>
            </div>
          </div>

          {post.sourceType === 'external' && post.sourceUrl && (
            <aside className="blog-source-box">
              <div>
                <span>{copy.sourceLabel}</span>
                <strong>{post.sourceName}</strong>
              </div>
              <a href={post.sourceUrl} target="_blank" rel="noreferrer">
                {copy.readOriginal}
                <ExternalLink size={16} />
              </a>
            </aside>
          )}

          <div className="blog-detail-content">
            {renderPlainText(post.content)}
          </div>
        </article>

        <aside className="blog-detail-aside" aria-label={isVi ? 'Tương tác bài viết' : 'Post interactions'}>
          <div className="blog-action-panel">
            <button
              type="button"
              className={interaction.liked ? 'active' : ''}
              onClick={() => toggleInteraction('like')}
              aria-pressed={interaction.liked}
            >
              <Heart size={18} />
              <span>{interaction.liked ? copy.liked : copy.like}</span>
              <strong>{post.likesCount}</strong>
            </button>
            <button
              type="button"
              className={interaction.bookmarked ? 'active' : ''}
              onClick={() => toggleInteraction('bookmark')}
              aria-pressed={interaction.bookmarked}
            >
              <Bookmark size={18} />
              <span>{interaction.bookmarked ? copy.bookmarked : copy.bookmark}</span>
              <strong>{post.bookmarksCount}</strong>
            </button>
            <button type="button" onClick={copyLink}>
              <LinkIcon size={18} />
              <span>{copy.share}</span>
            </button>
          </div>

          <p className="blog-footnote">{copy.savedHint}</p>
          {notice && <p className="blog-notice" role="status">{notice}</p>}
        </aside>

        <section className="blog-comments-section" aria-labelledby="blog-comments-title">
          <div className="blog-comments-heading">
            <MessageCircle size={20} />
            <h2 id="blog-comments-title">{copy.comments}</h2>
            <span>{post.commentsCount}</span>
          </div>

          <form className="blog-comment-form" onSubmit={submitComment}>
            <label>
              <span>{copy.authorLabel}</span>
              <input
                type="text"
                value={commentAuthor}
                maxLength={120}
                placeholder={copy.authorPlaceholder}
                onChange={(event) => setCommentAuthor(event.target.value)}
              />
            </label>
            <label>
              <span>{copy.commentLabel}</span>
              <textarea
                value={commentContent}
                maxLength={1000}
                placeholder={copy.commentPlaceholder}
                onChange={(event) => setCommentContent(event.target.value)}
              />
            </label>
            {commentError && <p className="blog-form-error">{commentError}</p>}
            <button type="submit" className="blog-write-button" disabled={submittingComment}>
              <Send size={17} />
              {copy.send}
            </button>
          </form>

          <div className="blog-comment-list">
            {post.comments.length === 0 && (
              <p className="blog-empty-comment">{copy.noComments}</p>
            )}
            {post.comments.map((comment) => (
              <article className="blog-comment" key={comment.id}>
                <div>
                  <strong>{comment.authorName}</strong>
                  <time dateTime={comment.createdAt}>{formatDate(comment.createdAt, language)}</time>
                </div>
                <p>{comment.content}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default BlogDetailPage;
