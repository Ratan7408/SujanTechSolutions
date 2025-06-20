// Matrix Rain Effect
function createMatrixRain() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.1';
    
    document.body.appendChild(canvas);
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const matrix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
    const matrixArray = matrix.split("");
    
    const fontSize = 10;
    const columns = canvas.width / fontSize;
    
    const drops = [];
    for(let x = 0; x < columns; x++) {
        drops[x] = 1;
    }
    
    function draw() {
        ctx.fillStyle = 'rgba(10, 10, 10, 0.04)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff88';
        ctx.font = fontSize + 'px JetBrains Mono';
        
        for(let i = 0; i < drops.length; i++) {
            const text = matrixArray[Math.floor(Math.random() * matrixArray.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            
            if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 35);
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Search functionality
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data);
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });
    
    // Hide search results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchResults.style.display = 'none';
        }
    });
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('search-results');
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result">No results found</div>';
    } else {
        searchResults.innerHTML = results.map(product => `
            <div class="search-result" onclick="viewDetails(${product.id})">
                <div class="search-result-title">${product.name}</div>
                <div class="search-result-category">${product.category}</div>
                <div class="search-result-price">$${product.price.toFixed(2)}</div>
            </div>
        `).join('');
    }
    
    searchResults.style.display = 'block';
}

// Filter functionality
function initFilters() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    const productCards = document.querySelectorAll('.product-card');
    
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Update active tab
            filterTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.dataset.filter;
            
            // Filter products
            productCards.forEach(card => {
                if (filter === 'all' || card.dataset.category === filter) {
                    card.style.display = 'block';
                    card.style.animation = 'fadeIn 0.5s ease-in-out';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

// Product actions
function viewDetails(productId) {
    window.location.href = `/product/${productId}`;
}

function viewDemo(productId) {
    // In a real implementation, you would fetch the actual code preview
    const products = [
        {
            id: 1,
            code: `# Telegram Admin Bot Preview
import telebot
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("👥 User Management", callback_data="users")
    btn2 = types.InlineKeyboardButton("📊 Analytics", callback_data="stats")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                    "🚀 Welcome to Admin Panel!", 
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "users":
        # User management logic
        bot.send_message(call.message.chat.id, "👥 User Management Panel")
    elif call.data == "stats":
        # Analytics logic
        bot.send_message(call.message.chat.id, "📊 Analytics Dashboard")

bot.infinity_polling()`
        },
        {
            id: 2,
            code: `# Discord Server Manager Preview
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'{bot.user} has landed!')

@bot.command()
async def role_auto(ctx, member: discord.Member, role: discord.Role):
    """Automatically assign roles"""
    await member.add_roles(role)
    await ctx.send(f"✅ Assigned {role.name} to {member.display_name}")

@bot.command()
async def security_scan(ctx):
    """Security monitoring"""
    guild = ctx.guild
    suspicious_users = []
    
    for member in guild.members:
        if member.created_at > discord.utils.utcnow() - discord.timedelta(days=7):
            suspicious_users.append(member)
    
    await ctx.send(f"🔍 Found {len(suspicious_users)} new accounts")

bot.run('YOUR_BOT_TOKEN')`
        },
        {
            id: 3,
            code: `# Crypto Trading Bot Preview
import ccxt
import pandas as pd
import numpy as np

class TradingBot:
    def __init__(self, exchange, api_key, secret):
        self.exchange = getattr(ccxt, exchange)({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': True  # Use sandbox for testing
        })
        
    def get_market_data(self, symbol, timeframe='1h', limit=100):
        """Fetch OHLCV data"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def trading_strategy(self, symbol):
        """Main trading logic"""
        df = self.get_market_data(symbol)
        df['rsi'] = self.calculate_rsi(df['close'])
        
        # Buy signal: RSI < 30 (oversold)
        # Sell signal: RSI > 70 (overbought)
        if df['rsi'].iloc[-1] < 30:
            return "BUY"
        elif df['rsi'].iloc[-1] > 70:
            return "SELL"
        else:
            return "HOLD"

# Initialize bot
bot = TradingBot('binance', 'your_api_key', 'your_secret')
signal = bot.trading_strategy('BTC/USDT')
print(f"Signal: {signal}")`
        },
        {
            id: 4,
            code: `# Social Media Automation Preview
import schedule
import time
import tweepy
import instagrapi
from datetime import datetime

class SocialMediaBot:
    def __init__(self):
        # Twitter API setup
        self.twitter_api = tweepy.Client(
            consumer_key="your_consumer_key",
            consumer_secret="your_consumer_secret",
            access_token="your_access_token",
            access_token_secret="your_access_token_secret"
        )
        
        # Instagram API setup
        self.instagram = instagrapi.Client()
        self.instagram.login("username", "password")
    
    def post_to_twitter(self, content):
        """Post to Twitter"""
        try:
            self.twitter_api.create_tweet(text=content)
            print(f"✅ Posted to Twitter: {content[:50]}...")
        except Exception as e:
            print(f"❌ Twitter error: {e}")
    
    def post_to_instagram(self, image_path, caption):
        """Post to Instagram"""
        try:
            self.instagram.photo_upload(image_path, caption)
            print(f"✅ Posted to Instagram")
        except Exception as e:
            print(f"❌ Instagram error: {e}")
    
    def get_analytics(self):
        """Get engagement analytics"""
        # Twitter analytics
        user = self.twitter_api.get_me()
        followers = user.data.public_metrics['followers_count']
        
        print(f"📊 Analytics Report:")
        print(f"Twitter Followers: {followers}")
        print(f"Last updated: {datetime.now()}")

# Initialize and run bot
bot = SocialMediaBot()
bot.schedule_posts()`
        },
        {
            id: 5,
            code: `# Web Scraping Suite Preview
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
from fake_useragent import UserAgent

class WebScrapingSuite:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.proxies = [
            "http://proxy1:port",
            "http://proxy2:port",
            "http://proxy3:port"
        ]
    
    def rotate_proxy(self):
        """Rotate proxy for requests"""
        proxy = random.choice(self.proxies)
        self.session.proxies = {"http": proxy, "https": proxy}
    
    def get_random_headers(self):
        """Generate random headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def scrape_ecommerce(self, url):
        """Scrape e-commerce products"""
        self.rotate_proxy()
        headers = self.get_random_headers()
        
        try:
            response = self.session.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = []
            for item in soup.find_all('div', class_='product-item'):
                product = {
                    'name': item.find('h3').text.strip(),
                    'price': item.find('span', class_='price').text.strip(),
                    'rating': len(item.find_all('i', class_='star-filled'))
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []

# Usage example
scraper = WebScrapingSuite()
products = scraper.scrape_ecommerce("https://example-store.com")`
        },
        {
            id: 6,
            code: `# File Organizer Pro Preview
import os
import shutil
import hashlib
from pathlib import Path
import magic

class FileOrganizerPro:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.file_types = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'music': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'code': ['.py', '.js', '.html', '.css', '.cpp', '.java']
        }
    
    def find_duplicates(self):
        """Find duplicate files"""
        file_hashes = {}
        duplicates = []
        
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                file_hash = self.get_file_hash(file_path)
                
                if file_hash in file_hashes:
                    duplicates.append({
                        'original': file_hashes[file_hash],
                        'duplicate': file_path
                    })
                else:
                    file_hashes[file_hash] = file_path
        
        return duplicates
    
    def organize_files(self):
        """Organize files into categories"""
        organized = {'moved': 0, 'errors': 0}
        
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                try:
                    category = self.classify_file(file_path)
                    
                    # Create category folder
                    category_path = self.base_path / category
                    category_path.mkdir(exist_ok=True)
                    
                    # Move file
                    new_path = category_path / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    organized['moved'] += 1
                    
                except Exception as e:
                    print(f"❌ Error moving {file_path}: {e}")
                    organized['errors'] += 1
        
        return organized

# Usage example
organizer = FileOrganizerPro("/path/to/messy/folder")
result = organizer.organize_files()
print(f"✅ Organized {result['moved']} files")`
        }
    ];
    
    const product = products.find(p => p.id === productId);
    if (product) {
        const modal = document.getElementById('demo-modal');
        const codePreview = document.getElementById('code-preview');
        codePreview.textContent = product.code;
        modal.style.display = 'block';
    }
}

function closeDemo() {
    const modal = document.getElementById('demo-modal');
    modal.style.display = 'none';
}

function purchaseProduct(productId) {
    // In a real implementation, this would redirect to payment gateway
    window.location.href = `/purchase/${productId}`;
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Intersection Observer for animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
            }
        });
    }, observerOptions);
    
    // Observe product cards
    document.querySelectorAll('.product-card').forEach(card => {
        observer.observe(card);
    });
    
    // Observe sections
    document.querySelectorAll('.section-title').forEach(title => {
        observer.observe(title);
    });
}

