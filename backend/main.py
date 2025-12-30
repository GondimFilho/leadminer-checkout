import os
import smtplib
import uuid
from email.message import EmailMessage
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# Carrega variáveis do arquivo .env
load_dotenv()

app = FastAPI()

# --- CONFIGURAÇÃO DE CORS ---
# Permite que o site (Frontend) converse com este Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÕES E VARIÁVEIS ---
INFINITE_HANDLE = os.getenv("INFINITE_HANDLE") 
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
LINK_DRIVE = "https://drive.google.com/drive/folders/1Te08NxdiLM7yIF9vOkK2DXCnbg1-0EgN?usp=sharing"

# Modelo de dados que vem do site
class PurchaseRequest(BaseModel):
    amount: int       # Valor em centavos (Ex: 9700)
    customer_email: str
    item_name: str

# --- ROTA HEALTH CHECK (Para manter o servidor acordado no Render) ---
@app.get("/")
def health_check():
    return {"status": "ok", "message": "LeadMiner API is running"}

# --- FUNÇÃO DE ENVIAR E-MAIL ---
def enviar_email_entrega(destinatario):
    msg = EmailMessage()
    msg['Subject'] = 'Seu Acesso ao LeadMiner - Licença Vitalícia 💎'
    msg['From'] = EMAIL_USER
    msg['To'] = destinatario
    
    # Corpo do e-mail em HTML
    msg.set_content(f"""
    <html>
    <body>
        <h2 style="color: #3eaf59;">Pagamento Aprovado! 🚀</h2>
        <p>Olá,</p>
        <p>Obrigado por adquirir o <strong>LeadMiner</strong>. O seu pagamento foi confirmado.</p>
        
        <p>Acesse a pasta segura abaixo para baixar o instalador e os manuais:</p>
        
        <div style="background-color: #f4f4f4; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <a href="{LINK_DRIVE}" style="background-color: #3eaf59; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                BAIXAR SOFTWARE AGORA
            </a>
        </div>
        
        <p>Recomendamos que salve os arquivos no seu computador.</p>
        <hr>
        <p style="font-size: 12px; color: gray;">Equipe LeadMiner</p>
    </body>
    </html>
    """, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ E-mail enviado com sucesso para {destinatario}")
            return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

# --- ROTA 1: GERAR LINK DE PAGAMENTO ---
@app.post("/create-checkout")
def create_checkout(order: PurchaseRequest):
    # Endpoint da API Pública da InfinitePay
    url = "https://api.infinitepay.io/invoices/public/checkout/links"
    
    # Gera um ID único para o pedido
    order_id = str(uuid.uuid4())

    # Payload (Dados da venda)
    # CORREÇÃO: Adicionado 'description' dentro de 'items'
    payload = {
        "handle": INFINITE_HANDLE,
        "order_nsu": order_id,
        "items": [
            {
                "id": "1",
                "description": order.item_name, # Campo obrigatório exigido pela API
                "price": order.amount,        # Valor em centavos
                "quantity": 1
            }
        ],
        "metadata": {
            "email": order.customer_email,
            "origin": "leadminer_site"
        },
        # Para onde o cliente vai após pagar (ajuste conforme seu ambiente: local ou render)
        "redirect_url": "https://leadminer-lp.onrender.com/"
    }

    try:
        # Envia para InfinitePay
        response = requests.post(url, json=payload)
        response.raise_for_status() # Levanta erro se não for 200 OK
        
        data = response.json()
        
        # Retorna a URL gerada para o site
        return {"checkout_url": data.get("url")}
        
    except requests.exceptions.RequestException as e:
        print(f"Erro de Conexão InfinitePay: {e}")
        # Mostra o erro detalhado que veio da API (ajuda muito no debug)
        if hasattr(e.response, 'text'):
            print("Detalhes da API:", e.response.text)
        raise HTTPException(status_code=400, detail="Erro ao gerar link de pagamento")

# --- ROTA 2: WEBHOOK (Confirmação Automática) ---
@app.post("/webhook/infinitepay")
async def receive_webhook(request: Request):
    try:
        data = await request.json()
        print(f"Webhook recebido: {data}")
        
        # Verifica se o status é aprovado
        status = data.get("status")
        
        if status == "approved":
            # Tenta pegar o e-mail que enviamos no metadata
            metadata = data.get("metadata", {})
            email_cliente = metadata.get("email")
            
            if email_cliente:
                print(f"💰 Venda confirmada! Enviando e-mail para {email_cliente}...")
                enviar_email_entrega(email_cliente)
            else:
                print("⚠️ Email não encontrado nos metadados do webhook.")
                
        return {"status": "received"}
        
    except Exception as e:
        print(f"Erro crítico no webhook: {e}")
        return {"status": "error"}