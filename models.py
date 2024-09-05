from datetime import datetime

from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String, Text, Enum
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.orm import Session
import enum


class Domains(enum.Enum):
    EDW = 1
    DATA_DOT_GOV = 2
    FS_GEODATA = 3
    CRV = 4


class Visibility(enum.Enum):
    PUBLIC = 1
    INTERNAL = 2


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=True, unique=True)
    description = Column(Text, nullable=True, unique=False)
    metadata_url = Column(String(500), nullable=True, unique=True)
    visibility = Column(
        Enum(Visibility), nullable=False, unique=False, default=Visibility.PUBLIC
    )
    domain = Column(Enum(Domains), nullable=False, default=Domains.EDW)

    def __init__(self, title, description=None, metadata_url=None):
        self.title = title
        if description:
            self.description = description
        if metadata_url:
            self.metadata_url = metadata_url

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):
        return f"Asset({self.title})"


if __name__ == "__main__":
    engine = create_engine("sqlite:///catalog.db")
    Base.metadata.create_all(engine)
    session = Session(autoflush=True, bind=engine)

    assets = []
    for i in range(0, 100):
        assets.append(
            Asset(
                title=f"Asset Title {i}",
                description=f"Description {i}",
                metadata_url=f"https://{i}",
            )
        )

    session.add_all(assets)
    session.commit()

    assets = session.query(Asset).all()
    print(assets)
