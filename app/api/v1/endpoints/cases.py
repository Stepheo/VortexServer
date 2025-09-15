"""Case endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import random
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.case import get_case_dao, CaseDAO
from app.models.case import Case

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseBase(BaseModel):
    name: str
    img: Optional[str] = None
    price: float


class CaseCreate(CaseBase):
    gift_ids: List[int] = []


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    img: Optional[str] = None
    price: Optional[float] = None
    gift_ids: Optional[List[int]] = None


@router.get("/", response_model=List[dict])
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    dao = get_case_dao(session)
    cases = await dao.get_all(skip=skip, limit=limit)
    out = []
    for c in cases:
        d = c.to_dict()
        out.append(d)
    return out


@router.get("/{case_id}", response_model=dict)
async def get_case(case_id: int, session: AsyncSession = Depends(get_async_session)):
    dao = get_case_dao(session)
    c = await dao.get_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    # Возвращаем массив объектов подарков (словарей)
    gift_objs = []
    for g in c.gifts:
        gd = g.to_dict()
        gd.pop('real_rarity', None)
        gd.pop('visual_rarity', None)
        gift_objs.append(gd)
    return c.to_dict() | {"gifts": gift_objs}


@router.post("/{case_id}/open-case", response_model=dict, summary="Открыть кейс: рулетка 111 элементов")
async def open_case(case_id: int, session: AsyncSession = Depends(get_async_session)):
    """Открыть кейс и вернуть структуру рулетки.

    Требования:
    - Массив из 111 элементов (дубликаты допустимы) формируется по распределению visual_rarity.
    - Выпавший приз выбирается отдельно по real_rarity.
    - Случайный индекс в диапазоне [90, 100] (включительно) заменяется на реально выпавший приз.
    - Поля created_at / updated_at / real_rarity / visual_rarity не возвращаем.

    Ответ:
    {
        "gifts": [ {gift}, {gift}, ... (111 шт) ... ],
        "drop_index": <int>
    }
    """
    dao = get_case_dao(session)
    c = await dao.get_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    if not c.gifts:
        raise HTTPException(status_code=400, detail="Case is empty")

    # Подготовка исходных данных (оригинальные gift объекты)
    gifts = list(c.gifts)

    # --- Выбор выигрышного подарка по real_rarity ---
    real_weights: list[float] = []
    for g in gifts:
        try:
            w = float(getattr(g, 'real_rarity', 0) or 0)
        except Exception:
            w = 0.0
        real_weights.append(max(w, 0.0))
    total_real = sum(real_weights)
    if total_real <= 0:
        winner = random.choice(gifts)
    else:
        r = random.random() * total_real
        acc = 0.0
        winner = gifts[0]
        for g, w in zip(gifts, real_weights):
            acc += w
            if r <= acc:
                winner = g
                break

    # --- Формирование рулетки по visual_rarity ---
    VISUAL_LEN = 111
    visual_weights: list[float] = []
    for g in gifts:
        try:
            wv = float(getattr(g, 'visual_rarity', 0) or 0)
        except Exception:
            wv = 0.0
        visual_weights.append(max(wv, 0.0))
    total_visual = sum(visual_weights)

    roulette: list[dict] = []
    if total_visual <= 0:
        # Равномерно
        for _ in range(VISUAL_LEN):
            g = random.choice(gifts)
            d = g.to_dict()
            d.pop('real_rarity', None)
            d.pop('visual_rarity', None)
            roulette.append(d)
    else:
        # Для каждого слота делаем независимый weighted pick
        cumulative = []
        acc_v = 0.0
        for wv in visual_weights:
            acc_v += wv
            cumulative.append(acc_v)
        for _ in range(VISUAL_LEN):
            rv = random.random() * total_visual
            # линейный поиск (список предположительно короткий)
            for idx, bound in enumerate(cumulative):
                if rv <= bound:
                    g = gifts[idx]
                    break
            else:  # fallback
                g = gifts[-1]
            d = g.to_dict()
            d.pop('real_rarity', None)
            d.pop('visual_rarity', None)
            roulette.append(d)

    # --- Вставляем победителя в диапазон 90..100 ---
    drop_index = random.randint(90, 100)  # включительно
    winner_dict = winner.to_dict()
    winner_dict.pop('real_rarity', None)
    winner_dict.pop('visual_rarity', None)
    roulette[drop_index] = winner_dict

    return {"gifts": roulette, "drop_index": drop_index}


@router.post("/", response_model=dict)
async def create_case(data: CaseCreate, session: AsyncSession = Depends(get_async_session)):
    dao: CaseDAO = get_case_dao(session)
    case = await dao.create(name=data.name, img=data.img, price=data.price)
    if data.gift_ids:
        case = await dao.add_gifts(case.id, data.gift_ids)
    return case.to_dict() | {"gift_ids": [g.id for g in case.gifts]}


@router.put("/{case_id}", response_model=dict)
async def update_case(case_id: int, data: CaseUpdate, session: AsyncSession = Depends(get_async_session)):
    dao: CaseDAO = get_case_dao(session)
    case = await dao.get_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if any([data.name, data.img, data.price is not None]):
        case = await dao.update(case_id, **{k: v for k, v in data.model_dump(exclude_unset=True).items() if k in {"name", "img", "price"}})

    if data.gift_ids is not None:
        # Полная замена списка подарков
        case.gifts.clear()
        await session.commit()
        if data.gift_ids:
            case = await dao.add_gifts(case_id, data.gift_ids)
        else:
            case = await dao.get_by_id(case_id)

    return case.to_dict() | {"gift_ids": [g.id for g in case.gifts]}


@router.post("/{case_id}/gifts", response_model=dict)
async def add_gifts(case_id: int, gift_ids: List[int], session: AsyncSession = Depends(get_async_session)):
    dao: CaseDAO = get_case_dao(session)
    case = await dao.add_gifts(case_id, gift_ids)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.to_dict() | {"gift_ids": [g.id for g in case.gifts]}


@router.delete("/{case_id}", response_model=dict)
async def delete_case(case_id: int, session: AsyncSession = Depends(get_async_session)):
    dao = get_case_dao(session)
    deleted = await dao.delete(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"message": "Case deleted"}