// Typing effect for hero text
function initTypingEffect() {
    const texts = [
        "PREMIUM SOFTWARE",
        "AUTOMATION SCRIPTS",
        "DEVELOPER TOOLS",
        "BOT FRAMEWORKS"
    ];
    
    const glitchText = document.querySelector('.glitch-text');
    if (!glitchText) return;
    
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    
    function typeWriter() {
        const currentText = texts[textIndex];
        
        if (isDeleting) {
            glitchText.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
        } else {
            glitchText.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
        }
        
        glitchText.setAttribute('data-text', glitchText.textContent);
        
        let typeSpeed = isDeleting ? 50 : 100;
        
        if (!isDeleting && charIndex === currentText.length) {
            typeSpeed = 2000; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            typeSpeed = 500; // Pause before starting new text
        }
        
        setTimeout(typeWriter, typeSpeed);
    }
    
    // Start after a delay
    setTimeout(typeWriter, 1000);
}

// Add CSS animations
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 8px 8px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        
        .search-result {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .search-result:hover {
            background: rgba(0, 255, 136, 0.1);
        }
        
        .search-result:last-child {
            border-bottom: none;
        }
        
        .search-result-title {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .search-result-category {
            font-size: 0.8rem;
            color: var(--accent-green);
            margin-bottom: 0.25rem;
        }
        
        .search-result-price {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
    `;
    document.head.appendChild(style);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    createMatrixRain();
    initSearch();
    initFilters();
    initSmoothScrolling();
    initScrollAnimations();
    initTypingEffect();
    addAnimationStyles();
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('demo-modal');
        if (event.target === modal) {
            closeDemo();
        }
    });
    
    // Add loading animation to buttons
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('loading')) {
                this.classList.add('loading');
                setTimeout(() => {
                    this.classList.remove('loading');
                }, 2000);
            }
        });
    });
});

// Add some console art for fun
console.log(`
 ██████╗██╗   ██╗██████╗ ███████╗██████╗  ██████╗ ██████╗ ██████╗ ███████╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║     ██║   ██║██║  ██║█████╗  
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║     ██║   ██║██║  ██║██╔══╝  
╚██████╗   ██║   ██████╔╝███████╗██║  ██║╚██████╗╚██████╔╝██████╔╝███████╗
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝

Welcome to CyberCode Marketplace!
Premium software solutions for developers.
`);

console.log("🚀 System initialized successfully");
console.log("💻 Ready for premium software deployment");
console.log("🔐 All systems secure and operational");