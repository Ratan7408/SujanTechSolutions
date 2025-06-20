from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SujanTech Solutions</title>
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
                margin: 3rem 0;
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
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">
                    <i class="fas fa-code text-success"></i> SujanTech Solutions
                </a>
            </div>
        </nav>

        <div class="container">
            <div class="hero-section text-center">
                <h1 class="display-3 fw-bold mb-4">
                    <i class="fas fa-rocket text-success"></i> Premium Bot Marketplace
                </h1>
                <p class="lead mb-4">🚀 Professional automation solutions and premium bots</p>
                <div class="row justify-content-center">
                    <div class="col-md-4 mb-3">
                        <div class="card text-center py-3">
                            <h4 class="text-success mb-1">✅ LIVE</h4>
                            <small class="text-muted">Deployed Successfully!</small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <i class="fab fa-telegram fa-3x text-success mb-3"></i>
                            <h5 class="card-title">Telegram Bots</h5>
                            <p class="card-text">Advanced automation bots</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <i class="fab fa-discord fa-3x text-success mb-3"></i>
                            <h5 class="card-title">Discord Bots</h5>
                            <p class="card-text">Server management solutions</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-robot fa-3x text-success mb-3"></i>
                            <h5 class="card-title">Automation</h5>
                            <p class="card-text">Workflow automation tools</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="py-5 text-center text-muted">
            <div class="container">
                <p>&copy; 2024 SujanTech Solutions | 🚀 Deployed on Vercel</p>
            </div>
        </footer>
    </body>
    </html>
    ''')

@app.route('/about')
def about():
    return render_template_string('''
    <h1>About SujanTech Solutions</h1>
    <p>Premium bot marketplace for automation solutions!</p>
    <a href="/">← Back to Home</a>
    ''')

# This is needed for Vercel
if __name__ == "__main__":
    app.run()