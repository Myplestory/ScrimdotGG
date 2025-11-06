# Support Pages Architecture

## Overview
Support system for FAQs and ticket management.

---

## Entity Models

```
FAQ (Django) - NEW ENTITY
├── id: UUID (PK)
├── category: string ('account', 'matchmaking', 'technical', 'rules', 'billing')
├── question: string
├── answer: text (markdown)
├── order: int (display priority)
├── is_popular: boolean
├── views: int
├── helpful_count: int
├── created_at: datetime
└── updated_at: datetime

SupportTicket (Django) - NEW ENTITY
├── id: UUID (PK)
├── ticket_number: string (unique, e.g., 'SCR-12345')
├── user: ForeignKey → Player
├── category: string ('technical', 'account', 'report_player', 'billing', 'other')
├── priority: string ('low', 'medium', 'high', 'urgent')
├── status: string ('open', 'assigned', 'waiting_response', 'resolved', 'closed')
├── subject: string
├── description: text
├── assigned_to: ForeignKey → Player (support staff)
├── created_at: datetime
├── updated_at: datetime
├── resolved_at: datetime (nullable)
├── attachments: JSONField [
│     {
│       'filename': string,
│       'url': string,
│       'type': string
│     }
│   ]
└── tags: JSONField [string]

TicketMessage (Django) - NEW ENTITY
├── id: UUID (PK)
├── ticket: ForeignKey → SupportTicket
├── author: ForeignKey → Player
├── content: text (markdown)
├── is_staff_reply: boolean
├── is_internal_note: boolean (only visible to staff)
├── attachments: JSONField
├── created_at: datetime
└── edited_at: datetime (nullable)

TicketFeedback (Django) - NEW ENTITY
├── id: UUID (PK)
├── ticket: ForeignKey → SupportTicket (unique)
├── user: ForeignKey → Player
├── rating: int (1-5 stars)
├── feedback: text
└── created_at: datetime
```

---

## Page: FAQ (`faq.jsx`)

### Purpose
Self-service help documentation

