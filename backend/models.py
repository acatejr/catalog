from sqlalchemy import Column, Integer, String, DateTime

# from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
# from typing import Optional
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text

# import enum
# from sqlalchemy import Enum
# import sqlalchemy.types as types

Base = declarative_base()
target_metadata = Base.metadata

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    metadata_url = Column(String(250), unique=False, nullable=True)
    description = Column(String(2500), unique=False, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone="TRUE"), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone="TRUE"),
        nullable=False,
        server_default=text("now()"),
        server_onupdate=text("now()"),
    )

# from sqlalchemy import Column, Integer, String, DateTime
# # from pgvector.sqlalchemy import Vector
# from datetime import datetime
# from sqlalchemy.orm import declarative_base

# Base = declarative_base()
# target_metadata = Base.metadata
# # N_DIM = 1536

# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True)
#     metadata_url = Column(String(250), unique=True, nullable=True)
#     description = Column(String(2500), unique=False, nullable=True)
#     created_at = Column(DateTime, default=datetime.now)
#     updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# from sqlalchemy import Column, Integer, String, DateTime
# from pgvector.sqlalchemy import Vector
# from datetime import datetime
# from sqlalchemy.orm import declarative_base

# Base = declarative_base()
# target_metadata = Base.metadata
# N_DIM = 1536

# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True)
#     identifier = Column(String(125), nullable=True, unique=True)
#     url = Column(String(250), unique=False, nullable=True)
#     description = Column(String(2500), unique=False, nullable=True)
#     created_at = Column(DateTime, default=datetime.now)
#     updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
#     embedding = Vector(N_DIM)

# from sqlalchemy import Column, Integer, String, DateTime

# # from pgvector.sqlalchemy import Vector
# from datetime import datetime
# from sqlalchemy.orm import declarative_base, relationship
# from typing import Optional
# from sqlalchemy.sql.sqltypes import TIMESTAMP
# from sqlalchemy.sql.expression import text
# import enum
# from sqlalchemy import Enum
# import sqlalchemy.types as types

# Base = declarative_base()
# target_metadata = Base.metadata
# # N_DIM = 1536

# # class SourceTypeEnum(enum.Enum):
# #     national_data_set = "National Data Set"
# #     data_gov = "Data.gov"

# class SourceType(types.TypeDecorator):

#     impl = types.String

#     def __init__(self, choices, **kw):
#         self.choices = dict(choices)
#         super(SourceType, self).__init__(**kw)

#     def process_bind_param(self, value, dialect):
#         return [k for k, v in self.choices.iteritems() if v == value][0]

#     def process_result_value(self, value, dialect):
#         return self.choices[value]

# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True)
#     identifier = Column(String(125), nullable=True, unique=True)
#     url = Column(String(250), unique=False, nullable=True)
#     description = Column(String(2500), unique=False, nullable=True)
#     source_type = Column(SourceType({"national_data_set": "National Data Set", "data_dot_gov": "Data.gov"}), nullable=True)

#     # source_type = Column(Enum(SourceTypeEnum))
#     created_at = Column(
#         TIMESTAMP(timezone="TRUE"), nullable=False, server_default=text("now()")
#     )
#     updated_at = Column(
#         TIMESTAMP(timezone="TRUE"),
#         nullable=False,
#         server_default=text("now()"),
#         server_onupdate=text("now()"),
#     )
#     # embedding = Vector(N_DIM)


# class USFSNationalDataset(Base):
#     __tablename__ = "usfs_national_dataset"

#     id = Column(Integer, primary_key=True)
#     title = Column(String(125), nullable=True, unique=True)
#     metadata_url = Column(String(500), unique=True, nullable=True)
#     description = Column(String(2500), unique=False, nullable=True)
#     purpose = Column(String(500), unique=False, nullable=True)
#     created_at = Column(
#         TIMESTAMP(timezone="TRUE"), nullable=False, server_default=text("now()")
#     )
#     updated_at = Column(
#         TIMESTAMP(timezone="TRUE"),
#         nullable=False,
#         server_default=text("now()"),
#         server_onupdate=text("now()"),
#     )
