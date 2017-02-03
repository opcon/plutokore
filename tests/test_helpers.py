import pytest
from plutokore import helpers

def test_calculate_unit_values(astro_jet, makino_env):
    helpers.get_unit_values(makino_env, astro_jet)

def test_datadir(datadir_copy):
    print(datadir_copy['test.txt'])
    with open(datadir_copy['test.txt']) as fp:
        contents = fp.read()
    print(contents)
    assert contents == 'hello\n'