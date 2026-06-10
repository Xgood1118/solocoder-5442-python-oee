from flask import Flask, jsonify
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes.oee_routes import oee_bp
    from routes.production_routes import production_bp
    from routes.downtime_routes import downtime_bp
    from routes.loss_routes import loss_bp
    from routes.report_routes import report_bp
    from routes.alert_routes import alert_bp

    app.register_blueprint(oee_bp, url_prefix='/api/oee')
    app.register_blueprint(production_bp, url_prefix='/api/production')
    app.register_blueprint(downtime_bp, url_prefix='/api/downtime')
    app.register_blueprint(loss_bp, url_prefix='/api/loss')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(alert_bp, url_prefix='/api/alert')

    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'OEE System is running'})

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=app.config['DEBUG'])
