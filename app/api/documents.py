from fastapi import APIRouter, Depends, BackgroundTasks, status
from .. import repository, services
from ..schemas import(
    DocumentRequest, DocumentResponse, AsyncDocumentRequest
)
from ..security import get_api_key

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    dependencies=[Depends(get_api_key)],
)

@router.post("/generate/sync", response_model=DocumentResponse)
def generate_document_sync(req: DocumentRequest):
    user = repository.get_user_by_id(req.user_id)
    link = services.generate_fake_document(user, req.content_type)
    return DocumentResponse(message="Документ сгенерирован", document_url=link)


@router.post("/generate/async", status_code=status.HTTP_202_ACCEPTED)
def generate_document_async(
    req: AsyncDocumentRequest,
    tasks: BackgroundTasks
):
    user = repository.get_user_by_id(req.user_id)
    tasks.add_task(
        services.generate_and_send_callback,
        req.user_id,
        req.content_type,
        req.callback_url
    )
    return {"message": "Задача по генерацию документа принята"}
