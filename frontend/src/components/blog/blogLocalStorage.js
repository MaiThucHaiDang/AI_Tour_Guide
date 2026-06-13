const BLOG_INTERACTIONS_KEY = 'ai_tour_blog_interactions';
export const BLOG_DRAFT_KEY = 'ai_tour_blog_draft';

const readJson = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
};

const writeJson = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value));
};

// Per-device persistence: without auth, liked/bookmarked is tracked on this browser only.
export const getBlogInteraction = (slug) => {
  const allInteractions = readJson(BLOG_INTERACTIONS_KEY, {});
  return allInteractions[slug] || { liked: false, bookmarked: false };
};

export const setBlogInteraction = (slug, nextInteraction) => {
  const allInteractions = readJson(BLOG_INTERACTIONS_KEY, {});
  allInteractions[slug] = {
    liked: Boolean(nextInteraction.liked),
    bookmarked: Boolean(nextInteraction.bookmarked)
  };
  writeJson(BLOG_INTERACTIONS_KEY, allInteractions);
};

// Drafts stay on this device until the visitor publishes the post.
export const getBlogDraft = () => readJson(BLOG_DRAFT_KEY, null);

export const saveBlogDraft = (draft) => {
  writeJson(BLOG_DRAFT_KEY, {
    ...draft,
    savedAt: new Date().toISOString()
  });
};

export const clearBlogDraft = () => {
  localStorage.removeItem(BLOG_DRAFT_KEY);
};
