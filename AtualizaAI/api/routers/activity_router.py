import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/activity", tags=["Real-time Feed"])

async def activity_generator(request: Request):
    """Gerador de eventos SSE simulado para o feed v3"""
    try:
        while True:
            if await request.is_disconnected():
                break

            # Em produção, aqui buscaria novos eventos de uma fila (Redis/PubSub)
            # Ou checaria alterações no bucket 'logs/executions/'
            payload = {
                "id": str(int(asyncio.get_event_loop().time())),
                "type": "system",
                "message": "Sistema monitorando novas demandas...",
                "agent": "Orquestrador",
                "timestamp": "Agora"
            }
            
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(10) # Intervalo do spec v3
    except asyncio.CancelledError:
        pass

@router.get("/stream")
async def stream_activity(request: Request):
    """Endpoint SSE para fornecer feed de atividades em tempo real"""
    return StreamingResponse(activity_generator(request), media_type="text/event-stream")
