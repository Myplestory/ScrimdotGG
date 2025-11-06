"""
Forum event handlers for categories, threads, and replies.
"""
from quart import current_app
from ..events import on


@on("get_forum_categories")
async def handle_get_forum_categories(payload: dict, client_id: int, ws, mgr):
    """Get all forum categories."""
    try:
        valorant_service = current_app.valorant
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('get_forum_categories', {})
        
        print(f"[FORUM] Forwarded get_forum_categories request to Django")
        
    except Exception as e:
        print(f"[ERROR] Failed to get forum categories: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to get forum categories: {str(e)}'})


@on("get_forum_threads")
async def handle_get_forum_threads(payload: dict, client_id: int, ws, mgr):
    """Get threads in a category."""
    category_slug = payload.get('category_slug')
    sort_by = payload.get('sort_by', 'recent')
    page = payload.get('page', 1)
    per_page = payload.get('per_page', 20)
    
    if not category_slug:
        await mgr.send(ws, 'error', {'message': 'category_slug is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('get_forum_threads', {
            'category_slug': category_slug,
            'sort_by': sort_by,
            'page': page,
            'per_page': per_page
        })
        
        print(f"[FORUM] Forwarded get_forum_threads for category: {category_slug}")
        
    except Exception as e:
        print(f"[ERROR] Failed to get forum threads: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to get forum threads: {str(e)}'})


@on("get_forum_thread")
async def handle_get_forum_thread(payload: dict, client_id: int, ws, mgr):
    """Get a specific thread with replies."""
    thread_id = payload.get('thread_id')
    page = payload.get('page', 1)
    per_page = payload.get('per_page', 20)
    
    if not thread_id:
        await mgr.send(ws, 'error', {'message': 'thread_id is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('get_forum_thread', {
            'thread_id': thread_id,
            'page': page,
            'per_page': per_page
        })
        
        print(f"[FORUM] Forwarded get_forum_thread for thread: {thread_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to get forum thread: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to get forum thread: {str(e)}'})


@on("create_forum_thread")
async def handle_create_forum_thread(payload: dict, client_id: int, ws, mgr):
    """Create a new forum thread."""
    category_slug = payload.get('category_slug')
    title = payload.get('title')
    content = payload.get('content')
    tags = payload.get('tags', [])
    
    if not category_slug or not title or not content:
        await mgr.send(ws, 'error', {'message': 'category_slug, title, and content are required'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id].get('puuid')
        
        if not puuid:
            await mgr.send(ws, 'error', {'message': 'Not authenticated'})
            return
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('create_forum_thread', {
            'author_puuid': puuid,
            'category_slug': category_slug,
            'title': title,
            'content': content,
            'tags': tags
        })
        
        print(f"[FORUM] Forwarded create_forum_thread: {title}")
        
    except Exception as e:
        print(f"[ERROR] Failed to create forum thread: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to create thread: {str(e)}'})


@on("create_forum_reply")
async def handle_create_forum_reply(payload: dict, client_id: int, ws, mgr):
    """Reply to a forum thread."""
    thread_id = payload.get('thread_id')
    content = payload.get('content')
    reply_to = payload.get('reply_to')  # Optional, for nested replies
    
    if not thread_id or not content:
        await mgr.send(ws, 'error', {'message': 'thread_id and content are required'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id].get('puuid')
        
        if not puuid:
            await mgr.send(ws, 'error', {'message': 'Not authenticated'})
            return
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('create_forum_reply', {
            'author_puuid': puuid,
            'thread_id': thread_id,
            'content': content,
            'reply_to': reply_to
        })
        
        print(f"[FORUM] Forwarded create_forum_reply for thread: {thread_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to create forum reply: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to create reply: {str(e)}'})


@on("edit_forum_thread")
async def handle_edit_forum_thread(payload: dict, client_id: int, ws, mgr):
    """Edit an existing forum thread."""
    thread_id = payload.get('thread_id')
    title = payload.get('title')
    content = payload.get('content')
    
    if not thread_id:
        await mgr.send(ws, 'error', {'message': 'thread_id is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id].get('puuid')
        
        if not puuid:
            await mgr.send(ws, 'error', {'message': 'Not authenticated'})
            return
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('edit_forum_thread', {
            'author_puuid': puuid,
            'thread_id': thread_id,
            'title': title,
            'content': content
        })
        
        print(f"[FORUM] Forwarded edit_forum_thread: {thread_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to edit forum thread: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to edit thread: {str(e)}'})


@on("delete_forum_thread")
async def handle_delete_forum_thread(payload: dict, client_id: int, ws, mgr):
    """Delete a forum thread."""
    thread_id = payload.get('thread_id')
    
    if not thread_id:
        await mgr.send(ws, 'error', {'message': 'thread_id is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id].get('puuid')
        
        if not puuid:
            await mgr.send(ws, 'error', {'message': 'Not authenticated'})
            return
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('delete_forum_thread', {
            'author_puuid': puuid,
            'thread_id': thread_id
        })
        
        print(f"[FORUM] Forwarded delete_forum_thread: {thread_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to delete forum thread: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to delete thread: {str(e)}'})


@on("like_forum_content")
async def handle_like_forum_content(payload: dict, client_id: int, ws, mgr):
    """Like/unlike a thread or reply."""
    content_type = payload.get('content_type')  # 'thread' or 'reply'
    content_id = payload.get('content_id')
    
    if not content_type or not content_id:
        await mgr.send(ws, 'error', {'message': 'content_type and content_id are required'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id].get('puuid')
        
        if not puuid:
            await mgr.send(ws, 'error', {'message': 'Not authenticated'})
            return
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('like_forum_content', {
            'user_puuid': puuid,
            'content_type': content_type,
            'content_id': content_id
        })
        
        print(f"[FORUM] Forwarded like_forum_content: {content_type}/{content_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to like forum content: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to like content: {str(e)}'})


@on("search_forums")
async def handle_search_forums(payload: dict, client_id: int, ws, mgr):
    """Search forum threads and replies."""
    query = payload.get('query')
    category_slug = payload.get('category_slug')
    
    if not query:
        await mgr.send(ws, 'error', {'message': 'query is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        
        # Forward to Django
        await valorant_service.api.pugsocket.send_message('search_forums', {
            'query': query,
            'category_slug': category_slug
        })
        
        print(f"[FORUM] Forwarded search_forums: {query}")
        
    except Exception as e:
        print(f"[ERROR] Failed to search forums: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to search forums: {str(e)}'})
