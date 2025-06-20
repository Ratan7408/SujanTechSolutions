from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Simple in-memory data for Vercel
CATEGORIES = [
    {"id": 1, "name": "Telegram Bots", "icon": "fab fa-telegram"},
    {"id": 2, "name": "Discord Bots", "icon": "fab fa-discord"},
    {"id": 3, "name": "Automation", "icon": "fas fa-robot"},
    {"id": 4, "name": "Trading", "icon": "fas fa-chart-line"},
    {"id": 5, "name": "Data Tools", "icon": "fas fa-database"},
    {"id": 6, "name": "Utilities", "icon": "fas fa-tools"}
]

PRODUCTS = [
    {"id": 1, "name": "Premium Telegram Bot", "price": 49.99, "category_id": 1},
    {"id": 2, "name": "Discord Server Manager", "price": 39.99, "category_id": 2},
    {"id": 3, "name": "Auto Trading Bot", "price": 99.99, "category_id": 4},
]

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SujanTech Solutions - Premium Bot Marketplace</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { 
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                color: white; 
                min-height: 100vh;
            }
            .hero-section {
                background: linear-gradient(135deg, rgba(0,255,136,0.1) 0%, rgba(0,123,255,0.1) 100%);
                padding: 4rem 0;
                margin-bottom: 3rem;
                border-radius: 20px;
            }
            .card { 
                background: rgba(255,255,255,0.05); 
                border: 1px solid rgba(0,255,136,0.2);
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            .card:hover { 
                transform: translateY(-5px); 
                border-color: #00ff88;
                box-shadow: 0 10px 30px rgba(0,255,136,0.2);
            }
            .text-success { color: #00ff88 !important; }
            .btn-success { background: #00ff88; border: none; color: #000; font-weight: bold; }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">
                    <i class="fas fa-code text-success"></i> SujanTech Solutions
                </a>
            </div>
        </nav>

        <!-- Hero Section -->
        <div class="container mt-4">
            <div class="hero-section text-center">
                <h1 class="display-3 fw-bold mb-4">
                    <i class="fas fa-rocket text-success"></i> Premium Bot Marketplace
                </h1>
                <p class="lead mb-4">Professional automation solutions and premium bots</p>
                <div class="row justify-content-center">
                    <div class="col-md-3 mb-3">
                        <div class="card text-center py-3">
                            <h4 class="text-success mb-1">6</h4>
                            <small class="text-muted">Categories</small>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card text-center py-3">
                            <h4 class="text-success mb-1">3</h4>
                            <small class="text-muted">Premium Bots</small>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card text-center py-3">
                            <h4 class="text-success mb-1">500+</h4>
                            <small class="text-muted">Downloads</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Categories -->
        <div class="container mb-5">
            <h2 class="text-success mb-4">
                <i class="fas fa-th-large"></i> Bot Categories
            </h2>
            <div class="row">
                {% for category in categories %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <div class="mb-3">
                                <i class="{{ category.icon }} fa-3x text-success"></i>
                            </div>
                            <h5 class="card-title text-white">{{ category.name }}</h5>
                            <p class="card-text text-muted">Professional {{ category.name.lower() }} solutions</p>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Products -->
        <div class="container mb-5">
            <h2 class="text-success mb-4">
                <i class="fas fa-star"></i> Featured Products
            </h2>
            <div class="row">
                {% for product in products %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{{ product.name }}</h5>
                            <p class="card-text text-muted flex-grow-1">Professional automation solution with advanced features.</p>
                            <div class="mt-auto">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span class="h5 text-success mb-0">${{ product.price }}</span>
                                    <small class="text-warning">
                                        <i class="fas fa-star"></i> 4.8/5
                                    </small>
                                </div>
                                <button class="btn btn-success w-100">
                                    <i class="fas fa-shopping-cart"></i> Buy Now
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <footer class="py-5 text-center text-muted">
            <div class="container">
                <p>&copy; 2024 SujanTech Solutions. Premium automation solutions.</p>
                <p>🚀 Deployed on Vercel | ⚡ Powered by Flask</p>
            </div>
        </footer>
    </body>
    </html>
    '''
    
    return render_template_string(html, categories=CATEGORIES, products=PRODUCTS)

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "SujanTech Solutions API is running!"}

# Vercel entry point
app = app