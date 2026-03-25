import google.generativeai as genai
import os
from src.agents.base_agent import BaseAgent

class AudioAgent(BaseAgent):
    def __init__(self, api_key=None, gcs_client=None):
        super().__init__(
            name="AudioAgent",
            purpose="Transcrição e análise de áudio (voz e música) para o Orchestrator.",
            tools=["audio_analysis"],
            gcs_client=gcs_client
        )
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_audio(self, audio_path, user_prompt=None):
        if not os.path.exists(audio_path):
            return "Erro: Arquivo de áudio não encontrado."
        
        default_audio_prompt = """
        Você é um especialista em análise de áudio da Flose AI.
        Sua tarefa é transcrever e analisar este áudio:
        1. Forneça a TRANSCRIÇÃO completa e precisa.
        2. Identifique o TOM DE VOZ e emoção predominante.
        3. Identifique PALAVRAS-CHAVE e intenções principais.
        4. Se houver ruído de fundo ou música, descreva-os.
        
        Responda de forma estruturada para o Orchestrator.
        """
        
        prompt = user_prompt if user_prompt else default_audio_prompt
        
        try:
            # Gemini 1.5-flash suporta upload de arquivos diretamente
            # Ou podemos passar o blob/file dependendo da versão do SDK
            # Para o SDK atual, o upload_file é a forma recomendada para arquivos maiores/multimídia
            import mimetypes
            mime_type, _ = mimetypes.guess_type(audio_path)
            if not mime_type:
                # Fallback para formatos comuns do Telegram
                if audio_path.endswith('.ogg'): mime_type = 'audio/ogg'
                elif audio_path.endswith('.oga'): mime_type = 'audio/ogg'
                else: mime_type = 'audio/mpeg'
            
            audio_file = genai.upload_file(path=audio_path, mime_type=mime_type)
            
            # Aguarda o processamento do arquivo se necessário (geralmente rápido para áudios curtos)
            import time
            while audio_file.state.name == "PROCESSING":
                time.sleep(1)
                audio_file = genai.get_file(audio_file.name)
            
            response = self.model.generate_content([prompt, audio_file])
            
            # Limpeza do arquivo no backend do Gemini após processar
            genai.delete_file(audio_file.name)
            
            return response.text
        except Exception as e:
            return f"Erro na análise de áudio: {str(e)}"

    def run(self, task_metadata):
        audio_path = task_metadata.get("audio_path")
        prompt = task_metadata.get("prompt", "Transcreva este áudio.")
        return self.analyze_audio(audio_path, prompt)
