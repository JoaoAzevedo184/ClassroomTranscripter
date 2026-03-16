#!/usr/bin/env python3
"""
Udemy Transcript Extractor
Extrai transcrições/legendas de cursos que você comprou na Udemy.

Uso:
  # Com .env (recomendado)
  python udemy_transcripts.py --url "https://www.udemy.com/course/SLUG/"

  # Ou passando o cookie diretamente
  python udemy_transcripts.py --cookie "COOKIE_STRING" --url "https://www.udemy.com/course/SLUG/"

Configuração (.env):
  Crie um arquivo .env no mesmo diretório com:
    UDEMY_COOKIES=sua_cookie_string_completa_aqui

Como obter os cookies:
  1. Abra a Udemy no navegador e faça login
  2. Abra o DevTools (F12) → Network
  3. Acesse qualquer página do curso
  4. Clique em alguma requisição para udemy.com
  5. Em "Request Headers", copie o valor COMPLETO do header "Cookie"
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

import requests
from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv


# ─── Configuração ───────────────────────────────────────────────────────────

BASE_URL = "https://www.udemy.com"
API_BASE = f"{BASE_URL}/api-2.0"

HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL,
}

LANG_PRIORITY = ["pt", "pt-BR", "en", "en_US", "en_GB", "es"]


# ─── Modelos de Dados ──────────────────────────────────────────────────────

@dataclass
class Caption:
    locale: str
    url: str
    label: str


@dataclass
class Lecture:
    id: int
    title: str
    object_index: int
    captions: list[Caption] = field(default_factory=list)


@dataclass
class Section:
    title: str
    index: int
    lectures: list[Lecture] = field(default_factory=list)


# ─── Cliente da API ─────────────────────────────────────────────────────────

class UdemyClient:
    def __init__(self, cookie_data: str, debug: bool = False):
        # Usa curl_cffi que imita o TLS fingerprint do Chrome
        # Isso é necessário para passar pelo Cloudflare
        self.session = cffi_requests.Session(impersonate="chrome")
        self.debug = debug

        cookie_data = cookie_data.strip()
        # Remove prefixo "Cookie: " se presente
        if cookie_data.lower().startswith("cookie:"):
            cookie_data = cookie_data[7:].strip()

        self._raw_cookies = cookie_data

        # Monta os headers
        headers = dict(HEADERS_BASE)

        # Se contém ";" é uma cookie string completa do navegador
        if ";" in cookie_data:
            # Envia o Cookie header diretamente (mais confiável que cookie jar)
            headers["Cookie"] = cookie_data
            # Extrai o access_token individual para o header Authorization
            at = self._extract_cookie_value(cookie_data, "access_token")
            if at:
                headers["Authorization"] = f"Bearer {at}"
                headers["X-Udemy-Authorization"] = f"Bearer {at}"
            else:
                print("⚠ Aviso: access_token não encontrado nos cookies.")
        else:
            # Token simples (access_token apenas)
            token = cookie_data.strip('"').strip("'")
            headers["Authorization"] = f"Bearer {token}"
            headers["X-Udemy-Authorization"] = f"Bearer {token}"
            headers["Cookie"] = f"access_token={token}"

        self.session.headers.update(headers)

    @staticmethod
    def _extract_cookie_value(cookie_string: str, name: str) -> str | None:
        """Extrai o valor de um cookie específico da string."""
        for pair in cookie_string.split(";"):
            pair = pair.strip()
            if pair.startswith(f"{name}="):
                raw = pair.partition("=")[2].strip()
                # Remove aspas ao redor
                if (raw.startswith('"') and raw.endswith('"')):
                    raw = raw[1:-1]
                return raw
        return None

    def _get(self, url: str, params: dict = None) -> dict:
        if self.debug:
            print(f"  [DEBUG] GET {url}")
            if params:
                print(f"  [DEBUG] Params: {params}")

        resp = self.session.get(url, params=params)

        if self.debug:
            print(f"  [DEBUG] Status: {resp.status_code}")
            if resp.status_code >= 400:
                print(f"  [DEBUG] Response: {resp.text[:500]}")

        if resp.status_code == 403:
            print("✗ Erro 403: Acesso negado (Cloudflare).")
            print("  Possíveis causas:")
            print("    1. Cookies expirados — copie novos do navegador")
            print("    2. Curso não comprado — verifique se você tem acesso")
            print("    3. cf_clearance ausente — copie TODOS os cookies do header Cookie")
            print()
            print("  Dica: Use --debug para ver detalhes da requisição")
            sys.exit(1)
        elif resp.status_code == 401:
            print("✗ Erro 401: Token inválido ou expirado.")
            print("  Gere novos cookies no navegador.")
            sys.exit(1)
        resp.raise_for_status()
        return resp.json()

    def get_course_id(self, slug: str) -> tuple[int, str]:
        """Retorna (course_id, title) a partir do slug."""
        data = self._get(f"{API_BASE}/courses/{slug}/", params={
            "fields[course]": "id,title,locale"
        })
        return data["id"], data["title"]

    def get_curriculum(self, course_id: int) -> list[Section]:
        """Busca toda a grade do curso organizada por seções."""
        sections: list[Section] = []
        current_section = Section(title="Introdução", index=0)
        page_url = (
            f"{API_BASE}/courses/{course_id}/subscriber-curriculum-items/"
        )
        params = {
            "page_size": 200,
            "fields[lecture]": "id,title,object_index,asset",
            "fields[chapter]": "title,object_index",
            "fields[asset]": "captions",
        }

        while page_url:
            data = self._get(page_url, params=params)
            params = None  # Próximas páginas já têm params na URL

            for item in data.get("results", []):
                _class = item.get("_class")

                if _class == "chapter":
                    if current_section.lectures:
                        sections.append(current_section)
                    current_section = Section(
                        title=item.get("title", "Sem título"),
                        index=item.get("object_index", 0),
                    )

                elif _class == "lecture":
                    captions = []
                    asset = item.get("asset", {})
                    for cap in asset.get("captions", []):
                        captions.append(Caption(
                            locale=cap.get("locale_id", "unknown"),
                            url=cap.get("url", ""),
                            label=cap.get("title", cap.get("locale_id", "")),
                        ))
                    lecture = Lecture(
                        id=item["id"],
                        title=item.get("title", "Sem título"),
                        object_index=item.get("object_index", 0),
                        captions=captions,
                    )
                    current_section.lectures.append(lecture)

            page_url = data.get("next")

        if current_section.lectures:
            sections.append(current_section)

        return sections


# ─── Processamento de VTT ──────────────────────────────────────────────────

def parse_vtt(text: str) -> list[dict]:
    """
    Faz parse de um arquivo VTT e retorna lista de
    {'start': str, 'end': str, 'text': str}.
    """
    entries = []
    blocks = re.split(r"\n\n+", text.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        # Procura a linha de timestamp
        timestamp_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                timestamp_line = line
            elif timestamp_line and line.strip():
                text_lines.append(line.strip())

        if timestamp_line and text_lines:
            parts = timestamp_line.split("-->")
            entries.append({
                "start": parts[0].strip(),
                "end": parts[1].strip().split(" ")[0],
                "text": " ".join(text_lines),
            })

    return entries


def vtt_to_plain_text(vtt_content: str) -> str:
    """Converte VTT em texto limpo, removendo duplicatas de legendas."""
    entries = parse_vtt(vtt_content)
    seen = set()
    lines = []
    for entry in entries:
        clean = re.sub(r"<[^>]+>", "", entry["text"]).strip()
        if clean and clean not in seen:
            seen.add(clean)
            lines.append(clean)
    return " ".join(lines)


def vtt_to_timestamped(vtt_content: str) -> str:
    """Converte VTT em texto com timestamps para referência."""
    entries = parse_vtt(vtt_content)
    lines = []
    seen = set()
    for entry in entries:
        clean = re.sub(r"<[^>]+>", "", entry["text"]).strip()
        if clean and clean not in seen:
            seen.add(clean)
            ts = entry["start"].split(".")[0]  # Remove milissegundos
            lines.append(f"[{ts}] {clean}")
    return "\n".join(lines)


# ─── Seleção de Idioma ─────────────────────────────────────────────────────

def pick_caption(captions: list[Caption], preferred_lang: str = None) -> Caption | None:
    """Escolhe a melhor legenda disponível baseado na preferência."""
    if not captions:
        return None

    if preferred_lang:
        for cap in captions:
            if cap.locale.lower().startswith(preferred_lang.lower()):
                return cap

    for lang in LANG_PRIORITY:
        for cap in captions:
            if cap.locale.lower().startswith(lang.lower()):
                return cap

    return captions[0]


# ─── Sanitização de Nomes ──────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:100]


# ─── Download e Salvamento ─────────────────────────────────────────────────

def download_transcripts(
    client: UdemyClient,
    slug: str,
    output_dir: str,
    lang: str = None,
    with_timestamps: bool = False,
    merge: bool = False,
):
    print(f"\n🎓 Buscando informações do curso: {slug}")
    course_id, course_title = client.get_course_id(slug)
    print(f"   Título: {course_title}")
    print(f"   ID: {course_id}")

    print("\n📚 Carregando grade curricular...")
    sections = client.get_curriculum(course_id)

    total_lectures = sum(len(s.lectures) for s in sections)
    lectures_with_caps = sum(
        1 for s in sections for l in s.lectures if l.captions
    )
    print(f"   {len(sections)} seções, {total_lectures} aulas")
    print(f"   {lectures_with_caps} aulas com transcrição disponível")

    if lectures_with_caps == 0:
        print("\n⚠ Nenhuma transcrição encontrada neste curso.")
        print("  Isso pode acontecer se o curso não tiver legendas.")
        return

    course_dir = Path(output_dir) / sanitize_filename(course_title)
    course_dir.mkdir(parents=True, exist_ok=True)

    merged_content = []
    downloaded = 0
    errors = 0

    for section in sections:
        section_name = f"{section.index:02d} - {sanitize_filename(section.title)}"
        section_dir = course_dir / section_name
        section_dir.mkdir(exist_ok=True)

        if merge:
            merged_content.append(f"\n{'='*60}")
            merged_content.append(f"SEÇÃO: {section.title}")
            merged_content.append(f"{'='*60}\n")

        for lecture in section.lectures:
            caption = pick_caption(lecture.captions, lang)
            if not caption:
                continue

            lecture_name = f"{lecture.object_index:03d} - {sanitize_filename(lecture.title)}"
            print(f"   ⬇ {lecture_name} [{caption.label}]")

            try:
                resp = requests.get(caption.url, timeout=30)
                resp.raise_for_status()
                vtt_content = resp.text

                if with_timestamps:
                    text = vtt_to_timestamped(vtt_content)
                else:
                    text = vtt_to_plain_text(vtt_content)

                # Salva arquivo individual
                txt_path = section_dir / f"{lecture_name}.txt"
                txt_path.write_text(text, encoding="utf-8")

                if merge:
                    merged_content.append(f"\n--- {lecture.title} ---\n")
                    merged_content.append(text)
                    merged_content.append("")

                downloaded += 1
                time.sleep(0.3)  # Rate limiting leve

            except Exception as e:
                print(f"   ✗ Erro: {e}")
                errors += 1

    # Salva arquivo mesclado
    if merge and merged_content:
        merged_path = course_dir / "_CURSO_COMPLETO.txt"
        header = (
            f"Curso: {course_title}\n"
            f"Total de aulas transcritas: {downloaded}\n"
            f"{'='*60}\n"
        )
        merged_path.write_text(
            header + "\n".join(merged_content), encoding="utf-8"
        )
        print(f"\n📄 Arquivo completo: {merged_path}")

    # Salva metadados
    meta = {
        "course_id": course_id,
        "title": course_title,
        "slug": slug,
        "sections": len(sections),
        "total_lectures": total_lectures,
        "transcribed": downloaded,
        "language": lang or "auto",
    }
    meta_path = course_dir / "_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n✓ Concluído!")
    print(f"  Transcrições salvas: {downloaded}")
    if errors:
        print(f"  Erros: {errors}")
    print(f"  Diretório: {course_dir}")


# ─── CLI ────────────────────────────────────────────────────────────────────

def extract_slug(url_or_slug: str) -> str:
    """Extrai o slug do curso a partir de uma URL ou slug direto."""
    match = re.search(r"udemy\.com/course/([^/?#]+)", url_or_slug)
    if match:
        return match.group(1)
    return url_or_slug.strip("/")


def list_available_captions(client: UdemyClient, slug: str):
    """Lista os idiomas de legenda disponíveis no curso."""
    course_id, title = client.get_course_id(slug)
    print(f"\n🎓 {title}")
    sections = client.get_curriculum(course_id)

    langs = {}
    for section in sections:
        for lecture in section.lectures:
            for cap in lecture.captions:
                locale = cap.locale
                if locale not in langs:
                    langs[locale] = {"label": cap.label, "count": 0}
                langs[locale]["count"] += 1

    if not langs:
        print("  Nenhuma legenda disponível.")
        return

    print("  Idiomas disponíveis:")
    for locale, info in sorted(langs.items(), key=lambda x: -x[1]["count"]):
        print(f"    • {info['label']} ({locale}) — {info['count']} aulas")


def setup_env():
    """Cria ou atualiza o arquivo .env interativamente."""
    env_path = Path(".env")
    existing = {}

    if env_path.exists():
        print(f"📄 Arquivo .env encontrado em: {env_path.resolve()}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    existing[key.strip()] = value.strip()

        current = existing.get("UDEMY_COOKIES", existing.get("UDEMY_ACCESS_TOKEN", ""))
        if current:
            print(f"   Cookies atuais: {current[:30]}... ({len(current)} chars)")
    else:
        print("📄 Criando novo arquivo .env")

    print()
    print("  Como obter os cookies:")
    print("    1. Abra a Udemy no navegador (logado)")
    print("    2. DevTools (F12) → aba Network")
    print("    3. Recarregue a página do curso")
    print("    4. Clique em alguma requisição para 'www.udemy.com'")
    print("    5. Em 'Request Headers', copie o valor do header 'Cookie'")
    print()
    cookies = input("Cole a string completa de cookies (Enter para manter): ").strip()

    if not cookies and (existing.get("UDEMY_COOKIES") or existing.get("UDEMY_ACCESS_TOKEN")):
        print("✓ Cookies mantidos.")
        return

    if not cookies:
        print("✗ Nenhum cookie fornecido.")
        return

    # Remove prefixo "Cookie: " se colou do header
    if cookies.lower().startswith("cookie:"):
        cookies = cookies[7:].strip()

    # Remove a chave antiga se existir
    existing.pop("UDEMY_ACCESS_TOKEN", None)
    existing["UDEMY_COOKIES"] = cookies

    lines = [
        "# Udemy Transcript Extractor - Configuração",
        "# Obtenha os cookies em: DevTools (F12) → Network → Request Headers → Cookie",
        "# IMPORTANTE: Os cookies expiram. Se der erro 403, gere novos.",
        "",
    ]
    for key, value in existing.items():
        # Usa aspas simples — a cookie string contém aspas duplas internas
        # que conflitariam se usasse aspas duplas
        if ";" in value or " " in value or '"' in value:
            lines.append(f"{key}='{value}'")
        else:
            lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Adiciona .env ao .gitignore se existir
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            with open(gitignore, "a") as f:
                f.write("\n.env\n")
            print("   Adicionado .env ao .gitignore")
    else:
        gitignore.write_text(".env\n", encoding="utf-8")
        print("   Criado .gitignore com .env")

    print(f"✓ Token salvo em: {env_path.resolve()}")
    print("  Agora você pode rodar sem --cookie:")
    print("  python udemy_transcripts.py --url 'https://udemy.com/course/meu-curso/'")


def _read_env_raw(key: str) -> str | None:
    """Lê um valor do .env diretamente, sem depender do python-dotenv.
    Útil quando o valor contém aspas internas que confundem o parser."""
    env_path = Path(".env")
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            # Remove aspas externas (simples ou duplas)
            v = v.strip()
            if (v.startswith("'") and v.endswith("'")) or \
               (v.startswith('"') and v.endswith('"')):
                v = v[1:-1]
            return v
    return None


def main():
    # Carrega variáveis do .env (se existir)
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Extrai transcrições de cursos da Udemy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Configurar cookies (primeira vez)
  python udemy_transcripts.py --setup

  # Usando .env (após setup)
  python udemy_transcripts.py --url "https://udemy.com/course/meu-curso/"

  # Listar idiomas disponíveis
  python udemy_transcripts.py --url "https://udemy.com/course/meu-curso/" --list-langs

  # Baixar com timestamps + arquivo mesclado para IA
  python udemy_transcripts.py --url "https://udemy.com/course/meu-curso/" --timestamps --merge

  # Depurar problemas de autenticação
  python udemy_transcripts.py --url "https://udemy.com/course/meu-curso/" --list-langs --debug
        """,
    )
    parser.add_argument(
        "--cookie", "-c", default=None,
        help="String completa de cookies do navegador (opcional se usar .env)"
    )
    parser.add_argument(
        "--url", "-u", default=None,
        help="URL do curso ou slug (ex: python-bootcamp)"
    )
    parser.add_argument(
        "--output", "-o", default="./udemy_transcripts",
        help="Diretório de saída (padrão: ./udemy_transcripts)"
    )
    parser.add_argument(
        "--lang", "-l", default=None,
        help="Idioma preferido (ex: pt, en, es)"
    )
    parser.add_argument(
        "--timestamps", "-t", action="store_true",
        help="Incluir timestamps no texto"
    )
    parser.add_argument(
        "--merge", "-m", action="store_true",
        help="Gerar arquivo único com todo o curso (ideal para IA)"
    )
    parser.add_argument(
        "--list-langs", action="store_true",
        help="Apenas listar idiomas de legenda disponíveis"
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="Criar/atualizar arquivo .env interativamente"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Exibir detalhes das requisições para depuração"
    )

    args = parser.parse_args()

    # ─── Setup interativo do .env ───
    if args.setup:
        setup_env()
        return

    # ─── Resolver cookies: CLI > .env (UDEMY_COOKIES) > .env (UDEMY_ACCESS_TOKEN) ───
    cookie_data = args.cookie

    if not cookie_data:
        # Tenta via dotenv
        cookie_data = os.getenv("UDEMY_COOKIES") or os.getenv("UDEMY_ACCESS_TOKEN")

        # Fallback: se dotenv falhou com aspas internas, lê o arquivo direto
        if not cookie_data or (cookie_data and ";" not in cookie_data and len(cookie_data) < 50):
            fallback = _read_env_raw("UDEMY_COOKIES") or _read_env_raw("UDEMY_ACCESS_TOKEN")
            if fallback and len(fallback) > len(cookie_data or ""):
                cookie_data = fallback

    if not cookie_data:
        print("✗ Cookies não encontrados.")
        print("  Opções:")
        print("    1. Crie um .env:  python udemy_transcripts.py --setup")
        print("    2. Passe via CLI: --cookie 'SUA_COOKIE_STRING'")
        sys.exit(1)

    if not args.url:
        parser.error("--url é obrigatório (a menos que use --setup)")

    slug = extract_slug(args.url)
    client = UdemyClient(cookie_data, debug=args.debug)

    if args.debug:
        display = cookie_data[:30] + "..." if len(cookie_data) > 30 else cookie_data
        print(f"[DEBUG] Cookie data: {display} ({len(cookie_data)} chars)")
        print(f"[DEBUG] Slug: {slug}")
        print()

    if args.list_langs:
        list_available_captions(client, slug)
    else:
        download_transcripts(
            client=client,
            slug=slug,
            output_dir=args.output,
            lang=args.lang,
            with_timestamps=args.timestamps,
            merge=args.merge,
        )


if __name__ == "__main__":
    main()