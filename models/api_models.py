from pydantic import BaseModel, Field


class AssignmentRequest(BaseModel):
    title: str
    course: str
    difficulty: float = Field(..., ge=0, le=1)
    estimated_hours: float
    days_remaining: int
    completed: bool


class StudentRequest(BaseModel):
    current_grade: float
    stress_level: float
    available_time: float
    assignments: list[AssignmentRequest]
