"""
Copiloto de Venda IA - Flask REST API
Intelligent customer service chatbot for Christian fashion store
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

from config import config
from copiloto.conversation_flow import ConversationFlowManager, PurchaseIntent

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize conversation flow manager
flow_manager = ConversationFlowManager(config.PRODUCTS)


# ============== HEALTH CHECK ==============

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Copiloto de Venda IA"
    }), 200


# ============== SESSION MANAGEMENT ==============

@app.route('/api/v1/sessions', methods=['POST'])
def create_session():
    """
    Create a new conversation session
    
    Returns:
        - session_id: Unique identifier for the conversation
        - initial_message: First message from copilot
    """
    try:
        session_id = flow_manager.create_session()
        session = flow_manager.get_session(session_id)
        
        # Generate initial greeting
        initial_message = f"Olá! 👋 Bem-vindo à nossa loja de camisetas evangélicas. Como posso ajudá-lo hoje?"
        session.add_message("assistant", initial_message)
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "message": initial_message,
            "timestamp": datetime.now().isoformat()
        }), 201
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    try:
        session = flow_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "data": session.get_session_info()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete/end a session"""
    try:
        if flow_manager.end_session(session_id):
            return jsonify({
                "status": "success",
                "message": "Session ended successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============== CONVERSATION ==============

@app.route('/api/v1/chat', methods=['POST'])
def send_message():
    """
    Send a message and get response from copilot
    
    Request body:
    {
        "session_id": "uuid",
        "message": "user message text"
    }
    
    Response:
    {
        "status": "success",
        "session_id": "uuid",
        "user_message": "text",
        "assistant_message": "text",
        "current_stage": "stage_name",
        "timestamp": "iso datetime"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: session_id, message"
            }), 400
        
        session_id = data['session_id']
        user_message = data['message'].strip()
        
        # Get session
        session = flow_manager.get_session(session_id)
        if not session:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        # Add user message to history
        session.add_message("user", user_message)
        
        # Generate response based on current stage
        assistant_response = _generate_response(session, user_message)
        
        # Add assistant message to history
        session.add_message("assistant", assistant_response)
        
        # Advance stage if appropriate (simplified logic)
        session.advance_stage()
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "user_message": user_message,
            "assistant_message": assistant_response,
            "current_stage": session.current_stage.value,
            "customer_info": {
                "name": session.customer.name,
                "purchase_intent": session.customer.purchase_intent.value,
                "selected_products": session.customer.selected_products,
                "estimated_total": session.customer.estimated_total
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/sessions/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """Get complete conversation history"""
    try:
        session = flow_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "history": session.get_history(),
            "total_messages": len(session.get_history())
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============== HELPER FUNCTIONS ==============

def _generate_response(session, user_message: str) -> str:
    """
    Generate a response based on conversation stage and user input
    
    This is a simplified implementation. In production, integrate with:
    - OpenAI API for intelligent responses
    - NLP for intent detection
    - Custom business logic
    """
    
    from copiloto.conversation_flow import ConversationStage, PurchaseIntent
    
    current_stage = session.current_stage
    user_lower = user_message.lower()
    
    # GREETING STAGE
    if current_stage == ConversationStage.GREETING:
        if any(word in user_lower for word in ['oi', 'olá', 'opa', 'e aí']):
            return "Que bom ter você aqui! 😊 Está procurando algo específico ou gostaria de conhecer nossos produtos?"
        else:
            return "Para começar, gostaria de saber: você procura uma camiseta para presentear alguém ou para usar você mesmo?"
    
    # PURCHASE INTENT STAGE
    elif current_stage == ConversationStage.PURCHASE_INTENT:
        if any(word in user_lower for word in ['presente', 'presentear', 'regalo', 'dar']):
            session.customer.purchase_intent = PurchaseIntent.GIFT
            return "Que legal! 🎁 Presentes são sempre especiais. Em qual ocasião você quer presentear? (aniversário, natal, namoro, etc.)"
        elif any(word in user_lower for word in ['eu', 'mim', 'próprio', 'pessoal', 'para mim']):
            session.customer.purchase_intent = PurchaseIntent.PERSONAL
            return "Perfeito! Você procura uma camiseta feminina, masculina ou unissex?"
        else:
            return "Deixe-me perguntar de forma diferente: é uma compra para você ou um presente? 😊"
    
    # PRODUCT SELECTION STAGE
    elif current_stage == ConversationStage.PRODUCT_SELECTION:
        products_list = "\n".join([f"• {name.capitalize()}: {info.get('categoria')}" for name, info in session.products_catalog.items()])
        
        # Detect product interest
        if 'camiseta' in user_lower:
            session.customer.product_type = 'camisetas'
            return "Ótima escolha! Temos lindas camisetas evangélicas. Qual é o seu tamanho? (P, M, G, GG, XG, XXG)"
        else:
            return f"Ótimo! Temos essas opções:\n{products_list}\n\nQual mais interessa você?"
    
    # SPECIFICATIONS STAGE
    elif current_stage == ConversationStage.SPECIFICATIONS:
        # Extract size
        sizes = ['p', 'm', 'g', 'gg', 'xg', 'xxg']
        for size in sizes:
            if size in user_lower:
                session.customer.size = size.upper()
                break
        
        # Extract gender preference
        if 'feminina' in user_lower or 'mulher' in user_lower:
            session.customer.gender = 'Feminina'
        elif 'masculina' in user_lower or 'homem' in user_lower:
            session.customer.gender = 'Masculina'
        elif 'unissex' in user_lower:
            session.customer.gender = 'Unissex'
        
        if session.customer.size and session.customer.gender:
            session.customer.selected_products.append({
                "nome": "Camiseta Evangélica",
                "tamanho": session.customer.size,
                "genero": session.customer.gender,
                "preco": 79.90
            })
            session.customer.estimated_total += 79.90
            return "Perfeito! Camiseta " + session.customer.gender.lower() + " tamanho " + session.customer.size + ". 👕\n\nGostaria de adicionar uma ecobag, caneca ou bottom personalizado? São ótimas combinações!"
        else:
            return "Qual é seu tamanho e qual gênero de peça prefere?"
    
    # COMPLEMENTARY PRODUCTS STAGE
    elif current_stage == ConversationStage.COMPLEMENTARY_PRODUCTS:
        complementary_map = {
            'ecobag': {'nome': 'Eco Bag', 'preco': 49.90},
            'caneca': {'nome': 'Caneca', 'preco': 39.90},
            'bottom': {'nome': 'Bottom', 'preco': 89.90},
            'calça': {'nome': 'Calça', 'preco': 89.90},
            'shorts': {'nome': 'Shorts', 'preco': 89.90},
        }
        
        for key, product in complementary_map.items():
            if key in user_lower:
                session.customer.complementary_products.append(product)
                session.customer.estimated_total += product['preco']
                return f"Excelente! Adicionei {product['nome']} à sua compra. 🎁\n\nDeseja algo mais ou podemos seguir para confirmar seu pedido?"
        
        if any(word in user_lower for word in ['não', 'nada', 'só']):
            return "Tudo bem! Então é só a camiseta mesmo. Agora preciso de alguns dados seus. Qual é seu nome?"
        else:
            return "Temos: ecobag (R$49,90), caneca (R$39,90) ou bottoms (R$89,90). Quer algo?"
    
    # CUSTOMER INFO STAGE
    elif current_stage == ConversationStage.CUSTOMER_INFO:
        if not session.customer.name:
            session.customer.name = user_message.strip()
            return f"Prazer, {session.customer.name}! 😊 Qual é seu email?"
        elif not session.customer.email:
            session.customer.email = user_message.strip()
            return "E qual é seu número de telefone para contato?"
        elif not session.customer.phone:
            session.customer.phone = user_message.strip()
            return "Perfeito! Agora preciso do seu endereço de entrega."
        else:
            session.customer.delivery_address = user_message.strip()
            return "Obrigado! Todas as informações coletadas. Vamos para a confirmação?"
    
    # CONFIRM ORDER STAGE
    elif current_stage == ConversationStage.CONFIRM_ORDER:
        if any(word in user_lower for word in ['sim', 'confirma', 'fecha', 'ok', 'tudo bem']):
            order_summary = _generate_order_summary(session)
            return f"🎉 Perfeito! Seu pedido foi confirmado!\n\n{order_summary}\n\nObrigado pela compra, {session.customer.name}!"
        else:
            return "Há algo que gostaria de mudar?"
    
    # DEFAULT
    else:
        return "Como posso ajudá-lo?"


def _generate_order_summary(session) -> str:
    """Generate a summary of the order"""
    summary = "📋 **RESUMO DO PEDIDO**\n"
    summary += f"Cliente: {session.customer.name}\n"
    summary += f"Email: {session.customer.email}\n"
    summary += f"Telefone: {session.customer.phone}\n\n"
    
    summary += "**PRODUTOS:**\n"
    for product in session.customer.selected_products:
        summary += f"• {product['nome']} - R${product['preco']:.2f}\n"
    
    if session.customer.complementary_products:
        summary += "\n**PRODUTOS COMPLEMENTARES:**\n"
        for product in session.customer.complementary_products:
            summary += f"• {product['nome']} - R${product['preco']:.2f}\n"
    
    summary += f"\n**TOTAL: R${session.customer.estimated_total:.2f}**"
    
    return summary


# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == '__main__':
    port = config.API_PORT
    print(f"🚀 Copiloto de Venda IA running on http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/api/v1/")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG
    )
