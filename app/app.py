from flask import Flask

from api import api_bp
from exceptions import register_error_handlers
from models import init_db

app = Flask(__name__)

register_error_handlers(app)

app.register_blueprint(api_bp)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
