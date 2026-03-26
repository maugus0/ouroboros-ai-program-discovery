"""In-memory fake repositories for unit testing without a database."""

from typing import Any

from app.utils.helpers import generate_uuid


class FakeProgramRepository:
    """In-memory store that mimics ProgramRepository."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create_program(self, data: dict[str, Any]) -> str:
        program_id = data.get("id") or generate_uuid()
        self._store[program_id] = {"id": program_id, **data}
        return program_id

    async def get_by_id(self, program_id: str) -> dict[str, Any] | None:
        return self._store.get(program_id)

    async def search_programs(
        self, field=None, degree_type=None, university_id=None, limit=20, offset=0
    ) -> list[dict[str, Any]]:
        items = list(self._store.values())
        if field:
            items = [p for p in items if field.lower() in (p.get("field") or "").lower()]
        if degree_type:
            items = [p for p in items if p.get("degree_type") == degree_type]
        return items[offset : offset + limit]

    async def count_programs(self, field=None, degree_type=None) -> int:
        items = list(self._store.values())
        if field:
            items = [p for p in items if field.lower() in (p.get("field") or "").lower()]
        if degree_type:
            items = [p for p in items if p.get("degree_type") == degree_type]
        return len(items)

    async def get_stale_programs(self, staleness_days=30) -> list[dict[str, Any]]:
        return []

    async def update_program(self, program_id: str, updates: dict[str, Any]) -> int:
        if program_id not in self._store:
            return 0
        self._store[program_id].update(updates)
        return 1

    async def deactivate_program(self, program_id: str) -> int:
        if program_id in self._store:
            self._store[program_id]["is_active"] = False
            return 1
        return 0

    async def get_programs_by_university(self, university_id: str) -> list[dict[str, Any]]:
        return [p for p in self._store.values() if p.get("university_id") == university_id]


class FakeUniversityRepository:
    """In-memory store that mimics UniversityRepository."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create_university(self, data: dict[str, Any]) -> str:
        uid = data.get("id") or generate_uuid()
        self._store[uid] = {"id": uid, **data}
        return uid

    async def get_by_id(self, university_id: str) -> dict[str, Any] | None:
        return self._store.get(university_id)

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        for uni in self._store.values():
            if uni.get("name") == name:
                return uni
        return None

    async def list_universities(self, limit=50, offset=0, country=None) -> list[dict[str, Any]]:
        items = list(self._store.values())
        if country:
            items = [u for u in items if u.get("country") == country]
        return items[offset : offset + limit]

    async def count_universities(self) -> int:
        return len(self._store)

    async def update_last_crawled(self, university_id: str) -> int:
        if university_id in self._store:
            return 1
        return 0


class FakeCrawlJobRepository:
    """In-memory store that mimics CrawlJobRepository."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create_job(self, data: dict[str, Any]) -> str:
        job_id = generate_uuid()
        self._store[job_id] = {"id": job_id, "status": "pending", **data}
        return job_id

    async def get_by_id(self, job_id: str) -> dict[str, Any] | None:
        return self._store.get(job_id)

    async def update_status(self, job_id, status, **kwargs) -> int:
        if job_id in self._store:
            self._store[job_id]["status"] = status
            self._store[job_id].update(kwargs)
            return 1
        return 0

    async def list_jobs(self, limit=20, offset=0, status=None) -> list[dict[str, Any]]:
        items = list(self._store.values())
        if status:
            items = [j for j in items if j.get("status") == status]
        return items[offset : offset + limit]

    async def get_running_jobs_count(self) -> int:
        return sum(1 for j in self._store.values() if j.get("status") == "running")


class FakeRequirementRepository:
    """In-memory store that mimics RequirementRepository."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create_requirement(self, data: dict[str, Any]) -> str:
        req_id = generate_uuid()
        self._store[req_id] = {"id": req_id, **data}
        return req_id

    async def bulk_create_requirements(self, requirements: list[dict[str, Any]]) -> int:
        count = 0
        for req in requirements:
            await self.create_requirement(req)
            count += 1
        return count

    async def get_by_program_id(self, program_id: str) -> list[dict[str, Any]]:
        return [r for r in self._store.values() if r.get("program_id") == program_id]

    async def delete_by_program_id(self, program_id: str) -> int:
        to_delete = [rid for rid, r in self._store.items() if r.get("program_id") == program_id]
        for rid in to_delete:
            del self._store[rid]
        return len(to_delete)
