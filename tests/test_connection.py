import re
from http import HTTPStatus

import requests
from requests_html import HTMLSession


def _validate_link(
        path_to_deploy_info_file, deploy_info_file_content, link_key
        ) -> str:
    assert link_key in deploy_info_file_content, (
        f'Убедитесь, что файл `{path_to_deploy_info_file}` содержит ключ '
        f'`{link_key}`.'
    )
    link: str = deploy_info_file_content[link_key]
    assert link.startswith('https'), (
        f'Убедитесь, что cсылка ключ `{link_key}` в файле '
        f'`{path_to_deploy_info_file}` содержит ссылку, которая начинается с '
        'префикса `https`.'
    )
    link_pattern = re.compile(
        r'^https:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
        r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    )
    assert link_pattern.match(link), (
        f'Убедитесь, что ключ `{link_key}` в файле '
        f'`{path_to_deploy_info_file}` содержит корректную ссылку.'
    )
    return link


def _get_link(deploy_file_info, deploy_info_file_content, link_key) -> str:
    _, relative_path = deploy_file_info
    return _validate_link(relative_path, deploy_info_file_content, link_key)


def _make_safe_request(link, stream=False, js=False) -> requests.Response:
    try:
        if js:
            session = HTMLSession()
            response = session.get(link)
        else:
            response = requests.get(link, stream=stream)
    except requests.exceptions.SSLError:
        raise AssertionError(
            f'Убедитесь, что настроили шифрование для `{link}`.'
        )
    except requests.exceptions.ConnectionError:
        raise AssertionError(
            f'Убедитесь, что URL `{link}` доступен.'
        )
    expected_status = HTTPStatus.OK
    assert response.status_code == expected_status, (
        f'Убедитесь, что GET-запрос к `{link}` возвращает ответ со статусом '
        f'{int(expected_status)}.'
    )
    return response


def test_link_connection(
        deploy_file_info, deploy_info_file_content, link_key
        ):
    link = _get_link(deploy_file_info, deploy_info_file_content, link_key)
    response = _make_safe_request(link, js=True)
    response.html.render()
    cats_project_name = 'Kittygram'
    taski_project_name = 'Taski'
    assert_msg_template = (
        f'Убедитесь, что по ссылке `{link}` доступен проект '
        '`{project_name}`.'
    )
    if link_key == 'kittygram_domain':
        assert cats_project_name in response.html.text, (
            assert_msg_template.format(project_name=cats_project_name)
        )
    else:
        assert taski_project_name in response.html.text, (
            assert_msg_template.format(project_name='Taski')
        )


def test_projects_on_same_ip(
        deploy_file_info, deploy_info_file_content, kittygram_link_key,
        taski_link_key
        ):
    links = [
        _get_link(deploy_file_info, deploy_info_file_content, link_key)
        for link_key in (kittygram_link_key, taski_link_key)
    ]
    responses = [_make_safe_request(link, stream=True) for link in links]
    ips = [
        response.raw._original_response.fp.raw._sock.getpeername()
        for response in responses
    ]
    assert ips[0] == ips[1], (
        'Убедитесь, что оба проекта развернуты на одном сервере. В ходе '
        'проверки обнаружено, что проекты размещены на разных ip-адресах.'
    )


def test_kittygram_static_is_available(deploy_file_info,
                                       deploy_info_file_content,
                                       kittygram_link_key):
    link = _get_link(deploy_file_info, deploy_info_file_content,
                     kittygram_link_key)
    session = HTMLSession()
    try:
        response = session.get(link)
    except requests.ConnectionError:
        raise AssertionError(f'Убедитесь, что URL `{link}` доступен.')
    response.html.render()
    expected_status = HTTPStatus.OK
    assert response.status_code == expected_status, (
        f'Убедитесь, что GET-запрос к `{link}` возвращает ответ со статусом '
        f'{int(expected_status)}.'
    )
    images = response.html.find('img')
    static_file_link = None
    for image in images:
        image_src = image.attrs.get('src')
        if image_src and 'static' in image_src:
            static_file_link = image_src
            break
    assert static_file_link, (
        'На главной странице `Kittygram` не обнаружено статических файлов. '
        'Убедитесь, что проект настроен корректно.'
    )
    absolute_static_link = link + static_file_link
    assert_msg = 'Убедитесь, что статические файлы для `Kittygram` доступны.'
    try:
        static_response = requests.get(absolute_static_link)
    except requests.ConnectionError:
        raise AssertionError(assert_msg)
    assert static_response.status_code == expected_status, assert_msg


def test_kittygram_api_available(deploy_file_info,
                                 deploy_info_file_content,
                                 kittygram_link_key):
    link = _get_link(deploy_file_info, deploy_info_file_content,
                     kittygram_link_key)
    signup_link = f'{link}/api/users/'
    form_data = {
        'username': 'newuser',
        'password': ''
    }
    assert_msg = (
        'Убедитесь, что API проекта `Kittygram` доступен по ссылке формата '
        f'`{link}/api/...`.'
    )
    try:
        response = requests.post(signup_link, data=form_data)
    except requests.ConnectionError:
        raise AssertionError(assert_msg)
    expected_status = HTTPStatus.BAD_REQUEST
    assert response.status_code == expected_status, assert_msg
    assert 'password' in response.json(), assert_msg