### UI Components
- Search bar
- Category tabs/filters
- FAQ accordion
- "Was this helpful?" buttons
- Popular questions section
- Contact support button (if FAQ doesn't help)

### Events & Data Flow

#### 1. Get FAQs

**Frontend → Backend**
```javascript
Event: 'get_faqs'
Payload: {
  category: string | null,
  search_query: string | null
}
```

**Backend → Frontend**
```javascript
Event: 'faqs_list'
Payload: {
  faqs: [
    {
      id: UUID,
      category: string,
      question: string,
      answer: string,
      is_popular: boolean,
      helpful_count: int
    }
  ],
  popular_faqs: [
    // Top 5 most viewed/helpful FAQs
  ]
}
```

#### 2. Mark FAQ as Helpful

**Frontend → Backend**
```javascript
Event: 'mark_faq_helpful'
Payload: {
  faq_id: UUID,
  helpful: boolean
}
```

**Backend Processing**
1. Increment/decrement helpful_count
2. Update FAQ popularity ranking

**Backend → Frontend**
```javascript
Event: 'faq_feedback_recorded'
Payload: {
  faq_id: UUID,
  new_helpful_count: int
}
```

#### 3. Search FAQs

**Frontend → Backend**
```javascript
Event: 'search_faqs'
Payload: {
  query: string
}
```

**Backend Processing**
1. Full-text search on questions and answers
2. Rank by relevance
3. Highlight matched terms

**Backend → Frontend**
```javascript
Event: 'faq_search_results'
Payload: {
  results: [
    {
      faq: FAQ,
      relevance_score: float,
      matched_snippet: string // highlighted excerpt
    }
  ]
}
```

### Component Hierarchy
```
FAQ.jsx
├── FAQHeader
│   └── SearchBar
├── PopularQuestions
│   └── PopularFAQCard
├── CategoryTabs
│   └── CategoryTab
├── FAQList
│   └── FAQItem (Accordion)
│       ├── QuestionHeader
│       ├── AnswerContent (markdown)
│       └── HelpfulButtons
│           ├── HelpfulButton
│           └── NotHelpfulButton
└── SupportPrompt
    └── ContactSupportButton
```

---

## Page: Support Tickets (`tickets.jsx`)

### Purpose
Create and manage support tickets

### UI Components
- My tickets list with status filters
- Create new ticket button
- Ticket detail view
- Message thread
- Reply input
- File attachment
- Ticket status indicator
- Close ticket button
- Feedback form (on resolution)

### Events & Data Flow

#### 1. Get User's Tickets

**Frontend → Backend**
```javascript
Event: 'get_my_tickets'
Payload: {
  status_filter: string | null, // 'open', 'resolved', 'all'
  page: int
}
```

**Backend → Frontend**
```javascript
Event: 'user_tickets'
Payload: {
  tickets: [
    {
      id: UUID,
      ticket_number: string,
      subject: string,
      category: string,
      priority: string,
      status: string,
      assigned_to: Player | null,
      created_at: timestamp,
      updated_at: timestamp,
      unread_messages: int
    }
  ],
  pagination: {...}
}
```

#### 2. Create Ticket

**Frontend → Backend**
```javascript
Event: 'create_support_ticket'
Payload: {
  category: string,
  subject: string,
  description: string,
  attachments: [
    {
      filename: string,
      data: base64 | File,
      type: string
    }
  ]
}
```

**Backend Processing**
1. Generate unique ticket number
2. Validate and upload attachments
3. Create SupportTicket entity
4. Assign based on category/load balancing
5. Notify support team
6. Send confirmation email to user

**Backend → Frontend**
```javascript
Event: 'ticket_created'
Payload: {
  ticket: {
    id: UUID,
    ticket_number: string,
    status: 'open',
    created_at: timestamp
  },
  message: 'Your ticket has been created. We will respond within 24 hours.'
}
```

#### 3. Get Ticket Details

**Frontend → Backend**
```javascript
Event: 'get_ticket_details'
Payload: {
  ticket_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'ticket_details'
Payload: {
  ticket: {
    id: UUID,
    ticket_number: string,
    subject: string,
    category: string,
    priority: string,
    status: string,
    description: string,
    assigned_to: Player | null,
    created_at: timestamp,
    updated_at: timestamp,
    resolved_at: timestamp | null
  },
  messages: [
    {
      id: UUID,
      author: Player,
      content: string,
      is_staff_reply: boolean,
      attachments: [...],
      created_at: timestamp
    }
  ]
}
```

#### 4. Reply to Ticket

**Frontend → Backend**
```javascript
Event: 'reply_to_ticket'
Payload: {
  ticket_id: UUID,
  content: string,
  attachments: [...]
}
```

**Backend Processing**
1. Create TicketMessage
2. Update ticket status to 'waiting_response' (if user reply) or 'assigned' (if staff reply)
3. Update ticket updated_at
4. Notify ticket participants
5. Send email notification

**Backend → Frontend (Real-time to all viewing ticket)**
```javascript
Event: 'new_ticket_message'
Payload: {
  ticket_id: UUID,
  message: {
    id: UUID,
    author: Player,
    content: string,
    is_staff_reply: boolean,
    created_at: timestamp
  }
}
```

#### 5. Close Ticket

**Frontend → Backend**
```javascript
Event: 'close_ticket'
Payload: {
  ticket_id: UUID
}
```

**Backend Processing**
1. Update ticket status to 'closed'
2. Set resolved_at timestamp
3. Send feedback request

**Backend → Frontend**
```javascript
Event: 'ticket_closed'
Payload: {
  ticket_id: UUID,
  resolved_at: timestamp,
  feedback_request: boolean
}
```

#### 6. Submit Ticket Feedback

**Frontend → Backend**
```javascript
Event: 'submit_ticket_feedback'
Payload: {
  ticket_id: UUID,
  rating: int, // 1-5
  feedback: string
}
```

**Backend Processing**
1. Create TicketFeedback entity
2. Update support staff metrics
3. Thank user

**Backend → Frontend**
```javascript
Event: 'feedback_submitted'
Payload: {
  message: 'Thank you for your feedback!'
}
```

### Real-time Updates

**Backend → Frontend** (to user when staff updates)
```javascript
Event: 'ticket_updated'
Payload: {
  ticket_id: UUID,
  status: string,
  assigned_to: Player | null,
  priority: string
}
```

### Component Hierarchy
```
SupportTickets.jsx
├── TicketsHeader
│   ├── StatusFilterTabs
│   └── CreateTicketButton
├── TicketsList
│   └── TicketCard
│       ├── TicketNumber
│       ├── Subject
│       ├── StatusBadge
│       ├── PriorityIndicator
│       ├── CategoryTag
│       ├── LastUpdate
│       └── UnreadBadge
├── TicketDetailModal
│   ├── TicketHeader
│   │   ├── TicketNumber
│   │   ├── Subject
│   │   ├── StatusBadge
│   │   └── CloseTicketButton
│   ├── TicketInfo
│   │   ├── Category
│   │   ├── Priority
│   │   ├── AssignedTo
│   │   └── CreatedDate
│   ├── MessageThread
│   │   └── TicketMessage
│   │       ├── AuthorInfo
│   │       ├── StaffBadge (if staff)
│   │       ├── MessageContent
│   │       ├── AttachmentsList
│   │       └── Timestamp
│   └── ReplySection
│       ├── MessageInput
│       ├── AttachmentUploader
│       └── SendButton
├── CreateTicketModal
│   ├── CategorySelector
│   ├── SubjectInput
│   ├── DescriptionTextarea
│   ├── AttachmentUploader
│   └── SubmitButton
└── FeedbackModal
    ├── RatingStars
    ├── FeedbackTextarea
    └── SubmitButton
```

---

## Backend Django Architecture

### New Django App: `support`

```
support/
├── __init__.py
├── models.py
├── manager.py
├── views.py
├── admin.py
├── urls.py
├── notifications.py (email/notification handlers)
└── migrations/
```

#### Manager Methods

```python
# support/manager.py

class SupportManager:
    # FAQ operations
    async def get_faqs(self, category=None, search_query=None)
    async def get_popular_faqs(self, limit=5)
    async def search_faqs(self, query)
    async def mark_faq_helpful(self, faq_id, helpful)
    async def increment_faq_views(self, faq_id)
    
    # Ticket operations
    async def create_ticket(self, user_puuid, ticket_data)
    async def get_user_tickets(self, user_puuid, status_filter, page)
    async def get_ticket(self, ticket_id, user_puuid)
    async def update_ticket_status(self, ticket_id, new_status)
    async def assign_ticket(self, ticket_id, staff_puuid)
    async def close_ticket(self, ticket_id)
    
    # Message operations
    async def add_ticket_message(self, ticket_id, author_puuid, content, attachments, is_staff)
    async def get_ticket_messages(self, ticket_id)
    
    # Feedback
    async def submit_feedback(self, ticket_id, user_puuid, rating, feedback)
    async def get_staff_ratings(self, staff_puuid)
    
    # Admin/Staff operations
    async def get_all_tickets(self, filters, page)
    async def bulk_update_tickets(self, ticket_ids, updates)
    async def get_ticket_stats(self) # for dashboard
```

### Database Queries

```python
# Get user's tickets
tickets = await sync_to_async(
    SupportTicket.objects.filter(user__puuid=puuid)
    .select_related('assigned_to')
    .order_by('-updated_at')
    .all
)()

# Get ticket with messages
ticket = await sync_to_async(
    SupportTicket.objects.select_related('user', 'assigned_to').get
)(id=ticket_id)

messages = await sync_to_async(
    TicketMessage.objects.filter(ticket=ticket, is_internal_note=False)
    .select_related('author')
    .order_by('created_at')
    .all
)()

# Search FAQs (using Django full-text search)
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery

query = SearchQuery(search_text)
vector = SearchVector('question', weight='A') + SearchVector('answer', weight='B')

faqs = await sync_to_async(
    FAQ.objects.annotate(
        rank=SearchRank(vector, query)
    ).filter(rank__gte=0.1)
    .order_by('-rank')
    .all
)()
```

### Redis Caching

```python
# Cache popular FAQs (Redis Sorted Set)
Key: "support:popular_faqs"
Score: helpful_count + (views * 0.1)
Value: faq_id

# Ticket assignment queue (Redis List)
Key: "support:unassigned_tickets:{category}"
Value: ticket_id (FIFO)

# Staff availability (Redis Hash)
Key: "support:staff_availability"
Field: staff_puuid
Value: {
  'status': 'available' | 'busy' | 'offline',
  'active_tickets': int
}
```

### WebSocket Real-time Updates

```python
# Subscribe to ticket updates
await self.channel_layer.group_add(
    f"support_ticket_{ticket_id}",
    self.channel_name
)

# Broadcast new message
await self.channel_layer.group_send(
    f"support_ticket_{ticket_id}",
    {
        'type': 'new_ticket_message',
        'message': message_data
    }
)

# Notify user of ticket status change
await self.channel_layer.group_send(
    f"player_{user_puuid}",
    {
        'type': 'ticket_updated',
        'ticket': ticket_data
    }
)
```

### Email Notifications

```python
# support/notifications.py

async def send_ticket_created_email(ticket):
    """Send confirmation email when ticket is created"""
    
async def send_staff_assignment_email(ticket, staff):
    """Notify staff when assigned a ticket"""
    
async def send_new_message_email(ticket, message):
    """Notify user/staff of new message"""
    
async def send_ticket_resolved_email(ticket):
    """Send resolution confirmation and feedback request"""
```

### Permissions

```python
# Ticket permissions
- Users can only view their own tickets
- Staff can view all tickets
- Admins can reassign tickets and view internal notes
- Users cannot reopen closed tickets (must create new one)
```

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

**NONE** - No support system functionality has been implemented.

### ⚠️ PARTIALLY IMPLEMENTED

**NONE** - No support infrastructure exists.

### ❌ NOT IMPLEMENTED

1. **Support Django App**
   - ❌ No `support` Django app exists in `server/`
   - ❌ Need to create entire app structure

2. **Support Models** (`server/support/models.py` - DOES NOT EXIST)
   - ❌ FAQ model - Knowledge base articles with categories
   - ❌ SupportTicket model - User-submitted support tickets
   - ❌ TicketMessage model - Conversation thread for tickets
   - ❌ TicketFeedback model - User feedback on ticket resolution
   - ❌ TicketAttachment model - File attachments for tickets

3. **FAQ System** (`server/support/faq_manager.py` - DOES NOT EXIST)
   - ❌ No FAQ management:
     - create_faq()
     - update_faq()
     - search_faqs()
     - track_views()
     - track_helpfulness()
     - suggest_popular_faqs()

4. **Ticket Manager** (`server/support/ticket_manager.py` - DOES NOT EXIST)
   - ❌ No ticket business logic:
     - create_ticket()
     - assign_ticket()
     - add_ticket_message()
     - update_ticket_status()
     - close_ticket()
     - escalate_ticket()
     - generate_ticket_number()

5. **Ticket Assignment System**
   - ❌ No auto-assignment to support staff
   - ❌ No workload balancing
   - ❌ No priority-based routing

6. **Email Notifications**
   - ❌ No email on ticket creation
   - ❌ No email on staff reply
   - ❌ No email on ticket status change
   - ❌ No email integration (SendGrid, SES, etc.)

7. **File Attachment System**
   - ❌ No file upload for tickets
   - ❌ No file storage (S3, local)
   - ❌ No file validation (size, type)
   - ❌ No attachment preview

8. **Support Staff Dashboard**
   - ❌ No admin panel for viewing tickets
   - ❌ No ticket queue management
   - ❌ No ticket statistics (open, resolved, avg response time)
   - ❌ No staff performance metrics

9. **Support WebSocket Handlers** (`server/realtime/handlers/support_handler.py` - DOES NOT EXIST)
   - ❌ No real-time support events:
     - new_ticket_created
     - ticket_assigned
     - new_message_received
     - ticket_status_changed

10. **Frontend Integration**
    - ❌ No FAQ page with search
    - ❌ No ticket creation form
    - ❌ No ticket list page
    - ❌ No ticket detail/messaging page
    - ❌ No feedback submission
    - ❌ No staff dashboard

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Foundation)
1. **Create Support Django App** - Set up app structure in `server/support/`
2. **Create FAQ Model** - Simple knowledge base with categories
3. **Implement FAQ Manager** - CRUD for FAQs with search
4. **Build FAQ Frontend** - Searchable FAQ page
5. **Create SupportTicket Model** - Ticket system with status tracking
6. **Implement Ticket Manager** - Create, view, update tickets
7. **Build Ticket Creation Form** - Frontend form for submitting tickets

