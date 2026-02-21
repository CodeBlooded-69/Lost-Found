import os
import difflib
import random
import imagehash
from PIL import Image
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'campus_connection_secret_key_final'

# --- CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'campus_connect_v2.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'} 

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    karma = db.Column(db.Integer, default=0) 
    items = db.relationship('Item', backref='author', lazy=True, cascade="all, delete")

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False) # Lost or Found
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    
    # Geolocation
    lat = db.Column(db.String(50), nullable=True) 
    lng = db.Column(db.String(50), nullable=True)
    
    # AI & Security
    image_hash = db.Column(db.String(50), nullable=True)
    pin = db.Column(db.String(10), nullable=True) # Secure Handover PIN
    
    image_file = db.Column(db.String(200), nullable=False, default='default.jpg')
    is_urgent = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False) 
    contact_info = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='item', lazy=True, cascade="all, delete")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    body = db.Column(db.Text, nullable=False) 
    attachment = db.Column(db.String(200), nullable=True) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- HELPER FUNCTIONS ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_match_score(item1, item2):
    """Calculates similarity (0-100) based on Text, Location, and Image"""
    if item1.category != item2.category: return 0 
    
    score = 0
    # Text Match (50%)
    text1 = (item1.name + " " + item1.description).lower()
    text2 = (item2.name + " " + item2.description).lower()
    matcher = difflib.SequenceMatcher(None, text1, text2)
    score += (matcher.ratio() * 100) * 0.5 
    
    # Location Match (20%)
    if item1.location and item2.location:
        loc_matcher = difflib.SequenceMatcher(None, item1.location.lower(), item2.location.lower())
        score += (loc_matcher.ratio() * 100) * 0.2
    
    # AI Image Match (30%)
    if item1.image_hash and item2.image_hash:
        try:
            h1 = imagehash.hex_to_hash(item1.image_hash)
            h2 = imagehash.hex_to_hash(item2.image_hash)
            diff = h1 - h2
            if diff == 0: score += 30
            elif diff <= 10: score += 20
            elif diff <= 20: score += 10
        except: pass

    return round(score)

# Initialize DB
with app.app_context():
    db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

# --- ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password, method='scrypt')
        is_admin_user = (email == "admin@campus.com" or User.query.count() == 0)
        
        new_user = User(email=email, username=username, password=hashed_pw, is_admin=is_admin_user, karma=0)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Account created! Welcome to Campus Connect.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Incorrect email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    category_filter = request.args.get('category')
    query = Item.query.filter_by(is_resolved=False).order_by(Item.is_urgent.desc(), Item.date_posted.desc())
    if category_filter and category_filter != 'All':
        query = query.filter_by(category=category_filter)
    
    items = query.all()
    top_users = User.query.order_by(User.karma.desc()).limit(3).all()
    return render_template('index.html', items=items, current_category=category_filter, top_users=top_users)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q')
    items = []
    if query:
        items = Item.query.filter(
            (Item.name.contains(query) | Item.description.contains(query)) & 
            (Item.is_resolved == False)
        ).all()
    return render_template('index.html', items=items)

# --- NEW REPORT FUNCTION (Combined Location) ---
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        file = request.files.get('file')
        filename = 'default.jpg'
        img_hash = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                with Image.open(filepath) as img:
                    img_hash = str(imagehash.phash(img))
            except: pass

        secret_pin = str(random.randint(1000, 9999))
        
        # COMBINE LOCATION DATA
        # Format: "Library - Near the quiet section"
        area = request.form.get('area')
        specifics = request.form.get('specific_location')
        final_location_text = f"{area} - {specifics}"
        
        new_item = Item(
            type=request.form['type'],
            category=request.form['category'],
            name=request.form['name'],
            description=request.form['description'],
            
            # Save the combined location string
            location=final_location_text,
            
            lat=request.form.get('lat'),
            lng=request.form.get('lng'),
            contact_info=request.form['contact_info'],
            image_file=filename,
            image_hash=img_hash,
            pin=secret_pin,
            is_urgent=('is_urgent' in request.form),
            is_resolved=False,
            author=current_user
        )
        db.session.add(new_item)
        db.session.commit()
        
        flash('Report submitted! AI is scanning for matches...', 'info')
        return redirect(url_for('show_matches', item_id=new_item.id))
        
    return render_template('report.html')

@app.route('/matches/<int:item_id>')
@login_required
def show_matches(item_id):
    target_item = Item.query.get_or_404(item_id)
    search_type = 'Found' if target_item.type == 'Lost' else 'Lost'
    candidates = Item.query.filter_by(type=search_type, is_resolved=False).all()
    matches = []
    for item in candidates:
        confidence = get_match_score(target_item, item)
        if confidence > 30:
            matches.append((item, confidence))
    matches.sort(key=lambda x: x[1], reverse=True)
    return render_template('matches.html', target_item=target_item, matches=matches)

