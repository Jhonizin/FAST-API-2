from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, constr
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

app = FastAPI(
    title="FILA",
    description="",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TipoAtendimento(str, Enum):
    NORMAL = "N"
    PRIORITARIO = "P"

class Cliente(BaseModel):
    nome: constr(max_length=20)
    tipo_atendimento: TipoAtendimento
    posicao: int
    data_chegada: datetime
    atendido: bool = False

class ClienteInput(BaseModel):
    nome: constr(max_length=20)
    tipo_atendimento: TipoAtendimento

fila: List[Cliente] = []

def reorganizar_fila():
    """Reorganiza as posições na fila após remoção ou atendimento"""
    for i, cliente in enumerate(fila, 1):
        if not cliente.atendido:
            cliente.posicao = i

def inserir_cliente_com_prioridade(cliente_input: ClienteInput) -> Cliente:
    """Insere o cliente na fila respeitando a prioridade"""
    posicao = 1
    if cliente_input.tipo_atendimento == TipoAtendimento.PRIORITARIO:
        for cliente in fila:
            if not cliente.atendido and cliente.tipo_atendimento == TipoAtendimento.PRIORITARIO:
                posicao += 1
    else:
        posicao = len([c for c in fila if not c.atendido]) + 1

    novo_cliente = Cliente(
        nome=cliente_input.nome,
        tipo_atendimento=cliente_input.tipo_atendimento,
        posicao=posicao,
        data_chegada=datetime.now()
    )
    
    for cliente in fila:
        if not cliente.atendido and cliente.posicao >= posicao:
            cliente.posicao += 1
    
    fila.append(novo_cliente)
    return novo_cliente

@app.get("/")
async def root():
    """Página inicial com instruções básicas"""
    return {
        "mensagem": "Bem-vindo à API de Gerenciamento de Fila",
        "documentacao": "/docs",
        "endpoints_disponiveis": [
            "GET /fila - Lista todos os clientes na fila",
            "GET /fila/{id} - Obtém um cliente específico",
            "POST /fila - Adiciona um novo cliente",
            "PUT /fila - Atualiza a fila",
            "DELETE /fila/{id} - Remove um cliente"
        ]
    }

@app.get("/fila", response_model=List[Cliente])
async def listar_fila():
    """Retorna a lista de clientes não atendidos na fila"""
    return [cliente for cliente in fila if not cliente.atendido]

@app.get("/fila/{id}", response_model=Cliente)
async def obter_cliente(id: int):
    """Retorna os dados do cliente na posição especificada"""
    for cliente in fila:
        if cliente.posicao == id and not cliente.atendido:
            return cliente
    raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada")

@app.post("/fila", response_model=Cliente)
async def adicionar_cliente(cliente: ClienteInput):
    """Adiciona um novo cliente à fila"""
    return inserir_cliente_com_prioridade(cliente)

@app.put("/fila")
async def atualizar_fila():
    """Atualiza as posições na fila e marca o primeiro cliente como atendido"""
    primeiro_cliente = None
    for cliente in fila:
        if not cliente.atendido:
            if cliente.posicao == 1:
                cliente.posicao = 0
                cliente.atendido = True
                primeiro_cliente = cliente
            else:
                cliente.posicao -= 1
    
    if primeiro_cliente:
        return {"message": f"Cliente {primeiro_cliente.nome} foi atendido"}
    return {"message": "Fila vazia"}

@app.delete("/fila/{id}")
async def remover_cliente(id: int):
    """Remove um cliente da fila pela posição"""
    for i, cliente in enumerate(fila):
        if cliente.posicao == id and not cliente.atendido:
            fila.pop(i)
            reorganizar_fila()
            return {"message": f"Cliente {cliente.nome} removido da fila"}
    raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada")

if __name__ == "__main__":
    print("Servidor iniciado!")
    print("Acesse a documentação em: http://localhost:8000/docs")
    print("Acesse a API em: http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)