### 🔶 MEDIUM PRIORITY (Core Features)
8. **Add TicketMessage Model** - Conversation thread for tickets
9. **Implement Ticket Messaging** - Reply to tickets
10. **Build Ticket Detail Page** - View ticket and messages
11. **Add Ticket Assignment** - Assign tickets to support staff
12. **Build Staff Dashboard** - Admin panel for managing tickets
13. **Add Email Notifications** - Notify users of ticket updates

### 🔷 LOW PRIORITY (Enhanced Features)
14. **File Attachments** - Upload screenshots/logs to tickets
15. **Ticket Feedback** - Rate ticket resolution quality
16. **Auto-Suggestions** - Suggest FAQs based on ticket content
17. **Ticket Templates** - Pre-defined templates for common issues
18. **Knowledge Base Search** - Advanced search with filters
19. **Canned Responses** - Quick replies for support staff
20. **Ticket Escalation** - Auto-escalate unresolved tickets
21. **Real-Time Updates** - WebSocket for live ticket updates

---

## Summary

**Overall Status**: 0% Complete

The support system is **completely unimplemented**. There is no dedicated `support` Django app, no support models, no managers, no handlers, and no frontend integration.

**What's Missing (Everything)**:
- Entire Support Django app
- All support models (FAQ, SupportTicket, TicketMessage, TicketFeedback)
- FAQ system with search
- Ticket creation and management
- Ticket messaging/conversation
- Assignment system for support staff
- Email notification system
- File attachment handling
- Support staff dashboard
- All WebSocket handlers for support events
- All frontend pages (FAQ, ticket creation, ticket list/detail)

