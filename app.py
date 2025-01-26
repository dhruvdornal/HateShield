import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import TextVectorization

from flask import Flask, request, jsonify
from flask_cors import CORS

# 1. Load and preprocess your training data (train.csv)
df = pd.read_csv("train.csv", encoding="utf-8")  # Ensure train.csv is in the same folder
X = df["comment_text"].astype(str)
# Suppose your label columns are all columns from index 2 onward:
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
#    Make sure toxicity.h5 is also in the same folder (or provide the correct path).
MODEL_PATH = "toxicity.h5"
model = keras.models.load_model(MODEL_PATH)

# 4. Set up Flask
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests if you need them

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Toxicity API is running!"})

@app.route("/predict", methods=["POST"])
def predict():
    """
    Expects JSON like:
      {
        "text": "some comment here"
      }
    Returns JSON with each label and whether it's True/False.
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text field provided"}), 400

    text = data["text"]

    # 5. Vectorize the incoming text
    vectorized_comment = vectorizer([text])  # shape (1, 1800)

    # 6. Run model prediction
    results = model.predict(vectorized_comment)[0]  # shape (num_labels,)

    # 7. Build a response dict indicating True/False for each label
    #    E.g. label_columns might be ["toxic", "obscene", "threat", ...]
    response_dict = {}
    for idx, col in enumerate(label_columns):
        response_dict[col] = bool(results[idx] > 0.5)

    return jsonify({
        "input_text": text,
        "predictions": response_dict
    })

if __name__ == "__main__":
    # 8. Run on port 5000, accessible via 0.0.0.0
    app.run(host="0.0.0.0", port=5000, debug=True)
