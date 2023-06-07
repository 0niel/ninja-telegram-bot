import base64
from typing import Any, Coroutine, Dict, Union

from postgrest import AsyncFilterRequestBuilder, AsyncPostgrestClient, AsyncRequestBuilder
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from supabase import Client as SyncClient
from supabase.lib.client_options import ClientOptions

from bot import config


class Client(SyncClient):
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        options: ClientOptions = ClientOptions(),
    ):
        super().__init__(supabase_url=supabase_url, supabase_key=supabase_key, options=options)
        self.postgrest: AsyncPostgrestClient = self._init_postgrest_client(
            rest_url=self.rest_url,
            supabase_key=self.supabase_key,
            headers=options.headers,
            schema=options.schema,
        )

    def table(self, table_name: str) -> AsyncRequestBuilder:
        return self.from_(table_name)

    def from_(self, table_name: str) -> AsyncRequestBuilder:
        return self.postgrest.from_(table_name)

    def rpc(self, fn: str, params: Dict[Any, Any]) -> Coroutine[None, None, AsyncFilterRequestBuilder]:
        return self.postgrest.rpc(fn, params)

    @staticmethod
    def _init_postgrest_client(
        rest_url: str,
        supabase_key: str,
        headers: dict[str, str],
        schema: str,
        timeout: Union[int, float] = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
    ) -> AsyncPostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        client = AsyncPostgrestClient(rest_url, headers=headers, schema=schema, timeout=timeout)
        client.auth(token=supabase_key)
        return client


def create_client(
    supabase_url: str,
    supabase_key: str,
    supabase_username: str,
    supabase_password: str,
) -> Client:
    basic_auth_headers = {
        "Authorization": f'Basic {base64.b64encode(f"{supabase_username}:{supabase_password}".encode("utf-8")).decode("utf-8")}'
    }
    options = ClientOptions(headers=basic_auth_headers, postgrest_client_timeout=DEFAULT_POSTGREST_CLIENT_TIMEOUT)
    return Client(supabase_url=supabase_url, supabase_key=supabase_key, options=options)


supabase: Client = create_client(
    config.get_settings().SUPABASE_URL,
    config.get_settings().SUPABASE_KEY,
    config.get_settings().SUPABASE_USERNAME,
    config.get_settings().SUPABASE_PASSWORD,
)
