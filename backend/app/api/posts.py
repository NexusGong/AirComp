from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, Post
from app.schemas import PostCreate, PostResponse, UserResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostResponse])
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(2, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Post).order_by(Post.timestamp.desc())
    offset = (page - 1) * per_page
    return q.offset(offset).limit(per_page).all()


@router.get("/user/{username}", response_model=dict)
def user_page(
    username: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(2, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    q = db.query(Post).filter(Post.user_id == user.id).order_by(Post.timestamp.desc())
    offset = (page - 1) * per_page
    posts = q.offset(offset).limit(per_page).all()
    return {"user": UserResponse.model_validate(user), "posts": posts}


@router.post("", response_model=PostResponse)
def create_post(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(body=data.text, user_id=current_user.id)
    current_user.posts.append(post)
    db.commit()
    db.refresh(post)
    return post
