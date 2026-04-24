"""Flutter build service - one persistent container shared across all sessions."""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
import structlog

logger = structlog.get_logger()

# PREVIEW_BASE_URL: empty string → relative URLs (/preview/session/) for prod behind Nginx.
# Set to http://localhost:8080 for local dev without Docker.
_PREVIEW_BASE = os.environ.get("PREVIEW_BASE_URL", "http://localhost:8080")

CONTAINER_NAME = "flutter-build-server"
DOCKER_IMAGE = "flutter-dev-server:latest"
PROJECTS_DIR = "/projects"


class FlutterBuildService:
    """Manages one persistent Flutter build container for all sessions."""

    def __init__(self, output_dir: str = "./flutter_output"):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(exist_ok=True)
        self.container_id: Optional[str] = None
        self.initialized_projects: set = set()
        logger.info("FlutterBuildService initialized", output_dir=str(self.output_dir))

    async def start_build_container(self) -> bool:
        """Start the one persistent build container on backend startup."""
        try:
            # Remove any existing stopped container with the same name
            rm_proc = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", CONTAINER_NAME,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await rm_proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "docker", "run",
                "--name", CONTAINER_NAME,
                "--platform=linux/arm64",
                "-d",
                DOCKER_IMAGE,
                "sleep", "infinity",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error("Failed to start build container", error=stderr.decode())
                return False

            self.container_id = stdout.decode().strip()
            logger.info("Build container started", container_id=self.container_id[:12])
            return True

        except Exception as e:
            logger.error("Error starting build container", error=str(e), exc_info=True)
            return False

    def is_container_running(self) -> bool:
        """Check if the build container is up."""
        return self.container_id is not None

    async def warmup_session(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Initialize a Flutter project for a session. Yields phase events."""
        async for event in self._init_project(session_id):
            yield event

    async def _init_project(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Create project dir, flutter create, flutter pub get inside the container."""

        if not self.container_id:
            yield {"phase": "error", "message": "Build container is not running"}
            return

        yield {"phase": "starting", "message": "Setting up Flutter project..."}

        try:
            # Check if project already exists in the container (survives backend restarts)
            check_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "test", "-f", f"{PROJECTS_DIR}/{session_id}/pubspec.yaml",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await check_proc.communicate()

            if check_proc.returncode == 0:
                # pubspec.yaml exists — project is already set up
                self.initialized_projects.add(session_id)
                logger.info("Project already exists in container, skipping init", session_id=session_id)
                yield {"phase": "container_ready", "message": "Project ready!"}
                return

            # Create project dir inside container
            mkdir_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "mkdir", "-p", f"{PROJECTS_DIR}/{session_id}",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await mkdir_proc.communicate()

            yield {"phase": "project_creation_started", "message": "Creating Flutter project..."}

            # flutter create .
            create_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "sh", "-c",
                f"cd {PROJECTS_DIR}/{session_id} && flutter create . --platforms web --project-name dev_preview",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            await create_proc.communicate()

            if create_proc.returncode != 0:
                yield {"phase": "error", "message": "flutter create failed"}
                return

            yield {"phase": "dependency_resolution", "message": "Resolving dependencies..."}

            # flutter pub get
            pub_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "sh", "-c",
                f"cd {PROJECTS_DIR}/{session_id} && flutter pub get",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            await pub_proc.communicate()

            if pub_proc.returncode != 0:
                yield {"phase": "error", "message": "flutter pub get failed"}
                return

            yield {"phase": "dependencies_resolved", "message": "Dependencies ready"}

            self.initialized_projects.add(session_id)

            yield {"phase": "container_ready", "message": "Project ready!"}

        except Exception as e:
            logger.error("Error initializing project", session_id=session_id, error=str(e), exc_info=True)
            yield {"phase": "error", "message": f"Project init failed: {str(e)}"}

    async def restore_project(self, session_id: str) -> bool:
        """Re-initialize a session's Flutter project using saved host source files.

        Called silently in the background when a returning user's container project
        is gone (after a periodic restart) but source files still exist on the host.
        """
        if not self.container_id:
            return False

        saved_main = self.output_dir / session_id / "lib" / "main.dart"
        if not saved_main.exists():
            logger.info("No saved source to restore", session_id=session_id)
            return False

        try:
            async for event in self._init_project(session_id):
                if event.get("phase") == "error":
                    logger.warning("restore_project: init failed", session_id=session_id)
                    return False

            container_path = f"{PROJECTS_DIR}/{session_id}/lib/main.dart"
            cp_proc = await asyncio.create_subprocess_exec(
                "docker", "cp",
                str(saved_main),
                f"{CONTAINER_NAME}:{container_path}",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await cp_proc.communicate()
            if cp_proc.returncode != 0:
                logger.warning("restore_project: cp failed", session_id=session_id, error=stderr.decode())
                return False

            logger.info("Project restored into container", session_id=session_id)
            return True

        except Exception as e:
            logger.error("restore_project error", session_id=session_id, error=str(e))
            return False

    async def build_project(self, session_id: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Write files to host, copy into container, build, copy output back."""
        try:
            if not self.container_id:
                return {"success": False, "error": "Build container not running"}

            project_host_path = self.output_dir / session_id
            project_host_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Write files to host
            for file_data in files:
                filename = file_data["filename"]
                content = file_data["content"]
                file_path = project_host_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                logger.info(f"Written to host: {filename}")

            # Step 2: docker cp each file into container
            for file_data in files:
                filename = file_data["filename"]
                host_path = str(project_host_path / filename)
                container_path = f"{PROJECTS_DIR}/{session_id}/{filename}"

                # Ensure parent dir exists inside container
                parent_dir = str(Path(container_path).parent)
                mkdir_proc = await asyncio.create_subprocess_exec(
                    "docker", "exec", CONTAINER_NAME,
                    "mkdir", "-p", parent_dir,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await mkdir_proc.communicate()

                cp_proc = await asyncio.create_subprocess_exec(
                    "docker", "cp",
                    host_path,
                    f"{CONTAINER_NAME}:{container_path}",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await cp_proc.communicate()

                if cp_proc.returncode != 0:
                    return {"success": False, "error": f"Failed to copy {filename}: {stderr.decode()}"}

                logger.info(f"Copied into container: {filename}")

            # Step 3: flutter build web
            logger.info("Starting flutter build web", session_id=session_id)

            build_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "sh", "-c",
                f"cd {PROJECTS_DIR}/{session_id} && flutter build web --base-href /preview/{session_id}/",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            build_stdout, _ = await build_proc.communicate()

            if build_proc.returncode != 0:
                logger.error("flutter build web failed", output=build_stdout.decode())
                return {"success": False, "error": "flutter build web failed", "output": build_stdout.decode()}

            logger.info("flutter build web completed", session_id=session_id)

            # Step 4: docker cp build/web/ back to host
            build_output_host = project_host_path / "build" / "web"
            build_output_host.mkdir(parents=True, exist_ok=True)

            cp_back_proc = await asyncio.create_subprocess_exec(
                "docker", "cp",
                f"{CONTAINER_NAME}:{PROJECTS_DIR}/{session_id}/build/web/.",
                str(build_output_host),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await cp_back_proc.communicate()

            if cp_back_proc.returncode != 0:
                return {"success": False, "error": f"Failed to copy build output: {stderr.decode()}"}

            logger.info("Build output copied to host", session_id=session_id, path=str(build_output_host))

            return {
                "success": True,
                "sessionId": session_id,
                "previewUrl": f"{_PREVIEW_BASE}/preview/{session_id}/",
                "message": "Build complete"
            }

        except Exception as e:
            logger.error("Error building project", session_id=session_id, error=str(e), exc_info=True)
            return {"success": False, "error": str(e)}

    def _pinned_marker(self, session_id: str) -> Path:
        return self.output_dir / session_id / ".pinned"

    def pin_session(self, session_id: str) -> None:
        """Mark a session as pinned — its data will survive server shutdown."""
        marker = self._pinned_marker(session_id)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        logger.info("Session pinned", session_id=session_id)

    def unpin_session(self, session_id: str) -> None:
        """Remove the pinned marker from a session."""
        marker = self._pinned_marker(session_id)
        if marker.exists():
            marker.unlink()
        logger.info("Session unpinned", session_id=session_id)

    def is_pinned(self, session_id: str) -> bool:
        return self._pinned_marker(session_id).exists()

    async def delete_session(self, session_id: str) -> bool:
        """Fully delete a session: Docker project dir + host output + session storage."""
        try:
            # Remove project dir from container
            rm_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "rm", "-rf", f"{PROJECTS_DIR}/{session_id}",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await rm_proc.communicate()

            # Remove host output dir
            session_output = self.output_dir / session_id
            if session_output.exists():
                shutil.rmtree(session_output)

            # Remove session storage
            from config import settings
            session_file = Path(settings.session_storage_path) / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()

            self.initialized_projects.discard(session_id)
            logger.info("Session fully deleted", session_id=session_id)
            return True

        except Exception as e:
            logger.error("Error deleting session", session_id=session_id, error=str(e))
            return False

    async def shutdown(self):
        """Stop container and delete all non-pinned local data."""
        # Stop and remove container
        try:
            stop_proc = await asyncio.create_subprocess_exec(
                "docker", "stop", CONTAINER_NAME,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await stop_proc.communicate()
            logger.info("Build container stopped")
        except Exception as e:
            logger.warning("Error stopping container", error=str(e))

        from config import settings
        sessions_path = Path(settings.session_storage_path)

        # Delete per-session output — skip pinned ones
        if self.output_dir.exists():
            for session_dir in self.output_dir.iterdir():
                if session_dir.is_dir():
                    if (session_dir / ".pinned").exists():
                        logger.info("Keeping pinned session output", session_id=session_dir.name)
                    else:
                        shutil.rmtree(session_dir)
                        # Also delete session storage for unpinned sessions
                        session_file = sessions_path / f"{session_dir.name}.json"
                        if session_file.exists():
                            session_file.unlink()
            logger.info("flutter_output cleanup done (pinned sessions kept)")
        elif sessions_path.exists():
            # No output dir at all — clean up all sessions
            shutil.rmtree(sessions_path)
            logger.info("Sessions deleted", path=str(sessions_path))

    async def rebuild_project(self, session_id: str) -> Dict[str, Any]:
        """Re-run flutter build web using files already in the container (no copy step)."""
        try:
            if not self.container_id:
                return {"success": False, "error": "Build container not running"}

            if session_id not in self.initialized_projects:
                return {"success": False, "error": "Project not initialized — run warmup first"}

            logger.info("Re-running flutter build web", session_id=session_id)

            build_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", CONTAINER_NAME,
                "sh", "-c",
                f"cd {PROJECTS_DIR}/{session_id} && flutter build web --base-href /preview/{session_id}/",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            build_stdout, _ = await build_proc.communicate()

            if build_proc.returncode != 0:
                error_output = build_stdout.decode()
                logger.error("flutter rebuild failed", output=error_output)
                return {"success": False, "error": "flutter build web failed", "output": error_output}

            # Copy build output back to host
            project_host_path = self.output_dir / session_id
            build_output_host = project_host_path / "build" / "web"
            build_output_host.mkdir(parents=True, exist_ok=True)

            cp_proc = await asyncio.create_subprocess_exec(
                "docker", "cp",
                f"{CONTAINER_NAME}:{PROJECTS_DIR}/{session_id}/build/web/.",
                str(build_output_host),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await cp_proc.communicate()

            if cp_proc.returncode != 0:
                return {"success": False, "error": f"Failed to copy build output: {stderr.decode()}"}

            logger.info("Rebuild complete", session_id=session_id)
            return {
                "success": True,
                "sessionId": session_id,
                "previewUrl": f"{_PREVIEW_BASE}/preview/{session_id}/",
                "message": "Rebuild complete"
            }

        except Exception as e:
            logger.error("Error rebuilding project", session_id=session_id, error=str(e), exc_info=True)
            return {"success": False, "error": str(e)}

    # ── Legacy compatibility ──────────────────────────────────────────────────
    # Kept so existing callers don't break during transition

    async def get_or_create_session(self, main_session_id: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
        return await self.build_project(main_session_id, files)

    async def cleanup_all_sessions(self):
        await self.shutdown()


# Alias for backward compatibility
FlutterPreviewService = FlutterBuildService
