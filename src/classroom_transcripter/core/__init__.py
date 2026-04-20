"""Núcleo agnóstico de plataforma.

Contém tudo que é compartilhado entre Udemy, DIO e Alura:
- models: dataclasses do domínio (Course, Module, Lecture, Transcript)
- config: carregamento de .env e constantes
- exceptions: erros customizados
- utils: funções auxiliares (slugify, paths, etc.)
- vtt: parser WebVTT (usado por Udemy e Alura)
- formatters: saída em txt / obsidian
- enricher: enriquecimento com IA (Groq, Gemini, Ollama, Claude)
"""
