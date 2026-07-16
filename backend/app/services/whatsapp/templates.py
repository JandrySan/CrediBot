from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from string import Formatter


class TransactionalTemplateKey(StrEnum):
    HANDOFF_REQUESTED = "handoff_requested"
    ADVISOR_ASSIGNED = "advisor_assigned"
    PREQUALIFICATION_RECORDED = "prequalification_recorded"


@dataclass(frozen=True)
class TransactionalTemplate:
    key: TransactionalTemplateKey
    version: str
    body: str
    variables: tuple[str, ...] = ()


TRANSACTIONAL_TEMPLATES: dict[TransactionalTemplateKey, TransactionalTemplate] = {
    TransactionalTemplateKey.HANDOFF_REQUESTED: TransactionalTemplate(
        key=TransactionalTemplateKey.HANDOFF_REQUESTED,
        version="1.0",
        body=(
            "Listo, envié tu conversación al equipo de asesores. "
            "Una persona continuará contigo por este mismo chat."
        ),
    ),
    TransactionalTemplateKey.ADVISOR_ASSIGNED: TransactionalTemplate(
        key=TransactionalTemplateKey.ADVISOR_ASSIGNED,
        version="1.0",
        body=(
            "{advisor_name} tomó tu conversación. "
            "Desde ahora te responderá directamente por este chat."
        ),
        variables=("advisor_name",),
    ),
    TransactionalTemplateKey.PREQUALIFICATION_RECORDED: TransactionalTemplate(
        key=TransactionalTemplateKey.PREQUALIFICATION_RECORDED,
        version="1.0",
        body=(
            "Registramos tu simulación {application_reference} con resultado preliminar "
            "{result}. Un asesor debe verificar la información antes de una decisión final."
        ),
        variables=("application_reference", "result"),
    ),
}


def get_transactional_template(
    key: TransactionalTemplateKey | str,
) -> TransactionalTemplate:
    try:
        normalized_key = TransactionalTemplateKey(key)
    except ValueError as exc:
        raise KeyError(f"Plantilla transaccional desconocida: {key}") from exc
    return TRANSACTIONAL_TEMPLATES[normalized_key]


def render_transactional_template(
    key: TransactionalTemplateKey | str,
    variables: Mapping[str, object] | None = None,
) -> str:
    template = get_transactional_template(key)
    values = {name: str(value).strip() for name, value in (variables or {}).items()}
    required = set(template.variables)
    provided = set(values)
    missing = required - provided
    unexpected = provided - required

    if missing:
        raise ValueError(f"Faltan variables de plantilla: {', '.join(sorted(missing))}")
    if unexpected:
        raise ValueError(f"Variables de plantilla no esperadas: {', '.join(sorted(unexpected))}")
    if any(not values[name] for name in required):
        raise ValueError("Las variables de plantilla no pueden estar vacías")

    fields = {
        field_name
        for _, field_name, _, _ in Formatter().parse(template.body)
        if field_name is not None
    }
    if fields != required:
        raise RuntimeError(f"La plantilla {template.key} no coincide con su contrato de variables")
    return template.body.format_map(values)


def twilio_content_variables(
    key: TransactionalTemplateKey | str,
    variables: Mapping[str, object] | None = None,
) -> dict[str, str]:
    template = get_transactional_template(key)
    values = {name: str(value).strip() for name, value in (variables or {}).items()}
    render_transactional_template(key, values)
    return {str(index): values[name] for index, name in enumerate(template.variables, start=1)}
