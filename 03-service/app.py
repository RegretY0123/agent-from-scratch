import logging

from agent import run_agent
from deps import get_llm_client
from errors import ServiceError, translate
from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from logging_setup import setup_logging
from models import ChatRequest, ChatResponse
from openai import OpenAI

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent服务", description="把02里手写的循环包装成HTTP接口", version="0.1.0"
)


def error_body(code, message, detail=None):
    body = {"error": {"code": code, "message": message}}
    if detail is not None:
        body["error"]["detail"] = detail
    return body


@app.exception_handler(ServiceError)
async def handle_service_error(request: Request, exc: ServiceError):
    if exc.status_code >= 500:
        logger.exception("业务异常%s", exc.code)
    else:
        logger.warning("业务异常：%s，%s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.code, exc.message)
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_body(
            "VALIDATION_ERROR", "请求参数不合法", jsonable_encoder(exc.errors())
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("未处理的异常")
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "服务器内部错误，请稍后重试"),
    )


@app.post("/v1/chat", summary="问Agent一个问题")
def chat(req: ChatRequest, client: OpenAI = Depends(get_llm_client)) -> ChatResponse:
    try:
        return run_agent(req.message, client=client)
    except Exception as exc:
        raise translate(exc) from exc
