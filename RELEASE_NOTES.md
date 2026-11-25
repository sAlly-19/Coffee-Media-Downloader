# CoffeeMediaDownloader Pro v1.0.0

**Desenvolvido por Café - Sistemas & Softwares**

Primeira versão oficial do **CoffeeMediaDownloader Pro**, gerenciador desktop moderno em Python + PySide6 (Qt 6) para download de vídeos, áudios e playlists no Windows.

---

## Novidades desta Release (`v1.0.0`)

### Downloads e Motor (`yt-dlp` + `FFmpeg`)
- **Múltiplos formatos e qualidades**:
  - **Vídeo (MP4)**: Melhor Disponível até 4K (2160p), 1080p, 720p e 480p.
  - **Áudio (MP3)**: 320 kbps (Alta), 192 kbps (Média) e 128 kbps (Padrão), com metadados embutidos opcionais e conversão otimizada.
  - **Áudio Original (M4A)**: extração rápida preservando a qualidade original.
- **Fila paralela (1 a 10 downloads simultâneos)**: controle dinâmico de concorrência com aviso de carga elevada acima de 4 conexões e semáforo dedicado para instâncias do `FFmpeg`.
- **Playlists seletivas**: inspeção rápida (`extract_flat`) com seleção individual de faixas, busca interna, criação opcional de subpasta por playlist e numeração automática (`01 - Título`).
- **Prevenção de duplicatas**: verificação local por pasta de destino e arquivo de registro thread-safe (`downloaded_archive.txt`).
- **Suporte a vídeos com restrição de idade (+18)**: leitura opcional de cookies do navegador (`Firefox` / `Chrome` / `Edge`) ou importação direta de `cookies.txt` nas Configurações, sem precisar fazer login dentro do aplicativo.
- **Retomada automática da fila**: tarefas pendentes podem ser retomadas ao reabrir o aplicativo.

### Interface e Experiência de Uso
- **Tema Café Escuro (Qt 6 + QSS)**: janela sem bordas com controles integrados, xícara de café animada com vapor contínuo e brilho pulsante durante downloads ativos, e degradês animados ao passar o mouse.
- **Produtividade**: monitoramento opcional de links na área de transferência (*Auto-colar Links*), arrastar e soltar links ou arquivos `.txt`, filtros na fila e no histórico, barra de progresso global no rodapé e minimização para a bandeja do sistema.
- **Instalador Windows completo**: inclui `CoffeeMediaDownloader.exe` e `FFmpeg` / `FFprobe` embutidos — pronto para usar sem configurações manuais.

---

## Instalação (Windows)

1. Baixe o instalador **`CoffeeMediaDownloaderPro-Setup-v1.0.0.exe`** nos anexos (*Assets*) desta release.
2. Execute o instalador e siga as instruções na tela (não exige instalação separada de Python ou FFmpeg).
3. Abra o **CoffeeMediaDownloader Pro** pelo Menu Iniciar ou atalho na Área de Trabalho.

### Dica para vídeos +18 no YouTube
Caso algum vídeo exija confirmação de idade, acesse **Configurações** no aplicativo e selecione **Firefox** em *Cookies do navegador* ou importe um arquivo **`cookies.txt`** exportado do seu navegador.

---

## Verificação do Instalador

- **Arquivo**: `CoffeeMediaDownloaderPro-Setup-v1.0.0.exe` (157,57 MB)
- **SHA-256**: `F067D46FC4040B2133F9DD92D5BBB4D05F8252F2F4BF1B845EB7988AF524E247`

---

**Café - Sistemas & Softwares**
