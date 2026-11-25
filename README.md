# CoffeeMediaDownloader Pro

Gerenciador desktop moderno em **Python + PySide6** para download de vídeos, áudios e playlists usando `yt-dlp` e `FFmpeg`, desenvolvido pela **Café - Sistemas & Softwares**.

## Principais Recursos

- **Interface em tema café escuro (Qt 6 + QSS)**: janela sem bordas personalizada, xícara de café animada e botões com degradê animado.
- **Múltiplos formatos e qualidades**:
  - **Vídeo (MP4)** (Melhor Disponível até 4K)
  - **Áudio (MP3)** (128 / 192 / 320 kbps com metadados embutidos opcionais)
  - **Áudio Original (M4A)**
- **Playlists seletivas**: inspeção rápida (`extract_flat`) com escolha individual de faixas, busca interna, subpasta automática e numeração (`01 - Título`).
- **Downloads concorrentes (1–10)**: fila paralela com `ThreadPoolExecutor`, limite de banda e controle dedicado de instâncias simultâneas do `FFmpeg`.
- **Evita duplicatas e retoma fila**: registro persistente em `%APPDATA%\CoffeeMediaDownloader` e retomada de fila interrompida ao reabrir.
- **Suporte a vídeos restritos**: leitura opcional de cookies do navegador (`Firefox` / `Chrome` / `Edge`) ou importação de arquivo `cookies.txt`.
- **Produtividade**: auto-colar da área de transferência, arrastar e soltar links/`.txt`, histórico pesquisável e minimização para a bandeja do Windows.

## Estrutura do Projeto

```text
CoffeeMediaDownloader/
├── main.py                  # Ponto de entrada da aplicação
├── ui.py                    # Fachada retrocompatível da UI
├── downloader.py            # Fachada retrocompatível do motor de download
├── utils.py                 # Fachada retrocompatível de utilitários
├── requirements.txt         # Dependências Python
├── coffee_app/
│   ├── core/                # Constantes, storage, modelos, assets e DownloadManager
│   └── ui/                  # Tema, ícones SVG, widgets customizados, páginas e janela
└── tests/
    └── test_downloader_and_utils.py
```

## Como Executar

1. Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale as dependências:

```powershell
pip install -r requirements.txt
```

3. *(Recomendado)* Garanta o `FFmpeg` instalado no `PATH` do sistema ou posicione `ffmpeg.exe` na raiz do projeto (ou em `bin\ffmpeg.exe`).

4. Execute a aplicação:

```powershell
python main.py
```

## Testes

```powershell
python -m unittest discover -s tests -v
```

---

**Café - Sistemas & Softwares**
