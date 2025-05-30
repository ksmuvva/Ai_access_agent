# 🤖 AI Accessibility Testing Agent - Setup Instructions

## 🔑 API Key Setup

### Step 1: Get Claude API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (starts with `sk-ant-...`)

### Step 2: Configure Environment
1. Open the `.env` file in this directory
2. Replace `your_claude_api_key_here` with your actual API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-api-key-here
   ```
3. Save the file

## 🚀 Usage Commands

### Interactive Chat Mode (Recommended)
```bash
python main.py chat
```

Then type natural language prompts:
- `check accessibility for https://example.com`
- `test keyboard navigation on https://github.com`
- `analyze color contrast for https://mysite.com`
- `run full accessibility audit on https://company.com`

### Direct Testing Commands
```bash
# Test with AI analysis
python main.py test "https://example.com" --agents all --output report.json

# Test specific functionality
python main.py test "https://example.com" --agents keyboard-focus --output keyboard_report.json
```

### List Available Agents
```bash
python main.py list-agents
```

## 🧠 How the AI Brain Works

The AI agents use Claude 3.5 Sonnet as their "brain" to:

1. **Understand Natural Language**: Convert user prompts into testing strategies
2. **Smart Agent Selection**: Choose appropriate agents based on the request
3. **Generate Insights**: Provide human-readable analysis of results
4. **Suggest Improvements**: Offer specific, actionable recommendations

## 📝 Example Session

```bash
PS> python main.py chat
🤖 AI Accessibility Testing Agent - Interactive Mode
💬 Type your accessibility testing requests (or 'quit' to exit)

👤 check accessibility for https://github.com
🧠 Analyzing your request with AI...
🎯 Target: https://github.com
🔍 Focus: comprehensive accessibility testing with emphasis on navigation and visual accessibility
🤖 Agents: keyboard-focus, color-contrast
💭 Running full accessibility audit to check keyboard navigation, focus management, color contrast, and WCAG 2.2 compliance

🤖 Starting AI Accessibility Testing for: https://github.com
📋 Using agents: keyboard-focus, color-contrast
...testing results...

💡 AI Insights:
============================================================
GitHub shows good accessibility practices overall. The site has:
- Proper focus indicators for keyboard navigation
- Adequate color contrast ratios
- Skip links for main content
- Minor issues found with some interactive elements

Recommended fixes:
1. Improve focus visibility on certain buttons
2. Add ARIA labels to complex UI components
3. Ensure all interactive elements are keyboard accessible
============================================================

📄 Full report saved to: accessibility_report_20250529_230256.json

👤 quit
👋 Goodbye!
```

## 🔧 Troubleshooting

### API Key Issues
- Ensure your API key is valid and active
- Check that you have sufficient credits in your Anthropic account
- Verify the key is correctly set in the `.env` file

### Connection Issues
- Check your internet connection
- Verify firewall isn't blocking API calls
- Try testing with a simple prompt first

### Installation Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## 🎯 Next Steps

Once configured, the AI agents can:
- Understand complex accessibility requests
- Provide detailed WCAG 2.2 compliance analysis
- Generate actionable improvement recommendations
- Learn from your testing patterns over time

The AI brain makes accessibility testing as simple as having a conversation with an expert!
