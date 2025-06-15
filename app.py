from flask import Flask, render_template
from config import Config
from models import db
from routes import register_routes
import os
from datetime import datetime  # datetime ni import qilish

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register routes
    register_routes(app)
    # Root route for index page
    @app.route('/')
    def index():
        return render_template('index.html')
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    @app.context_processor
    def inject_global_variables():
        return {
            'app_name': app.config['APP_NAME'],
            'now': datetime.now() 
        }
    
    return app



# Create and initialize the database
def init_db(app):
    with app.app_context():
        db.create_all()
        
        # Add default admin user if not exists
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            from models import User
            admin = User(
                username='admin',
                password='admin123',  # This should be changed immediately after first login
                role='admin',
                first_name='Admin',
                last_name='User',
                email='admin@example.com'
            )
            db.session.add(admin)
            db.session.commit()
            print('Default admin user created. Username: admin, Password: admin123')
            print('Please change the password after first login!')

if __name__ == '__main__':
    app = create_app()
    init_db(app)
    app.run(debug=True)