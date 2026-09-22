"""Thin Odoo RPC helper: auth + execute_kw. JSON-RPC first, XML-RPC fallback.

Connection details come from TenantApp.extra_config, then the Odoo
PassThroughEndpoint (slug), then Django settings. Never log passwords.
"""
from __future__ import annotations

import logging
import xmlrpc.client
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_JSONRPC_PATH = "/jsonrpc"
_DEFAULT_TIMEOUT = 20


class OdooRpcError(Exception):
    """Typed Odoo RPC failure. status is auth_failed | connection_refused | error."""

    def __init__(self, status: str, message: str, **extra: Any):
        super().__init__(message)
        self.status = status
        extra.pop("password", None)
        extra.pop("odoo_password", None)
        self.extra = extra

    def as_dict(self) -> dict:
        data = {"status": self.status, "error": str(self)}
        data.update(self.extra)
        return data


def public_config(config: dict | None) -> dict:
    """Safe subset for logs / service_result (no secrets)."""
    cfg = config or {}
    return {
        "url": (cfg.get("url") or "").rstrip("/"),
        "db": cfg.get("db") or "",
        "username": cfg.get("username") or "",
        "has_password": bool(cfg.get("password")),
    }


def load_odoo_rpc_config(request=None, instruction_row=None) -> dict:
    """Resolve url / db / username / password for the current tenant.

    Priority (later wins): Django settings → PassThroughEndpoint → TenantApp
    extra_config → atomic Parameters → Instruction config.
    Endpoint must override settings so refine hits the same Odoo as passthrough.
    """
    config = {
        "url": str(getattr(settings, "ODOO_SHARED_URL", "http://localhost:8086") or "").rstrip("/"),
        "db": str(getattr(settings, "ODOO_SHARED_DB", "odoo") or "odoo"),
        "username": str(getattr(settings, "ODOO_XMLRPC_ADMIN_LOGIN", "admin") or "admin"),
        "password": str(getattr(settings, "ODOO_XMLRPC_ADMIN_PASSWORD", "") or ""),
    }

    tenant = getattr(request, "tenant", None) if request is not None else None
    if tenant is None and request is not None:
        try:
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
        except Exception:
            tenant = None

    _apply_passthrough_endpoint(config)

    extra = _tenant_app_extra(tenant)
    if extra:
        if extra.get("odoo_url"):
            config["url"] = str(extra["odoo_url"]).rstrip("/")
        if extra.get("odoo_db"):
            config["db"] = str(extra["odoo_db"])
        if extra.get("odoo_login"):
            config["username"] = str(extra["odoo_login"])
        elif extra.get("odoo_username"):
            config["username"] = str(extra["odoo_username"])
        if extra.get("odoo_password"):
            config["password"] = str(extra["odoo_password"])

    _apply_atomic_parameters(request, config)
    _apply_instruction_config(instruction_row, config)
    return config


def _tenant_app_extra(tenant) -> dict:
    if tenant is None:
        return {}
    try:
        from dose.tenant_app_lookup import get_tenant_app_in_schema
        ta = get_tenant_app_in_schema(tenant, "odoo")
        extra = getattr(ta, "extra_config", None) if ta else None
        return extra if isinstance(extra, dict) else {}
    except Exception as exc:
        logger.warning("[OdooRpc] TenantApp extra_config skipped: %s", exc)
        return {}


def _apply_passthrough_endpoint(config: dict) -> None:
    try:
        from dose.models.pass_through_endpoint import PassThroughEndpoint

        odoo_ep = (
            PassThroughEndpoint.objects.filter(slug="odoo", is_enabled=True)
            .order_by("-id")
            .first()
        )
        if odoo_ep is None:
            odoo_ep = (
                PassThroughEndpoint.objects.filter(
                    endpoint_url__icontains="odoo", is_enabled=True
                )
                .order_by("-id")
                .first()
            )
        if odoo_ep is None:
            return
        # Always prefer the live passthrough endpoint over settings defaults.
        if odoo_ep.endpoint_url:
            config["url"] = odoo_ep.endpoint_url.rstrip("/")
        if odoo_ep.auth_username:
            config["username"] = odoo_ep.auth_username
        if odoo_ep.auth_password:
            config["password"] = odoo_ep.auth_password
    except Exception as exc:
        logger.warning("[OdooRpc] PassThroughEndpoint config skipped: %s", exc)


def _apply_atomic_parameters(request, config: dict) -> None:
    params = getattr(request, "atomic_parameters", None) if request is not None else None
    if not params:
        return
    for p in params:
        val = getattr(p, "parameterValue", None)
        key = getattr(p, "parameterKey", None)
        if val is None and isinstance(p, dict):
            val = p.get("parameterValue")
            key = p.get("parameterKey")
        if not key or val in (None, ""):
            continue
        _overlay_config_key(config, str(key), str(val))


def _apply_instruction_config(instruction_row, config: dict) -> None:
    if instruction_row is None:
        return
    try:
        from dose.services.atomic_service_utils import instruction_config
        cfg = instruction_config(instruction_row)
    except Exception:
        return
    for key, val in cfg.items():
        if val in (None, ""):
            continue
        _overlay_config_key(config, str(key), str(val) if not isinstance(val, (dict, list)) else val)


