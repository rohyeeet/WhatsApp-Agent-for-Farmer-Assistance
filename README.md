# 🌾 Kisan Mitra (किसान मित्र) - ADK Agent

**Your Trusted Agricultural Advisor and Friend**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google-ADK-green.svg)](https://developers.google.com/adk)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

Kisan Mitra is an advanced multilingual agricultural assistant built using Google's Agent Development Kit (ADK). It serves as a comprehensive digital companion for Indian farmers, providing expert guidance across all aspects of modern agriculture.

### 🌟 Key Features

<img width="934" height="336" alt="image" src="https://github.com/user-attachments/assets/c33d981b-7d38-42a1-8b9c-fb4549fe56f8" />

- **🌦️ Weather Intelligence**: Real-time weather updates and agricultural forecasts
  
- **📅 Farming Calendar**: Comprehensive seasonal farming advice and crop-specific guidance

<img width="918" height="579" alt="image" src="https://github.com/user-attachments/assets/ba59a4dc-9d78-47fb-9fdb-fbc05dd8cf7e" />

- **🏛️ Government Schemes**: Complete database of agricultural schemes and subsidies
  
- **💰 Market Intelligence**: Live mandi prices and commodity market trends
  
<img width="928" height="789" alt="image" src="https://github.com/user-attachments/assets/20efd6df-f39b-48b6-baae-cb3d68fe8f99" />
<img width="931" height="799" alt="image" src="https://github.com/user-attachments/assets/350b61d5-189f-4457-938d-bad66a266e8b" />

- **🌱 Disease Detection**: AI-powered crop disease diagnosis with image analysis

<img width="933" height="369" alt="image" src="https://github.com/user-attachments/assets/098a37c3-da7b-476c-a623-e0c7deda81f5" />

- **🗣️ Multilingual & Voice-to-Voice Support**: Native Hindi support with regional language capabilities, enabling seamless voice-based interactions through Gemini-powered Speech-to-Text (STT) and Text-to-Speech (TTS) services.
- **👤 Farmer Profiles**: Personalized advice based on farmer's location, crops, and resources

## 🔧 Technical Architecture


<img width="1461" height="825" alt="image" src="https://github.com/user-attachments/assets/bfd9cf0d-b494-4d77-a6d6-c9f16ab78be5" />
### Core Technologies
- **Google ADK (Agent Development Kit)**: Advanced AI agent framework
- **Gemini 2.0 Flash**: Latest multimodal AI model with vision capabilities
- **Python 3.8+**: Modern Python development
- **Playwright**: Web scraping for real-time data
- **OpenWeather API**: Weather data integration

### Agent Capabilities
- **Built-in Vision**: Direct image analysis for crop disease detection
- **Tool Integration**: 14+ specialized agricultural tools
- **Context Awareness**: Farmer profile-based personalization
- **Error Resilience**: Robust fallback mechanisms

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google API Key (for ADK)
- OpenWeather API Key (optional, for weather features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/surajvaraha/KisanMitra-ADK.git
   cd KisanMitra-ADK
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

6. **Run the agent**
   ```bash
   adk web --no-reload
   ```

## 📁 Project Structure

```
KisanMitra-ADK/
├── kisan_mitra/
│   └── agent.py              # Main agent definition
├── tools/                    # Modular tool implementations
│   ├── __init__.py
│   ├── weather_tool.py       # Weather intelligence
│   ├── farming_calendar_tool.py
│   ├── agriculture_schemes_tool.py
│   ├── farmer_context_tools.py
│   └── mandi_prices_tool.py  # Market price intelligence
├── context/                  # Data and configurations
│   ├── farmer_profile.json   # Sample farmer profile
│   ├── farming_calendar_dataset.json
│   └── agriculture_schemes.json
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠️ Available Tools

### 1. Weather Tools
- `get_farmer_weather()`: Auto weather for farmer's location
- `get_agricultural_weather(location)`: Weather for specific locations

### 2. Farming Calendar Tools
- `get_farming_calendar_advice()`: Seasonal farming guidance
- `get_crop_specific_calendar()`: Detailed crop information

### 3. Agriculture Schemes Tools
- `get_relevant_schemes_for_farmer()`: Personalized recommendations
- `get_scheme_details(scheme_name)`: Detailed scheme information
- `list_all_available_schemes()`: Complete schemes database

### 4. Market Intelligence Tools
- `get_farmer_mandi_prices()`: Today's prices for farmer's location
- `get_mandi_prices_for_date(date)`: Historical price data
- `get_commodity_price_info(commodity)`: Specific commodity prices

### 5. Farmer Context Tools
- `load_farmer_profile()`: Profile management
- `get_farmer_context_summary()`: Quick farmer overview
- `get_crop_specific_context(crop)`: Crop-based insights
- `get_seasonal_recommendations()`: Season-specific advice

### 6. Disease Detection
- **Built-in Gemini Vision**: Direct image analysis for disease identification

## 💬 Usage Examples

### Hindi Conversations
```
User: "आज मौसम कैसा रहेगा?"
Kisan Mitra: "राज कुमार जी, आज मुजफ्फरनगर में तापमान 18-25°C रहेगा..."

User: "गेहूं का भाव क्या है?"
Kisan Mitra: "आज गेहूं का भाव ₹2,200-2,310 प्रति क्विंटल है..."

User: [Shares crop disease image]
Kisan Mitra: "मैं आपकी फसल की तस्वीर देख रहा हूँ। यह पत्ती पर फफूंद रोग है..."
```

### English Support
```
User: "What government schemes are available for cotton farmers?"
Kisan Mitra: Will respond in farmer's preferred language (Hindi) based on profile
```

## 🔧 Configuration

### Environment Variables (.env)
```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_google_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### Farmer Profile (context/farmer_profile.json)
Configure farmer details for personalized responses:
- Personal information
- Location details (state, district, village)
- Farm details (size, crops, irrigation)
- Economic profile
- Language preferences
- Agricultural practices

## 🤝 Contributing

We welcome contributions to improve Kisan Mitra! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google ADK Team**: For the powerful Agent Development Kit
- **Indian Agricultural Community**: For inspiration and feedback
- **Open Source Contributors**: For tools and libraries used

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/surajvaraha/KisanMitra-ADK/issues)
- **Discussions**: [GitHub Discussions](https://github.com/surajvaraha/KisanMitra-ADK/discussions)
- **Email**: [Your Contact Email]

---

**"किसान हमारे अन्नदाता हैं - हमारा कर्तव्य है उनकी सेवा करना!"**  
*"Farmers are our food providers - it is our duty to serve them!"*

---

Made with ❤️ for Indian Farmers 🇮🇳 
