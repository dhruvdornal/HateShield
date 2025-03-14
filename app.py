import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import TextVectorization

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
# Configure CORS to allow requests from React frontend
# CORS(app, 
#      resources={
#          r"/*": {
#              "origins": ["http://localhost:3000"],  # Your React frontend URL
#              "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#              "allow_headers": ["Content-Type", "Authorization"],
#              "supports_credentials": True,
#              "expose_headers": ["Access-Control-Allow-Credentials"],
#              "allow_credentials": True
#          }
#      })

CORS(app, supports_credentials=True, origins="http://localhost:3000")


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# 1. Load and preprocess your training data (train.csv)
df = pd.read_csv("train.csv", encoding="utf-8")
X = df["comment_text"].astype(str)
label_columns = df.columns[2:].tolist()

# 2. Create and adapt a TextVectorization layer
MAX_FEATURES = 200000
vectorizer = TextVectorization(
    max_tokens=MAX_FEATURES,
    output_sequence_length=1800,
    output_mode='int'
)
vectorizer.adapt(X.values)

# 3. Load your pre-trained model (toxicity.h5)
MODEL_PATH = "toxicity.h5"
model = keras.models.load_model(MODEL_PATH)

# 4. Set up Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Toxicity API is running!"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text field provided"}), 400

    text = data["text"]
    vectorized_comment = vectorizer([text])
    results = model.predict(vectorized_comment)[0]

    response_dict = {}
    for idx, col in enumerate(label_columns):
        response_dict[col] = bool(results[idx] > 0.5)

    return jsonify({
        "input_text": text,
        "predictions": response_dict
    })

# New route to serve the HTML page
@app.route("/scan", methods=["GET"])
def scan_page():
    return render_template("scan.html")

@app.route("/process", methods=["POST"])
def process_text():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text field provided"}), 400

    words = data["text"].split()
    censored_text = []
    
    for word in words:
        vectorized_word = vectorizer([word])
        results = model.predict(vectorized_word)[0]
        
        # Check if the word is toxic, obscene, or insulting
        if results[label_columns.index("toxic")] > 0.5 or \
           results[label_columns.index("obscene")] > 0.5 or \
           results[label_columns.index("insult")] > 0.5:
            censored_text.append("****")
        else:
            censored_text.append(word)
    
    return jsonify({"censored_text": " ".join(censored_text)})

# Add new route for censoring posts
@app.route("/censor-post", methods=["POST"])
def censor_post():

    if request.method == 'OPTIONS':
        # CORS Preflight request handling
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

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

@app.route("/censor-posts", methods=["POST", "OPTIONS"])
def censor_posts():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
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
    
    response = jsonify({
        "censored_posts": censored_posts
    })
    # Ensure proper CORS headers are added to the response
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# # Add route for checking multiple posts
# @app.route("/censor-posts", methods=["POST"])
# def censor_posts():
#     data = request.get_json()
#     if not data or "posts" not in data:
#         return jsonify({"error": "No posts provided"}), 400

#     censored_posts = []
#     for post in data["posts"]:
#         text = post.get("text", "")
#         words = text.split()
#         censored_text = []
        
#         for word in words:
#             vectorized_word = vectorizer([word])
#             results = model.predict(vectorized_word)[0]
            
#             if results[label_columns.index("toxic")] > 0.5 or \
#                results[label_columns.index("obscene")] > 0.5 or \
#                results[label_columns.index("insult")] > 0.5:
#                 censored_text.append("****")
#             else:
#                 censored_text.append(word)
        
#         censored_posts.append({
#             "id": post.get("id"),
#             "original_text": text,
#             "censored_text": " ".join(censored_text),
#             "has_profanity": "****" in censored_text
#         })
    
#     return jsonify({
#         "censored_posts": censored_posts
#     })

