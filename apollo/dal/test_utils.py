from apollo.dal.utils import has_model
from apollo.users.models import User, UserUpload


def test_has_model_with_single_model(db):
    """Test the existence of a single model."""
    query = db.session.query(User)
    assert has_model(query, User)
    assert not has_model(query, UserUpload)


def test_has_model_with_joined_model(db):
    """Tests the existence of the joined model."""
    query = db.session.query(User).join(User.uploads)
    assert has_model(query, User)
    assert has_model(query, UserUpload)


def test_has_model_with_no_model(db):
    """Test the non-existence of a model when not explicitly specified."""
    query = db.session.query(User).filter(User.id == 1)
    assert has_model(query, User)
    assert not has_model(query, UserUpload)
