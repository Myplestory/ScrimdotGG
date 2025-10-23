# Forum Pages Architecture

## Overview
Community forum system for discussions, announcements, and player interaction.

---

## Entity Models

```
ForumCategory (Django) - NEW ENTITY
├── id: UUID (PK)
├── name: string
├── slug: string (unique)
├── description: text
├── icon: string (icon name)
├── order: int (display order)
├── color: string (hex color for UI)
├── is_locked: boolean (read-only if true)
├── required_role: string | null ('admin', 'moderator', 'verified')
└── post_count: int (cached)

ForumThread (Django) - NEW ENTITY
├── id: UUID (PK)
├── category: ForeignKey → ForumCategory
├── author: ForeignKey → Player
├── title: string (max 200 chars)
├── content: text (markdown supported)
├── is_pinned: boolean
├── is_locked: boolean
├── is_announcement: boolean
├── tags: JSONField [string]
├── view_count: int
├── reply_count: int
├── created_at: datetime
├── updated_at: datetime
├── last_activity_at: datetime
└── last_reply_by: ForeignKey → Player (nullable)

ForumReply (Django) - NEW ENTITY
├── id: UUID (PK)
├── thread: ForeignKey → ForumThread
├── author: ForeignKey → Player
├── content: text (markdown supported)
├── reply_to: ForeignKey → ForumReply (nullable, for nested replies)
├── is_deleted: boolean
├── edited_at: datetime (nullable)
├── likes: int
├── created_at: datetime
└── attachments: JSONField

ForumLike (Django) - NEW ENTITY
├── id: UUID (PK)
├── user: ForeignKey → Player
├── thread: ForeignKey → ForumThread (nullable)
├── reply: ForeignKey → ForumReply (nullable)
├── created_at: datetime
└── Unique constraint: (user, thread) OR (user, reply)

ForumReport (Django) - NEW ENTITY
├── id: UUID (PK)
├── reporter: ForeignKey → Player
├── content_type: string ('thread' | 'reply')
├── thread: ForeignKey → ForumThread (nullable)
├── reply: ForeignKey → ForumReply (nullable)
├── reason: string
├── details: text
├── status: string ('pending', 'reviewing', 'resolved', 'dismissed')
├── reviewed_by: ForeignKey → Player (nullable, moderator)
├── created_at: datetime
└── resolved_at: datetime (nullable)
```

---

## Page: Forum Index (`index.jsx`)

### Purpose
Browse forum categories and threads, search discussions

### UI Components
- Category list
- Trending/hot threads
- Recent activity feed
- Search bar
- Thread sorting (recent, popular, unanswered)
- Pagination

### Events & Data Flow

#### 1. Get Forum Categories

**Frontend → Backend**
```javascript
Event: 'get_forum_categories'
Payload: {}
```

**Backend → Frontend**
```javascript
Event: 'forum_categories'
Payload: {
  categories: [
    {
      id: UUID,
      name: string,
      slug: string,
      description: string,
      icon: string,
      color: string,
      post_count: int,
      is_locked: boolean,
      latest_thread: {
        id: UUID,
        title: string,
        author: Player,
        created_at: timestamp
      }
    }
  ]
}
```

#### 2. Get Threads in Category

**Frontend → Backend**
```javascript
Event: 'get_forum_threads'
Payload: {
  category_slug: string,
  sort_by: 'recent' | 'popular' | 'unanswered',
  page: int,
  per_page: int (default: 20)
}
```

**Backend → Frontend**
```javascript
Event: 'forum_threads'
Payload: {
  category: ForumCategory,
  threads: [
    {
      id: UUID,
      title: string,
      author: {
        puuid: string,
        alias: string,
        rank: string,
        avatar: string
      },
      content_preview: string, // first 200 chars
      is_pinned: boolean,
      is_locked: boolean,
      tags: [string],
      view_count: int,
      reply_count: int,
      created_at: timestamp,
      last_activity_at: timestamp,
      last_reply_by: Player | null
    }
  ],
  pagination: {
    current_page: int,
    total_pages: int,
    total_threads: int
  }
}
```

#### 3. Search Forums

**Frontend → Backend**
```javascript
Event: 'search_forums'
Payload: {
  query: string,
  category_slug: string | null,
  tags: [string] | null,
  author_puuid: string | null
}
```

**Backend → Frontend**
```javascript
Event: 'forum_search_results'
Payload: {
  results: [
    {
      type: 'thread' | 'reply',
      thread: ForumThread,
      reply: ForumReply | null,
      relevance_score: float,
      matched_content: string // highlighted excerpt
    }
  ],
  total_results: int
}
```