**Dependencies**:
- Requires basic Player authentication (already exists ✅)
- Requires email integration (does not exist ❌)
- Requires file storage (S3 or local - does not exist ❌)
- Should wait until core matchmaking is stable

**Estimated Development Time**: 3-5 weeks for basic support, 6-8 weeks for full features

**Key Features Needed**:
1. **FAQ System**: Searchable knowledge base to reduce ticket volume
2. **Ticket Creation**: Simple form to submit support requests
3. **Ticket Tracking**: View status and history of submitted tickets
4. **Ticket Messaging**: Two-way conversation between user and support staff
5. **Staff Dashboard**: Admin panel for support staff to manage tickets
6. **Email Notifications**: Alert users when tickets are updated
7. **Attachments**: Upload screenshots/logs to help diagnose issues

**Recommendation**: Support system is a **Phase 3-4 feature**. It's important for user experience but not critical for launch. Should be implemented after:
- ✅ PUG matchmaking is production-ready
- ⚠️ Email integration is set up (for notifications)
- ⚠️ File storage is configured (for attachments)

**Alternative Approach for Launch**:
1. **Discord Support Channel**: Use Discord for community support initially
2. **Simple Contact Form**: Basic email form that sends to support@scrimgg.com
3. **Static FAQ Page**: Hardcoded FAQ in HTML (no database)
4. **Google Forms**: Use Google Forms for bug reports/feedback
5. **Zendesk/Intercom**: Third-party support platform for early days

This allows providing user support without building a full ticketing system, then migrate to custom solution once platform grows.

**Build Priority**: Low - Can be postponed until after core matchmaking, league system, and other critical features are stable.
