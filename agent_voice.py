import os
import whisper
import edge_tts
import logging

logger = logging.getLogger(__name__)

class VoiceAgent:
    def __init__(self):
        self.whisper_model = None
        self.tts_voice = "pt-BR-FranciscaNeural"

    def transcribe(self, file_path):
        if not self.whisper_model:
            logger.info("VoiceAgent: Carregando Whisper...")
            self.whisper_model = whisper.load_model("base")
        result = self.whisper_model.transcribe(file_path)
        return result.get("text", "")

    async def speak(self, context, chat_id, text):
        clean_text = text.replace("*", "").replace("#", "").replace("_", "").replace("`", "")
        path = f"voice_{chat_id}.mp3"
        try:
            comm = edge_tts.Communicate(clean_text, self.tts_voice)
            await comm.save(path)
            with open(path, 'rb') as f:
                await context.bot.send_voice(chat_id=chat_id, voice=f)
        except Exception as e:
            logger.error(f"VoiceAgent (TTS): {e}")
        finally:
            if os.path.exists(path):
                os.remove(path)