### Component Hierarchy
```
ForumIndex.jsx
├── ForumHeader
│   ├── SearchBar
│   └── NewThreadButton
├── CategoryList
│   └── CategoryCard
│       ├── CategoryIcon
│       ├── CategoryInfo
│       ├── PostCount
│       └── LatestThreadPreview
├── TrendingSection
│   └── TrendingThreadCard
├── ThreadList
│   ├── SortSelector
│   └── ThreadRow
│       ├── ThreadIcon (pinned, locked, hot)
│       ├── ThreadTitle
│       ├── AuthorInfo
│       ├── TagList
│       ├── Stats (views, replies)
│       └── LastActivityInfo
└── Pagination
```

---

## Page: Post New Thread (`postnew.jsx`)

### Purpose
Create new forum thread

### UI Components
- Category selector
- Title input
- Rich text editor (markdown)
- Tag selector/input
- Preview mode
- Submit/Draft buttons
- Image/attachment upload

### Events & Data Flow

#### 1. Create Thread

**Frontend → Backend**
```javascript
Event: 'create_forum_thread'
Payload: {
  category_slug: string,
  title: string,
  content: string, // markdown
  tags: [string],
  attachments: [
    {
      type: 'image' | 'video' | 'file',
      url: string,
      filename: string
    }
  ]
}
```

**Backend Processing**
1. Validate title and content
2. Check user not rate-limited
3. Validate tags
4. Process attachments
5. Create ForumThread entity
6. Update category post count
7. Send notifications to category followers

**Backend → Frontend**
```javascript
Event: 'thread_created'
Payload: {
  thread: {
    id: UUID,
    category: ForumCategory,
    title: string,
    author: Player,
    content: string,
    tags: [string],
    created_at: timestamp,
    url: string // redirect URL
  }
}
```

#### 2. Save Draft

**Frontend → Backend**
```javascript
Event: 'save_forum_draft'
Payload: {
  draft_id: UUID | null,
  category_slug: string,
  title: string,
  content: string,
  tags: [string]
}
```

**Backend → Frontend**
```javascript
Event: 'draft_saved'
Payload: {
  draft_id: UUID,
  saved_at: timestamp
}
```

### Component Hierarchy
```
PostNew.jsx
├── ThreadForm
│   ├── CategorySelector
│   ├── TitleInput
│   ├── TagSelector
│   │   └── TagChip
│   ├── MarkdownEditor
│   │   ├── Toolbar
│   │   └── TextArea
│   ├── AttachmentUploader
│   │   └── AttachmentPreview
│   └── PreviewPanel (toggle)
└── ActionButtons
    ├── SaveDraftButton
    ├── PreviewButton
    └── SubmitButton
```

---

## Page: Thread View (not in current structure, but needed)

### Purpose
View thread and replies, participate in discussion

### UI Components
- Thread header (title, author, date)
- Original post content
- Reply list (threaded/flat view toggle)
- Reply editor
- Like/upvote button
- Report button
- Thread actions (lock, pin - for moderators)

### Events & Data Flow

#### 1. Get Thread Details

**Frontend → Backend**
```javascript
Event: 'get_forum_thread'
Payload: {
  thread_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'forum_thread_details'
Payload: {
  thread: {
    id: UUID,
    category: ForumCategory,
    author: Player,
    title: string,
    content: string,
    tags: [string],
    is_pinned: boolean,
    is_locked: boolean,
    view_count: int,
    reply_count: int,
    likes: int,
    user_liked: boolean,
    created_at: timestamp,
    updated_at: timestamp
  },
  replies: [
    {
      id: UUID,
      author: Player,
      content: string,
      reply_to: UUID | null,
      likes: int,
      user_liked: boolean,
      created_at: timestamp,
      edited_at: timestamp | null,
      is_deleted: boolean
    }
  ]
}
```

#### 2. Post Reply

**Frontend → Backend**
```javascript
Event: 'post_forum_reply'
Payload: {
  thread_id: UUID,
  content: string,
  reply_to: UUID | null // for threaded replies
}
```

**Backend Processing**
1. Validate thread not locked
2. Check user not rate-limited
3. Create ForumReply entity
4. Update thread reply count and last activity
5. Send notification to thread author
6. Broadcast to thread subscribers

**Backend → Frontend (to all viewing thread)**
```javascript
Event: 'new_forum_reply'
Payload: {
  thread_id: UUID,
  reply: {
    id: UUID,
    author: Player,
    content: string,
    reply_to: UUID | null,
    created_at: timestamp
  }
}
```

#### 3. Like/Unlike

**Frontend → Backend**
```javascript
Event: 'toggle_forum_like'
Payload: {
  content_type: 'thread' | 'reply',
  content_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'like_toggled'
Payload: {
  content_type: string,
  content_id: UUID,
  liked: boolean,
  new_like_count: int
}
```

#### 4. Report Content

