import typing
import strawberry
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.query import QueryRecord
from app.models.document import Document
from app.models.audit import AuditLog
from app.agents.orchestrator import run_pipeline

@strawberry.type
class QueryRecordGQL:
    id: int
    query_text: str
    response_text: str
    confidence_score: float
    processing_time_ms: typing.Optional[int]
    created_at: typing.Optional[str]

@strawberry.type
class DocumentGQL:
    id: int
    filename: str
    file_type: str
    status: str
    created_at: typing.Optional[str]

@strawberry.type
class AuditLogGQL:
    id: int
    action: str
    resource: typing.Optional[str]
    ip_address: typing.Optional[str]
    timestamp: typing.Optional[str]

@strawberry.type
class Query:
    @strawberry.field
    def get_queries(self, limit: int = 10, skip: int = 0) -> typing.List[QueryRecordGQL]:
        db: Session = SessionLocal()
        try:
            records = db.query(QueryRecord).order_by(QueryRecord.id.desc()).offset(skip).limit(limit).all()
            return [
                QueryRecordGQL(
                    id=record.id,
                    query_text=record.query_text,
                    response_text=record.response_text or "",
                    confidence_score=record.confidence_score or 0.0,
                    processing_time_ms=record.processing_time_ms,
                    created_at=record.created_at.isoformat() if record.created_at else None
                )
                for record in records
            ]
        finally:
            db.close()

    @strawberry.field
    def get_documents(self, limit: int = 10, skip: int = 0) -> typing.List[DocumentGQL]:
        db: Session = SessionLocal()
        try:
            records = db.query(Document).order_by(Document.id.desc()).offset(skip).limit(limit).all()
            return [
                DocumentGQL(
                    id=record.id,
                    filename=record.filename,
                    file_type=record.file_type,
                    status=record.status,
                    created_at=record.created_at.isoformat() if record.created_at else None
                )
                for record in records
            ]
        finally:
            db.close()

    @strawberry.field
    def get_audit_logs(self, limit: int = 10, skip: int = 0) -> typing.List[AuditLogGQL]:
        db: Session = SessionLocal()
        try:
            records = db.query(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
            return [
                AuditLogGQL(
                    id=record.id,
                    action=record.action,
                    resource=record.resource,
                    ip_address=record.ip_address,
                    timestamp=record.timestamp.isoformat() if record.timestamp else None
                )
                for record in records
            ]
        finally:
            db.close()

@strawberry.type
class Mutation:
    @strawberry.mutation
    def submit_query(self, query: str, user_id: int = 1) -> QueryRecordGQL:
        db: Session = SessionLocal()
        try:
            import time
            start_time = time.time()
            result = run_pipeline(query, user_id=user_id)
            total_ms = int((time.time() - start_time) * 1000)
            
            # Persist query for GraphQL response
            query_rec = QueryRecord(
                user_id=user_id,
                query_text=query,
                response_text=result["answer"],
                confidence_score=result["confidence"],
                processing_time_ms=total_ms
            )
            db.add(query_rec)
            db.commit()
            db.refresh(query_rec)
            
            return QueryRecordGQL(
                id=query_rec.id,
                query_text=query_rec.query_text,
                response_text=query_rec.response_text or "",
                confidence_score=query_rec.confidence_score or 0.0,
                processing_time_ms=query_rec.processing_time_ms,
                created_at=query_rec.created_at.isoformat() if query_rec.created_at else None
            )
        finally:
            db.close()

schema = strawberry.Schema(query=Query, mutation=Mutation)
