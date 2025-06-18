# Future Social API Documentation

Generated: 2025-06-17T20:14:53.960968

## User Service

### /register

#### POST

- **Function**: `register`
- **File**: `/home/ubuntu/fs_project/src/user_service/app.py`


### /login

#### POST

- **Function**: `login`
- **File**: `/home/ubuntu/fs_project/src/user_service/app.py`


## Post Service

### /posts

#### POST

- **Function**: `create_post`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`


### /posts/<int:post_id>

#### GET

- **Function**: `get_post`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`

#### PUT

- **Function**: `update_post`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`

#### DELETE

- **Function**: `delete_post`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`


### /users/<int:user_id>/posts

#### GET

- **Function**: `get_posts_by_user`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`


### /feed

#### GET

- **Function**: `get_feed`
- **File**: `/home/ubuntu/fs_project/src/post_service/app.py`


## Messaging Service

### /conversations

#### POST

- **Function**: `create_or_get_conversation`
- **File**: `/home/ubuntu/fs_project/src/messaging_service/app.py`


### /conversations/<int:conversation_id>/messages

#### POST

- **Function**: `send_message`
- **File**: `/home/ubuntu/fs_project/src/messaging_service/app.py`

#### GET

- **Function**: `get_messages`
- **File**: `/home/ubuntu/fs_project/src/messaging_service/app.py`


### /users/<int:user_id>/conversations

#### GET

- **Function**: `get_user_conversations_list`
- **File**: `/home/ubuntu/fs_project/src/messaging_service/app.py`


## Group Service

### /groups

#### POST

- **Function**: `create_group`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`

#### GET

- **Function**: `get_all_groups`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


### /groups/<int:group_id>

#### GET

- **Function**: `get_group`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


### /groups/<int:group_id>/join

#### POST

- **Function**: `join_group`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


### /groups/<int:group_id>/leave

#### POST

- **Function**: `leave_group`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


### /groups/<int:group_id>/members

#### GET

- **Function**: `get_group_members_list`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


### /users/<int:user_id>/groups

#### GET

- **Function**: `get_user_groups_list`
- **File**: `/home/ubuntu/fs_project/src/group_service/app.py`


## Ai Sandbox Service

### /ai_sandbox/modules

#### POST

- **Function**: `create_learning_module`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`

#### GET

- **Function**: `get_all_learning_modules`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /ai_sandbox/modules/<int:module_id>

#### GET

- **Function**: `get_learning_module`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /ai_sandbox/users/<int:user_id>/progress/<int:module_id>

#### POST

- **Function**: `update_user_progress`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`

#### PUT

- **Function**: `update_user_progress`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`

#### GET

- **Function**: `get_user_progress_for_module`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /ai_sandbox/users/<int:user_id>/progress

#### GET

- **Function**: `get_all_user_progress`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /ai_sandbox/users/<int:user_id>/preferences

#### GET

- **Function**: `get_user_ai_preferences`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`

#### PUT

- **Function**: `update_user_ai_preferences`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /ai_sandbox/users/<int:user_id>/recommendations

#### GET

- **Function**: `get_learning_recommendations`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


### /api/ai_sandbox/status

#### GET

- **Function**: `sandbox_status`
- **File**: `/home/ubuntu/fs_project/src/ai_sandbox_service/app.py`


