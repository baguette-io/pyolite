import mock
import os
import pytest
from pyolite import Pyolite
from pyolite import Group

@pytest.fixture
def olite(tmpdir):
    with mock.patch('pyolite.git.Git.commit', mock.MagicMock()):
        pyolite = Pyolite(str(tmpdir))
        os.makedirs(os.path.join(str(tmpdir), 'keydir'))
        os.makedirs(os.path.join(str(tmpdir), 'conf', 'repos'))
        os.makedirs(os.path.join(str(tmpdir), 'conf', 'groups'))
        yield pyolite

@pytest.fixture
def group1(olite):
    return olite.groups.create('group1')

@pytest.fixture
def user_factory(olite):
    def factory(name):
        open(os.path.join(olite.admin_repository, 'keydir', '%s.pub'% name), 'w').write("")
        return name
    return factory

def test_create(olite):
    group = olite.groups.create('test_create')
    assert os.path.exists(group.config)
    assert open(group.config).read() == ""

def test_create_idempotent(olite):
    group = olite.groups.create('test_create')
    assert olite.groups.create('test_create')
    assert os.path.exists(group.config)
    assert open(group.config).read() == ""

def test_get(olite, group1):
    group2 = olite.groups.get('group1')
    assert group1.name == group2.name
    assert group1.path == group2.path
    assert group1.config == group2.config
    assert open(group1.config).read() == open(group2.config).read() == ""
    #
    group3 = Group('group1', olite.groups.path, olite.groups.git)
    assert group1.config == group2.config == group3.config

def test_get_not_exist(olite):
    with pytest.raises(ValueError):
        olite.groups.get('inexistant')
    #
    with pytest.raises(ValueError):
        Group.get('inexistant', olite.groups.path, olite.groups.git)

def test_get_or_create(olite):
    group1 = olite.groups.get_or_create('test_create')
    group2 = olite.groups.get_or_create('test_create')
    assert group1.name == group2.name
    assert group1.path == group2.path
    assert group1.config == group2.config
    assert open(group1.config).read() == ""
    assert open(group2.config).read() == ""

def test_all(olite):
    olite.groups.create('group1')
    olite.groups.create('group2')
    olite.groups.create('group3')
    listdir = os.listdir(os.path.join(olite.admin_repository, 'conf', 'groups'))
    assert len(listdir) == 3
    assert sorted(listdir) == ['group1.conf', 'group2.conf', 'group3.conf']

def test_delete(olite, group1):
    assert os.path.exists(group1.config) is True
    assert olite.groups.delete('group1') is True
    assert os.path.exists(group1.config) is False

def test_delete_not_exist(olite):
    assert olite.groups.delete('group2') is False

def test_add_user(olite, group1, user_factory):
    user_factory('user1')
    assert olite.groups.user_add('group1', 'user1') is True
    assert open(group1.config).read() == "@group1 = user1\n"

def test_add_user_idempotent(olite, group1, user_factory):
    user_factory('user1')
    assert olite.groups.user_add('group1', 'user1') is True
    assert olite.groups.user_add('group1', 'user1') is True
    assert open(group1.config).read() == "@group1 = user1\n"

def test_add_user_invalid(olite, group1, user_factory):
    assert olite.groups.user_add('group1', 'user1') is False
    #
    user_factory('user1')
    assert olite.groups.user_add('group2', 'user1') is False
    #
    assert open(group1.config).read() == ""

def test_delete_user(olite, group1, user_factory):
    user_factory('user1')
    user_factory('user2')
    user_factory('user3')
    olite.groups.user_add('group1', 'user1')
    olite.groups.user_add('group1', 'user2')
    olite.groups.user_add('group1', 'user3')
    assert open(group1.config).read() == "@group1 = user1\n@group1 = user2\n@group1 = user3\n"
    #Delete user2
    assert olite.groups.user_delete('group1', 'user2') is True
    assert open(group1.config).read() == "@group1 = user1\n@group1 = user3\n"
    #Delete user1
    assert olite.groups.user_delete('group1', 'user1') is True
    assert open(group1.config).read() == "@group1 = user3\n"
    #Delete user3
    assert olite.groups.user_delete('group1', 'user3') is True
    assert open(group1.config).read() == ""

def test_delete_user_idempotent(olite, group1, user_factory):
    user_factory('user1')
    assert olite.groups.user_add('group1', 'user1')
    assert open(group1.config).read() == "@group1 = user1\n"
    #
    assert olite.groups.user_delete('group1', 'user1') is True
    assert open(group1.config).read() == ""
    #
    assert olite.groups.user_delete('group1', 'user1') is True
    assert open(group1.config).read() == ""

def test_delete_user_invalid(olite, group1, user_factory):
    assert olite.groups.user_delete('group1', 'user1') is False
    #
    user_factory('user1')
    assert olite.groups.user_delete('group2', 'user1') is False
