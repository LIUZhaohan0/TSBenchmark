import abc
import os
from pathlib import Path
import yaml, os
from typing import List

from hypernets.hyperctl.batch import ShellJob, Batch, BackendConf, ServerConf
from hypernets.hyperctl.appliation import BatchApplication

# from hypernets.hyperctl.scheduler import run_batch
from hypernets.hyperctl.server import create_hyperctl_handlers
from hypernets.utils import logging
from tsbenchmark.server import BenchmarkBatchApplication
logging.set_level('DEBUG')

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(__file__)


class BaseMRGConfig:
    pass


class CondaVenvMRGConfig(BaseMRGConfig):
    def __init__(self, name):
        self.name = name


class CustomPyMRGConfig(BaseMRGConfig):
    pass


class BaseReqsConfig:
    pass


class ReqsRequirementsTxtConfig(BaseReqsConfig):

    def __init__(self, py_version, file_name):
        self.py_version = py_version
        self.file_name = file_name


class ReqsCondaYamlConfig(BaseReqsConfig):

    def __init__(self, file_name):
        self.file_name = file_name


class PythonEnv:

    def __init__(self, venv_config: BaseMRGConfig, requirements: BaseReqsConfig):
        self.venv_config = venv_config
        self.requirements = requirements

    KIND_CUSTOM_PYTHON = 'custom_python'
    KIND_CONDA = 'conda'

    REQUIREMENTS_REQUIREMENTS_TXT = 'requirements_txt'
    REQUIREMENTS_CONDA_YAML = 'conda_yaml'

    @property
    def venv_kind(self):
        if isinstance(self.venv_config,  CondaVenvMRGConfig):
            return PythonEnv.KIND_CONDA
        elif isinstance(self.venv_config,  CustomPyMRGConfig):
            return PythonEnv.KIND_CUSTOM_PYTHON
        else:
            return None

    @property
    def reqs_kind(self):
        if isinstance(self.venv_config,  ReqsRequirementsTxtConfig):
            return PythonEnv.REQUIREMENTS_REQUIREMENTS_TXT
        elif isinstance(self.venv_config,  ReqsCondaYamlConfig):
            return PythonEnv.REQUIREMENTS_CONDA_YAML
        else:
            return None


class Player:
    def __init__(self, base_dir, exec_file: str, env: PythonEnv):
        self.base_dir = base_dir
        self.base_dir_path = Path(base_dir)

        self.env: PythonEnv = env
        self.exec_file = exec_file
        # 1. check env file
        # 2. check config file

    @property
    def name(self):
        return Path(self.base_dir).name


class JobParams:
    def __init__(self, bm_task_id, task_config_id,  random_state,  max_trails, reward_metric, **kwargs):
        self.bm_task_id = bm_task_id
        self.task_config_id = task_config_id
        self.random_state = random_state
        self.max_trails = max_trails
        self.reward_metric = reward_metric

    def to_dict(self):
        return self.__dict__


def load_player(folder):
    config_file = Path(folder) / "player.yaml"
    if not config_file.exists():
        raise FileNotFoundError(config_file)

    assert config_file.exists()
    with open(config_file, 'r') as f:
        content = f.read()

    play_dict = yaml.load(content, Loader=yaml.CLoader)

    # exec_file, env: EnvSpec
    play_dict['exec_file'] = "exec.py"  # TODO load exec.py from config

    # PythonEnv(**play_dict['env'])
    env_dict = play_dict['env']

    env_mgr_dict = env_dict.get('mgr')
    env_mgr_kind = env_mgr_dict['kind']
    env_mgr_config = env_mgr_dict.get('config', {})

    if env_mgr_kind == PythonEnv.KIND_CONDA:
        mgr_config = CondaVenvMRGConfig(**env_mgr_config)
        requirements_dict = env_dict.get('requirements')
        requirements_kind = requirements_dict['kind']
        requirements_config = requirements_dict.get('config', {})

        if requirements_kind == PythonEnv.REQUIREMENTS_CONDA_YAML:
            reqs_config = ReqsCondaYamlConfig(**requirements_config)
        elif requirements_kind == PythonEnv.REQUIREMENTS_REQUIREMENTS_TXT:
            reqs_config = ReqsRequirementsTxtConfig(**requirements_config)
        else:
            raise Exception(f"Unsupported env manager {env_mgr_kind}")

    elif env_mgr_kind == PythonEnv.KIND_CUSTOM_PYTHON:
        mgr_config = CustomPyMRGConfig()
        reqs_config = None
    else:
        raise Exception(f"Unsupported env manager {env_mgr_kind}")

    play_dict['env'] = PythonEnv(venv_config=mgr_config, requirements=reqs_config)
    play_dict['base_dir'] = Path(folder).absolute().as_posix()
    return Player(**play_dict)


def load_players(player_specs):

    def put_player(dict_obj, _: Player):
        if _.name not in dict_obj:
            dict_obj[_.name] = _
        else:
            raise RuntimeError(f"already exists key {_.name}")

    default_players = {}

    # 1. load default players
    default_players_dir = Path(SRC_DIR).parent / "players"
    logger.debug(f"default players dir is at {default_players_dir}")
    for player_folder in os.listdir(default_players_dir):
        # filter dirs
        player_dir = default_players_dir / player_folder
        if os.path.isdir(player_dir):
            logger.debug(f'detected player at {player_dir}')
            player = load_player(player_dir)
            put_player(default_players, player)

    # 2. load user custom players
    selected_players = {}
    for player_name_or_path in player_specs:
        if player_name_or_path not in default_players:  # is a path
            # load as a directory
            abs_player_path = os.path.abspath(player_name_or_path)
            logger.info(f"read player from dir {abs_player_path}")

            player = load_player(Path(player_name_or_path))
            put_player(selected_players, player)
        else:
            player_name = player_name_or_path
            put_player(selected_players, default_players[player_name])

    return list(selected_players.values())

