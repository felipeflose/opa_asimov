import google.generativeai as genai
from PIL import Image
import os
from src.agents.base_agent import BaseAgent

class VisionAgent(BaseAgent):
    def __init__(self, api_key=None, gcs_client=None):
        super().__init__(
            name="VisionAgent",
            purpose="Analisar imagens e descrever conteúdos de forma detalhada para o Orchestrator.",
            tools=["vision_analysis"],
            gcs_client=gcs_client
        )
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash') # Versão 2.5 conforme solicitado

    def analyze_image(self, image_path, user_prompt=None):
        if not os.path.exists(image_path):
            return "Erro: Arquivo de imagem não encontrado."
        
        # Prompt especializado para identificação de tecnologia e perfis (Instagram/Redes)
        default_vision_prompt = """
        Analise esta imagem com foco em IDENTIFICAÇÃO DE TECNOLOGIA E NEGÓCIOS:
        1. Se for um perfil de rede social (Instagram, LinkedIn, etc), extraia o Nome do Perfil e a Bio.
        2. Identifique qual é a TECNOLOGIA ou PRODUTO sendo anunciado/vendido.
        3. Liste palavras-chave técnicas e propostas de valor (ex: 'Automação de IA', 'SaaS de CRM').
        4. Capture qualquer URL ou link visível.
        5. Se for um erro de sistema, descreva o erro técnico.
        
        Responda de forma estruturada para o Orchestrator.
        """
        
        prompt = user_prompt if user_prompt else default_vision_prompt
        
        try:
            img = Image.open(image_path)
            response = self.model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            return f"Erro na análise de visão: {str(e)}"

    def run(self, task_metadata):
        image_path = task_metadata.get("image_path")
        prompt = task_metadata.get("prompt", "O que você vê nesta imagem?")
        return self.analyze_image(image_path, prompt)
