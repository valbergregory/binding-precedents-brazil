# Prompts (versioned measurement instruments)

Any local LLM used to label or extract information from decisions is a measurement instrument.
Each prompt version lives in its own folder, `prompts/vNN/`, with:

- `prompt.txt` — the exact text sent to the model;
- `config.yml` — model name and tag (Ollama) or Hugging Face id and revision hash, temperature
  (always 0), seed, context length, date;
- `validation.csv` — metrics against the gold standard (`annotations` table): precision, recall,
  F1 per class, α/κ when a second annotator exists.

No prompt exists yet (Phase 0). Only local models are used (Ollama `llama3.1:8b`, `qwen2.5:7b`
already installed on the reference machine) unless the author authorises a paid API in writing.
