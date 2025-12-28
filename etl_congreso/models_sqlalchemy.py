from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    MetaData,
    Index,
    func,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

# Definimos que estos modelos pertenecen al esquema 'silver'
metadata = MetaData(schema="silver")
Base = declarative_base(metadata=metadata)


class Autonomia(Base):
    __tablename__ = "autonomia"

    ine_code = Column(Text, primary_key=True)
    nombre = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Provincia(Base):
    __tablename__ = "provincia"

    ine_code = Column(Text, primary_key=True)
    auto_code = Column(Text, ForeignKey("silver.autonomia.ine_code"))
    nombre = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Municipio(Base):
    __tablename__ = "municipio"

    prov_code = Column(Text, ForeignKey("silver.provincia.ine_code"), primary_key=True)
    muni_code = Column(Text, primary_key=True)
    nombre = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Eleccion(Base):
    __tablename__ = "eleccion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    tipo = Column(Text, nullable=False)
    auto_id = Column(Text, ForeignKey("silver.autonomia.ine_code"), nullable=True)
    prov_id = Column(Text, nullable=True)
    muni_id = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ano", "mes", "tipo", "auto_id", "prov_id", "muni_id", name="eleccion_unique_idx"
        ),
        # FK compuesta manual si fuera necesaria, pero por simplicidad solo referenciamos IDs simples o lógica app
    )


class Partido(Base):
    __tablename__ = "partido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(Text, nullable=False)
    siglas = Column(Text)
    color = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PartidoEleccion(Base):
    __tablename__ = "partido_eleccion"

    partido_id = Column(UUID(as_uuid=True), ForeignKey("silver.partido.id"), primary_key=True)
    eleccion_id = Column(UUID(as_uuid=True), ForeignKey("silver.eleccion.id"), primary_key=True)
    siglas_eleccion = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("eleccion_id", "siglas_eleccion", name="partido_eleccion_siglas_unique"),
    )


class Mesa(Base):
    __tablename__ = "mesa"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cod_prov = Column(Text, nullable=False)
    cod_muni = Column(Text, nullable=False)
    cod_distrito = Column(Text, nullable=False)
    cod_seccion = Column(Text, nullable=False)
    cod_mesa = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "cod_prov",
            "cod_muni",
            "cod_distrito",
            "cod_seccion",
            "cod_mesa",
            name="mesa_unique_idx",
        ),
    )


class Voto(Base):
    __tablename__ = "voto"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mesa_id = Column(UUID(as_uuid=True), ForeignKey("silver.mesa.id"), nullable=False)
    eleccion_id = Column(UUID(as_uuid=True), ForeignKey("silver.eleccion.id"), nullable=False)
    candidatura = Column(UUID(as_uuid=True), ForeignKey("silver.partido.id"), nullable=False)
    votos = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("mesa_id", "eleccion_id", "candidatura", name="voto_unique_idx"),
    )
