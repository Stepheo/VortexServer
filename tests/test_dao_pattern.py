"""Test DAO pattern implementation."""

import pytest
from unittest.mock import Mock

from app.dao.base import BaseDAO
from app.dao.user import UserDAO
from app.models.user import User


def test_base_dao_pattern():
    """Test the base DAO pattern can be used correctly."""
    mock_session = Mock()
    
    # Test BaseDAO can be instantiated
    dao = BaseDAO(User, mock_session)
    assert dao.model == User
    assert dao.session == mock_session


def test_user_dao_extends_base_dao():
    """Test UserDAO properly extends BaseDAO."""
    mock_session = Mock()
    
    user_dao = UserDAO(mock_session)
    
    # Should inherit from BaseDAO
    assert isinstance(user_dao, BaseDAO)
    assert user_dao.model == User
    assert user_dao.session == mock_session


def test_user_dao_has_specialized_methods():
    """Test UserDAO has specialized methods."""
    mock_session = Mock()
    user_dao = UserDAO(mock_session)
    
    # Check specialized methods exist
    assert hasattr(user_dao, 'get_by_username')
    assert hasattr(user_dao, 'get_by_email') 
    assert hasattr(user_dao, 'get_by_id_cached')
    assert hasattr(user_dao, 'get_all_cached')
    assert hasattr(user_dao, 'search_users')
    assert hasattr(user_dao, 'get_user_count')
    
    # Check methods are callable
    assert callable(user_dao.get_by_username)
    assert callable(user_dao.get_by_email)
    assert callable(user_dao.get_by_id_cached)
    assert callable(user_dao.get_all_cached)
    assert callable(user_dao.search_users)
    assert callable(user_dao.get_user_count)


def test_dao_factory_functions():
    """Test DAO factory functions work correctly."""
    from app.dao.base import get_dao
    from app.dao.user import get_user_dao
    
    mock_session = Mock()
    
    # Test generic factory
    base_dao = get_dao(User, mock_session)
    assert isinstance(base_dao, BaseDAO)
    assert base_dao.model == User
    
    # Test specialized factory
    user_dao = get_user_dao(mock_session)
    assert isinstance(user_dao, UserDAO)
    assert user_dao.model == User


def test_user_dao_imports():
    """Test UserDAO can be imported from different locations."""
    # Test direct import
    from app.dao.user import UserDAO, get_user_dao
    assert UserDAO is not None
    assert get_user_dao is not None
    
    # Test import from dao module
    from app.dao import UserDAO as DAOUserDAO, get_user_dao as dao_get_user_dao
    assert DAOUserDAO is not None
    assert dao_get_user_dao is not None
    
    # Should be the same classes
    assert UserDAO == DAOUserDAO
    assert get_user_dao == dao_get_user_dao


if __name__ == "__main__":
    pytest.main([__file__, "-v"])