**Frontend → Backend**
```javascript
Event: 'report_forum_content'
Payload: {
  content_type: 'thread' | 'reply',
  content_id: UUID,
  reason: 'spam' | 'harassment' | 'offensive' | 'other',
  details: string
}
```

**Backend Processing**
1. Create ForumReport entity
2. Notify moderators
3. Auto-hide if multiple reports

**Backend → Frontend**
```javascript
Event: 'report_submitted'
Payload: {
  report_id: UUID,
  message: 'Thank you for your report'
}
```

---

## Backend Django Architecture

### New Django App: `forums`

```
forums/
├── __init__.py
├── models.py
├── manager.py
├── views.py
├── admin.py
├── urls.py
├── signals.py (for post-save hooks)
└── migrations/
```

#### Manager Methods

```python
# forums/manager.py

class ForumManager:
    # Category operations
    async def get_categories(self)
    async def get_category_by_slug(self, slug)
    
    # Thread operations
    async def create_thread(self, author_puuid, category_slug, data)
    async def get_thread(self, thread_id, increment_views=True)
    async def get_threads_in_category(self, category_slug, sort_by, page, per_page)
    async def update_thread(self, thread_id, updates)
    async def delete_thread(self, thread_id, deleter_puuid)
    async def lock_thread(self, thread_id, moderator_puuid)
    async def pin_thread(self, thread_id, moderator_puuid)
    
    # Reply operations
    async def post_reply(self, thread_id, author_puuid, content, reply_to=None)
    async def edit_reply(self, reply_id, new_content)
    async def delete_reply(self, reply_id, deleter_puuid)
    async def get_replies(self, thread_id, sort_by='oldest')
    
    # Likes
    async def toggle_like(self, user_puuid, content_type, content_id)
    async def get_like_count(self, content_type, content_id)
    
    # Search
    async def search_forums(self, query, filters=None)
    
    # Moderation
    async def report_content(self, reporter_puuid, content_type, content_id, reason, details)
    async def get_pending_reports(self)
    async def resolve_report(self, report_id, moderator_puuid, action)
    
    # Drafts
    async def save_draft(self, author_puuid, draft_data)
    async def get_drafts(self, author_puuid)
    async def delete_draft(self, draft_id)
```

### Database Queries

```python
# Get threads with author and last reply info
threads = await sync_to_async(
    ForumThread.objects.filter(category__slug=slug)
    .select_related('author', 'last_reply_by', 'category')
    .order_by('-last_activity_at')
    .all
)()

# Get thread with replies
thread = await sync_to_async(
    ForumThread.objects.select_related('author', 'category').get
)(id=thread_id)

replies = await sync_to_async(
    ForumReply.objects.filter(thread=thread)
    .select_related('author')
    .order_by('created_at')
    .all
)()

# Check if user liked content
has_liked = await sync_to_async(
    ForumLike.objects.filter(
        user__puuid=puuid,
        thread_id=thread_id
    ).exists
)()
```

### Redis Caching

```python
# Cache hot threads (Redis Sorted Set)
Key: "forums:hot_threads"
Score: (views * 0.3) + (replies * 0.5) + (likes * 0.2)
Value: thread_id

# Cache thread view count (Redis Hash)
Key: f"forums:thread:{thread_id}:views"
Value: count (sync to DB every 100 views)

# Rate limiting (Redis)
Key: f"forums:ratelimit:{puuid}:posts"
TTL: 300 seconds (5 minutes)
Value: post_count (max 5 per 5 min)
```

### WebSocket Real-time Updates

```python
# Subscribe to thread updates
await self.channel_layer.group_add(
    f"forum_thread_{thread_id}",
    self.channel_name
)

# Broadcast new reply
await self.channel_layer.group_send(
    f"forum_thread_{thread_id}",
    {
        'type': 'new_forum_reply',
        'reply': reply_data
    }
)
```

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

**NONE** - No forum functionality has been implemented.

### ⚠️ PARTIALLY IMPLEMENTED

**NONE** - No forum infrastructure exists.

### ❌ NOT IMPLEMENTED

1. **Forum Django App**
   - ❌ No `forums` Django app exists in `server/`
   - ❌ Need to create entire app structure

2. **Forum Models** (`server/forums/models.py` - DOES NOT EXIST)
   - ❌ ForumCategory model - Organize forum into categories
   - ❌ ForumThread model - Forum threads with author, title, content
   - ❌ ForumReply model - Replies to threads with nested reply support
   - ❌ ForumLike model - Like tracking for posts/replies
   - ❌ ForumDraft model - Save draft posts before publishing
   - ❌ ForumReport model - Report inappropriate content
   - ❌ ForumSubscription model - Subscribe to threads for notifications

