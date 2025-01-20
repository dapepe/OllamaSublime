# OllamaSublime

OllamaSublime is a Sublime Text plugin that provides seamless integration with Ollama, allowing you to interact with AI models directly from your editor.

## Features

- 🤖 Direct integration with Ollama API
- 📝 Context-aware prompts using selected text or entire file
- 🔄 Streaming responses directly into your editor
- 📚 Template system for quick access to common prompts
- ⚡️ Keyboard shortcuts for quick access

## Installation

### Prerequisites

1. Install [Ollama](https://ollama.ai)
2. Have Sublime Text 3 or 4 installed
3. Have Package Control installed in Sublime Text

### Installation Steps

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Select "Package Control: Install Package"
3. Search for "OllamaSublime" and install

## Usage

### Basic Commands

- `Cmd/Ctrl + Shift + O`: Quick prompt input
- `Cmd/Ctrl + Shift + P` then type:
  - `OllamaSublime: Select Model` to choose an Ollama model
  - `OllamaSublime: Ask Prompt` to enter a prompt
  - `OllamaSublime: Use Template` to use a saved template
  - `OllamaSublime: Add Template` to save a new template
  - `OllamaSublime: Remove Template` to delete a template
  - `OllamaSublime: Settings` to configure the plugin

### Working with Context

1. Select text in editor (optional)
2. Use any of the prompt commands
3. If text is selected, it will be used as context
4. If no text is selected, the entire file content will be used

### Working with Templates

Templates allow you to save frequently used prompts for quick access.

To add a template:
1. Open Command Palette
2. Select "OllamaSublime: Add Template"
3. Enter template title
4. Enter template prompt

To use a template:
1. Open Command Palette
2. Select "OllamaSublime: Use Template"
3. Choose template from list
4. Edit prompt if needed
5. Press Enter to execute

## Configuration

Default settings can be modified through: Preferences > Package Settings > OllamaSublime > Settings

```json
{
  "ollamaUrl": "http://localhost:11434",
  "systemPrompt": "You are a helpful assistant.",
  "selected_model": "",
  "templates": [
    {
      "title": "Summarize",
      "prompt": "Summarize the text.",
      "model": "phi4:latest" // model is optional
    },
    {
      "title": "Translate",
      "prompt": "Translate the following text to French."
    }
  ]
}
```

### Settings Description

- `ollamaUrl`: URL where Ollama is running
- `systemPrompt`: Default system prompt for all requests
- `selected_model`: Currently selected Ollama model
- `templates`: Array of saved templates
  - `title`: Template name shown in selection menu
  - `prompt`: The prompt text
  - `model`: (Optional) Specific model for this template

## Requirements

- Sublime Text 3 or 4
- Ollama installed and running
- `requests` Python package (installed automatically)

## Troubleshooting

1. **No models available**
   - Ensure Ollama is running (`ollama serve`)
   - Check the Ollama URL in settings
   - Verify you have at least one model pulled (`ollama pull modelname`)

2. **Connection errors**
   - Check if Ollama is running
   - Verify the URL in settings
   - Check console for detailed error messages

3. **Slow responses**
   - Consider using a smaller/faster model
   - Check your system resources
   - Verify network connection

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request