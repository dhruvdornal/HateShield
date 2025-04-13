import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import TextVectorization

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask import send_from_directory

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Load and preprocess training data
df = pd.read_csv("train.csv", encoding="utf-8")
X = df["comment_text"].astype(str)
label_columns = df.columns[2:].tolist()

# Text vectorization
MAX_FEATURES = 200000
vectorizer = TextVectorization(
    max_tokens=MAX_FEATURES,
    output_sequence_length=1800,
    output_mode='int'
)
vectorizer.adapt(X.values)

# Load pre-trained model
MODEL_PATH = "toxicity.h5"
model = keras.models.load_model(MODEL_PATH)


@app.route("/", methods=["GET"])
def demo():
    return render_template("scan.html")

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route("/test", methods=["GET"])
def home():
    return jsonify({"message": "Toxicity API is running on Hugging Face!"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text field provided"}), 400

    text = data["text"]
    vectorized_comment = vectorizer([text])
    results = model.predict(vectorized_comment)[0]

    response_dict = {col: bool(results[idx] > 0.5) for idx, col in enumerate(label_columns)}

    return jsonify({
        "input_text": text,
        "predictions": response_dict
    })

@app.route("/censor-post", methods=["POST"])
def censor_post():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text field provided"}), 400

    text = data["text"]
    words = text.split()
    censored_text = []

    for word in words:
        vectorized_word = vectorizer([word])
        results = model.predict(vectorized_word)[0]

        if results[label_columns.index("toxic")] > 0.5 or \
           results[label_columns.index("obscene")] > 0.5 or \
           results[label_columns.index("insult")] > 0.5:
            censored_text.append("****")
        else:
            censored_text.append(word)

    return jsonify({
        "original_text": text,
        "censored_text": " ".join(censored_text),
        "has_profanity": "****" in censored_text
    })

@app.route("/censor-posts", methods=["POST"])
def censor_posts():
    data = request.get_json()
    if not data or "posts" not in data:
        return jsonify({"error": "No posts provided"}), 400

    censored_posts = []

    for post in data["posts"]:
        text = post.get("text", "")
        words = text.split()
        censored_text = []

        for word in words:
            vectorized_word = vectorizer([word])
            results = model.predict(vectorized_word)[0]

            if results[label_columns.index("toxic")] > 0.5 or \
               results[label_columns.index("obscene")] > 0.5 or \
               results[label_columns.index("insult")] > 0.5:
                censored_text.append("****")
            else:
                censored_text.append(word)

        censored_posts.append({
            "id": post.get("id"),
            "original_text": text,
            "censored_text": " ".join(censored_text),
            "has_profanity": "****" in censored_text
        })

    return jsonify({"censored_posts": censored_posts})
