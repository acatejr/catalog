from datetime import datetime

from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.orm import Session


# Base = declarative_base()

class Base(DeclarativeBase):
    pass

class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=True, unique=True)
    description = Column(Text, nullable=True, unique=False)
    metadata_url = Column(String(500), nullable=True, unique=True)

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
    session = Session(engine)

    assets = []
    for i in range(0, 100):
        assets.append(
            Asset(title=f"Asset Title {i}", description=f"Description {i}", metadata_url=f"https://{i}")
        )


    session.add_all(assets)
    session.commit()

    assets = session.query(Asset).all()
    print(assets)

    #  # create catalog
    # tshirt, mug, hat, crowbar = (
    #     Item("SA T-Shirt", 10.99),
    #     Item("SA Mug", 6.50),
    #     Item("SA Hat", 8.99),
    #     Item("MySQL Crowbar", 16.99),
    # )
    # session.add_all([tshirt, mug, hat, crowbar])
    # session.commit()


# class Order(Base):
#     __tablename__ = "order"

#     order_id = Column(Integer, primary_key=True)
#     customer_name = Column(String(30), nullable=False)
#     order_date = Column(DateTime, nullable=False, default=datetime.now())
#     order_items = relationship(
#         "OrderItem", cascade="all, delete-orphan", backref="order"
#     )

#     def __init__(self, customer_name):
#         self.customer_name = customer_name
