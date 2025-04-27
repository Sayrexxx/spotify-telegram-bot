from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db_setup import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    url = Column(String, nullable=False)
    duration = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    tracks = relationship("PlaylistTrack", back_populates="playlist")


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(
        Integer, ForeignKey("playlists.id"), nullable=False, index=True
    )
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    playlist = relationship("Playlist", back_populates="tracks")
