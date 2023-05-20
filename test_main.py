import pytest
from flask import Flask
from main import app, get_contact_vcard_route
from unittest.mock import patch
import json
import requests


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_get_all_contacts_route(client):
    # Test the GET /contacts route to retrieve all contacts
    response = client.get('/contacts')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert len(response.get_json()) > 0


def test_get_contact_vcard_route_with_redis(client, monkeypatch):
    # Test the GET /contacts/vcard route when contacts exist in Redis
    url = 'https://idg2001-oblig2-api.onrender.com/contacts/1/vcard'
    monkeypatch.setattr("main.redis_client.exists", lambda key: True)
    monkeypatch.setattr(
        "main.redis_client.get", lambda key: json.dumps([{"name": "John Doe"}])
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.get_json() == [{"name": "John Doe"}]


def test_get_contact_vcard_route_without_redis(client, monkeypatch):
    # Test the GET /contacts/vcard route when contacts do not exist in Redis
    url = 'https://idg2001-oblig2-api.onrender.com/contacts/1/vcard'
    def mock_get_requests(url):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"message": [{"name": "John Doe"}]}'
        return response
    monkeypatch.setattr("main.redis_client.exists", lambda key: False)
    monkeypatch.setattr("requests.get", mock_get_requests)
    response = client.get(url)
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.get_json() == [{"name": "John Doe"}]


def test_set_new_contacts_route(client):
    # Test the POST /contacts route to create new contacts
    with patch('main.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'json': '{"contact_id": 1}',
            'vcard': 'VCARD'
        }
        response = client.post('/contacts', json={'name': 'John Doe', 'email': 'john@example.com'})
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert response.get_json() == {'message': 'Contacts created successfully'}


def test_set_new_contacts_route_failure(client, monkeypatch):
    # Test the failure case of POST /contacts route
    url = 'https://idg2001-oblig2-api.onrender.com/contacts'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {API_KEY}'}
    data = {'name': 'John Doe', 'email': 'johndoe@example.com'}
    def mock_post_requests(url, headers, json):
        response = requests.Response()
        response.status_code = 400
        response._content = b'{"message": "Bad request"}'
        return response
    monkeypatch.setattr("requests.post", mock_post_requests)
    response = client.post('/contacts', headers=headers, json=data)
    assert response.status_code == 400
    assert response.content_type == 'application/json'
    assert response.get_json() == {'message': 'Bad request'}


if __name__ == '__main__':
    pytest.main()
