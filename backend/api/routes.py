from fastapi import APIRouter, HTTPException
import logging

from api.controller import RecoveryController
from models.api_models import StudentRequest

logger = logging.getLogger(__name__)

router = APIRouter()

controller = RecoveryController()


@router.get("/")
def home():

    return {

        "message": "ARWA AI Backend",

        "status": "running",

        "version": "1.0",

    }


@router.get("/health")
def health():

    return {

        "status": "healthy",

        "agent": "RecoveryOrchestrator",

    }


@router.post("/analyze")
def analyze(student: StudentRequest):

    try:

        result = controller.analyze(student)

        return result

    except KeyError as e:
        logger.error(f"Missing required field in data: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Invalid value in request: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /analyze: {e}", exc_info=True)
        raise HTTPException(

            status_code=500,

            detail=f"Analysis failed: {str(e)}",

        )