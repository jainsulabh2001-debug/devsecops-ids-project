import uuid
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gallery.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('gallery'))
    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------- GALLERY ----------------
@app.route('/', methods=['GET', 'POST'])
@login_required
def gallery():
    if request.method == 'POST':
        file = request.files.get('image')

        if file and file.filename:
            # Get file extension
            ext = os.path.splitext(file.filename)[1]

            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}{ext}"

            # Secure the filename
            unique_filename = secure_filename(unique_filename)

            # Save file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Save to database
            img = Image(filename=unique_filename, user_id=current_user.id)
            db.session.add(img)
            db.session.commit()

    images = Image.query.filter_by(user_id=current_user.id).all()
    return render_template('gallery.html', images=images)


# ---------------- DELETE IMAGE ----------------
@app.route('/delete/<int:image_id>')
@login_required
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)

    # Ensure user owns the image
    if image.user_id != current_user.id:
        return redirect(url_for('gallery'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)

    # Safely delete file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete database record
    db.session.delete(image)
    db.session.commit()

    return redirect(url_for('gallery'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
