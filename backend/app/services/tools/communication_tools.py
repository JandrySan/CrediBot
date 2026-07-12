from app.services.tools.base import Tool


class HandoffToAgentTool(Tool):
    @property
    def name(self) -> str:
        return "handoff_to_agent"

    @property
    def description(self) -> str:
        return (
            "Deriva la conversación a un asesor humano. "
            "Úsala cuando el usuario solicite explícitamente hablar con una persona, "
            "cuando no se pueda resolver su solicitud automáticamente, "
            "o cuando el usuario manifieste insatisfacción."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Motivo de la derivación a asesor humano",
                },
            },
            "required": ["reason"],
        }
    def run(self, **kwargs) -> dict:
        return {
            "handoff": True,
            "reason": kwargs.get("reason", "Solicitud del usuario"),
            "message": (
                "Entendido. Te voy a derivar con un asesor humano. "
                "Por favor espera un momento."
            ),
        }
