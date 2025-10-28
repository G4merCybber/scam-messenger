from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import json
import os
import hashlib
import secrets
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Создаем папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/avatars', exist_ok=True)
os.makedirs('static/group_avatars', exist_ok=True)

USERS_FILE = 'users.json'
MESSAGES_FILE = 'messages.json'
POSTS_FILE = 'posts.json'
GROUPS_FILE = 'groups.json'
CHANNELS_FILE = 'channels.json'

def load_users():
    try:
        if os.path.exists(USERS_FILE) and os.path.getsize(USERS_FILE) > 0:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except:
        pass

def load_messages():
    try:
        if os.path.exists(MESSAGES_FILE) and os.path.getsize(MESSAGES_FILE) > 0:
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_messages(messages):
    try:
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=4, ensure_ascii=False)
    except:
        pass

def load_posts():
    try:
        if os.path.exists(POSTS_FILE) and os.path.getsize(POSTS_FILE) > 0:
            with open(POSTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except:
        return []

def save_posts(posts):
    try:
        with open(POSTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4, ensure_ascii=False)
    except:
        pass

def load_groups():
    try:
        if os.path.exists(GROUPS_FILE) and os.path.getsize(GROUPS_FILE) > 0:
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_groups(groups):
    try:
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, indent=4, ensure_ascii=False)
    except:
        pass

def load_channels():
    try:
        if os.path.exists(CHANNELS_FILE) and os.path.getsize(CHANNELS_FILE) > 0:
            with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_channels(channels):
    try:
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(channels, f, indent=4, ensure_ascii=False)
    except:
        pass

def compress_image(image_data, max_size=10 * 1024 * 1024):
    try:
        if len(image_data) > max_size:
            print(f"Image too large: {len(image_data)} bytes")
            return image_data[:max_size]
        return image_data
    except Exception as e:
        print(f"Compression error: {e}")
        return image_data

def save_avatar(username, avatar_data, folder='avatars'):
    try:
        if avatar_data.startswith('data:image'):
            header, avatar_data = avatar_data.split(',', 1)
            
        avatar_bytes = base64.b64decode(avatar_data)
        avatar_bytes = compress_image(avatar_bytes, 5 * 1024 * 1024)
        
        avatar_path = f'static/{folder}/{username}.jpg'
        
        with open(avatar_path, 'wb') as f:
            f.write(avatar_bytes)
        
        return f'{folder}/{username}.jpg'
    except Exception as e:
        print(f"Error saving avatar: {e}")
        return None

def get_avatar_url(username, folder='avatars'):
    avatar_path = f'static/{folder}/{username}.jpg'
    if os.path.exists(avatar_path):
        return f'{folder}/{username}.jpg'
    return f'{folder}/default.jpg'

def save_uploaded_file(file, username):
    try:
        if file and file.filename:
            filename = secure_filename(f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return f'uploads/{filename}'
    except Exception as e:
        print(f"Error saving file: {e}")
    return None

def initialize_files():
    files = [
        (USERS_FILE, {}),
        (MESSAGES_FILE, {}),
        (POSTS_FILE, []),
        (GROUPS_FILE, {}),
        (CHANNELS_FILE, {})
    ]
    
    for filename, default in files:
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=4)

