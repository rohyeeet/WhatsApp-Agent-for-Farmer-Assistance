# Contributing to Kisan Mitra (किसान मित्र)

Thank you for your interest in contributing to Kisan Mitra! We welcome contributions from developers, agricultural experts, and community members.

## 🌾 Ways to Contribute

### 1. Code Contributions
- **Bug fixes**: Fix issues in existing tools or agent logic
- **New features**: Add new agricultural tools or capabilities
- **Performance improvements**: Optimize existing functionality
- **Documentation**: Improve code documentation and examples

### 2. Agricultural Expertise
- **Crop data**: Improve farming calendar and crop-specific information
- **Regional knowledge**: Add location-specific agricultural practices
- **Government schemes**: Update or add new agricultural schemes
- **Best practices**: Share modern farming techniques and knowledge

### 3. Language Support
- **Hindi improvements**: Enhance Hindi agricultural vocabulary
- **Regional languages**: Add support for Punjabi, Bengali, Tamil, etc.
- **Translation accuracy**: Improve technical term translations

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google ADK knowledge (basic)
- Git and GitHub familiarity
- Agricultural domain knowledge (preferred)

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/KisanMitra-ADK.git
   cd KisanMitra-ADK
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Add your API keys
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where applicable
- Write descriptive docstrings
- Keep functions focused and modular

### ADK Compatibility
- **No default parameters** in tool functions (ADK requirement)
- Hardcode file paths internally, don't use parameters
- Return proper Dict[str, Any] responses
- Handle errors gracefully with Hindi messages

### Tool Development
```python
def new_agricultural_tool() -> Dict[str, Any]:
    """Tool description in English.
    ADK Compatible - No parameters required.
    
    Returns:
        Dict[str, Any]: Tool response in Hindi
    """
    try:
        # Internal logic here
        return {
            "status": "success",
            "data": "response_data",
            "message": "हिंदी में संदेश"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error_message": f"त्रुटि: {str(e)}"
        }
```

### Language Guidelines
- **Primary language**: Hindi (Devanagari script)
- **Technical terms**: Use Hindi equivalents when available
- **Error messages**: Always in Hindi
- **Code comments**: English for international collaboration
- **Documentation**: English with Hindi examples

## 🧪 Testing

### Before Submitting
1. **Test with ADK**: Run `adk web --no-reload` and test functionality
2. **Check all tools**: Ensure all tools work without parameters
3. **Verify Hindi responses**: Confirm agent responds in Hindi
4. **Test error handling**: Verify graceful error responses

### Test Cases
- Tool functionality with farmer profile
- Tool functionality without farmer profile  
- Error handling and fallback mechanisms
- Hindi language consistency
- Regional price variations

## 📋 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Update CHANGELOG** with your changes
4. **Create descriptive PR title**:
   - `feat: add crop rotation planning tool`
   - `fix: mandi prices timeout issue`
   - `docs: improve Hindi vocabulary guide`

5. **PR Description Template**:
   ```markdown
   ## Changes Made
   - Describe your changes
   
   ## Testing Done
   - List testing performed
   
   ## Agricultural Impact
   - How this helps farmers
   
   ## Screenshots/Examples
   - Add if applicable
   ```

## 🌱 Agricultural Content Guidelines

### Farming Calendar
- Include crop varieties specific to regions
- Add seasonal timing recommendations
- Consider climate variations across India
- Use locally relevant agricultural practices

### Government Schemes
- Verify scheme accuracy and current status
- Include eligibility criteria clearly
- Add application process information
- Use official scheme names and details

### Market Intelligence
- Ensure price data accuracy
- Include seasonal price variations
- Add commodity grade considerations
- Consider regional market differences

## 🤝 Community Guidelines

### Be Respectful
- Respect diverse agricultural practices
- Consider farmer's economic constraints
- Use inclusive language
- Value traditional and modern knowledge

### Share Knowledge
- Explain agricultural concepts clearly
- Provide practical, actionable advice
- Share reliable sources and references
- Consider sustainability and environment

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create a GitHub Issue
- **Ideas**: Share in GitHub Discussions
- **Direct contact**: [Your contact method]

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Special thanks for agricultural expertise
- Community showcases

---

**Together, let's build technology that serves our farmers! 🚜🌾**

*"किसान हमारे अन्नदाता हैं - आइए मिलकर उनकी सेवा करें!"* 