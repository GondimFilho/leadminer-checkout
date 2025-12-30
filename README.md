# leadminer-lp

Estrutura mínima do projeto `leadminer-lp`.

Conteúdo:

- backend/: lógica do servidor (FastAPI). Endpoint exemplo em `backend/main.py` para enviar e-mail com link do Drive.
- frontend/: landing page simples em `frontend/index.html` e imagem `frontend/image_98db8c.png`.

Como usar (rápido):

1. Backend: entre em `backend/`, crie um ambiente virtual e instale dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Preencha `backend/.env` com suas credenciais (NUNCA comite este arquivo).

3. Rode o servidor:

```powershell
uvicorn main:app --reload --port 8000
```

4. Abra `frontend/index.html` no navegador para ver a landing page.

Observações:
- `frontend/image_98db8c.png` contém uma string base64 curta como placeholder; substitua pela imagem real se necessário.
- `.gitignore` já inclui `.env`.
