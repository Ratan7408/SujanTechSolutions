# app.py - Enhanced Flask Application with Authentication, Admin Panel & More
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Flask-Babel setup with version compatibility
try:
    from flask_babel import Babel
    babel = Babel(app)
    print("✅ Flask-Babel imported successfully")
except ImportError:
    print("⚠️ Flask-Babel not installed, language features disabled")
    babel = None

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cybercode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Google OAuth Configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

# Multi-language Configuration (simplified)
app.config['LANGUAGES'] = {
    'en': 'English',
    'es': 'Español', 
    'fr': 'Français',
    'de': 'Deutsch',
    'hi': 'हिंदी',
    'ja': '日本語'
}

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
oauth = OAuth(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)

# Google OAuth Setup
google = None
print("🔧 Setting up Google OAuth...")

if app.config['GOOGLE_OAUTH_CLIENT_ID'] and app.config['GOOGLE_OAUTH_CLIENT_SECRET']:
    try:
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        print("✅ Google OAuth configured successfully")
    except Exception as e:
        print(f"⚠️ Google OAuth primary setup failed: {e}")
        
        try:
            google = oauth.register(
                name='google',
                client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
                client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
                authorize_url='https://accounts.google.com/o/oauth2/auth',
                access_token_url='https://accounts.google.com/o/oauth2/token',
                userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
                client_kwargs={'scope': 'openid email profile'},
            )
            print("✅ Google OAuth configured with alternative method")
        except Exception as e2:
            print(f"⚠️ Google OAuth alternative setup also failed: {e2}")
            google = None
else:
    print("⚠️ Google OAuth credentials not found in environment variables")

# Babel locale selector with version compatibility
def get_locale():
    return session.get('language', 'en')

if babel:
    try:
        # Try newer Flask-Babel versions first
        if hasattr(babel, 'locale_selector'):
            babel.locale_selector(get_locale)
            print("✅ Babel locale_selector configured")
        elif hasattr(babel, 'localeselector'):
            babel.localeselector(get_locale)
            print("✅ Babel localeselector configured")
        else:
            print("⚠️ Babel version not supported, using basic language support")
    except Exception as e:
        print(f"⚠️ Babel configuration failed: {e}")
else:
    print("⚠️ Babel not available, using basic language support")

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.String(5), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    chat_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.user_id', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon_class = db.Column(db.String(50))  # Font Awesome icon class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300))
    demo_video_url = db.Column(db.String(300))
    code_preview = db.Column(db.Text)
    features = db.Column(db.Text)  # JSON string of features
    downloads = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=4.5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships
    orders = db.relationship('Order', backref='product', lazy=True)
    media_files = db.relationship('ProductMedia', backref='product', lazy=True, cascade='all, delete-orphan')

class ProductMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(50))  # 'image', 'video_phone', 'video_laptop', 'screenshot'
    description = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    status = db.Column(db.String(50), default='contact_pending')  # contact_pending, completed, cancelled
    telegram_contacted = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.String(100))  # For chat rooms
    
    # Explicit relationships to avoid ambiguity
    admin_user = db.relationship('User', foreign_keys=[admin_user_id], backref='admin_messages')

# Forms
class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    code_preview = TextAreaField('Code Preview')
    features = TextAreaField('Features (one per line)')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'])])
    demo_video = FileField('Demo Video', validators=[FileAllowed(['mp4', 'mov', 'avi'])])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin Panel Views
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class AdminDashboard(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('login'))
        
        # Dashboard statistics
        total_products = Product.query.count()
        total_users = User.query.count()
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='contact_pending').count()
        
        return self.render('admin/index.html',
                         total_products=total_products,
                         total_users=total_users,
                         total_orders=total_orders,
                         pending_orders=pending_orders)

class ProductAdminView(SecureModelView):
    column_list = ['name', 'category_id', 'price', 'downloads', 'rating', 'is_active', 'created_at']
    column_searchable_list = ['name', 'description']
    column_filters = ['category_id', 'is_active', 'created_at']
    form_excluded_columns = ['orders', 'media_files', 'created_at', 'updated_at']
    column_labels = {'category_id': 'Category'}
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.created_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()

# Initialize Admin
admin = Admin(app, name='CyberCode Admin', template_mode='bootstrap4', index_view=AdminDashboard())
admin.add_view(ProductAdminView(Product, db.session))
admin.add_view(SecureModelView(Category, db.session))
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Order, db.session))
admin.add_view(SecureModelView(ChatMessage, db.session))

