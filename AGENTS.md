# Project Standards

You are working on ARWA.

Always optimize for readability over cleverness.

## Stack

Frontend

- React
- JavaScript
- Tailwind

Backend

- FastAPI
- Python

## Rules

Never duplicate code.

Keep components small.

Prefer composition.

Keep API routes RESTful.

Always validate request bodies.

Write docstrings.

Write type hints.

Every endpoint should return proper HTTP status codes.

Never break existing API contracts.

Always update documentation after adding features.

Always test before marking a task complete.

## Architecture

Presentation Layer

↓

API Layer

↓

Business Logic

↓

AI Service

↓

Data Layer

Always preserve this separation.