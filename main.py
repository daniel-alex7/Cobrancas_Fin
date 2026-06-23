from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
import uuid

app = FastAPI(title="Sistema de Cobranças API")

# ---- BANCO DE DADOS EM MEMÓRIA ----
db_customers = {}
db_charges = {}

# ---- MODELOS DE DADOS (PYDANTIC) ----
class CustomerCreate(BaseModel):
    name: str
    document: str  # CPF ou CNPJ
    email: EmailStr

class CustomerResponse(CustomerCreate):
    id: str

class ChargeCreate(BaseModel):
    customer_id: str
    amount: int  # Valor em centavos (Ex: R$ 10,50 -> 1050)
    payment_method: str  # PIX, BOLETO, CREDIT_CARD
    due_date: date

class ChargeResponse(ChargeCreate):
    id: str
    status: str  # PENDING, PAID, OVERDUE

class WebhookNotification(BaseModel):
    charge_id: str
    event: str  # payment.confirmed, payment.failed


# ---- ENDPOINTS DE CLIENTES ----

@app.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate):
    # Verifica se o documento já existe
    for c in db_customers.values():
        if c["document"] == customer.document:
            raise HTTPException(status_code=400, detail="Documento já cadastrado.")
    
    customer_id = str(uuid.uuid4())
    new_customer = {"id": customer_id, **customer.model_dump()}
    db_customers[customer_id] = new_customer
    return new_customer

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str):
    if customer_id not in db_customers:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return db_customers[customer_id]


# ---- ENDPOINTS DE COBRANÇAS ----

@app.post("/charges", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
def create_charge(charge: ChargeCreate):
    # Valida se o cliente existe
    if charge.customer_id not in db_customers:
        raise HTTPException(status_code=404, detail="Cliente não encontrado para esta cobrança.")
    
    charge_id = str(uuid.uuid4())
    new_charge = {
        "id": charge_id,
        "status": "PENDING",  # Toda cobrança nova nasce pendente
        **charge.model_dump()
    }
    db_charges[charge_id] = new_charge
    return new_charge

@app.get("/charges/{charge_id}", response_model=ChargeResponse)
def get_charge(charge_id: str):
    if charge_id not in db_charges:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada.")
    return db_charges[charge_id]


# ---- ENDPOINT DE WEBHOOK (Retorno do Banco/Gateway) ----

@app.post("/webhooks/payment", status_code=status.HTTP_200_OK)
def handle_webhook(notification: WebhookNotification):
    charge_id = notification.charge_id
    
    # Verifica se a cobrança existe no nosso sistema
    if charge_id not in db_charges:
        raise HTTPException(status_code=404, detail="Cobrança não localizada.")
    
    # Processa o evento enviado pelo gateway
    if notification.event == "payment.confirmed":
        db_charges[charge_id]["status"] = "PAID"
        return {"message": f"Cobrança {charge_id} atualizada para PAGA."}
        
    elif notification.event == "payment.failed":
        # Aqui você poderia disparar um e-mail de aviso ao cliente
        return {"message": f"Tentativa de pagamento da cobrança {charge_id} falhou."}
    
    raise HTTPException(status_code=400, detail="Evento não suportado.")