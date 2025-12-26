from flask import Flask
from mongoengine import connect
from flask_cors import CORS
from flask_compress import Compress
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Config
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev_key')
    app.config['COMPRESS_ALGORITHM'] = 'gzip'
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    
    # Extensions
    Compress(app)
    
    # Database Connection
    connect(host=os.getenv('MONGODB_URI'))
    
    # Extensions - CORS configuration (permissive for development)
    CORS(app, 
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:3000", 
                 "http://127.0.0.1:3000", 
                 "http://localhost:5000", 
                 "http://127.0.0.1:5000", 
                 "https://travel-frontend-cygy0u6x0-shamsullah123s-projects.vercel.app",
                 "https://travel-backend-jmld.onrender.com",
                 "https://travel-frontend-git-main-shamsullah123s-projects.vercel.app",
                 "https://travel-frontend-mocha.vercel.app"
              
             ],
             "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Auth-Token"],
             "expose_headers": ["Content-Type", "Authorization", "X-Auth-Token"],
             "supports_credentials": True
         }})
    
    # Register Blueprints
    from .api.auth import auth_bp
    from .api.customers import customers_bp
    from .api.visa_cases import visa_cases_bp
    from .api.quotations import quotations_bp
    from .api.accounting import accounting_bp
    from .api.bookings import bookings_bp # Register new blueprint
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(visa_cases_bp, url_prefix='/api/visa-cases')
    app.register_blueprint(quotations_bp, url_prefix='/api/quotations')
    app.register_blueprint(accounting_bp, url_prefix='/api/accounting')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings') # Register new blueprint
    
    from .api.agents import agents_bp
    app.register_blueprint(agents_bp, url_prefix='/api/agents')

    from .api.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from .api.agent_profiles import agent_profiles_bp
    app.register_blueprint(agent_profiles_bp, url_prefix='/api/agent-profiles')

    from .api.packages import packages_bp
    app.register_blueprint(packages_bp, url_prefix='/api/packages')
    
    from .api.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    from .api.facilities import facilities_bp
    app.register_blueprint(facilities_bp, url_prefix='/api/facilities')

    from .api.service_cards import service_cards_bp
    app.register_blueprint(service_cards_bp, url_prefix='/api/service-cards')

    from .api.contact import contact_bp
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    
    @app.route('/')
    def health_check():
        return {"status": "ok", "service": "Bannu Pilot Backend"}
        
    from app.api.feed import feed_bp
    app.register_blueprint(feed_bp, url_prefix='/api/feed')

    from app.api.admin_moderation import admin_moderation_bp
    app.register_blueprint(admin_moderation_bp, url_prefix='/api/admin')

    from app.api.notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    from app.api.media import media_bp
    app.register_blueprint(media_bp, url_prefix='/api/media')

    from app.api.financial_summary import financial_summary_bp
    app.register_blueprint(financial_summary_bp, url_prefix='/api/agency')

    from app.api.ticket_inventory import ticket_inventory_bp
    app.register_blueprint(ticket_inventory_bp, url_prefix='/api/ticket-groups')

    from app.api.ticket_bookings import ticket_bookings_bp
    app.register_blueprint(ticket_bookings_bp, url_prefix='/api/ticket-bookings')

    from app.api.profile import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/api/profile')

    from app.api.booking_actions import booking_actions_bp
    app.register_blueprint(booking_actions_bp, url_prefix='/api/bookings')

    from app.api.system_config import system_config_bp
    app.register_blueprint(system_config_bp, url_prefix='/api/system-config')

    from app.api.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/api/agency/reports')

    return app
