from typing import Optional

from pydantic import BaseModel, field_validator


class AddCommentRequest(BaseModel):
    content: str
    author_nickname: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("댓글 내용을 입력해주세요.")
        if len(v) > 120:
            raise ValueError("댓글은 120자 이내로 입력해주세요.")
        return v
