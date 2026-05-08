"""
Configuration settings for Copiloto de Venda IA
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', False)
    API_PORT = int(os.getenv('API_PORT', 5000))
    
    # Copilot configuration
    STORE_NAME = "Christian Fashion Store"
    STORE_CURRENCY = "R$"
    
    # Context for the copilot
    SYSTEM_PROMPT = """Você é um assistente de vendas inteligente para uma loja de camisetas evangélicas.
    Seu objetivo é:
    1. Oferecer atendimento personalizado e acolhedor
    2. Identificar a intenção de compra (compra pessoal ou presente)
    3. Recomendar produtos complementares
    4. Coletar informações do cliente de forma natural
    5. Aumentar o ticket médio
    
    Sempre mantenha um tom amigável, profissional e orientado às vendas."""
    
    # Product catalog
    PRODUCTS = {
        "camisetas": {
            "categoria": "Camisetas Evangélicas",
            "preco_medio": 79.90,
            "opcoes": ["Feminina", "Masculina", "Unissex"],
            "tamanhos": ["P", "M", "G", "GG", "XG", "XXG"]
        },
        "ecobags": {
            "categoria": "Eco Bags Personalizadas",
            "preco": 49.90,
            "descricao": "Bolsas ecológicas reutilizáveis"
        },
        "canecas": {
            "categoria": "Canecas Personalizadas",
            "preco": 39.90,
            "opcoes": ["Branca", "Preta", "Colorida"]
        }
    }

config = Config()
