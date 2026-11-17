from flask import Blueprint

from app.interfaces.serializers import tempo_medio_json

from .support import container, endpoint

bp = Blueprint("metricas", __name__, url_prefix="/api/admin/metricas")


@endpoint(bp, "/tempo-medio-execucao", "GET",
          resumo="Tempo médio de execução (da aprovação à finalização) das OS executadas",
          tag="Métricas", resposta="TempoMedioExecucao")
def tempo_medio_execucao():
    return tempo_medio_json(container().ordens.tempo_medio_execucao())
