# Kashiza AI Providers Guide

Kashiza supports multiple AI providers for maximum flexibility and cost optimization.

## Supported Providers

| Provider | Type | Best For | Pricing |
|----------|------|----------|---------|
| **Anthropic** | Cloud | Complex reasoning, long context | $$$ |
| **OpenAI** | Cloud | General tasks, vision | $$$ |
| **Google** | Cloud | Long context (2M tokens) | $$ |
| **Groq** | Cloud | Fast inference, low latency | $ |
| **Kimi** | Cloud | Chinese/English, reasoning | $$ |
| **DeepSeek** | Cloud | Coding, cost-effective | $ |
| **Ollama** | Local | Privacy, zero cost | FREE |
| **OpenRouter** | Gateway | Unified access to many models | Varies |

---

## Quick Setup

### 1. Cloud Providers

Add your API keys to `.env`:

```bash
# Required: At least one provider
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...
KIMI_API_KEY=...
DEEPSEEK_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

### 2. Local Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.2
ollama pull qwen2.5-coder
ollama pull mistral

# Start server (default: localhost:11434)
ollama serve
```

Set in `.env` (optional, defaults to localhost):
```bash
OLLAMA_HOST=http://localhost:11434
```

---

## CLI Commands

### List configured providers
```bash
kashiza providers list
```

### List all available models
```bash
kashiza providers models
```

### Get model recommendation
```bash
kashiza providers recommend high quality
```

### Compare models
```bash
kashiza providers compare
```

### Test provider connection
```bash
kashiza providers test deepseek
```

---

## Provider Details

### Anthropic (Claude)
- **Models**: claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-3.5-sonnet
- **Strengths**: Complex reasoning, long context (200k), coding
- **Get key**: https://console.anthropic.com

### OpenAI (GPT)
- **Models**: gpt-4o, gpt-4o-mini, gpt-4-turbo, o1-preview, o1-mini
- **Strengths**: Vision, general tasks, JSON mode
- **Get key**: https://platform.openai.com

### Google (Gemini)
- **Models**: gemini-1.5-pro (2M context!), gemini-1.5-flash
- **Strengths**: Massive context window, multimodal
- **Get key**: https://aistudio.google.com/app/apikey

### Groq
- **Models**: llama-3.1-70b, llama-3.1-8b, mixtral-8x7b, gemma2-9b
- **Strengths**: Extremely fast inference, cheap
- **Get key**: https://console.groq.com/keys

### Kimi (Moonshot AI)
- **Models**: kimi-k2.5, kimi-k1-6, kimi-k1-6-thinking
- **Strengths**: Chinese/English bilingual, reasoning
- **Get key**: https://platform.moonshot.cn

### DeepSeek
- **Models**: deepseek-chat, deepseek-coder, deepseek-reasoner
- **Strengths**: Excellent for coding, very cheap
- **Get key**: https://platform.deepseek.com

### Ollama (Local)
- **Models**: llama3.2, qwen2.5, mistral, codellama, phi4
- **Strengths**: 100% private, zero cost, offline capable
- **Install**: https://ollama.com

### OpenRouter
- **Models**: Access to 100+ models via single API
- **Strengths**: Unified interface, automatic failover
- **Get key**: https://openrouter.ai/keys

---

## Auto-Selection

Kashiza automatically selects the best available model based on:

1. **Task complexity** (low/medium/high)
2. **Priority** (cost/quality/speed/balanced)
3. **Available providers**
4. **Budget constraints**

Example:
```python
# Automatically uses cheapest available model for simple task
# Automatically uses Claude/GPT-4 for complex architecture tasks
```

---

## Cost Optimization Tips

1. **Use Groq or DeepSeek** for high-volume, simple tasks
2. **Use Ollama** for privacy-sensitive work
3. **Enable auto-switch** in config to use cheaper alternatives
4. **Set budget alerts** to track spending

---

## Docker Compose

For Ollama in Docker, add to `docker-compose.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    
volumes:
  ollama-data:
```

Update `OLLAMA_HOST=http://ollama:11434` in `.env`.

---

## Troubleshooting

### Provider not detected
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Test provider
kashiza providers test anthropic
```

### Ollama connection failed
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check OLLAMA_HOST env var
echo $OLLAMA_HOST
```

### Model not available
- Verify API key has access to the model
- Check provider's model availability in your region
- Use `providers compare` to see all available models
