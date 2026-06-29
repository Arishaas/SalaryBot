import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import products
from app.bot import create_bot, create_dispatcher
from app.scheduler import create_scheduler

import app.models.user  # noqa: F401
import app.models.product  # noqa: F401
import app.models.price_history  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot = create_bot()
    dp = create_dispatcher()
    scheduler = create_scheduler(bot)

    polling_task = asyncio.create_task(dp.start_polling(bot))
    scheduler.start()

    app.state.bot = bot
    app.state.scheduler = scheduler

    yield

    scheduler.shutdown(wait=False)
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()


app = FastAPI(title="Price Tracker Bot", lifespan=lifespan)

Base.metadata.create_all(bind=engine)

app.include_router(products.router)


@app.get("/test")
def root():
    return {"message": "🚀 API работает!"}