def _overlay_config_key(config: dict, key: str, val) -> None:
    if not isinstance(val, str):
        return
    if key == "odoo_url":
        config["url"] = val.rstrip("/")
    elif key == "odoo_db":
        config["db"] = val
    elif key in ("odoo_username", "odoo_login"):
        config["username"] = val
    elif key == "odoo_password":
        config["password"] = val


class OdooRpcClient:
    """JSON-RPC `/jsonrpc` with XML-RPC `/xmlrpc/2` fallback."""

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        self.url = (url or "").rstrip("/")
        self.db = db or ""
        self.username = username or ""
        self.password = password or ""
        self.timeout = timeout
        self.uid: Optional[int] = None
        self.transport: Optional[str] = None

    @classmethod
    def from_config(cls, config: dict) -> "OdooRpcClient":
        return cls(
            url=config.get("url") or "",
            db=config.get("db") or "",
            username=config.get("username") or "",
            password=config.get("password") or "",
        )

    def authenticate(self) -> int:
        if not self.url or not self.db or not self.username or not self.password:
            raise OdooRpcError(
                "error",
                "missing_odoo_config",
                **public_config(self._as_config()),
            )
        try:
            uid = self._jsonrpc_authenticate()
            self.transport = "jsonrpc"
        except OdooRpcError:
            raise
        except Exception as json_exc:
            logger.info("[OdooRpc] JSON-RPC unavailable (%s); trying XML-RPC", type(json_exc).__name__)
            try:
                uid = self._xmlrpc_authenticate()
                self.transport = "xmlrpc"
            except OdooRpcError:
                raise
            except Exception as xml_exc:
                raise self._wrap_connect_or_error(xml_exc) from xml_exc

        if not uid:
            raise OdooRpcError(
                "auth_failed",
                "Odoo authentication failed",
                **public_config(self._as_config()),
            )
        self.uid = int(uid)
        return self.uid

    def execute_kw(
        self,
        model: str,
        method: str,
        args: list | None = None,
        kwargs: dict | None = None,
    ) -> Any:
        if self.uid is None:
            self.authenticate()
        args = list(args) if args is not None else []
        kwargs = dict(kwargs) if kwargs else {}
        try:
            if self.transport == "xmlrpc":
                return self._xmlrpc_execute_kw(model, method, args, kwargs)
            return self._jsonrpc_execute_kw(model, method, args, kwargs)
        except OdooRpcError:
            raise
        except Exception as exc:
            raise self._wrap_connect_or_error(exc) from exc

    def _as_config(self) -> dict:
        return {
            "url": self.url,
            "db": self.db,
            "username": self.username,
            "password": self.password,
        }

    def _jsonrpc_call(self, service: str, method: str, args: list) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
        endpoint = urljoin(self.url + "/", _JSONRPC_PATH.lstrip("/"))
        try:
            resp = requests.post(endpoint, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, ConnectionRefusedError) as exc:
            raise OdooRpcError(
                "connection_refused",
                f"Could not connect to Odoo at {self.url}",
                url=self.url,
            ) from exc
        if resp.status_code >= 500:
            raise OdooRpcError("error", f"Odoo HTTP {resp.status_code}", url=self.url)
        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError("jsonrpc_not_json") from exc
        if not isinstance(data, dict):
            raise RuntimeError("jsonrpc_not_object")
        if data.get("error"):
            err = data["error"]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            detail = ""
            if isinstance(err, dict) and isinstance(err.get("data"), dict):
                detail = err["data"].get("message") or err["data"].get("name") or ""
            raise OdooRpcError("error", detail or msg or "Odoo JSON-RPC error", url=self.url)
        return data.get("result")

    def _jsonrpc_authenticate(self) -> int:
        result = self._jsonrpc_call(
            "common", "authenticate", [self.db, self.username, self.password, {}]
        )
        return int(result) if result else 0

    def _jsonrpc_execute_kw(self, model: str, method: str, args: list, kwargs: dict) -> Any:
        rpc_args = [self.db, self.uid, self.password, model, method, args]
        if kwargs:
            rpc_args.append(kwargs)
        return self._jsonrpc_call("object", "execute_kw", rpc_args)

    def _xmlrpc_authenticate(self) -> int:
        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            uid = common.authenticate(self.db, self.username, self.password, {})
        except (ConnectionRefusedError, OSError) as exc:
            raise OdooRpcError(
                "connection_refused",
                f"Could not connect to Odoo at {self.url}",
                url=self.url,
            ) from exc
        except xmlrpc.client.ProtocolError as exc:
            raise OdooRpcError("error", str(exc), url=self.url) from exc
        return int(uid) if uid else 0

    def _xmlrpc_execute_kw(self, model: str, method: str, args: list, kwargs: dict) -> Any:
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def _wrap_connect_or_error(self, exc: Exception) -> OdooRpcError:
        if isinstance(exc, (ConnectionRefusedError, requests.ConnectionError, OSError)):
            return OdooRpcError(
                "connection_refused",
                f"Could not connect to Odoo at {self.url}",
                url=self.url,
            )
        return OdooRpcError("error", str(exc), url=self.url, db=self.db)
