"""
Worker do robô: atende o botão "Executar Fluxo Agora" do painel (API no modo real).
Detalhes em src/worker.py.

Variáveis de ambiente:
    API_URL                  URL da API do monitor (ex.: http://api:8000/api). Obrigatória.
    RPA_API_TOKEN            Token que a API exige nas rotas do robô.
    RPA_WORKER_POLL_SECONDS  Intervalo entre as consultas à fila (padrão: 3).
    E as mesmas do main.py (credenciais LGE, LMS_*, HEADLESS), repassadas ao robô.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.worker import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
