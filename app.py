import os
import logging
import random

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = random.randbytes(16)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'edf', 'zip', 'csv', 'fasta', 'hdf5', 'gct', 'tsv', 'h5ad', 'feather', 'parquet', 'vcf', 'bam', 'sam', 'crm', 'tiff', 'xlsx', 'bed'}

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage for posts, comments, likes, comment likes, and users (for simplicity)
posts = []
comments = []
likes = []
comment_likes = []
users = {}
downloads = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def file_info(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_size = os.path.getsize(filepath)
    file_extension = filename.rsplit('.', 1)[1].lower()
    download_count = downloads.get(filename, 0)
    return file_size, file_extension, download_count

class User(UserMixin):
    def __init__(self, id, name, job_title, email, department, profile_picture, bio='', research_interests='', website=''):
        self.id = id
        self.name = name
        self.job_title = job_title
        self.email = email
        self.department = department
        self.profile_picture = profile_picture
        self.bio = bio
        self.research_interests = research_interests
        self.website = website
        self.followers = []
        self.following = []

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        job_title = request.form['job_title']
        email = request.form['email']
        department = request.form['department']
        bio = request.form['bio']
        research_interests = request.form['research_interests']
        website = request.form['website']
        profile_picture = request.files.get('profile_picture')
        user_id = str(len(users) + 1)
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        new_user = User(user_id, name, job_title, email, department, filename, bio, research_interests, website)
        users[user_id] = new_user
        flash('Account created successfully. Please log in.', 'success')
        with open('users.tsv', 'a') as f:
            f.write(f"{name}\t{job_title}\t{email}\t{department}\t{filename}\t{bio}\t{research_interests}\t{website}\n")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Log in request")
    if request.method == 'POST':
        email = request.form['email']
        for user_id, user in users.items():
            if user.email == email:
                login_user(user)
                return redirect(url_for('index'))
        flash('Sorry, we cannot find an account registered with that email', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        keywords = request.form['keywords'].split()
        dataset_type = request.form['dataset_type']
        collection_period = request.form['collection_period']
        organism = request.form['organism']
        genes = request.form['genes']
        tissue_celltype = request.form['tissue_celltype']
        condition = request.form['condition']
        technique = request.form['technique']
        instrument_platform = request.form['instrument_platform']
        software = request.form['software']
        usage_restrictions = request.form['usage_restrictions']
        related_datasets = request.form['related_datasets']
        link = request.form['link']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        post = {
            'title': title,
            'description': description,
            'keywords': keywords,
            'dataset_type': dataset_type,
            'collection_period': collection_period,
            'organism': organism,
            'genes': genes,
            'tissue_celltype': tissue_celltype,
            'condition': condition,
            'technique': technique,
            'instrument_platform': instrument_platform,
            'software': software,
            'usage_restrictions': usage_restrictions,
            'related_datasets': related_datasets,
            'link': link,
            'filename': filename,
            'user': current_user.name,
            'id': len(posts) + 1,
            'likes': 0
        }
        posts.append(post)
        return redirect(url_for('posts_view'))
    return render_template('results.html')

@app.route('/posts', methods=['GET', 'POST'])
@login_required
def posts_view():
    if request.method == 'POST':
        if 'comment' in request.form:
            post_id = int(request.form['post_id'])
            comment_text = request.form['comment']
            comment = {'post_id': post_id, 'user': current_user.name, 'text': comment_text, 'id': len(comments) + 1}
            comments.append(comment)
        elif 'like' in request.form:
            post_id = int(request.form['post_id'])
            if not any(like['post_id'] == post_id and like['user'] == current_user.name for like in likes):
                likes.append({'post_id': post_id, 'user': current_user.name})
                for post in posts:
                    if post['id'] == post_id:
                        post['likes'] += 1
                        break
        elif 'like_comment' in request.form:
            comment_id = int(request.form['comment_id'])
            if not any(like['comment_id'] == comment_id and like['user'] == current_user.name for like in comment_likes):
                comment_likes.append({'comment_id': comment_id, 'user': current_user.name})
    return render_template('posts.html', posts=posts, comments=comments, likes=likes, comment_likes=comment_likes, file_info=file_info)

@app.route('/profile')
@login_required
def profile():
    user_posts = [post for post in posts if post['user'] == current_user.name]
    liked_posts = [post for post in posts if any(like['post_id'] == post['id'] and like['user'] == current_user.name for like in likes)]
    return render_template('profile.html', user=current_user, posts=user_posts, liked_posts=liked_posts, users=users)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.job_title = request.form['job_title']
        current_user.email = request.form['email']
        current_user.department = request.form['department']
        current_user.bio = request.form['bio']
        current_user.research_interests = request.form['research_interests']
        current_user.website = request.form['website']
        profile_picture = request.files.get('profile_picture')
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_picture = filename
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=current_user)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    query = ''
    results = []
    user_results = []
    sort = 'date'
    start_date = ''
    end_date = ''
    file_type = ''
    department = ''
    user = ''

    if request.method == 'POST':
        query = request.form['query'].lower()  # Convert to lowercase for case-insensitive search
        sort = request.form['sort']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        file_type = request.form['file_type']
        department = request.form['department'].lower()
        user = request.form['user'].lower()

        results = [post for post in posts if query in post['title'].lower() or query in post['description'].lower() or query in ' '.join(post['keywords']).lower() or any(query in comment['text'].lower() and comment['post_id'] == post['id'] for comment in comments) or (post['filename'] and query == file_info(post['filename'])[1].lower())]
        if start_date:
            results = [post for post in results if post.get('date') and post['date'] >= start_date]
        if end_date:
            results = [post for post in results if post.get('date') and post['date'] <= end_date]
        if file_type:
            results = [post for post in results if post.get('filename') and post['filename'].endswith(file_type)]
        if department:
            results = [post for post in results if post.get('user') and users[find_user_id(post['user'])].department.lower() == department]
        if user:
            results = [post for post in results if post.get('user') and user in post['user'].lower()]

        user_results = [user for user in users.values() if query in user.name.lower() or query in user.department.lower()]

        if sort == 'popularity':
            results.sort(key=lambda x: x['likes'], reverse=True)
        elif sort == 'comments':
            results.sort(key=lambda x: len([comment for comment in comments if comment['post_id'] == x['id']]), reverse=True)
        else:
            results.sort(key=lambda x: x.get('date', ''), reverse=True)

    return render_template('search.html', query=query, results=results, user_results=user_results, sort=sort, start_date=start_date, end_date=end_date, file_type=file_type, department=department, user=user, file_info=file_info)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    downloads[filename] = downloads.get(filename, 0) + 1
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def view_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        if request.method == 'POST':
            if 'comment' in request.form:
                comment_text = request.form['comment']
                comment = {'post_id': post_id, 'user': current_user.name, 'text': comment_text, 'id': len(comments) + 1}
                comments.append(comment)
            elif 'like_comment' in request.form:
                comment_id = int(request.form['comment_id'])
                if not any(like['comment_id'] == comment_id and like['user'] == current_user.name for like in comment_likes):
                    comment_likes.append({'comment_id': comment_id, 'user': current_user.name})
        post_comments = [comment for comment in comments if comment['post_id'] == post_id]
        post_likes = [like for like in likes if like['post_id'] == post_id]
        return render_template('single_post.html', post=post, comments=post_comments, likes=post_likes, comment_likes=comment_likes, file_info=file_info)
    else:
        flash('Post not found.', 'error')
        return redirect(url_for('posts_view'))

@app.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    user = users.get(str(user_id))
    if user:
        user_posts = [post for post in posts if post['user'] == user.name]
        liked_posts = [post for post in posts if any(like['post_id'] == post['id'] and like['user'] == user.name for like in likes)]
        return render_template('view_profile.html', user=user, posts=user_posts, liked_posts=liked_posts, users=users)
    else:
        flash('User not found.', 'error')
        return redirect(url_for('index'))

@app.route('/follow/<int:user_id>')
@login_required
def follow_user(user_id):
    user_to_follow = users.get(str(user_id))
    if user_to_follow and current_user.id != str(user_id):
        if str(user_id) not in current_user.following:
            current_user.following.append(str(user_id))
            user_to_follow.followers.append(current_user.id)
        flash(f'You are now following {user_to_follow.name}', 'success')
    else:
        flash('User not found or you cannot follow yourself', 'error')
    return redirect(url_for('view_user_profile', user_id=user_id))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow_user(user_id):
    user_to_unfollow = users.get(str(user_id))
    if user_to_unfollow and current_user.id != str(user_id):
        if str(user_id) in current_user.following:
            current_user.following.remove(str(user_id))
            user_to_unfollow.followers.remove(current_user.id)
        flash(f'You have unfollowed {user_to_unfollow.name}', 'success')
    else:
        flash('User not found or you cannot unfollow yourself', 'error')
    return redirect(url_for('view_user_profile', user_id=user_id))

@app.context_processor
def utility_processor():
    def find_user_id(username):
        for user_id, user in users.items():
            if user.name == username:
                return user_id
        return None
    return dict(find_user_id=find_user_id)

def make_files():
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    if not os.path.exists('users.tsv'):
        with open('users.tsv', 'w') as f:
            f.write('Name\tJob Title\tEmail\tDepartment\tProfile Picture\tBio\tResearch Interests\tWebsite\n')

    if not os.path.exists('posts.tsv'):
        with open('posts.tsv', 'w') as f:
            f.write('Title\tDescription\tKeywords\tDataset Type\tCollection Period\tOrganism\tGenes\tTissue/Cell Type\tCondition\tTechnique\tInstrument Platform\tSoftware\tUsage Restrictions\tRelated Datasets\tLink\tFilename\tUser\tPost ID\tLikes\n')

    with open('users.tsv', 'r') as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            name, job_title, email, department, profile_picture, bio, research_interests, website = line.split('\t')
            user = User(str(i), name, job_title, email, department, profile_picture, bio, research_interests, website)
            users[str(i)] = user

    with open('posts.tsv', 'r') as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            title, description, keywords, dataset_type, collection_period, organism, genes, tissue_celltype, condition, technique, instrument_platform, software, usage_restrictions, related_datasets, link, filename, user, post_id, post_likes = line.split('\t')
            post = {
                'title': title,
                'description': description,
                'keywords': keywords.split(),
                'dataset_type': dataset_type,
                'collection_period': collection_period,
                'organism': organism,
                'genes': genes,
                'tissue_celltype': tissue_celltype,
                'condition': condition,
                'technique': technique,
                'instrument_platform': instrument_platform,
                'software': software,
                'usage_restrictions': usage_restrictions,
                'related_datasets': related_datasets,
                'link': link,
                'filename': filename,
                'user': user,
                'id': int(post_id),
                'likes': int(post_likes)
            }
            posts.append(post)

if __name__ == '__main__':
    make_files()
    app.run(debug=True, port=5001)
