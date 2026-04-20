"""Configuração global e carregamento de `.env`.

MIGRAÇÃO (Fase 2):
-----------------
Copiar aqui o conteúdo atual de `udemy_transcripter/config.py`, mantendo:
- Função de carregar `.env` (python-dotenv)
- Constantes de paths padrão (OUTPUT_DIR, CACHE_DIR)
- Leitura de variáveis: UDEMY_COOKIE, GROQ_API_KEY, GEMINI_API_KEY,
  CLAUDE_API_KEY, OLLAMA_URL, ...

ADICIONAR (novo, pra multi-plataforma):
- ALURA_EMAIL, ALURA_PASSWORD (ou ALURA_TOKEN)
- DIO_VIDEO_DIR (pasta padrão onde o usuário baixa os .mp4)
- WHISPER_MODEL (padrão: "small"), WHISPER_LANGUAGE (padrão: "pt")

Estrutura sugerida:
    from pathlib import Path
    from dotenv import load_dotenv
    import os

    load_dotenv()

    DEFAULT_OUTPUT_DIR = Path("./transcripts")

    # Udemy
    UDEMY_COOKIE = os.getenv("UDEMY_COOKIE", "")

    # DIO
    DIO_VIDEO_DIR = Path(os.getenv("DIO_VIDEO_DIR", "./dio_videos"))
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

    # Alura
    ALURA_EMAIL = os.getenv("ALURA_EMAIL", "")
    ALURA_PASSWORD = os.getenv("ALURA_PASSWORD", "")

    # Providers de IA (compartilhado)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", "")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
"""
# TODO Fase 2: migrar conteúdo de udemy_transcripter/config.py
