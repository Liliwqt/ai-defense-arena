"""Safe public errors shared by room AI workflows."""

import os
from fastapi import HTTPException
from openai import OpenAIError
from pydantic import ValidationError
from backend.question_generator import DEFAULT_MODEL, QuestionGenerationError, describe_openai_error

def safe_generation_error(error: Exception) -> str:
    if isinstance(error, HTTPException):
        return str(error.detail)
    if isinstance(error, QuestionGenerationError):
        return str(error)
    if isinstance(error, OpenAIError):
        return describe_openai_error(error, DEFAULT_MODEL, os.getenv("OPENROUTER_API_KEY"))
    if isinstance(error, ValidationError):
        return "The AI returned an unexpected response. Please try again."
    return "The AI request failed. Please try again."
