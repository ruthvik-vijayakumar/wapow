"""GET /api/conversion-jobs/{job_id} — batch story conversion status."""

from fastapi import APIRouter, HTTPException

from api.services.conversion_jobs import get_job, serialize_job

router = APIRouter(prefix="/conversion-jobs", tags=["conversion-jobs"])


@router.get("/{job_id}")
async def get_conversion_job(job_id: str):
    doc = get_job(job_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "data": serialize_job(doc)}
