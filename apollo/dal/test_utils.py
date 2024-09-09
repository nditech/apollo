import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.declarative import declarative_base

from apollo.dal.utils import has_model

BaseModel = declarative_base()


class User(BaseModel):
    __tablename__ = 'users'
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Address(BaseModel):
    __tablename__ = 'addresses'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    email = sa.Column(sa.String)
    
    user = so.relationship('User', backref='addresses')


@pytest.fixture(scope='module')
def engine():
    engine = sa.create_engine('sqlite:///:memory:')
    BaseModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='function')
def session(engine):
    Session = so.sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_has_model_with_single_model(session):
    query = session.query(User)
    assert has_model(query, User)
    assert not has_model(query, Address)

def test_has_model_with_joined_model(session):
    query = session.query(User).join(User.addresses)
    assert has_model(query, User)
    assert has_model(query, Address)

def test_has_model_with_no_model(session):
    query = session.query(User).filter(User.id == 1)
    assert has_model(query, User)
    assert not has_model(query, Address)
