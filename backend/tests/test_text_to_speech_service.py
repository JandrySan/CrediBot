from app.services.audio.text_to_speech import TextToSpeechService


def test_prepare_text_for_voice_normalizes_business_result_words():
    service = TextToSpeechService()

    text = "Resultado de precalificacion: PREAPROBADO. Caso OBSERVADO y RECHAZADO."
    prepared = service._prepare_text_for_voice(text)

    assert "PREAPROBADO" not in prepared
    assert "OBSERVADO" not in prepared
    assert "RECHAZADO" not in prepared
    assert "preaprobado" in prepared
    assert "observado" in prepared
    assert "rechazado" in prepared


def test_prepare_text_for_voice_lowercases_long_uppercase_words():
    service = TextToSpeechService()

    text = "Tu NOMBRE es JUAN y tu RESULTADO es PREAPROBADO."
    prepared = service._prepare_text_for_voice(text)

    assert "NOMBRE" not in prepared
    assert "RESULTADO" not in prepared
    assert "PREAPROBADO" not in prepared
    assert "nombre" in prepared
    assert "resultado" in prepared
    assert "preaprobado" in prepared
