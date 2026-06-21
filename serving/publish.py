import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from dotenv import load_dotenv

snapshot_files = ('players.json', 'history.json', 'trend_curve.json')


def _github_headers(token):
    return {
        'Authorization': f'{token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }


def _github_request(method, url, token, payload=None):
    headers = _github_headers(token)
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')

    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request) as response:
        body = response.read().decode('utf-8')
        return json.loads(body) if body else None


def _api_request(method, url, token, payload=None):
    try:
        return _github_request(method, url, token, payload)
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise RuntimeError(
            f'GitHub API {method} {url} failed ({e.code}): {error_body}'
        ) from e


def get_file_sha(owner, repo, repo_path, token):
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}'
    try:
        result = _github_request('GET', url, token)
    except HTTPError as e:
        if e.code == 404:
            return None
        error_body = e.read().decode('utf-8')
        raise RuntimeError(
            f'GitHub API GET {url} failed ({e.code}): {error_body}'
        ) from e

    return result['sha']


def publish_file(owner, repo, repo_path, local_path, message, token):
    content_b64 = base64.b64encode(Path(local_path).read_bytes()).decode('ascii')
    sha = get_file_sha(owner, repo, repo_path, token)

    payload = {'message': message, 'content': content_b64}
    if sha:
        payload['sha'] = sha

    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}'
    return _api_request('PUT', url, token, payload)


def publish_snapshot(output_dir, message=None):
    load_dotenv()

    token = os.getenv('GITHUB_TOKEN')
    repo = os.getenv('GITHUB_REPO')
    if not token or not repo:
        raise RuntimeError('GITHUB_TOKEN and GITHUB_REPO must be set in the environment')

    owner, repo_name = repo.split('/', 1)
    output_dir = Path(output_dir)

    if message is None:
        players_payload = json.loads((output_dir / 'players.json').read_text())
        message = f"chore: refresh snapshot {players_payload['generated_at']}"

    for filename in snapshot_files:
        local_path = output_dir / filename
        repo_path = f'frontend/public/data/{filename}'
        publish_file(owner, repo_name, repo_path, local_path, message, token)
        print(f'Published {repo_path}')
