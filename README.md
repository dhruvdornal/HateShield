# 🛡️ HateShield – Real-Time Hate Speech Detection Extension

**HateShield** is a browser extension that detects and censors hate speech in real-time as you browse social media platforms like X (Twitter), Reddit, and Instagram. Powered by a TensorFlow LSTM model and served through a Flask backend, HateShield helps create a safer online experience by automatically filtering offensive content.

🔗 **[Try Demo (Hugging Face)](https://ozymozy-toxi.hf.space)**  
⚙️ **Full extension available in the `/toxicity-filter-extension` folder**


## 🚀 Features

- **Real-time Detection**: Identifies hate speech as you browse
- **Multi-platform Support**: Works on X (Twitter), Reddit, Instagram and more
- **Seamless Integration**: Runs in the background without disrupting your browsing experience
- **TensorFlow-Powered**: Uses a trained LSTM model for accurate detection
- **Simple Controls**: Easy to enable/disable filtering with a toggle switch

## 📋 Requirements

- Google Chrome or any Chromium-based browser (Edge, Brave, etc.)
- Node.js and npm (for development only)
- Python 3.7+ and Flask (for running the backend locally)

## 🔧 Installation

### Install the Chrome Extension

1. **Clone this repository**
   ```bash
   git clone https://github.com/dhruvdornal/HateShield.git
   cd hateshield
   ```

2. **Open Chrome Extensions page**
   - Open Chrome
   - Go to `chrome://extensions/` in your browser
   - Enable "Developer mode" by toggling the switch in the top right corner

3. **Load the extension**
   - Click on "Load unpacked"
   - Navigate to the cloned repository and select the `/toxicity-filter-extension` folder
   - Click "Open"

4. **Verify installation**
   - HateShield should now appear in your extensions list
   - The HateShield icon should be visible in your browser toolbar

### Running the Backend (Optional - for development)

1. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Flask server**
   ```bash
   python app.py
   ```
   The backend will start running on `http://localhost:5000`

## 🔍 How It Works

1. HateShield monitors text content on supported websites
2. When new content appears, it sends the text to be analyzed by our API
3. The TensorFlow LSTM model evaluates the text for hate speech
4. If offensive content is detected, HateShield censors it in real-time
5. Users can click on censored content to reveal it if desired

## ⚙️ Configuration

Click on the HateShield extension icon in your browser toolbar to access settings:

- **Enable filtering**: Toggle switch to turn the filter on or off
- **API Endpoint**: Shows the current API endpoint being used (not editable)
- **Save Settings**: Button to save your configuration changes
- **Cache Settings**: View cache status and clear cached items as needed


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<p align="center">Made with ❤️ to promote safer online environment</p>