# Helper functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_sample_data():
    """Create sample categories with one bot in each category"""
    
    try:
        # Create admin user if none exists
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User(
                email='admin@cybercode.com',
                name='Admin User',
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created (admin@cybercode.com)")
        
        # Clear existing data first
        if Product.query.count() > 0:
            print("🧹 Clearing existing products...")
            Product.query.delete()
            db.session.commit()
        
        if Category.query.count() > 0:
            print("🧹 Clearing existing categories...")
            Category.query.delete()
            db.session.commit()
        
        # Create categories
        print("📁 Creating categories...")
        categories_data = [
            {'name': 'Telegram Bots', 'description': 'Advanced Telegram automation tools', 'icon_class': 'fab fa-telegram'},
            {'name': 'Discord Bots', 'description': 'Discord server management solutions', 'icon_class': 'fab fa-discord'},
            {'name': 'Automation', 'description': 'Workflow automation scripts', 'icon_class': 'fas fa-robot'},
            {'name': 'Trading', 'description': 'Crypto trading tools', 'icon_class': 'fas fa-chart-line'},
            {'name': 'Data Tools', 'description': 'Web scraping and data analysis', 'icon_class': 'fas fa-database'},
            {'name': 'Utilities', 'description': 'System utilities and tools', 'icon_class': 'fas fa-tools'}
        ]
        
        categories = []
        for i, cat_data in enumerate(categories_data):
            category = Category(**cat_data)
            db.session.add(category)
            categories.append(category)
            print(f"  ✅ Category {i+1}: {cat_data['name']}")
        
        db.session.commit()
        print("✅ All 6 categories created!")
        
        # Wait a moment and refresh categories with their IDs
        db.session.refresh(categories[0])
        db.session.refresh(categories[1])
        db.session.refresh(categories[2])
        db.session.refresh(categories[3])
        db.session.refresh(categories[4])
        db.session.refresh(categories[5])
        
        # Create products - ONE for each category
        print("🤖 Creating bots for each category...")
        products_data = [
            # Telegram Bot (Category 1)
            {
                'name': 'Telegram Admin Bot',
                'description': 'Advanced admin panel with user management, analytics, and automated moderation features.',
                'price': 49.99,
                'category_id': categories[0].id,
                'image_url': 'https://via.placeholder.com/600x400/007bff/ffffff?text=Telegram+Admin+Bot',
                'demo_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'features': 'User Management\nAuto Moderation\nAnalytics Dashboard\nCustom Commands',
                'code_preview': '''# Telegram Admin Bot
import telebot
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("👥 Users", callback_data="users")
    btn2 = types.InlineKeyboardButton("📊 Stats", callback_data="stats")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, "🚀 Admin Panel!", reply_markup=markup)

bot.infinity_polling()''',
                'downloads': 1249,
                'rating': 4.8
            },
            # Discord Bot (Category 2)
            {
                'name': 'Discord Server Manager Bot',
                'description': 'Complete Discord server automation with role management and security features.',
                'price': 39.99,
                'category_id': categories[1].id,
                'image_url': 'https://via.placeholder.com/600x400/7289da/ffffff?text=Discord+Server+Bot',
                'demo_video_url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
                'features': 'Role Automation\nSecurity Monitoring\nEvent Scheduling\nMember Analytics',
                'code_preview': '''# Discord Server Manager
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'{bot.user} has landed!')

@bot.command()
async def role_auto(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Assigned {role.name} to {member.display_name}")

bot.run('YOUR_BOT_TOKEN')''',
                'downloads': 2103,
                'rating': 4.7
            },
            # Automation Bot (Category 3)
            {
                'name': 'Auto Workflow Bot',
                'description': 'Smart automation bot for workflow management and task scheduling.',
                'price': 59.99,
                'category_id': categories[2].id,
                'image_url': 'https://via.placeholder.com/600x400/28a745/ffffff?text=Automation+Bot',
                'demo_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
                'features': 'Task Scheduling\nWorkflow Automation\nAPI Integration\nSmart Notifications',
                'code_preview': '''# Automation Bot
import schedule
import time

class AutoBot:
    def __init__(self):
        self.tasks = []
    
    def add_task(self, func, interval):
        schedule.every(interval).minutes.do(func)
        print(f"✅ Task scheduled every {interval} minutes")
    
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

bot = AutoBot()
print("🤖 Automation Bot Started!")''',
                'downloads': 856,
                'rating': 4.6
            },
            # Trading Bot (Category 4)
            {
                'name': 'Crypto Trading Bot',
                'description': 'Advanced cryptocurrency trading bot with technical analysis and risk management.',
                'price': 199.99,
                'category_id': categories[3].id,
                'image_url': 'https://via.placeholder.com/600x400/f39c12/ffffff?text=Trading+Bot',
                'demo_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
                'features': 'Technical Analysis\nRisk Management\nMulti-Exchange\nBacktesting\nProfit Tracking',
                'code_preview': '''# Crypto Trading Bot
import ccxt
import pandas as pd

class TradingBot:
    def __init__(self, exchange, api_key, secret):
        self.exchange = getattr(ccxt, exchange)({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': True
        })
    
    def analyze_market(self, symbol):
        return "BUY_SIGNAL"
    
    def execute_trade(self, symbol, action):
        print(f"🚀 Executing {action} for {symbol}")

bot = TradingBot('binance', 'key', 'secret')
print("📈 Trading Bot Active!")''',
                'downloads': 412,
                'rating': 4.9
            },
            # Data Tools Bot (Category 5)
            {
                'name': 'Data Scraper Bot',
                'description': 'Powerful web scraping and data analysis bot with advanced parsing capabilities.',
                'price': 79.99,
                'category_id': categories[4].id,
                'image_url': 'https://via.placeholder.com/600x400/e83e8c/ffffff?text=Data+Scraper+Bot',
                'demo_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4',
                'features': 'Web Scraping\nData Analysis\nCSV Export\nAPI Integration\nScheduled Tasks',
                'code_preview': '''# Data Scraper Bot
import requests
from bs4 import BeautifulSoup
import pandas as pd

class ScraperBot:
    def __init__(self):
        self.session = requests.Session()
        self.data = []
    
    def scrape_website(self, url):
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    
    def export_data(self, filename):
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"✅ Data exported to {filename}")

bot = ScraperBot()
print("🔍 Data Scraper Bot Ready!")''',
                'downloads': 634,
                'rating': 4.5
            },
            # Utilities Bot (Category 6)
            {
                'name': 'System Monitor Bot',
                'description': 'Comprehensive system monitoring and maintenance utility bot.',
                'price': 29.99,
                'category_id': categories[5].id,
                'image_url': 'https://via.placeholder.com/600x400/6f42c1/ffffff?text=System+Monitor+Bot',
                'demo_video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4',
                'features': 'System Monitoring\nPerformance Alerts\nLog Analysis\nCleanup Tools\nHealth Reports',
                'code_preview': '''# System Monitor Bot
import psutil
import time

class MonitorBot:
    def __init__(self):
        self.alerts = []
    
    def check_system(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        if cpu_percent > 80:
            print(f"⚠️ High CPU usage: {cpu_percent}%")
        
        if memory.percent > 85:
            print(f"⚠️ High memory usage: {memory.percent}%")
    
    def generate_report(self):
        print("📊 System Health Report Generated")

bot = MonitorBot()
print("🔧 System Monitor Bot Active!")''',
                'downloads': 923,
                'rating': 4.4
            }
        ]
        
        # Create all products
        for i, product_data in enumerate(products_data):
            product = Product(**product_data)
            db.session.add(product)
            print(f"  ✅ Bot {i+1}: {product_data['name']} → Category ID {product_data['category_id']}")
        
        db.session.commit()
        print("✅ All 6 bots created successfully!")
        
        # Verify the data
        total_categories = Category.query.count()
        total_products = Product.query.count()
        print(f"\n📊 Database Summary:")
        print(f"   📁 Total Categories: {total_categories}")
        print(f"   🤖 Total Bots: {total_products}")
        
        # Show products per category
        for category in Category.query.all():
            product_count = Product.query.filter_by(category_id=category.id).count()
            print(f"   📁 {category.name}: {product_count} bot(s)")
        
        print("✅ Sample data creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

# Routes
@app.route('/')
def index():
    products = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    
    # Try to render template, fallback to HTML if template missing
    try:
        return render_template('index.html', products=products, categories=categories)
    except:
        # Create fallback HTML for homepage
        
        # Featured products section
        featured_products_html = ""
        for product in products[:6]:  # Show first 6 products
            featured_products_html += f"""
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm product-card">
                    <img src="{product.image_url or 'https://via.placeholder.com/400x300/333333/ffffff?text=No+Image'}" 
                         class="card-img-top" style="height: 200px; object-fit: cover;"
                         onerror="this.src='https://via.placeholder.com/400x300/333333/ffffff?text=No+Image'">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">{product.name}</h5>
                        <p class="card-text text-muted">{product.description[:100]}{'...' if len(product.description) > 100 else ''}</p>
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <span class="h5 text-success mb-0">${product.price}</span>
                                <div class="text-end">
                                    <small class="text-muted d-block">
                                        <i class="fas fa-download"></i> {product.downloads}
                                    </small>
                                    <small class="text-warning">
                                        <i class="fas fa-star"></i> {product.rating}
                                    </small>
                                </div>
                            </div>
                            <div class="d-grid gap-2">
                                <a href="/product/{product.id}" class="btn btn-primary btn-sm">
                                    <i class="fas fa-eye"></i> View Details
                                </a>
                                <a href="/contact-telegram/{product.id}" class="btn btn-success btn-sm">
                                    <i class="fab fa-telegram"></i> Buy Now
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        # Categories section
        categories_html = ""
        for category in categories:
            categories_html += f"""
            <div class="col-md-6 col-lg-4 mb-4">
                <a href="/category/{category.id}" class="text-decoration-none">
                    <div class="card h-100 category-card">
                        <div class="card-body text-center">
                            <div class="category-icon mb-3">
                                <i class="{category.icon_class} fa-3x text-success"></i>
                            </div>
                            <h5 class="card-title text-white">{category.name}</h5>
                            <p class="card-text text-muted">{category.description}</p>
                            <div class="mt-3">
                                <span class="badge bg-success">
                                    {Product.query.filter_by(category_id=category.id, is_active=True).count()} bot(s)
                                </span>
                            </div>
                        </div>
                    </div>
                </a>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CyberCode Marketplace - Premium Bot Solutions</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    color: white; 
                    min-height: 100vh;
                }}
                .navbar {{ background: rgba(0,0,0,0.95) !important; backdrop-filter: blur(10px); }}
                .hero-section {{
                    background: linear-gradient(135deg, rgba(0,255,136,0.1) 0%, rgba(0,123,255,0.1) 100%);
                    padding: 4rem 0;
                    margin-bottom: 3rem;
                    border-radius: 20px;
                }}
                .card {{ 
                    background: rgba(255,255,255,0.05); 
                    border: 1px solid rgba(0,255,136,0.2);
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                }}
                .card:hover {{ 
                    transform: translateY(-5px); 
                    border-color: #00ff88;
                    box-shadow: 0 10px 30px rgba(0,255,136,0.2);
                }}
                .product-card:hover {{ border-color: #007bff; }}
                .category-card {{ cursor: pointer; }}
                .category-card:hover {{ 
                    border-color: #00ff88 !important;
                    transform: translateY(-8px);
                }}
                .text-success {{ color: #00ff88 !important; }}
                .btn-primary {{ background: #007bff; border: none; }}
                .btn-success {{ background: #00ff88; border: none; color: #000; font-weight: bold; }}
                .section-title {{ 
                    color: #00ff88; 
                    font-weight: bold; 
                    margin-bottom: 2rem;
                    position: relative;
                }}
                .section-title::after {{
                    content: '';
                    position: absolute;
                    bottom: -10px;
                    left: 0;
                    width: 50px;
                    height: 3px;
                    background: #00ff88;
                }}
                .stats-card {{
                    background: linear-gradient(135deg, rgba(0,255,136,0.1) 0%, rgba(0,123,255,0.1) 100%);
                    border: 1px solid rgba(0,255,136,0.3);
                }}
            </style>
        </head>
        <body>
            <!-- Navigation -->
            <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
                <div class="container">
                    <a class="navbar-brand fw-bold" href="/">
                        <i class="fas fa-code text-success"></i> CyberCode
                    </a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav me-auto">
                            <li class="nav-item">
                                <a class="nav-link" href="/">
                                    <i class="fas fa-home"></i> Home
                                </a>
                            </li>
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="#" id="categoriesDropdown" role="button" data-bs-toggle="dropdown">
                                    <i class="fas fa-th-large"></i> Categories
                                </a>
                                <ul class="dropdown-menu bg-dark">
                                    {"".join([f'<li><a class="dropdown-item text-light" href="/category/{cat.id}"><i class="{cat.icon_class}"></i> {cat.name}</a></li>' for cat in categories])}
                                </ul>
                            </li>
                        </ul>
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/login">
                                    <i class="fas fa-sign-in-alt"></i> Login
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/admin-access">
                                    <i class="fas fa-cog"></i> Admin
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <!-- Hero Section -->
            <div class="container" style="margin-top: 100px;">
                <div class="hero-section text-center">
                    <h1 class="display-3 fw-bold mb-4">
                        <i class="fas fa-rocket text-success"></i> CyberCode Marketplace
                    </h1>
                    <p class="lead mb-4">Premium bots, automation tools, and digital solutions for developers</p>
                    <div class="row justify-content-center">
                        <div class="col-md-3 mb-3">
                            <div class="stats-card card text-center py-3">
                                <h4 class="text-success mb-1">{len(categories)}</h4>
                                <small class="text-muted">Categories</small>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="stats-card card text-center py-3">
                                <h4 class="text-success mb-1">{len(products)}</h4>
                                <small class="text-muted">Premium Bots</small>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="stats-card card text-center py-3">
                                <h4 class="text-success mb-1">{sum(p.downloads for p in products):,}</h4>
                                <small class="text-muted">Downloads</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Featured Products -->
            <div class="container mb-5">
                <h2 class="section-title">
                    <i class="fas fa-star"></i> Featured Bots
                </h2>
                <div class="row">
                    {featured_products_html}
                </div>
            </div>

            <!-- Explore Categories -->
            <div class="container mb-5">
                <h2 class="section-title">
                    <i class="fas fa-th-large"></i> Explore Other Categories
                </h2>
                <div class="row">
                    {categories_html}
                </div>
            </div>

            <!-- Call to Action -->
            <div class="container mb-5">
                <div class="card text-center py-5">
                    <div class="card-body">
                        <h3 class="mb-4">Ready to Automate Your Workflow?</h3>
                        <p class="lead mb-4">Join thousands of developers who trust our premium bot solutions</p>
                        <div>
                            <a href="#categories" class="btn btn-success btn-lg me-3">
                                <i class="fas fa-rocket"></i> Browse Bots
                            </a>
                            <a href="/admin-access" class="btn btn-outline-light btn-lg">
                                <i class="fas fa-cog"></i> Admin Panel
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <footer class="py-5 text-center text-muted">
                <div class="container">
                    <p>&copy; 2024 CyberCode Marketplace. Premium bot solutions for developers.</p>
                    <p>
                        <a href="/admin-access" class="text-success text-decoration-none">Admin Panel</a> | 
                        <a href="/reset-database" class="text-warning text-decoration-none">Reset Database</a>
                    </p>
                </div>
            </footer>

            <!-- Bootstrap JS -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/auth/google')
def google_auth():
    if not google:
        flash('Google OAuth is not configured. Please contact administrator.', 'error')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_auth_callback():
    if not google:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('login'))
    
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            user = User.query.filter_by(email=user_info['email']).first()
            
            if not user:
                # Create new user
                user = User(
                    email=user_info['email'],
                    name=user_info['name'],
                    profile_pic=user_info.get('picture', '')
                )
                # Make first user admin
                if User.query.count() == 0:
                    user.is_admin = True
                
                db.session.add(user)
                db.session.commit()
                flash('Account created successfully!', 'success')
            
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        
    except Exception as e:
        print(f"OAuth error: {e}")
        flash('Authentication failed. Please try again.', 'error')
    
    return redirect(url_for('login'))

# Direct admin access route
@app.route('/admin-access')
def admin_access():
    # Create admin user if none exists and log them in
    admin_user = User.query.filter_by(email='admin@cybercode.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@cybercode.com',
            name='Admin User',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        flash('Admin account created!', 'success')
    
    login_user(admin_user)
    flash('Logged in as admin!', 'success')
    return redirect('/admin/')

# Database reset route to fix issues
@app.route('/reset-database')
def reset_database():
    try:
        print("🔄 Resetting database...")
        
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create fresh sample data
        create_sample_data()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Reset - CyberCode</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 50px; background: #1a1a1a; color: white; text-align: center; }
                .container { max-width: 600px; margin: 0 auto; }
                .success { color: #00ff88; font-size: 24px; margin: 20px 0; }
                .btn { display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; 
                       border-radius: 5px; font-weight: bold; font-size: 16px; }
                .btn-primary { background: #007bff; color: white; }
                .btn-success { background: #28a745; color: white; }
                .info { background: #333; padding: 20px; border-radius: 10px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Database Reset Complete!</h1>
                <div class="success">✅ Fresh database created with 6 categories and 6 bots!</div>
                
                <div class="info">
                    <h3>🎯 What was created:</h3>
                    <p>📁 6 Categories: Telegram, Discord, Automation, Trading, Data Tools, Utilities</p>
                    <p>🤖 6 Bots: One bot in each category</p>
                    <p>👤 Admin user: admin@cybercode.com</p>
                    <p>🔧 Fixed admin panel category issues</p>
                </div>
                
                <div>
                    <a href="/" class="btn btn-primary">🏠 View Homepage</a>
                    <a href="/admin-access" class="btn btn-success">🛠️ Admin Panel</a>
                    <a href="/quick-add-product" class="btn btn-success">➕ Quick Add Product</a>
                </div>
                
                <div style="margin-top: 30px; color: #888;">
                    <small>The admin panel should now work properly for creating new products.</small>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <h1 style="color: red;">❌ Database Reset Failed</h1>
        <p>Error: {str(e)}</p>
        <p><a href="/">Go Back to Homepage</a></p>
        <pre>{str(e)}</pre>
        '''

# Force rebuild database route (nuclear option)
@app.route('/force-rebuild-db')
def force_rebuild_db():
    try:
        print("💥 FORCE REBUILDING DATABASE...")
        
        # Import os to delete file
        import os
        
        # Close all database connections
        db.session.close()
        db.engine.dispose()
        
        # Delete database file completely
        if os.path.exists('cybercode.db'):
            os.remove('cybercode.db')
            print("🗑️ Deleted old database file")
        
        # Recreate everything from scratch
        db.create_all()
        print("🔧 Created fresh database tables")
        
        # Create sample data
        create_sample_data()
        print("📦 Added sample data")
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Force Database Rebuild - CyberCode</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 50px; background: #1a1a1a; color: white; text-align: center; }
                .container { max-width: 600px; margin: 0 auto; }
                .success { color: #00ff88; font-size: 24px; margin: 20px 0; }
                .btn { display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; 
                       border-radius: 5px; font-weight: bold; font-size: 16px; }
                .btn-primary { background: #007bff; color: white; }
                .btn-success { background: #28a745; color: white; }
                .warning { background: #ff9800; color: #000; padding: 20px; border-radius: 10px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💥 Database Force Rebuilt!</h1>
                <div class="success">✅ Completely fresh database created!</div>
                
                <div class="warning">
                    <h3>⚠️ What happened:</h3>
                    <p>🗑️ Deleted old database file completely</p>
                    <p>🔧 Created brand new database</p>
                    <p>📦 Added fresh sample data</p>
                    <p>🔄 All integrity issues should be fixed</p>
                </div>
                
                <div>
                    <a href="/" class="btn btn-primary">🏠 View Homepage</a>
                    <a href="/admin-access" class="btn btn-success">🛠️ Test Admin Panel</a>
                    <a href="/quick-add-product" class="btn btn-success">➕ Quick Add Product</a>
                </div>
                
                <div style="margin-top: 30px; color: #888;">
                    <small>Try creating a new product now - the category issue should be completely fixed!</small>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <h1 style="color: red;">❌ Force Rebuild Failed</h1>
        <p>Error: {str(e)}</p>
        <p><a href="/">Go Back to Homepage</a></p>
        <pre>{str(e)}</pre>
        '''

# Quick product creation route (fix for admin issues)
@app.route('/quick-add-product', methods=['GET', 'POST'])
def quick_add_product():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = float(request.form.get('price', 0))
            category_id = int(request.form.get('category_id'))
            image_url = request.form.get('image_url', '').strip()
            demo_video_url = request.form.get('demo_video_url', '').strip()
            
            # Validate required fields
            if not name or not description or not category_id:
                return jsonify({'error': 'Name, description, and category are required'}), 400
            
            # Create new product
            new_product = Product(
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                image_url=image_url if image_url else None,
                demo_video_url=demo_video_url if demo_video_url else None,
                code_preview='',
                features='',
                downloads=0,
                rating=4.5,
                is_active=True
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'Product "{name}" created successfully!', 'product_id': new_product.id})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to create product: {str(e)}'}), 500
    
    # GET request - show form
    categories = Category.query.all()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quick Add Product - CyberCode</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 30px; background: #1a1a1a; color: white; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #00ff88; }}
            input, select, textarea {{ 
                width: 100%; padding: 10px; border: 1px solid #444; 
                background: #333; color: white; border-radius: 5px; font-size: 16px; 
            }}
            textarea {{ height: 100px; resize: vertical; }}
            .btn {{ 
                background: #00ff88; color: #000; padding: 15px 30px; border: none; 
                border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px; 
            }}
            .btn:hover {{ background: #00cc6a; }}
            .success {{ color: #00ff88; background: rgba(0,255,136,0.1); padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .error {{ color: #ff4444; background: rgba(255,68,68,0.1); padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .back-link {{ color: #007bff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Quick Add Product</h1>
            <p>Use this form to quickly add a new bot/product with proper category selection.</p>
            
            <form id="productForm">
                <div class="form-group">
                    <label for="name">Product Name *</label>
                    <input type="text" id="name" name="name" required placeholder="e.g., Advanced Telegram Bot">
                </div>
                
                <div class="form-group">
                    <label for="description">Description *</label>
                    <textarea id="description" name="description" required placeholder="Describe what your bot does..."></textarea>
                </div>
                
                <div class="form-group">
                    <label for="category_id">Category *</label>
                    <select id="category_id" name="category_id" required>
                        <option value="">-- Select Category --</option>
                        {''.join([f'<option value="{cat.id}">{cat.name}</option>' for cat in categories])}
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="price">Price ($)</label>
                    <input type="number" id="price" name="price" min="0" step="0.01" value="0" placeholder="0.00">
                </div>
                
                <div class="form-group">
                    <label for="image_url">Image URL</label>
                    <input type="url" id="image_url" name="image_url" placeholder="/static/images/my-bot.jpg or https://i.imgur.com/abc123.jpg">
                    <small style="color: #888;">Recommended: 600x400 pixels. Use /static/images/ for local files or imgur.com links.</small>
                </div>
                
                <div class="form-group">
                    <label for="demo_video_url">Demo Video URL</label>
                    <input type="url" id="demo_video_url" name="demo_video_url" placeholder="https://youtube.com/watch?v=... or /static/videos/demo.mp4">
                </div>
                
                <div class="form-group">
                    <button type="submit" class="btn">✅ Create Product</button>
                </div>
            </form>
            
            <div id="result"></div>
            
            <div style="margin-top: 30px;">
                <a href="/admin-access" class="back-link">← Back to Admin Panel</a> | 
                <a href="/" class="back-link">🏠 Homepage</a>
            </div>
        </div>
        
        <script>
            document.getElementById('productForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                
                const formData = new FormData(this);
                const resultDiv = document.getElementById('result');
                
                fetch('/quick-add-product', {{
                    method: 'POST',
                    body: formData
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        resultDiv.innerHTML = '<div class="success">✅ ' + data.message + '</div>';
                        this.reset(); // Clear form
                    }} else {{
                        resultDiv.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                    }}
                }})
                .catch(error => {{
                    resultDiv.innerHTML = '<div class="error">❌ Error: ' + error.message + '</div>';
                }});
            }});
        </script>
    </body>
    </html>
    '''
@app.route('/setup-static')
def setup_static():
    import os
    try:
        # Create static directories if they don't exist
        os.makedirs('static', exist_ok=True)
        os.makedirs('static/images', exist_ok=True)
        os.makedirs('static/videos', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        
        # Create a test image
        test_image_content = '''<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
<rect width="600" height="400" fill="#1a1a1a"/>
<text x="300" y="200" font-family="Arial" font-size="24" fill="#00ff88" text-anchor="middle">
Test Bot Image
</text>
<text x="300" y="230" font-family="Arial" font-size="16" fill="#ffffff" text-anchor="middle">
600x400 pixels - Static files working!
</text>
</svg>'''
        
        with open('static/images/test-bot.svg', 'w') as f:
            f.write(test_image_content)
        
        # Test if static route works
        static_test_url = '/static/images/test-bot.svg'
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Static Files Setup - CyberCode</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 30px; background: #1a1a1a; color: white; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .success {{ color: #00ff88; }}
                .test-section {{ background: #333; padding: 20px; margin: 20px 0; border-radius: 10px; }}
                .btn {{ display: inline-block; padding: 10px 20px; margin: 10px 5px; text-decoration: none; 
                       border-radius: 5px; font-weight: bold; }}
                .btn-primary {{ background: #007bff; color: white; }}
                .btn-success {{ background: #28a745; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 Static Files Setup</h1>
                
                <div class="test-section">
                    <h3 class="success">✅ Folders Created:</h3>
                    <ul>
                        <li>📁 static/</li>
                        <li>📁 static/images/</li>
                        <li>📁 static/videos/</li>
                        <li>📁 static/css/</li>
                        <li>📁 static/js/</li>
                        <li>🖼️ static/images/test-bot.svg (test image)</li>
                    </ul>
                </div>
                
                <div class="test-section">
                    <h3>🧪 Test Static Image:</h3>
                    <p><strong>URL:</strong> {static_test_url}</p>
                    <img src="{static_test_url}" style="max-width: 300px; border: 2px solid #00ff88; border-radius: 10px;">
                    <p>👆 If you see the test image above, static files are working!</p>
                </div>
                
                <div class="test-section">
                    <h3>📝 How to Add Your Images:</h3>
                    <ol>
                        <li>Save your images in the <code>static/images/</code> folder</li>
                        <li>Name them like: <code>telegram-bot.jpg</code>, <code>discord-bot.png</code></li>
                        <li>Use URLs like: <code>/static/images/telegram-bot.jpg</code></li>
                        <li>Update your product image URLs in the admin panel</li>
                    </ol>
                </div>
                
                <div class="test-section">
                    <h3>🎯 Your Project Structure Should Look Like:</h3>
                    <pre style="background: #1a1a1a; padding: 15px; border-radius: 5px;">
your-project/
├── app.py
├── cybercode.db
└── static/
    ├── images/
    │   ├── test-bot.svg
    │   ├── telegram-bot.jpg  ← Put your images here
    │   └── discord-bot.png   ← Put your images here
    ├── videos/
    ├── css/
    └── js/
                    </pre>
                </div>
                
                <div>
                    <a href="/" class="btn btn-primary">🏠 Back to Homepage</a>
                    <a href="/admin-access" class="btn btn-success">🛠️ Admin Panel</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <h1 style="color: red;">❌ Static Setup Failed</h1>
        <p>Error: {str(e)}</p>
        <pre>{str(e)}</pre>
        '''

# Simple manual login for testing
@app.route('/manual-login')
def manual_login():
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        admin_user = User(
            email='admin@cybercode.com',
            name='Admin User',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
    
    login_user(admin_user)
    flash('Logged in as admin for testing!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/category/<int:category_id>')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id, is_active=True).all()
    all_categories = Category.query.all()  # Get all categories for the "Explore Other" section
    
    # Try to render template, fallback to HTML if template missing
    try:
        return render_template('category.html', products=products, category=category, all_categories=all_categories)
    except:
        # Create fallback HTML when template is missing
        products_html = ""
        
        if products:
            for product in products:
                products_html += f"""
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <img src="{product.image_url or 'https://via.placeholder.com/400x300/333333/ffffff?text=No+Image'}" 
                             class="card-img-top" style="height: 250px; object-fit: cover;"
                             onerror="this.src='https://via.placeholder.com/400x300/333333/ffffff?text=No+Image'">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{product.name}</h5>
                            <p class="card-text text-muted">{product.description[:150]}{'...' if len(product.description) > 150 else ''}</p>
                            <div class="mt-auto">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span class="h4 text-success mb-0">${product.price}</span>
                                    <div>
                                        <small class="text-muted">
                                            <i class="fas fa-download"></i> {product.downloads} downloads
                                        </small>
                                        <br>
                                        <small class="text-warning">
                                            <i class="fas fa-star"></i> {product.rating}/5
                                        </small>
                                    </div>
                                </div>
                                <div class="d-grid gap-2">
                                    <a href="/product/{product.id}" class="btn btn-primary">
                                        <i class="fas fa-eye"></i> View Details
                                    </a>
                                    <a href="/contact-telegram/{product.id}" class="btn btn-success">
                                        <i class="fab fa-telegram"></i> Buy Now
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
        else:
            products_html = """
            <div class="col-12 text-center">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> No bots available in this category yet.
                    <br><br>
                    <a href="/" class="btn btn-primary">← Back to Homepage</a>
                </div>
            </div>
            """
        
        # Create "Explore Other Categories" section
        other_categories_html = ""
        for cat in all_categories:
            if cat.id != category_id:  # Don't show current category
                product_count = Product.query.filter_by(category_id=cat.id, is_active=True).count()
                other_categories_html += f"""
                <div class="col-md-6 col-lg-4 mb-4">
                    <a href="/category/{cat.id}" class="text-decoration-none">
                        <div class="card h-100 category-card">
                            <div class="card-body text-center">
                                <div class="category-icon mb-3">
                                    <i class="{cat.icon_class} fa-3x text-success"></i>
                                </div>
                                <h5 class="card-title text-white">{cat.name}</h5>
                                <p class="card-text text-muted">{cat.description}</p>
                                <div class="mt-3">
                                    <span class="badge bg-success">
                                        {product_count} bot(s)
                                    </span>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{category.name} - CyberCode Marketplace</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    color: white; 
                    min-height: 100vh;
                }}
                .navbar {{ background: rgba(0,0,0,0.95) !important; backdrop-filter: blur(10px); }}
                .card {{ 
                    background: rgba(255,255,255,0.05); 
                    border: 1px solid rgba(0,255,136,0.2);
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                }}
                .card:hover {{ 
                    transform: translateY(-5px); 
                    border-color: #00ff88;
                    box-shadow: 0 10px 30px rgba(0,255,136,0.2);
                }}
                .category-card {{ cursor: pointer; }}
                .category-card:hover {{ 
                    border-color: #00ff88 !important;
                    transform: translateY(-8px);
                }}
                .text-success {{ color: #00ff88 !important; }}
                .btn-primary {{ background: #007bff; border: none; }}
                .btn-success {{ background: #00ff88; border: none; color: #000; font-weight: bold; }}
                .category-header {{
                    background: linear-gradient(135deg, rgba(0,255,136,0.2) 0%, rgba(0,123,255,0.2) 100%);
                    border-radius: 15px;
                    padding: 2rem;
                    margin-bottom: 2rem;
                    text-align: center;
                }}
                .section-title {{ 
                    color: #00ff88; 
                    font-weight: bold; 
                    margin-bottom: 2rem;
                    position: relative;
                }}
                .section-title::after {{
                    content: '';
                    position: absolute;
                    bottom: -10px;
                    left: 0;
                    width: 50px;
                    height: 3px;
                    background: #00ff88;
                }}
            </style>
        </head>
        <body>
            <!-- Navigation -->
            <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
                <div class="container">
                    <a class="navbar-brand fw-bold" href="/">
                        <i class="fas fa-code text-success"></i> CyberCode
                    </a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav me-auto">
                            <li class="nav-item">
                                <a class="nav-link" href="/">
                                    <i class="fas fa-home"></i> Home
                                </a>
                            </li>
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="#" id="categoriesDropdown" role="button" data-bs-toggle="dropdown">
                                    <i class="fas fa-th-large"></i> Categories
                                </a>
                                <ul class="dropdown-menu bg-dark">
                                    {"".join([f'<li><a class="dropdown-item text-light" href="/category/{cat.id}"><i class="{cat.icon_class}"></i> {cat.name}</a></li>' for cat in all_categories])}
                                </ul>
                            </li>
                        </ul>
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/login">
                                    <i class="fas fa-sign-in-alt"></i> Login
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/admin-access">
                                    <i class="fas fa-cog"></i> Admin
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <!-- Main Content -->
            <div class="container" style="margin-top: 100px;">
                <!-- Category Header -->
                <div class="category-header">
                    <div class="row align-items-center">
                        <div class="col-md-2 text-center">
                            <i class="{category.icon_class} fa-4x text-success"></i>
                        </div>
                        <div class="col-md-10">
                            <h1 class="display-4 mb-2">{category.name}</h1>
                            <p class="lead mb-0">{category.description}</p>
                            <small class="text-muted">{len(products)} bot(s) available</small>
                        </div>
                    </div>
                </div>

                <!-- Products in This Category -->
                <div class="mb-5">
                    <h2 class="section-title">
                        <i class="{category.icon_class}"></i> {category.name} Collection
                    </h2>
                    <div class="row">
                        {products_html}
                    </div>
                </div>

                <!-- Explore Other Categories -->
                <div class="mb-5">
                    <h2 class="section-title">
                        <i class="fas fa-th-large"></i> Explore Other Categories
                    </h2>
                    <div class="row">
                        {other_categories_html}
                    </div>
                </div>

                <!-- Back to Home -->
                <div class="text-center mb-5">
                    <a href="/" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-home"></i> Back to Homepage
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <footer class="py-4 text-center text-muted">
                <div class="container">
                    <small>&copy; 2024 CyberCode Marketplace. Premium bot solutions for developers.</small>
                </div>
            </footer>

            <!-- Bootstrap JS -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

@app.route('/api/search')
def search_products():
    query = request.args.get('q', '').lower()
    products = Product.query.filter(
        Product.is_active == True,
        db.or_(
            Product.name.contains(query),
            Product.description.contains(query)
        )
    ).all()
    
    results = [{
        'id': p.id,
        'name': p.name,
        'description': p.description[:100] + '...' if len(p.description) > 100 else p.description,
        'price': p.price,
        'category': p.category.name
    } for p in products]
    
    return jsonify(results)

@app.route('/api/product/<int:product_id>/code-preview')
def get_code_preview(product_id):
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'success': True,
        'id': product.id,
        'name': product.name,
        'code_preview': product.code_preview or '# Code preview not available for this product'
    })

@app.route('/api/product/<int:product_id>/demo')
def get_product_demo(product_id):
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'success': True,
        'id': product.id,
        'name': product.name,
        'demo_video': product.demo_video_url,
        'description': product.description
    })

@app.route('/contact-telegram/<int:product_id>')
@login_required
def contact_telegram(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Create order record
    order = Order(
        user_id=current_user.id,
        product_id=product_id,
        status='contact_pending'
    )
    db.session.add(order)
    db.session.commit()
    
    # Telegram contact URL
    telegram_url = "https://t.me/Sujan_bhaiii"
    message = f"Hi! I'm interested in purchasing '{product.name}' from CyberCode Marketplace. Order ID: {order.id}"
    telegram_deep_link = f"{telegram_url}?text={message}"
    
    return render_template('telegram_contact.html', 
                         product=product, 
                         order=order,
                         telegram_url=telegram_deep_link)

@app.route('/dashboard')
@login_required
def user_dashboard():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('dashboard.html', orders=user_orders)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/change-language/<language>')
def change_language(language):
    session['language'] = language
    if current_user.is_authenticated:
        current_user.preferred_language = language
        db.session.commit()
    
    return redirect(request.referrer or url_for('index'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# WebSocket Events for Live Chat
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{current_user.name} has entered the chat.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{current_user.name} has left the chat.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    
    # Save message to database
    chat_msg = ChatMessage(
        user_id=current_user.id,
        message=message,
        room_id=room
    )
    db.session.add(chat_msg)
    db.session.commit()
    
    # Emit to room
    emit('message', {
        'user': current_user.name,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Context processors
@app.context_processor
def utility_processor():
    def format_datetime(dt, format_string='%Y-%m-%d %H:%M'):
        if dt:
            return dt.strftime(format_string)
        return ''
    
    def time_ago(dt):
        if not dt:
            return 'Unknown'
        
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    return dict(
        get_locale=get_locale,
        languages=app.config['LANGUAGES'],
        format_datetime=format_datetime,
        time_ago=time_ago,
        current_year=datetime.utcnow().year,
        datetime=datetime
    )

if __name__ == '__main__':
    import os
    
    try:
        with app.app_context():
            print("🔧 Setting up database...")
            db.create_all()
            
            # Only create sample data if database is empty
            if Category.query.count() == 0 or Product.query.count() == 0:
                print("📦 Database is empty, creating sample data...")
                create_sample_data()
            else:
                print("📦 Database already has data, skipping sample data creation")
                print(f"   📁 Categories: {Category.query.count()}")
                print(f"   🤖 Products: {Product.query.count()}")
    except Exception as e:
        print(f"⚠️ Database setup error: {e}")
        print("   💡 Try visiting /reset-database to fix this")
    
    # Railway deployment configuration
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"\n🚀 CyberCode Marketplace starting on {host}:{port}...")
    print("📊 Admin panel: /admin/")
    print("🔑 Admin access: /admin-access")
    print("🔄 Database reset: /reset-database")
    print("📁 Static files setup: /setup-static")
    print("💬 Live chat enabled")
    print("🌍 Multi-language support active")
    print("🔐 Google OAuth configured" if google else "⚠️  Google OAuth disabled (check credentials)")
    print("🧪 Manual admin login: /manual-login")
    print("\n🎯 Quick Access URLs:")
    print("   • Homepage: /")
    print("   • Admin Panel: /admin-access")
    print("   • Database Reset: /reset-database")
    print("   • Static Files Setup: /setup-static")
    print("   • Login: /login")
    print("\n📁 Static Files:")
    print("   • Create folder: static/images/")
    print("   • Add your images: telegram-bot.jpg, discord-bot.png, etc.")
    print("   • Use URLs: /static/images/telegram-bot.jpg")
    print("\n" + "="*50)
    
    # Use socketio.run for Railway
    socketio.run(app, debug=debug, host=host, port=port, allow_unsafe_werkzeug=True)