initialize_files()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle_theme', methods=['POST'])
def toggle_theme():
    data = request.get_json()
    session['dark_theme'] = data.get('dark_theme', False)
    return jsonify({'status': 'success'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        avatar_data = request.form.get('avatar', '')
        
        users = load_users()
        
        if username in users:
            return "Username already exists!"
        
        avatar_url = 'avatars/default.jpg'
        if avatar_data:
            saved_avatar = save_avatar(username, avatar_data)
            if saved_avatar:
                avatar_url = saved_avatar
        
        users[username] = {
            'name': name,
            'password': password,
            'avatar': avatar_url,
            'bio': '',
            'created_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
        
        save_users(users)
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['name'] = users[username]['name']
            session['avatar'] = users[username].get('avatar', 'avatars/default.jpg')
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users = load_users()
    posts = load_posts()
    groups = load_groups()
    channels = load_channels()
    current_user = session['username']
    
    # Фильтруем группы и каналы где пользователь участник
    user_groups = {}
    user_channels = {}
    
    for group_id, group in groups.items():
        if current_user in group.get('members', []):
            user_groups[group_id] = group
    
    for channel_id, channel in channels.items():
        if current_user in channel.get('subscribers', []):
            user_channels[channel_id] = channel
    
    other_users = {k: v for k, v in users.items() if k != current_user}
    
    return render_template('dashboard.html', 
                         name=session['name'],
                         avatar=session.get('avatar', 'avatars/default.jpg'),
                         users=other_users,
                         posts=posts,
                         groups=user_groups,
                         channels=user_channels)

@app.route('/search', methods=['POST'])
def search_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    search_term = request.form['search_term'].lower()
    users = load_users()
    current_user = session['username']
    
    filtered_users = {}
    for username, user_data in users.items():
        if (username != current_user and 
            (search_term in username.lower() or 
             search_term in user_data['name'].lower())):
            filtered_users[username] = user_data
    
    return render_template('dashboard.html',
                         name=session['name'],
                         avatar=session.get('avatar', 'avatars/default.jpg'),
                         users=filtered_users,
                         posts=load_posts(),
                         groups=load_groups(),
                         channels=load_channels(),
                         search_term=search_term)

@app.route('/discover')
def discover():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    groups = load_groups()
    channels = load_channels()
    current_user = session['username']
    
    # Публичные группы и каналы где пользователь не участник
    public_groups = {}
    public_channels = {}
    
    for group_id, group in groups.items():
        if group.get('is_public', True) and current_user not in group.get('members', []):
            public_groups[group_id] = group
    
    for channel_id, channel in channels.items():
        if channel.get('is_public', True) and current_user not in channel.get('subscribers', []):
            public_channels[channel_id] = channel
    
    return render_template('discover.html',
                         public_groups=public_groups,
                         public_channels=public_channels)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users = load_users()
    username = session['username']
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        bio = request.form.get('bio', '')
        avatar_data = request.form.get('avatar', '')
        
        if name:
            users[username]['name'] = name
            session['name'] = name
        
        if bio:
            users[username]['bio'] = bio
        
        if avatar_data:
            saved_avatar = save_avatar(username, avatar_data)
            if saved_avatar:
                users[username]['avatar'] = saved_avatar
                session['avatar'] = saved_avatar
        
        save_users(users)
        return redirect(url_for('profile'))
    
    user_data = users.get(username, {})
    return render_template('profile.html',
                         name=user_data.get('name', ''),
                         bio=user_data.get('bio', ''),
                         avatar=user_data.get('avatar', 'avatars/default.jpg'),
                         created_at=user_data.get('created_at', ''))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    text = request.form.get('text', '')
    image_file = request.files.get('image')
    
    if not text and not image_file:
        return jsonify({'status': 'error', 'message': 'Empty post'})
    
    posts = load_posts()
    
    post = {
        'id': len(posts) + 1,
        'author': session['username'],
        'author_name': session['name'],
        'author_avatar': session.get('avatar', 'avatars/default.jpg'),
        'text': text,
        'image': None,
        'created_at': datetime.now().isoformat(),
        'likes': [],
        'comments': []
    }
    
    if image_file:
        image_url = save_uploaded_file(image_file, session['username'])
        if image_url:
            post['image'] = image_url
    
    posts.insert(0, post)
    save_posts(posts)
    
    return jsonify({'status': 'success'})

@app.route('/like_post', methods=['POST'])
def like_post():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    post_id = int(request.form.get('post_id'))
    username = session['username']
    
    posts = load_posts()
    
    for post in posts:
        if post['id'] == post_id:
            if username in post['likes']:
                post['likes'].remove(username)
            else:
                post['likes'].append(username)
            break
    
    save_posts(posts)
    return jsonify({'status': 'success'})

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    post_id = int(request.form.get('post_id'))
    text = request.form.get('text', '')
    
    if not text:
        return jsonify({'status': 'error'})
    
    posts = load_posts()
    
    for post in posts:
        if post['id'] == post_id:
            comment = {
                'author': session['username'],
                'author_name': session['name'],
                'author_avatar': session.get('avatar', 'avatars/default.jpg'),
                'text': text,
                'created_at': datetime.now().isoformat()
            }
            post['comments'].append(comment)
            break
    
    save_posts(posts)
    return jsonify({'status': 'success'})

@app.route('/create_group', methods=['POST'])
def create_group():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    avatar_data = request.form.get('avatar', '')
    members_input = request.form.get('members', '')
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Group name required'})
    
    groups = load_groups()
    users = load_users()
    group_id = f"group_{len(groups) + 1}"
    
    # Обрабатываем список участников
    valid_members = []
    if members_input:
        members_list = [m.strip() for m in members_input.split(',')]
        for member in members_list:
            if member in users and member != session['username']:
                valid_members.append(member)
    
    avatar_url = 'group_avatars/default.jpg'
    if avatar_data:
        saved_avatar = save_avatar(group_id, avatar_data, 'group_avatars')
        if saved_avatar:
            avatar_url = saved_avatar
    
    # Создатель автоматически становится участником
    all_members = [session['username']] + valid_members
    
    groups[group_id] = {
        'id': group_id,
        'name': name,
        'description': description,
        'avatar': avatar_url,
        'creator': session['username'],
        'members': list(set(all_members)),
        'created_at': datetime.now().isoformat(),
        'is_public': True
    }
    
    save_groups(groups)
    return jsonify({'status': 'success', 'group_id': group_id})

@app.route('/create_channel', methods=['POST'])
def create_channel():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    avatar_data = request.form.get('avatar', '')
    is_public = request.form.get('is_public', 'true') == 'true'
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Channel name required'})
    
    channels = load_channels()
    channel_id = f"channel_{len(channels) + 1}"
    
    avatar_url = 'group_avatars/default.jpg'
    if avatar_data:
        saved_avatar = save_avatar(channel_id, avatar_data, 'group_avatars')
        if saved_avatar:
            avatar_url = saved_avatar
    
    channels[channel_id] = {
        'id': channel_id,
        'name': name,
        'description': description,
        'avatar': avatar_url,
        'creator': session['username'],
        'subscribers': [session['username']],
        'created_at': datetime.now().isoformat(),
        'is_public': is_public,
        'messages': []
    }
    
    save_channels(channels)
    return jsonify({'status': 'success', 'channel_id': channel_id})

@app.route('/invite_to_group', methods=['POST'])
def invite_to_group():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    group_id = request.form.get('group_id')
    invite_username = request.form.get('username')
    
    groups = load_groups()
    group = groups.get(group_id)
    users = load_users()
    
    if not group or session['username'] != group['creator']:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    if invite_username not in users:
        return jsonify({'status': 'error', 'message': 'User not found'})
    
    if invite_username in group['members']:
        return jsonify({'status': 'error', 'message': 'User already in group'})
    
    group['members'].append(invite_username)
    save_groups(groups)
    
    return jsonify({'status': 'success', 'message': f'User {invite_username} invited to group'})

@app.route('/invite_to_channel', methods=['POST'])
def invite_to_channel():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    channel_id = request.form.get('channel_id')
    invite_username = request.form.get('username')
    
    channels = load_channels()
    channel = channels.get(channel_id)
    users = load_users()
    
    if not channel or session['username'] != channel['creator']:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    if invite_username not in users:
        return jsonify({'status': 'error', 'message': 'User not found'})
    
    if invite_username in channel['subscribers']:
        return jsonify({'status': 'error', 'message': 'User already subscribed'})
    
    channel['subscribers'].append(invite_username)
    save_channels(channels)
    
    return jsonify({'status': 'success', 'message': f'User {invite_username} invited to channel'})

@app.route('/group/<group_id>')
def group_chat(group_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    groups = load_groups()
    group = groups.get(group_id)
    
    if not group or session['username'] not in group.get('members', []):
        return "Group not found or access denied"
    
    messages = load_messages()
    conversation_key = f"group_{group_id}"
    conversation = messages.get(conversation_key, [])
    
    return render_template('group_chat.html',
                         group=group,
                         messages=conversation)

@app.route('/channel/<channel_id>')
def channel_view(channel_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    channels = load_channels()
    channel = channels.get(channel_id)
    
    if not channel or session['username'] not in channel.get('subscribers', []):
        return "Channel not found or access denied"
    
    return render_template('channel.html', channel=channel)

@app.route('/send_group_message', methods=['POST'])
def send_group_message():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    group_id = request.form['group_id']
    message_text = request.form['message']
    image_file = request.files.get('image')
    
    if not message_text.strip() and not image_file:
        return jsonify({'status': 'error', 'message': 'Empty message'})
    
    groups = load_groups()
    group = groups.get(group_id)
    
    if not group or session['username'] not in group.get('members', []):
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    messages = load_messages()
    conversation_key = f"group_{group_id}"
    
    if conversation_key not in messages:
        messages[conversation_key] = []
    
    message = {
        'sender': session['username'],
        'group_id': group_id,
        'text': message_text,
        'image': None,
        'timestamp': datetime.now().isoformat(),
        'sender_name': session['name'],
        'sender_avatar': session.get('avatar', 'avatars/default.jpg')
    }
    
    if image_file:
        image_url = save_uploaded_file(image_file, session['username'])
        if image_url:
            message['image'] = image_url
    
    messages[conversation_key].append(message)
    save_messages(messages)
    
    return jsonify({'status': 'success'})

@app.route('/send_channel_message', methods=['POST'])
def send_channel_message():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    channel_id = request.form['channel_id']
    message_text = request.form['message']
    image_file = request.files.get('image')
    
    if not message_text.strip() and not image_file:
        return jsonify({'status': 'error', 'message': 'Empty message'})
    
    channels = load_channels()
    channel = channels.get(channel_id)
    
    if not channel or session['username'] != channel.get('creator'):
        return jsonify({'status': 'error', 'message': 'Only creator can post'})
    
    message = {
        'sender': session['username'],
        'text': message_text,
        'image': None,
        'timestamp': datetime.now().isoformat(),
        'sender_name': session['name'],
        'sender_avatar': session.get('avatar', 'avatars/default.jpg')
    }
    
    if image_file:
        image_url = save_uploaded_file(image_file, session['username'])
        if image_url:
            message['image'] = image_url
    
    channel['messages'].insert(0, message)
    save_channels(channels)
    
    return jsonify({'status': 'success'})

@app.route('/join_group', methods=['POST'])
def join_group():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    group_id = request.form.get('group_id')
    groups = load_groups()
    group = groups.get(group_id)
    
    if not group:
        return jsonify({'status': 'error', 'message': 'Group not found'})
    
    if session['username'] not in group['members']:
        group['members'].append(session['username'])
        save_groups(groups)
    
    return jsonify({'status': 'success'})

@app.route('/subscribe_channel', methods=['POST'])
def subscribe_channel():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    channel_id = request.form.get('channel_id')
    channels = load_channels()
    channel = channels.get(channel_id)
    
    if not channel:
        return jsonify({'status': 'error', 'message': 'Channel not found'})
    
    if session['username'] not in channel['subscribers']:
        channel['subscribers'].append(session['username'])
        save_channels(channels)
    
    return jsonify({'status': 'success'})

@app.route('/get_group_messages/<group_id>')
def get_group_messages(group_id):
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    messages = load_messages()
    conversation_key = f"group_{group_id}"
    conversation = messages.get(conversation_key, [])
    
    return jsonify({'messages': conversation})

@app.route('/chat/<receiver>')
def chat(receiver):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    sender = session['username']
    messages = load_messages()
    
    conversation_key = '-'.join(sorted([sender, receiver]))
    conversation = messages.get(conversation_key, [])
    
    return render_template('chat.html',
                         receiver=receiver,
                         messages=conversation,
                         sender=sender)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    sender = session['username']
    receiver = request.form['receiver']
    message_text = request.form['message']
    image_file = request.files.get('image')
    
    if not message_text.strip() and not image_file:
        return jsonify({'status': 'error', 'message': 'Empty message'})
    
    messages = load_messages()
    conversation_key = '-'.join(sorted([sender, receiver]))
    
    if conversation_key not in messages:
        messages[conversation_key] = []
    
    message = {
        'sender': sender,
        'receiver': receiver,
        'text': message_text,
        'image': None,
        'timestamp': datetime.now().isoformat()
    }
    
    if image_file:
        image_url = save_uploaded_file(image_file, sender)
        if image_url:
            message['image'] = image_url
    
    messages[conversation_key].append(message)
    save_messages(messages)
    
    return jsonify({'status': 'success'})

@app.route('/get_messages/<receiver>')
def get_messages(receiver):
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    sender = session['username']
    messages = load_messages()
    conversation_key = '-'.join(sorted([sender, receiver]))
    conversation = messages.get(conversation_key, [])
    
    return jsonify({'messages': conversation})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)