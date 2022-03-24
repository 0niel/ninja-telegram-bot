import grpc
import logging
import bot.utils.yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
import bot.utils.yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc
from bot import config

logger = logging.getLogger(__name__)

CHUNK_SIZE = 4000


def gen(folder_id, audio_file_name):
    # speechkit settings
    specification = stt_service_pb2.RecognitionSpec(
        language_code='ru-RU',
        profanity_filter=True,
        model='general',
        partial_results=True,
        audio_encoding='OGG_OPUS',
        sample_rate_hertz=8000
    )
    streaming_config = stt_service_pb2.RecognitionConfig(
        specification=specification, folder_id=folder_id)

    # Send a message with recognition settings
    yield stt_service_pb2.StreamingRecognitionRequest(config=streaming_config)

    # Read the audio file and send its contents in chunks
    with open(audio_file_name, 'rb') as f:
        data = f.read(CHUNK_SIZE)
        while data != b'':
            yield stt_service_pb2.StreamingRecognitionRequest(audio_content=data)
            data = f.read(CHUNK_SIZE)


def run(audio_file_name, folder_id=config.YANDEX_FOLDER_ID, api_key=config.YANDEX_API_KEY):
    # Establish a connection with the server
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stub = stt_service_pb2_grpc.SttServiceStub(channel)

    # Send data for recognition
    it = stub.StreamingRecognize(gen(folder_id, audio_file_name), metadata=(
        ('authorization', 'Api-Key %s' % api_key),))


    # Process server responses and output the result to the console.
    try:
        for r in it:
            try:
                if r.chunks[0].final:
                    for alternative in r.chunks[0].alternatives:
                        return alternative.text

            except LookupError:
                logger.error('Not available chunks')
    except grpc._channel._Rendezvous as err:
        logger.error('Error code %s, message: %s' %
                     (err._state.code, err._state.details))
