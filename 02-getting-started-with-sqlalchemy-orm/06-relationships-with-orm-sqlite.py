import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, Table, Column 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 
from sqlalchemy.sql import select 
from sqlalchemy.orm import joinedload, subqueryload, selectinload # Eager loading Strategies

## Configuration for Database Connection 
# SQLite uses a file-based database.
# The 'relationships.db' file will be created in the same directory as the script.
DATABASE_URL = "sqlite:///relationships.db"

# Defining the Declarative Base Class
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass

# Association Table for Many to Many 
# This is a core table definition, no an ORM Model
# It explicitly defines the intermediate table for the many-to-many relationship
post_tags_association = Table(
    "post_tags",
    Base.metadata, # Associate with the same metadata as ORM models
    Column("post_id", ForeignKey('posts.id'), primary_key=True),
    Column("tag_id", ForeignKey('tags.id'), primary_key=True),
)

# Defining ORM Models
class User(Base):
    """ORM Model for User Table"""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # One-to-Many relationship with Post
    posts: Mapped[List['Post']] = relationship(back_populates='author', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, email={self.email!r})'
    
class Post(Base):
    """ORM Model for Post Table"""
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))

    # Many-to-One relationship with User
    author: Mapped[Optional['User']] = relationship(back_populates='posts')

    # Many-to-Many relationship with Tag
    tags: Mapped[List['Tag']] = relationship(secondary=post_tags_association, back_populates='posts')

    def __repr__(self) -> str:
        return f'Post(id={self.id!r}, title={self.title!r})'
    
class Tag(Base):
    """ORM Model for Tag Table"""
    __tablename__ = 'tags'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    # Many-to-May relationship with Post
    posts: Mapped[List['Post']] = relationship(secondary=post_tags_association, back_populates='tags')

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r})'    
    

# Helper function to setup and populate data
def setup_orm_data_for_relationships(engine):
    """Setting up the Data Tables with Data"""
    print(f'\n#------------------------------- ℹ️ Setting Up Tables with data ---------------------------------#\n')
    # Dropping all tables if exists
    Base.metadata.drop_all(engine)
    # Creating all tables 
    Base.metadata.create_all(engine)    
    print(f'✅ Database Tables Creted Successfully')

    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        # Create Users
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        session.add_all([user1, user2])
        session.commit()

        # Create posts and assign to users
        # Note: We can create posts and assign author directly
        post1 = Post(title="Alice's First Post", content="Content for A1", author=user1)
        post2 = Post(title="Bob's Important Post", content="Content for B1", author=user2)
        post3 = Post(title="Alice's Second Post", content="Content for A2", author=user1)
        post4 = Post(title="Standalone Post", content="No author yet") # Will have user_id=None
        session.add_all([post1, post2, post3, post4])
        session.commit()

        # Create tags
        tag_python = Tag(name="Python")
        tag_sqlalchemy = Tag(name="SQLAlchemy")
        tag_webdev = Tag(name="WebDev")
        session.add_all([tag_python, tag_sqlalchemy, tag_webdev])
        session.commit()

        # Associate posts with tags (Many-to-Many)
        # post1 (Alice's First Post) will have Python and SQLAlchemy tags
        post1.tags.append(tag_python)
        post1.tags.append(tag_sqlalchemy)
        # post2 (Bob's Important Post) will have Python and WebDev tags
        post2.tags.append(tag_python)
        post2.tags.append(tag_webdev)
        # post3 (Alice's Second Post) will have SQLAlchemy tag
        post3.tags.append(tag_sqlalchemy)

        session.commit()
        print(f'✅ Initial Data Populated for Relationships Examples.....')