@app.route('/test-cors', methods=['OPTIONS', 'POST'])
def test_cors():
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight successful"}), 200
    data = request.get_json()  # Just echo back the posted data for testing
    return jsonify({"received_data": data}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



# import os
# import pandas as pd
# import numpy as np
# import tensorflow as tf
# from tensorflow import keras
# from tensorflow.keras.layers import TextVectorization

# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS

# app = Flask(__name__)
# # Configure CORS to allow requests from React frontend
# CORS(app, resources={
#     r"/*": {
#         "origins": ["http://localhost:3000"],  # Your React frontend URL
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization","application/json"]
#     }
# })

# # 1. Load and preprocess your training data (train.csv)
# df = pd.read_csv("train.csv", encoding="utf-8")
# X = df["comment_text"].astype(str)
# label_columns = df.columns[2:].tolist()

# # 2. Create and adapt a TextVectorization layer
# MAX_FEATURES = 200000
# vectorizer = TextVectorization(
#     max_tokens=MAX_FEATURES,
#     output_sequence_length=1800,
#     output_mode='int'
# )
# vectorizer.adapt(X.values)

# # 3. Load your pre-trained model (toxicity.h5)
# MODEL_PATH = "toxicity.h5"
# model = keras.models.load_model(MODEL_PATH)

# # 4. Set up Flask
# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})

# @app.route("/", methods=["GET"])
# def home():
#     return jsonify({"message": "Toxicity API is running!"})

# @app.route("/predict", methods=["POST"])
# def predict():
#     data = request.get_json()
#     if not data or "text" not in data:
#         return jsonify({"error": "No text field provided"}), 400

#     text = data["text"]
#     vectorized_comment = vectorizer([text])
#     results = model.predict(vectorized_comment)[0]

#     response_dict = {}
#     for idx, col in enumerate(label_columns):
#         response_dict[col] = bool(results[idx] > 0.5)

#     return jsonify({
#         "input_text": text,
#         "predictions": response_dict
#     })

# # New route to serve the HTML page
# @app.route("/scan", methods=["GET"])
# def scan_page():
#     return render_template("scan.html")

# @app.route("/process", methods=["POST"])
# def process_text():
#     data = request.get_json()
#     if not data or "text" not in data:
#         return jsonify({"error": "No text field provided"}), 400

#     words = data["text"].split()
#     censored_text = []
    
#     for word in words:
#         vectorized_word = vectorizer([word])
#         results = model.predict(vectorized_word)[0]
        
#         # Check if the word is toxic, obscene, or insulting
#         if results[label_columns.index("toxic")] > 0.5 or \
#            results[label_columns.index("obscene")] > 0.5 or \
#            results[label_columns.index("insult")] > 0.5:
#             censored_text.append("****")
#         else:
#             censored_text.append(word)
    
#     return jsonify({"censored_text": " ".join(censored_text)})

# # Add new route for censoring posts
# @app.route("/censor-post", methods=["POST"])
# def censor_post():
#     data = request.get_json()
#     if not data or "text" not in data:
#         return jsonify({"error": "No text field provided"}), 400

#     text = data["text"]
#     words = text.split()
#     censored_text = []
    
#     for word in words:
#         vectorized_word = vectorizer([word])
#         results = model.predict(vectorized_word)[0]
        
#         if results[label_columns.index("toxic")] > 0.5 or \
#            results[label_columns.index("obscene")] > 0.5 or \
#            results[label_columns.index("insult")] > 0.5:
#             censored_text.append("****")
#         else:
#             censored_text.append(word)
    
#     return jsonify({
#         "original_text": text,
#         "censored_text": " ".join(censored_text),
#         "has_profanity": "****" in censored_text
#     })

# # Add route for checking multiple posts
# @app.route("/censor-posts", methods=["POST"])
# def censor_posts():
#     data = request.get_json()
#     if not data or "posts" not in data:
#         return jsonify({"error": "No posts provided"}), 400

#     censored_posts = []
#     for post in data["posts"]:
#         text = post.get("text", "")
#         words = text.split()
#         censored_text = []
        
#         for word in words:
#             vectorized_word = vectorizer([word])
#             results = model.predict(vectorized_word)[0]
            
#             if results[label_columns.index("toxic")] > 0.5 or \
#                results[label_columns.index("obscene")] > 0.5 or \
#                results[label_columns.index("insult")] > 0.5:
#                 censored_text.append("****")
#             else:
#                 censored_text.append(word)
        
#         censored_posts.append({
#             "id": post.get("id"),
#             "original_text": text,
#             "censored_text": " ".join(censored_text),
#             "has_profanity": "****" in censored_text
#         })
    
#     return jsonify({
#         "censored_posts": censored_posts
#     })

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
