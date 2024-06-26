from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage for posts and users (for simplicity)
posts = []
users = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        post = {'title': title, 'description': description, 'filename': filename, 'user': current_user.name}
        posts.append(post)
        return redirect(url_for('posts_view'))
    return render_template('upload.html')

@app.route('/posts')
@login_required
def posts_view():
    return render_template('posts.html', posts=posts)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True, port=5001)





#In PowerShell, run the following: 
# cd "C:\Users\ngoble\Documents\Python Scripts\BroadHackathon"
# .\.venv\Scripts\Activate.ps1
# python app.py
#Navigate to http://127.0.0.1:5001 to see your website in action.

#OR, in cmd run the following: # Navigate to the project directory
# cd "C:\Users\ngoble\Documents\Python Scripts\BroadHackathon"

# Activate the virtual environment
# .\.venv\Scripts\activate

# Run the Flask application
# python app.py

#Go to http://127.0.0.1:5001 in browser