import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, BookOpen, PenLine, RefreshCw, Search, SlidersHorizontal } from 'lucide-react';
import BlogCard from './BlogCard';
import { BLOG_TAGS, getBlogPostsAPI } from '../../services/apiService';

const BlogListPage = ({
  language,
  onBackHome,
  onOpenBlogDetail,
  onCreatePost
}) => {
  const isVi = language === 'vi';
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const copy = useMemo(() => ({
    back: isVi ? 'Về trang chủ' : 'Home',
    kicker: isVi ? 'Cẩm nang tham quan Đại Nội' : 'Imperial City field guide',
    title: isVi ? 'Chọn đúng điểm dừng, đúng thời điểm, đúng nhịp đi.' : 'Choose the right stop, time, and pace.',
    desc: isVi
      ? 'Lịch trình ngắn, mẹo mua vé, góc nhìn văn hóa, món nên thử và kinh nghiệm thực tế cho người đang chuẩn bị vào Đại Nội Huế.'
      : 'Short routes, ticket notes, cultural context, food ideas, and practical tips for a real visit to Hue Imperial City.',
    write: isVi ? 'Chia sẻ chuyến đi của bạn' : 'Share your visit',
    searchLabel: isVi ? 'Tìm kinh nghiệm tham quan' : 'Search visit notes',
    searchPlaceholder: isVi ? 'Tìm vé, nắng, Ngọ Môn, món Huế...' : 'Search tickets, heat, Ngo Mon, Hue food...',
    allTags: isVi ? 'Tất cả' : 'All',
    filter: isVi ? 'Bạn đang cần' : 'Need now',
    loading: isVi ? 'Đang tải cẩm nang...' : 'Loading guide notes...',
    retry: isVi ? 'Thử lại' : 'Retry',
    noBlog: isVi ? 'Chưa có kinh nghiệm tham quan nào.' : 'No visit notes yet.',
    noResult: isVi ? 'Không có bài phù hợp với nhu cầu này.' : 'No notes match this need.',
    count: isVi ? `Đang hiển thị ${posts.length} bài phù hợp` : `${posts.length} matching notes`
  }), [isVi, posts.length]);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getBlogPostsAPI({
        search,
        tag: selectedTag,
        limit: 60
      });
      setPosts(data.posts);
      setTotal(data.total);
    } catch (err) {
      setError(err.message || (isVi ? 'Không thể tải cẩm nang tham quan.' : 'Unable to load the visit guide.'));
    } finally {
      setLoading(false);
    }
  }, [isVi, search, selectedTag]);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  const emptyText = search || selectedTag ? copy.noResult : copy.noBlog;

  return (
    <div className="blog-page">
      <header className="blog-topbar">
        <button type="button" className="blog-back-button" onClick={onBackHome}>
          <ArrowLeft size={18} />
          {copy.back}
        </button>
        <button type="button" className="blog-write-button" onClick={onCreatePost}>
          <PenLine size={18} />
          {copy.write}
        </button>
      </header>

      <main className="blog-list-main">
        <section className="blog-hero">
          <div className="blog-hero-copy">
            <span className="blog-kicker">
              <BookOpen size={17} />
              {copy.kicker}
            </span>
            <h1>{copy.title}</h1>
            <p>{copy.desc}</p>
          </div>
          <div className="blog-hero-panel" aria-label={isVi ? 'Gợi ý đọc nhanh' : 'Quick reading guide'}>
            <strong>{total}</strong>
            <span>{isVi ? 'gợi ý trước khi vào Đại Nội' : 'notes before you enter'}</span>
            <small>{isVi ? 'Lọc theo điều bạn cần ngay: vé, lộ trình, văn hóa, món ăn hoặc kinh nghiệm đi thật.' : 'Filter by what you need next: tickets, routes, culture, food, or practical experience.'}</small>
          </div>
        </section>

        <section className="blog-toolbar" aria-label={isVi ? 'Tìm kiếm và lọc cẩm nang' : 'Guide search and filters'}>
          <label className="blog-search-field">
            <Search size={18} aria-hidden="true" />
            <span className="sr-only">{copy.searchLabel}</span>
            <input
              type="search"
              value={search}
              placeholder={copy.searchPlaceholder}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <div className="blog-filter-group">
            <span>
              <SlidersHorizontal size={16} />
              {copy.filter}
            </span>
            <button
              type="button"
              className={!selectedTag ? 'active' : ''}
              onClick={() => setSelectedTag('')}
            >
              {copy.allTags}
            </button>
            {BLOG_TAGS.map((tag) => (
              <button
                type="button"
                className={selectedTag === tag ? 'active' : ''}
                key={tag}
                onClick={() => setSelectedTag(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        </section>

        <div className="blog-list-status" aria-live="polite">
          <span>{copy.count}</span>
        </div>

        {loading && (
          <section className="blog-state">
            <RefreshCw size={22} className="spin" />
            <p>{copy.loading}</p>
          </section>
        )}

        {!loading && error && (
          <section className="blog-state error">
            <p>{error}</p>
            <button type="button" onClick={loadPosts}>
              <RefreshCw size={17} />
              {copy.retry}
            </button>
          </section>
        )}

        {!loading && !error && posts.length === 0 && (
          <section className="blog-state">
            <BookOpen size={24} />
            <p>{emptyText}</p>
            <button type="button" onClick={onCreatePost}>
              <PenLine size={17} />
              {copy.write}
            </button>
          </section>
        )}

        {!loading && !error && posts.length > 0 && (
          <section className="blog-grid" aria-label={isVi ? 'Danh sách kinh nghiệm tham quan' : 'Visit notes'}>
            {posts.map((post) => (
              <BlogCard
                key={post.slug}
                post={post}
                language={language}
                onOpen={onOpenBlogDetail}
              />
            ))}
          </section>
        )}
      </main>
    </div>
  );
};

export default BlogListPage;