3. **Forum Manager** (`server/forums/manager.py` - DOES NOT EXIST)
   - ❌ No forum business logic:
     - create_category()
     - create_thread()
     - reply_to_thread()
     - edit_post()
     - delete_post()
     - like_post()
     - pin_thread()
     - lock_thread()
     - search_forums()

4. **Moderation Tools** (`server/forums/moderation.py` - DOES NOT EXIST)
   - ❌ No moderation capabilities:
     - delete_inappropriate_content()
     - ban_user_from_forums()
     - merge_threads()
     - move_thread_to_category()
     - review_reports()

5. **Forum Search** (`server/forums/search.py` - DOES NOT EXIST)
   - ❌ No search functionality
   - ❌ No indexing for full-text search
   - ❌ No advanced search filters (author, date, category)

6. **Rate Limiting** (`server/forums/rate_limiter.py` - DOES NOT EXIST)
   - ❌ No rate limiting for post creation
   - ❌ No spam detection
   - ❌ No cooldown periods

7. **Notification System**
   - ❌ No notifications for thread replies
   - ❌ No notifications for mentions (@username)
   - ❌ No notification preferences

8. **Forum WebSocket Handlers** (`server/realtime/handlers/forum_handler.py` - DOES NOT EXIST)
   - ❌ No real-time forum events:
     - new_thread_created
     - new_reply_posted
     - thread_locked
     - thread_pinned

9. **Frontend Integration**
   - ❌ No forum category browser
   - ❌ No thread list page
   - ❌ No thread detail/reply page
   - ❌ No rich text editor (markdown)
   - ❌ No search interface
   - ❌ No moderation panel

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Foundation)
1. **Create Forums Django App** - Set up app structure in `server/forums/`
2. **Create Forum Models** - ForumCategory, ForumThread, ForumReply
3. **Implement ForumManager** - Basic CRUD for categories, threads, replies
4. **Build Frontend Thread List** - Display threads in categories
5. **Build Frontend Thread Detail** - Display thread content and replies
6. **Add Rich Text Editor** - Markdown editor for posts

### 🔶 MEDIUM PRIORITY (Core Features)
7. **Implement Like System** - ForumLike model and handlers
8. **Add Search Functionality** - Full-text search with filters
9. **Implement Pinning/Locking** - Moderator controls
10. **Add Rate Limiting** - Prevent spam with cooldowns
11. **Build Moderation Tools** - Admin panel for content management
12. **Add Thread Subscriptions** - Email/notification on replies

### 🔷 LOW PRIORITY (Enhanced Features)
13. **Nested Replies** - Reply-to-reply threading
14. **Draft Saving** - Auto-save drafts before posting
15. **File Attachments** - Upload images/files to posts
16. **Emoji Reactions** - Quick emoji reactions to posts
17. **User Reputation** - Karma/upvote system based on forum activity
18. **Thread Tags** - Organize threads with tags
19. **Advanced Moderation** - Merge threads, move to categories, ban users
20. **Real-Time Updates** - WebSocket for live post updates

---

## Summary

**Overall Status**: 0% Complete

The forum system is **completely unimplemented**. There is no dedicated `forums` Django app, no forum models, no managers, no handlers, and no frontend integration.

**What's Missing (Everything)**:
- Entire Forums Django app
- All forum models (ForumCategory, ForumThread, ForumReply, ForumLike)
- All business logic (ForumManager, moderation tools, search)
- Rate limiting and spam prevention
- All WebSocket handlers for forum events
- All frontend pages (category browser, thread list, thread detail)
- Rich text editor (markdown support)
- Notification system for thread activity

**Dependencies**:
- Requires basic Player authentication (already exists ✅)
- Requires notification system (does not exist ❌)
- Should wait until core matchmaking is stable

**Estimated Development Time**: 4-6 weeks for basic forum, 8-10 weeks for full features

**Key Features Needed**:
1. **Category Organization**: Organize forums into categories (Announcements, General, Strategy, etc.)
2. **Thread CRUD**: Create, read, update, delete threads and replies
3. **Rich Text**: Markdown editor with preview
4. **Moderation**: Pin, lock, delete threads; ban users from forums
5. **Search**: Full-text search across threads and replies
6. **Rate Limiting**: Prevent spam with cooldowns (e.g., 1 thread per 5 minutes)
7. **Likes**: Like posts and replies
8. **Notifications**: Notify users of replies to their threads

**Recommendation**: Forum system is a **Phase 5+ feature** (community engagement). It's not critical for core matchmaking functionality but enhances community building. Should be implemented after:
- ✅ PUG matchmaking is production-ready
- ✅ League system is implemented (if doing leagues)
- ⚠️ Notification system exists

**Alternative Approach**: Use Discord for community discussions initially and build forum system later as a "nice-to-have" feature. Many competitive gaming platforms rely on Discord for community interaction and only add forums for long-form content (guides, announcements).
