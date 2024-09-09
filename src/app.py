from . import create_app
import os

app = create_app(os.environ.get("FLASK_ENV"))

if __name__ == "__main__":

    app.run(debug=True)

