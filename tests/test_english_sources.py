import httpx
import pytest
from astrbot_plugin_game_torrent.exception import RequestError
from astrbot_plugin_game_torrent.fetcher import AHF, FGF, TorrentTag


@pytest.mark.parametrize(
    "cls,html",
    [
        (AHF, '<h2 class="title front-view-title"><a href="/game" title="Game">Game</a></h2>'),
        (FGF, '<h1 class="entry-title"><a href="/game">Game</a></h1>'),
    ],
)
async def test_english_search_and_fetch(cls, html):
    if cls is AHF:
        detail = '<figure class="aligncenter"><a href="https://example.com/download">Download</a></figure>'
    else:
        detail = '<a href="magnet:?xt=example">Download</a>'
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, text=html if request.url.path == "/" else detail)

    fetcher = cls()
    fetcher._client = httpx.AsyncClient(
        base_url=fetcher.base_url, transport=httpx.MockTransport(handler)
    )
    try:
        results = await fetcher.search("Test Game & More")
        assert requests[0].url.params["s"] == "Test Game & More"
        assert results[0].game_name == "Game"
        resource = await fetcher.fetch(results[0])
        assert resource and resource.magnet
    finally:
        await fetcher.aclose()
    assert fetcher._client is None


@pytest.mark.parametrize("cls", [AHF, FGF])
async def test_english_error_and_missing_link(cls):
    fetcher = cls()
    fetcher._client = httpx.AsyncClient(
        base_url=fetcher.base_url,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                403 if request.url.path == "/" else 200, text="<p>Empty</p>"
            ),
        ),
    )
    try:
        with pytest.raises(RequestError):
            await fetcher.search("Game")
        assert await fetcher.fetch(TorrentTag(game_name="Game", url="/game")) is None
    finally:
        await fetcher.aclose()
