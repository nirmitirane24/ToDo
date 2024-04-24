from flask import Flask, redirect, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from flask_login import UserMixin
import bcrypt
import os

app = Flask(__name__)

# Configure database folder
db_folder = os.path.join(app.instance_path, 'databases')
os.makedirs(db_folder, exist_ok=True)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Function to create a database URI for each user
def get_db_uri(username):
    return f'sqlite:///{os.path.join(db_folder, username.lower() + ".db")}'

db = SQLAlchemy()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def is_active(self):
        # Check if the user is authenticated (logged in)
        return self.is_authenticated
    
class Todos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route("/", methods=['POST', 'GET'])
@login_required
def home():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        
        todo = Todos(title=title, desc=desc, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
    
    all_todos = Todos.query.filter_by(user_id=current_user.id).all()
    
    return render_template('index.html', todos=all_todos)

@app.route('/delete/<int:_id>')
@login_required
def delete(_id):
    todo = Todos.query.get(_id)  # Use get method instead of filter_by to get the Todo by ID
    if todo:
        db.session.delete(todo)
        db.session.commit()
        return redirect('/')
    else:
        return "Todo not found", 404


@app.route('/update/<int:_id>', methods=["POST", "GET"])
@login_required
def update(_id):
    todo = Todos.query.get(_id)  # Use get method instead of filter_by to get the Todo by ID

    if todo:
        if request.method == 'POST':
            title = request.form['title']
            desc = request.form['description']
            
            todo.title = title
            todo.desc = desc
            db.session.commit()
            return redirect('/')
        
        return render_template('update.html', todo=todo)
    else:
        return "Todo not found", 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/index")
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

if __name__ == "__main__":
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri('default')  # Use a default database for user authentication
    with app.app_context():
        db.init_app(app)
        db.create_all()

    app.run(debug=True)
