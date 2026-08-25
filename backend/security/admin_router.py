from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .authentication import get_current_admin_user
from .db import get_db
from .db_models import SearchHistory, User
from .schemas import AdminStatsResponse, AdminUpdateUserRequest, AdminUserResponse

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_PLANS = {"free", "pro"}


def _to_admin_user_response(db: Session, user: User) -> AdminUserResponse:
    search_count = db.query(func.count(SearchHistory.id)).filter(SearchHistory.user_id == user.id).scalar()
    return AdminUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        plan=user.plan,
        is_admin=user.is_admin,
        created_at=user.created_at,
        search_count=search_count or 0,
    )


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    counts = dict(db.query(SearchHistory.user_id, func.count(SearchHistory.id)).group_by(SearchHistory.user_id).all())
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        AdminUserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            plan=u.plan,
            is_admin=u.is_admin,
            created_at=u.created_at,
            search_count=counts.get(u.id, 0),
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    payload: AdminUpdateUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """The only way to change a user's plan right now — no billing is wired
    up, so this is how "upgrading to Pro" actually happens today. Guards
    against an admin accidentally revoking their own admin access, since
    there's no other bootstrapping path back in (see scripts/promote_admin.py)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.plan is not None:
        if payload.plan not in VALID_PLANS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"plan must be one of {sorted(VALID_PLANS)}"
            )
        user.plan = payload.plan

    if payload.is_admin is not None:
        if user.id == current_admin.id and not payload.is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove your own admin access")
        user.is_admin = payload.is_admin

    db.commit()
    db.refresh(user)
    return _to_admin_user_response(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    if user_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account here")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)  # cascades to their reset tokens + search history (see db_models.py relationships)
    db.commit()


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    def count(query) -> int:
        return query.scalar() or 0

    return AdminStatsResponse(
        total_users=count(db.query(func.count(User.id))),
        pro_users=count(db.query(func.count(User.id)).filter(User.plan == "pro")),
        admin_users=count(db.query(func.count(User.id)).filter(User.is_admin.is_(True))),
        total_searches=count(db.query(func.count(SearchHistory.id))),
        searches_via_llm=count(db.query(func.count(SearchHistory.id)).filter(SearchHistory.understanding_source == "llm")),
        searches_via_rule_based=count(
            db.query(func.count(SearchHistory.id)).filter(SearchHistory.understanding_source == "rule_based")
        ),
    )
