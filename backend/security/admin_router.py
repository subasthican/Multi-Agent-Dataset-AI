from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from agents.discovery_agent import vector_store
from agents.discovery_agent.models import CatalogDatasetCreate, CatalogDatasetResponse, CatalogDatasetUpdate

from .authentication import get_current_admin_user
from .db import get_db
from .db_models import CatalogDataset, Plan, SearchHistory, User
from .schemas import (
    AdminSearchHistoryItem,
    AdminStatsResponse,
    AdminUpdateUserRequest,
    AdminUserDetailResponse,
    AdminUserResponse,
    PlanCreateRequest,
    PlanResponse,
    PlanUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])

SORT_OPTIONS = {"newest", "oldest", "most_searches", "name"}
MAX_DETAIL_HISTORY = 100


def _valid_plan_names(db: Session) -> set[str]:
    """Plans are admin-managed now (see /admin/plans below), not a fixed
    set — this replaces what used to be a hardcoded {"free", "pro"}."""
    return {name for (name,) in db.query(Plan.name).all()}


def _to_admin_user_response(db: Session, user: User) -> AdminUserResponse:
    search_count = db.query(func.count(SearchHistory.id)).filter(SearchHistory.user_id == user.id).scalar()
    return AdminUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        plan=user.plan,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        search_count=search_count or 0,
    )


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    q: str | None = Query(default=None, description="Case-insensitive substring match on name or email"),
    plan: str | None = Query(default=None, description="Exact plan name"),
    is_admin: bool | None = None,
    is_active: bool | None = None,
    sort: str = Query(default="newest", description=f"One of {sorted(SORT_OPTIONS)}"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    if sort not in SORT_OPTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sort must be one of {sorted(SORT_OPTIONS)}")

    counts = dict(db.query(SearchHistory.user_id, func.count(SearchHistory.id)).group_by(SearchHistory.user_id).all())

    query = db.query(User)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(func.lower(User.name).like(like) | func.lower(User.email).like(like))
    if plan is not None:
        query = query.filter(User.plan == plan)
    if is_admin is not None:
        query = query.filter(User.is_admin.is_(is_admin))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    if sort == "oldest":
        query = query.order_by(User.created_at.asc())
    elif sort == "name":
        query = query.order_by(func.lower(User.name).asc())
    else:
        # "most_searches" still needs the in-memory counts dict below (a
        # per-user aggregate, not a plain column) — sorted after fetching.
        query = query.order_by(User.created_at.desc())

    users = query.all()
    if sort == "most_searches":
        users = sorted(users, key=lambda u: counts.get(u.id, 0), reverse=True)

    return [
        AdminUserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            plan=u.plan,
            is_admin=u.is_admin,
            is_active=u.is_active,
            created_at=u.created_at,
            search_count=counts.get(u.id, 0),
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def get_user_detail(user_id: str, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """Single-user profile plus their raw search history (not just the
    aggregated domain/task mode recommendation_agent/agent.py's
    _build_profile computes) — for a support/admin view into what a
    specific account has actually been searching."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    history = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(MAX_DETAIL_HISTORY)
        .all()
    )
    base = _to_admin_user_response(db, user)
    return AdminUserDetailResponse(
        **base.model_dump(),
        search_history=[AdminSearchHistoryItem.model_validate(h) for h in history],
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    payload: AdminUpdateUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """The only way to change a user's plan right now — no billing is wired
    up, so this is how "upgrading to Pro" actually happens today. Guards
    against an admin accidentally revoking their own admin access or
    suspending themselves, since there's no other bootstrapping path back in
    (see scripts/promote_admin.py)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.plan is not None:
        valid_plans = _valid_plan_names(db)
        if payload.plan not in valid_plans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"plan must be one of {sorted(valid_plans)}"
            )
        user.plan = payload.plan

    if payload.is_admin is not None:
        if user.id == current_admin.id and not payload.is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove your own admin access")
        user.is_admin = payload.is_admin

    if payload.is_active is not None:
        if user.id == current_admin.id and not payload.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend your own account")
        user.is_active = payload.is_active

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
        catalog_size=count(db.query(func.count(CatalogDataset.id))),
    )


@router.get("/catalog", response_model=list[CatalogDatasetResponse])
def list_catalog(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(CatalogDataset).order_by(CatalogDataset.created_at).all()


@router.post("/catalog", response_model=CatalogDatasetResponse, status_code=status.HTTP_201_CREATED)
def create_catalog_entry(
    payload: CatalogDatasetCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    entry = CatalogDataset(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    vector_store.invalidate_cache()
    return entry


@router.patch("/catalog/{dataset_id}", response_model=CatalogDatasetResponse)
def update_catalog_entry(
    dataset_id: str,
    payload: CatalogDatasetUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    entry = db.get(CatalogDataset, dataset_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    vector_store.invalidate_cache()
    return entry


@router.delete("/catalog/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_entry(
    dataset_id: str, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    entry = db.get(CatalogDataset, dataset_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    db.delete(entry)
    db.commit()
    vector_store.invalidate_cache()


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.created_at).all()


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreateRequest, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    if db.query(Plan).filter(Plan.name == payload.name).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'A plan named "{payload.name}" already exists')

    plan = Plan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    payload: PlanUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """name is intentionally not editable here — it's the stable key
    User.plan stores, and this project doesn't do a User-row rewrite on
    rename (see the Plan model's own docstring)."""
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    updates = payload.model_dump(exclude={"clear_search_limit"}, exclude_unset=True)
    for field, value in updates.items():
        setattr(plan, field, value)

    if payload.clear_search_limit:
        plan.daily_search_limit = None

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    users_on_plan = db.query(func.count(User.id)).filter(User.plan == plan.name).scalar() or 0
    if users_on_plan > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{users_on_plan} user(s) are still on this plan — move them to another plan first",
        )

    db.delete(plan)
    db.commit()