# Perform Relationship and Loading Strategy Examples
def perform_relationship_operations(engine):
    """Performing Relationship and Loading Strategy Examples"""
    print(f'\n#-------------------------- ℹ️ Relationship Operations and Loading Strategies -------------------------#\n')

    # 1. Lazy Loading (Default)
    print(f'\n#--------------------------- ℹ️ Lazy Loading (Default) ---------------------------------#\n')
    
    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        users = session.execute(
            select(User)
        ).scalars().all()

        # Looping through Users
        for user in users:
            print(f'User: {user.name}')
            # Now Accessing user.posts here triggers a separate SELECT for each user
            for post in user.posts:
                print(f'   - Post: {post.title}')

            print(f'\n    - Tags for {user.name}\'s first post: if any')
            if user.posts:
                # Accessing post.tags here triggers another SELECT for each post
                for tag in user.posts[0].tags:
                    print(f'      - Tag: {tag.name}')
            else:
                print(f'ℹ️ No Posts for this user yet')
    
    # 2. Eager Loading with joinedload
    print(f'\n#--------------------------- ℹ️ Eager Loading with joinedload ---------------------------------#\n')
    
    
    with Session() as session:
        # Using one query a JOIN to fetch users and their posts
        print(f'\nℹ️ Eager Loading for User -> Posts\n')
        users_with_posts = session.execute(
            select(User).options(joinedload(User.posts))
        ).unique().scalars().all()

        for user in users_with_posts:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional query here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
        print(f'\nℹ️ Eager Loading for User -> Posts -> Tags\n')
        users_with_posts_and_tags = session.execute(
            select(User).options(joinedload(User.posts).joinedload(Post.tags))
        ).unique().scalars().all()

        for user in users_with_posts_and_tags:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            for post in user.posts:
                print(f'.   - Post: {post.title}, Tags loaded: {len(post.tags)}')
                if post.tags:
                    for tag in post.tags:
                        print(f'      - Tag: {tag.name}')
            
    
    # 3.  Eager Loading with subqueryload for User -> Posts
    print(f'\n#--------------------------- ℹ️ Eager Loading with subqueryload ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using subquery
        users = session.execute(
            select(User).options(subqueryload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
    
    # 4. Eager Loading with selectinload (Recommended for collection)
    print(f'\n#--------------------------- ℹ️ Eager Loading with selectinload (Recommended) ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using an IN clause (very efficient)
        users = session.execute(
            select(User).options(selectinload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
    # 5. Combined Eager Loading (User -> Posts -> Tags)
    print(f'\n#--------------------------- ℹ️ Eager Loading Combined (User -> Posts -> Tags) --------------------#\n')
    with Session() as session: 
        # Fetch users, their posts, and posts' tags in efficient queries
        users = session.execute(
            select(User).options(
                selectinload(User.posts).selectinload(Post.tags) # Chain selectinload for nested collections
            )
        ).scalars().all()
        for user in users:
            print(f"User: {user.name}")
            for post in user.posts:
                tag_names = [tag.name for tag in post.tags]
                print(f"  - Post: {post.title}, Tags: {', '.join(tag_names) if tag_names else 'None'}")
        

    # 6. Cascade "delete-orphan" demonstration
    print("\n#--------------- ℹ️ Cascade 'delete-orphan' Demo (removing a post from user.posts) --------------------#")
    with Session() as session:
        alice = session.execute(select(User).where(User.name == "Alice")).scalar_one_or_none()
        if alice and alice.posts:
            original_post_count = session.query(Post).count()
            print(f"ℹ️ Initial total posts: {original_post_count}")
            post_to_remove = alice.posts[0] # Get Alice's first post
            print(f"ℹ️ Removing '{post_to_remove.title}' from Alice's posts collection...")
            alice.posts.remove(post_to_remove) # This marks post_to_remove as an orphan
            session.commit() # The orphaned post will be deleted here            
            print(f"✅ Post '{post_to_remove.title}' should now be deleted from DB.")
            new_post_count = session.query(Post).count()
            print(f"ℹ️ New total posts: {new_post_count}")
            # Verify the specific post is gone
            if not session.execute(select(Post).where(Post.id == post_to_remove.id)).scalar_one_or_none():
                print(f"✅ Verification: Post with ID {post_to_remove.id} is indeed gone.")
        else:
            print("ℹ️ Alice or her posts not found for cascade demo.")

# Main Execution Block
if __name__ == "__main__":
    # Create an Engine
    engine = create_engine(DATABASE_URL, echo=True)
    # Setup Data
    setup_orm_data_for_relationships(engine)
    # Perform Operations
    perform_relationship_operations(engine)