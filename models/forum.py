from datetime import datetime
from typing import List

from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.users import Users
from database.database import Base

class Categories(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(32))
    required_role: Mapped[str | None] = mapped_column(String(16), nullable=True)

    subcategories: Mapped[List["SubCategories"]] = relationship(back_populates="category")

class SubCategories(Base):
    __tablename__ = "sub_categories"

    name: Mapped[str] = mapped_column(String(32))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"))
    required_role: Mapped[str | None] = mapped_column(String(16), nullable=True)

    category: Mapped["Categories"] = relationship(foreign_keys=[category_id])

class Posts(Base):
    __tablename__ = "posts"

    title: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)
    views: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    subcategory_id: Mapped[int] = mapped_column(Integer, ForeignKey("sub_categories.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    allow_comms: Mapped[bool] = mapped_column(Boolean, server_default="1")
    is_pinned: Mapped[bool] = mapped_column(Boolean, server_default="0")

    author: Mapped["Users"] = relationship(foreign_keys=[author_id])
    subcategory: Mapped["SubCategories"] = relationship(foreign_keys=[subcategory_id])
    images: Mapped[List["PostImages"]] = relationship(back_populates="post")


class PostImages(Base):
    __tablename__ = "post_images"

    path: Mapped[str] = mapped_column(String(128))
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))

    post: Mapped["Posts"] = relationship(back_populates="images", foreign_keys=[post_id])

class PostComments(Base):
    __tablename__ = "post_comments"

    body: Mapped[str] = mapped_column(Text)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)

    post: Mapped["Posts"] = relationship(foreign_keys=[post_id])
    author: Mapped["Users"] = relationship(foreign_keys=[author_id])

class CommentsLikes(Base):
    __tablename__ = "comments_likes"

    comment_id: Mapped[int] = mapped_column(Integer, ForeignKey("post_comments.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

class PostLikes(Base):
    __tablename__ = "post_likes"

    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

class Reports(Base):
    __tablename__ = "reports"

    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    additional_info: Mapped[str] = mapped_column(Text, nullable=True)

    post: Mapped["Posts"] = relationship(foreign_keys=[post_id])
    user: Mapped["Users"] = relationship(foreign_keys=[user_id])


class VisibilityOptions(Base):
    __tablename__ = "f_visibility_options"

    name: Mapped[str] = mapped_column(String(32))