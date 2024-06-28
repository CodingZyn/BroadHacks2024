import os

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'edf', 'zip', 'csv', 'fasta', 'hdf5', 'gct', 'tsv', 'h5ad', 'feather', 'parquet', 'vcf', 'bam', 'sam', 'crm', 'tiff', 'xlsx', 'bed'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage for posts, comments, likes, and users (for simplicity)
posts = []
comments = []
likes = []
users = {}
downloads = {}

if not os.path.exists('posts.tsv'):
    with open('posts.tsv', 'w') as f:
        f.write('Title\tDescription\tKeywords\tDataset Type\tCollection Period\tOrganism\tGenes\tTissue/Cell Type\tCondition\tTechnique\tInstrument Platform\tSoftware\tUsage Restrictions\tRelated Datasets\tFilename\tUser\tPost ID\tLikes\n')

with open('posts.tsv', 'r') as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        title, description, keywords, dataset_type, collection_period, organism, genes, tissue_celltype, condition, technique, instrument_platform, software, usage_restrictions, related_datasets, filename, user, post_id, post_likes = line.strip().split('\t')
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
            'filename': filename,
            'user': user,
            'id': int(post_id),
            'likes': int(post_likes)
        }
        posts.append(post)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def file_info(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_size = os.path.getsize(filepath)
    file_extension = filename.rsplit('.', 1)[1].lower()
    download_count = downloads.get(filename, 0)
    return file_size, file_extension, download_count

class User(UserMixin):
    def __init__(self, id, name, job_title, email, department, profile_picture):
        self.id = id
        self.name = name
        self.job_title = job_title
        self.email = email
        self.department = department
        self.profile_picture = profile_picture

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
        profile_picture = request.files.get('profile_picture')
        user_id = str(len(users) + 1)
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        new_user = User(user_id, name, job_title, email, department, filename)
        users[user_id] = new_user
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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

# @app.route('/upload', methods=['GET', 'POST'])
# @login_required
# def upload():
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         hashtags = request.form['hashtags'].split()
#         file = request.files['file']
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         else:
#             filename = None
#         post = {'title': title, 'description': description, 'hashtags': hashtags, 'filename': filename, 'user': current_user.name, 'id': len(posts) + 1, 'likes': 0}
#         posts.append(post)
#         with open('posts.tsv', 'a') as f:
#             f.write(f"{post['title']}\t{post['description']}\t{' '.join(post['hashtags'])}\t{post['filename']}\t{post['user']}\t{post['id']}\t{post['likes']}\n")
#         return redirect(url_for('posts_view'))
#     return render_template('upload.html')

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
            comment = {'post_id': post_id, 'user': current_user.name, 'text': comment_text}
            comments.append(comment)
        elif 'like' in request.form:
            post_id = int(request.form['post_id'])
            if not any(like['post_id'] == post_id and like['user'] == current_user.name for like in likes):
                likes.append({'post_id': post_id, 'user': current_user.name})
                for post in posts:
                    if post['id'] == post_id:
                        post['likes'] += 1
                        break
    return render_template('posts.html', posts=posts, comments=comments, likes=likes, file_info=file_info)

@app.route('/profile')
@login_required
def profile():
    user_posts = [post for post in posts if post['user'] == current_user.name]
    liked_posts = [post for post in posts if any(like['post_id'] == post['id'] and like['user'] == current_user.name for like in likes)]
    return render_template('profile.html', user=current_user, posts=user_posts, liked_posts=liked_posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.job_title = request.form['job_title']
        current_user.email = request.form['email']
        current_user.department = request.form['department']
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
    if request.method == 'POST':
        query = request.form['query']
        results = [post for post in posts if query in post['title'] or query in post['description'] or query in ' '.join(post['keywords']) or any(query in comment['text'] and comment['post_id'] == post['id'] for comment in comments) or (post['filename'] and query.lower() == file_info(post['filename'])[1])]
        user_results = [user for user in users.values() if query.lower() in user.name.lower() or query.lower() in user.department.lower()]
    return render_template('search.html', query=query, results=results, user_results=user_results, file_info=file_info)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    downloads[filename] = downloads.get(filename, 0) + 1
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        post_comments = [comment for comment in comments if comment['post_id'] == post_id]
        post_likes = [like for like in likes if like['post_id'] == post_id]
        return render_template('single_post.html', post=post, comments=post_comments, likes=post_likes, file_info=file_info)
    else:
        flash('Post not found.', 'error')
        return redirect(url_for('posts_view'))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True, port=5001)