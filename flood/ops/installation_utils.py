from __future__ import annotations

import subprocess

import flood


def get_local_installation() -> flood.FloodInstallation:
    result = subprocess.check_output(['which', 'vegeta'])
    vegeta_path = result.decode().rstrip()

    flood_version = flood.__version__

    # add git commit hash if not in a tagged release
    use_git_dir = None
    use_git_commit = None
    try:
        import os

        module_dir = os.path.realpath(flood.__path__[0])
        parent_dir = os.path.dirname(module_dir)
        parent_dir_files = os.listdir(parent_dir)
        if 'pyproject.toml' in parent_dir_files and '.git' in parent_dir_files:
            git_dir = os.path.join(parent_dir, '.git')

            # check whether in tagged release
            try:
                cmd = 'git --git-dir={git_dir} describe --tags --exact-match'
                cmd = cmd.format(git_dir=git_dir)
                subprocess.check_call(cmd.split(' '), stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # get git commit
                cmd = 'git --git-dir={git_dir} rev-parse HEAD'.format(
                    git_dir=git_dir
                )
                output = subprocess.check_output(cmd.split(' '))
                git_commit = output.decode().strip()

                # specify commit in flood version
                flood_version = flood.__version__ + '-' + git_commit[:8]
            use_git_dir = git_dir
            use_git_commit = git_commit
    except Exception:
        pass

    return {
        'flood_version': flood_version,
        'vegeta_path': vegeta_path,
        'git_dir': use_git_dir,
        'git_commit': use_git_commit,
        'semver': flood.__version__,
    }


def get_remote_installation(
    host: str, username: str | None = None
) -> flood.FloodInstallation:
    # create command
    if username is not None:
        url = username + '@' + host
    else:
        url = host
    template = (
        "ssh {url} bash -c "
        "'source ~/.profile; "
        "echo $(python3 -m flood version --json)'"
    )
    cmd = template.format(url=url)

    # run command
    try:
        result = subprocess.check_output(
            cmd.split(' '), stderr=subprocess.DEVNULL
        )
    except Exception:
        raise flood.SshError('could not ssh')

    try:
        import json

        output: flood.FloodInstallation = json.loads(result.decode().strip())
        return output

    except Exception:
        return {
            'vegeta_path': None,
            'flood_version': None,
            'git_dir': None,
            'git_commit': None,
            'semver': None,
        }

