from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.parent_routes import parent_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(parent_bp)