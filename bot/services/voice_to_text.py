import logging

import grpc

import bot.utils.yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import bot.utils.yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
from bot import config

# import bot.utils.yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
# import bot.utils.yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc


logger = logging.getLogger(__name__)


CHUNK_SIZE = 4000


def gen(audio_file_name):
    # Задать настройки распознавания.
    recognize_options = stt_pb2.StreamingOptions(
        recognition_model=stt_pb2.RecognitionModelOptions(
            audio_format=stt_pb2.AudioFormatOptions(
                container_audio=stt_pb2.ContainerAudio(
                    container_audio_type=stt_pb2.ContainerAudio.ContainerAudioType.OGG_OPUS,
                )
            ),
            text_normalization=stt_pb2.TextNormalizationOptions(
                text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                profanity_filter=False,
                literature_text=True,
            ),
            language_restriction=stt_pb2.LanguageRestrictionOptions(
                restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                language_code=["ru-RU"],
            ),
            audio_processing_type=stt_pb2.RecognitionModelOptions.FULL_DATA,
        ),
        # eou_classifier=stt_pb2.EouClassifierOptions(
        #     default_classifier=stt_pb2.DefaultEouClassifier(
        #         type=1, max_pause_between_words_hint_ms=1000
        #     )
        # ),
    )

    # Отправить сообщение с настройками распознавания.
    yield stt_pb2.StreamingRequest(session_options=recognize_options)

    # Прочитать аудиофайл и отправить его содержимое порциями.
    with open(audio_file_name, "rb") as f:
        data = f.read(CHUNK_SIZE)
        while data != b"":
            yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
            data = f.read(CHUNK_SIZE)


def run(
    audio_file_name, folder_id=config.get_settings().YANDEX_FOLDER_ID, api_key=config.get_settings().YANDEX_API_KEY
):
    # Establish a connection with the server
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel("stt.api.cloud.yandex.net:443", cred)
    stub = stt_service_pb2_grpc.RecognizerStub(channel)

    # Отправить данные для распознавания.
    it = stub.RecognizeStreaming(
        gen(audio_file_name),
        metadata=(
            ("authorization", f"Api-Key {api_key}"),
            ("x-folder-id", f"{folder_id}"),
            ("x-node-alias", "speechkit.stt.rc"),
        ),
    )

    # Process server responses and output the result to the console.
    try:
        for r in it:
            event_type, alternatives = r.WhichOneof("Event"), None
            if event_type == "partial" and len(r.partial.alternatives) > 0:
                alternatives = [a.text for a in r.partial.alternatives]
            if event_type == "final":
                alternatives = [a.text for a in r.final.alternatives]
            if event_type == "final_refinement":
                alternatives = [a.text for a in r.final_refinement.normalized_text.alternatives]
                return alternatives[0]
    except grpc._channel._Rendezvous as err:
        print(f"Error code {err._state.code}, message: {err._state.details}")
        raise err