@app.route('/claim', methods=['GET', 'POST'])
@login_required
def claim_item():
    if request.method == 'POST':
        pin_input = request.form.get('pin')
        
        # 1. Find the FOUND item using the PIN
        found_item = Item.query.filter_by(pin=pin_input, is_resolved=False).first()
        
        if found_item:
            # Prevent Finder from claiming their own item
            if found_item.author == current_user:
                flash("You cannot claim your own item. The Owner must enter this PIN.", "danger")
                return redirect(url_for('my_items'))
            
            # 2. Mark the FOUND item as Resolved
            found_item.is_resolved = True
            found_item.author.karma += 20 # Reward Finder
            
            # 3. AUTO-RESOLVE the Owner's "Lost" Report
            # We look for a 'Lost' item posted by the person claiming (current_user)
            # that matches the category of the item found.
            my_lost_report = Item.query.filter_by(
                user_id=current_user.id, 
                type='Lost', 
                category=found_item.category,
                is_resolved=False
            ).order_by(Item.date_posted.desc()).first()
            
            msg = f"Success! You confirmed receipt of '{found_item.name}'."
            
            if my_lost_report:
                my_lost_report.is_resolved = True
                msg += f" Your lost report for '{my_lost_report.name}' has also been closed."
            
            db.session.commit()
            flash(msg, "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid Code. Please check the PIN provided by the finder.", "danger")
    return render_template('claim.html')

@app.route('/chat/<int:item_id>', methods=['GET', 'POST'])
@login_required
def chat(item_id):
    item = Item.query.get_or_404(item_id)
    
    # Security Check
    is_owner = (item.user_id == current_user.id)
    has_messaged = Message.query.filter_by(item_id=item.id, sender=current_user.username).first()
    if not is_owner and not has_messaged and not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        msg_body = request.form.get('message', '')
        file = request.files.get('attachment')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if not msg_body: msg_body = "[Sent an Attachment]"
            
        if msg_body or filename:
            new_msg = Message(item_id=item.id, sender=current_user.username, body=msg_body, attachment=filename)
            db.session.add(new_msg)
            db.session.commit()
        return redirect(url_for('chat', item_id=item.id))
        
    messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()
    return render_template('chat.html', item=item, messages=messages)

@app.route('/verify/<int:item_id>', methods=['GET', 'POST'])
@login_required
def verify(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        msg_body = request.form['message']
        if item.author == current_user:
            flash("You cannot verify your own item!", "warning")
            return redirect(url_for('index'))
        initial_msg = Message(
            item_id=item.id,
            sender=current_user.username, 
            body=f"VERIFICATION REQUEST: {msg_body}"
        )
        db.session.add(initial_msg)
        db.session.commit()
        flash('Request sent!', 'success')
        return redirect(url_for('chat', item_id=item.id))
    return render_template('verify.html', item=item)

@app.route('/my_items')
@login_required
def my_items():
    items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_posted.desc()).all()
    return render_template('my_items.html', items=items)

@app.route('/profile')
@login_required
def profile():
    items_posted = Item.query.filter_by(user_id=current_user.id).count()
    items_returned = Item.query.filter_by(user_id=current_user.id, is_resolved=True).count()
    return render_template('profile.html', user=current_user, items_posted=items_posted, items_returned=items_returned)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))

    hashed_new_password = generate_password_hash(new_password, method='scrypt')
    current_user.password = hashed_new_password
    db.session.commit()

    flash('Password updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin: return redirect(url_for('index'))
    
    users = User.query.all()
    items = Item.query.order_by(Item.date_posted.desc()).all()
    
    # Analytics for Charts
    lost_count = Item.query.filter_by(type='Lost').count()
    found_count = Item.query.filter_by(type='Found').count()
    categories = ['Electronics', 'Documents', 'Clothing', 'Keys', 'Other']
    cat_counts = [Item.query.filter_by(category=c).count() for c in categories]
    
    return render_template('admin.html', users=users, items=items, lost_count=lost_count, found_count=found_count, categories=categories, cat_counts=cat_counts)

@app.route('/admin/delete_item/<int:item_id>')
@login_required
def admin_delete_item(item_id):
    if not current_user.is_admin: return redirect(url_for('index'))
    db.session.delete(Item.query.get_or_404(item_id))
    db.session.commit()
    flash('Item deleted.', 'warning')
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin: return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if not user.is_admin:
        db.session.delete(user)
        db.session.commit()
        flash('User banned.', 'danger')
    return redirect(url_for('admin'))

@app.route('/messages')
@login_required
def messages():
    owned = Item.query.join(Message).filter(Item.user_id == current_user.id).all()
    found = Item.query.join(Message).filter(Message.sender == current_user.username).all()
    return render_template('messages.html', chats=list(set(owned + found)))

if __name__ == "__main__":
    app.run(debug=True)