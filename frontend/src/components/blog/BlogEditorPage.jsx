import React, { useMemo, useState } from 'react';
import { ArrowLeft, Image, PenLine, Save, Send } from 'lucide-react';
import { BLOG_TAGS, createBlogPostAPI } from '../../services/apiService';
import { clearBlogDraft, getBlogDraft, saveBlogDraft } from './blogLocalStorage';

const UNSAFE_TEXT_PATTERN = /(<\s*\/?\s*script\b|javascript\s*:|on[a-z]+\s*=)/i;

const DEFAULT_FORM = {
  title: '',
  coverImage: '',
  coverAlt: '',
  excerpt: '',
  content: '',
  tags: [],
  authorName: ''
};

const isValidCoverUrl = (value) => {
  const trimmed = value.trim();
  if (!trimmed) return true;
  if (trimmed.startsWith('/')) {
    return !trimmed.startsWith('//') && !trimmed.includes('..');
  }
  try {
    const url = new URL(trimmed);
    return ['http:', 'https:'].includes(url.protocol);
  } catch {
    return false;
  }
};

const BlogEditorPage = ({ language, onBackList, onPostCreated }) => {
  const isVi = language === 'vi';
  const draft = useMemo(() => getBlogDraft(), []);
  const [form, setForm] = useState(() => draft || DEFAULT_FORM);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState(draft?.savedAt ? (isVi ? 'Đã mở lại bản viết dở.' : 'Draft restored.') : '');
  const [submitting, setSubmitting] = useState(false);

  const copy = {
    back: isVi ? 'Quay lại cẩm nang' : 'Back to guide',
    kicker: isVi ? 'Chia sẻ kinh nghiệm đi thật' : 'Share a real visit note',
    title: isVi ? 'Ghi lại điều sẽ giúp người sau đi dễ hơn.' : 'Write what would help the next visitor.',
    desc: isVi
      ? 'Một lộ trình vừa sức, góc chụp đẹp, đoạn dễ nắng, món nên thử hoặc câu chuyện bạn nhớ nhất đều có giá trị.'
      : 'A manageable route, good photo angle, sunny section, dish to try, or remembered story can all help.',
    titleLabel: isVi ? 'Tiêu đề' : 'Title',
    coverLabel: isVi ? 'Ảnh bìa' : 'Cover image',
    coverPlaceholder: isVi ? 'Dán link ảnh, hoặc để trống để dùng ảnh bìa mặc định' : 'Paste an image link, or leave blank for the default cover photo',
    coverAltLabel: isVi ? 'Ảnh này nói về điều gì?' : 'What does this image show?',
    excerptLabel: isVi ? 'Tóm tắt cho người sắp đi' : 'Summary for visitors',
    contentLabel: isVi ? 'Kinh nghiệm chi tiết' : 'Detailed note',
    authorLabel: isVi ? 'Tên hiển thị' : 'Display name',
    tagsLabel: isVi ? 'Người đọc nên dùng bài này khi cần' : 'This helps with',
    draft: isVi ? 'Giữ lại để viết tiếp' : 'Save for later',
    publish: isVi ? 'Đăng bài' : 'Publish',
    localDraft: isVi ? 'Bản viết dở được giữ trên thiết bị này cho đến khi bạn đăng.' : 'Your unfinished note stays on this device until you publish.',
    requiredTitle: isVi ? 'Tiêu đề không được để trống.' : 'Title is required.',
    requiredExcerpt: isVi ? 'Mô tả ngắn không được để trống.' : 'Excerpt is required.',
    requiredContent: isVi ? 'Nội dung không được để trống.' : 'Content is required.',
    excerptLength: isVi ? 'Mô tả ngắn tối đa 420 ký tự.' : 'Excerpt must be at most 420 characters.',
    invalidCover: isVi ? 'Dán link ảnh hợp lệ, hoặc để trống để dùng ảnh bìa mặc định.' : 'Enter a valid image link, or leave it blank to use the default cover photo.',
    requiredTag: isVi ? 'Chọn ít nhất một chủ đề.' : 'Choose at least one topic.',
    unsafe: isVi ? 'Vui lòng nhập chữ thường, không dán mã HTML hoặc script.' : 'Please enter plain text, not HTML or scripts.',
    saved: isVi ? 'Đã giữ lại bản viết dở.' : 'Draft saved.',
    failed: isVi ? 'Không thể đăng bài lúc này.' : 'Unable to publish right now.'
  };

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
  };

  const toggleTag = (tag) => {
    setForm((current) => {
      const exists = current.tags.includes(tag);
      return {
        ...current,
        tags: exists ? current.tags.filter((item) => item !== tag) : [...current.tags, tag]
      };
    });
    setErrors((current) => ({ ...current, tags: '' }));
  };

  const validate = () => {
    const nextErrors = {};
    const textFields = [form.title, form.excerpt, form.content, form.authorName, form.coverAlt];

    if (!form.title.trim()) nextErrors.title = copy.requiredTitle;
    if (!form.excerpt.trim()) nextErrors.excerpt = copy.requiredExcerpt;
    if (form.excerpt.trim().length > 420) nextErrors.excerpt = copy.excerptLength;
    if (!form.content.trim()) nextErrors.content = copy.requiredContent;
    if (!isValidCoverUrl(form.coverImage)) nextErrors.coverImage = copy.invalidCover;
    if (form.tags.length === 0) nextErrors.tags = copy.requiredTag;
    if (textFields.some((value) => UNSAFE_TEXT_PATTERN.test(value))) {
      nextErrors.content = copy.unsafe;
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSaveDraft = () => {
    saveBlogDraft(form);
    setMessage(copy.saved);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    if (!validate()) return;

    setSubmitting(true);
    try {
      const createdPost = await createBlogPostAPI({
        ...form,
        coverImage: form.coverImage.trim() || '/assets/images/art_17_1.jpg',
        coverAlt: form.coverAlt.trim() || 'Ảnh bìa mặc định bài chia sẻ du lịch Huế',
        authorName: form.authorName.trim() || 'Khách',
        status: 'published'
      });
      clearBlogDraft();
      onPostCreated(createdPost.slug);
    } catch (err) {
      setMessage(err.message || copy.failed);
    } finally {
      setSubmitting(false);
    }
  };

  const coverPreview = form.coverImage.trim() || '/assets/images/art_17_1.jpg';

  return (
    <div className="blog-page">
      <header className="blog-topbar">
        <button type="button" className="blog-back-button" onClick={onBackList}>
          <ArrowLeft size={18} />
          {copy.back}
        </button>
      </header>

      <main className="blog-editor-main">
        <section className="blog-editor-heading">
          <span className="blog-kicker">
            <PenLine size={17} />
            {copy.kicker}
          </span>
          <h1>{copy.title}</h1>
          <p>{copy.desc}</p>
        </section>

        <form className="blog-editor-form" onSubmit={handleSubmit}>
          <div className="blog-form-grid">
            <label>
              <span>{copy.titleLabel}</span>
              <input
                type="text"
                value={form.title}
                maxLength={220}
                onChange={(event) => updateField('title', event.target.value)}
              />
              {errors.title && <small>{errors.title}</small>}
            </label>

            <label>
              <span>{copy.authorLabel}</span>
              <input
                type="text"
                value={form.authorName}
                maxLength={120}
                placeholder="Khách"
                onChange={(event) => updateField('authorName', event.target.value)}
              />
            </label>
          </div>

          <div className="blog-form-grid">
            <label>
              <span>{copy.coverLabel}</span>
              <input
                type="text"
                value={form.coverImage}
                placeholder={copy.coverPlaceholder}
                onChange={(event) => updateField('coverImage', event.target.value)}
              />
              {errors.coverImage && <small>{errors.coverImage}</small>}
            </label>

            <label>
              <span>{copy.coverAltLabel}</span>
              <input
                type="text"
                value={form.coverAlt}
                maxLength={260}
                onChange={(event) => updateField('coverAlt', event.target.value)}
              />
            </label>
          </div>

          <div className="blog-cover-preview">
            <Image size={18} />
            <img src={coverPreview} alt={form.coverAlt || 'Ảnh xem trước bài chia sẻ'} loading="lazy" />
          </div>

          <label>
            <span>{copy.excerptLabel}</span>
            <textarea
              className="short"
              value={form.excerpt}
              maxLength={420}
              onChange={(event) => updateField('excerpt', event.target.value)}
            />
            <em>{form.excerpt.length}/420</em>
            {errors.excerpt && <small>{errors.excerpt}</small>}
          </label>

          <fieldset className="blog-tag-fieldset">
            <legend>{copy.tagsLabel}</legend>
            <div className="blog-tag-picker">
              {BLOG_TAGS.map((tag) => (
                <label key={tag}>
                  <input
                    type="checkbox"
                    checked={form.tags.includes(tag)}
                    onChange={() => toggleTag(tag)}
                  />
                  <span>{tag}</span>
                </label>
              ))}
            </div>
            {errors.tags && <small>{errors.tags}</small>}
          </fieldset>

          <label>
            <span>{copy.contentLabel}</span>
            <textarea
              value={form.content}
              maxLength={12000}
              onChange={(event) => updateField('content', event.target.value)}
            />
            {errors.content && <small>{errors.content}</small>}
          </label>

          <div className="blog-editor-actions">
            <button type="button" className="blog-back-button" onClick={handleSaveDraft}>
              <Save size={17} />
              {copy.draft}
            </button>
            <button type="submit" className="blog-write-button" disabled={submitting}>
              <Send size={17} />
              {copy.publish}
            </button>
          </div>

          <p className="blog-footnote">{copy.localDraft}</p>
          {message && <p className="blog-notice" role="status">{message}</p>}
        </form>
      </main>
    </div>
  );
};

export default BlogEditorPage;
