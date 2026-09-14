from flask import Flask, render_template_string
from flask_pson import init_pson, jsonify_pson

app = Flask(__name__)
cfg = init_pson(app, "config.pson")

@app.route("/")
def index():
    # config.pson values available directly
    return render_template_string("""
    <h1>{{ config.app_name }}</h1>
    <p>Image size: {{ config.image_size }} (type: {{ config.image_size.__class__.__name__ }}) - tuple preserved!</p>
    <p>Features: {{ config.features }} (type: {{ config.features.__class__.__name__ }}) - set preserved!</p>
    <p>Upload path: {{ config.upload_path }}</p>
    <hr>
    <p>Filter test: {{ config.features|pson }}</p>
    """)

@app.route("/api/config")
def api_config():
    # Send as PSON (preserves types) instead of JSON that loses them
    return jsonify_pson(dict(app.config))

if __name__ == "__main__":
    app.run(debug=True)

