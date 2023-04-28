import yaml


def test_infra_files_exist(nginx_dir_info, expected_nginx_files):
    path, dir_name = nginx_dir_info
    nginx_dir_content = {obj.name for obj in path.glob('*') if obj.is_file()}
    missing_files = expected_nginx_files - nginx_dir_content
    action = 'создан файл' if len(missing_files) < 2 else 'созданы файлы'
    assert not missing_files, (
        f'Убедитесь, что в директории `{dir_name}/` {action} '
        f'`{"`, `".join(missing_files)}`.'
    )


def test_deploy_info_file_content(
        deploy_file_info,
        deploy_info_file_content,
        expected_deploy_info_file_content
        ):
    _, relative_path = deploy_file_info
    missing_content = {
        key: value for key, value in expected_deploy_info_file_content.items()
        if key not in deploy_info_file_content
    }
    action = 'содержится' if len(missing_content) < 2 else 'содержатся'
    key_word_form = 'ключ' if len(missing_content) < 2 else 'ключи'
    assert not missing_content, (
        f'Убедитесь, что в файле `{relative_path}` {action} '
        f'{", ".join(missing_content.values())}. Для вывода этой '
        f'информации необходимо использовать {key_word_form} '
        f'`{"`, `".join(missing_content.keys())}`.'
    )


def test_backend_dockerfile_exists(dockerfile_dir_info, dockerfile_name):
    path, relative_path = dockerfile_dir_info
    assert (path / dockerfile_name).is_file(), (
        f'Убедитесь, что в директории `{relative_path}/` создан файл '
        f'`{dockerfile_name}.'
    )


def test_backend_dokerfile_content(dockerfile_dir_info, dockerfile_name):
    path, _ = dockerfile_dir_info
    with open(path / dockerfile_name, encoding='utf-8', errors='ignore') as f:
        dockerfile_content = f.read()
    expected_keywords = ('from', 'run', 'cmd')
    for keyword in expected_keywords:
        assert keyword in dockerfile_content.lower(), (
            f'Убедитесь, что настроили {dockerfile_name} для образа '
            '`kittygram_backend`.'
        )


def test_workflow_file(workflow_file_location, workflow_file_name):
    path, reletive_path = workflow_file_location
    path_to_file = path / workflow_file_name
    assert path_to_file.is_file(), (
        f'Убедитесь, что директория `{reletive_path}` содержит файл '
        f'`{workflow_file_name}`, в котором описан workflow для Kittygram.'
    )
    with open(path_to_file, "r", encoding='utf-8', errors='ignore') as stream:
        try:
            workflow = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise AssertionError(
                f'Убедитесь, что в файле `{path_to_file}` используется '
                'корректный YAML-синтаксис. При попытке чтения файла возникло '
                'исключение:\n'
                f'{exc.__class__.__name__}: {exc}'
            )
    assert workflow, (
        f'Убедитесь, что настроили workflow в файле `{path_to_file}`.'
    )
