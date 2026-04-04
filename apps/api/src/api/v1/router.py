# API v1 router
from fastapi import APIRouter
from src.api.auth import router as auth_router
from src.api.v1 import sites as sites_router
from src.api.v1 import sync_jobs as sync_jobs_router
from src.api.v1 import connectors as connectors_router
from src.api.v1 import search as search_router
from src.api.v1 import drift as drift_router
from src.api.v1 import audit as audit_router
from src.api.v1 import useful_links as useful_links_router
from src.api.v1 import reports as reports_router
from src.api.v1 import runbooks as runbooks_router
from src.api.v1 import saved_queries as saved_queries_router
from src.api.v1 import health_checks as health_checks_router
from src.api.v1 import racks as racks_router
from src.api.v1 import hosts as hosts_router
from src.api.v1 import vms as vms_router
from src.api.v1 import storage as storage_router
from src.api.v1 import backups as backups_router
from src.api.v1 import proxmox_explorer as proxmox_explorer_router
from src.api.v1 import cloud_ops as cloud_ops_router
from src.api.v1 import certificates as certificates_router
from src.api.v1 import idrac as idrac_router
from src.api.v1 import change_events as change_events_router
from src.api.v1 import connectivity as connectivity_router
from src.api.v1 import insights as insights_router
from src.api.v1 import link_templates as link_templates_router
from src.api.v1 import favourites as favourites_router
from src.api.v1 import scripts as scripts_router
from src.api.v1 import dashboard_widgets as dashboard_widgets_router
from src.api.v1 import ops_requests as ops_requests_router
from src.api.v1 import internal_runner as internal_runner_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(sites_router.router)
router.include_router(racks_router.router)
router.include_router(hosts_router.router)
router.include_router(vms_router.router)
router.include_router(storage_router.router)
router.include_router(backups_router.router)
router.include_router(sync_jobs_router.router)
router.include_router(connectors_router.router)
router.include_router(search_router.router)
router.include_router(drift_router.router)
router.include_router(audit_router.router)
router.include_router(useful_links_router.router)
router.include_router(reports_router.router)
router.include_router(runbooks_router.router)
router.include_router(saved_queries_router.router)
router.include_router(health_checks_router.router)
router.include_router(proxmox_explorer_router.router)
router.include_router(cloud_ops_router.router)
router.include_router(certificates_router.router)
router.include_router(idrac_router.router)
router.include_router(change_events_router.router)
router.include_router(connectivity_router.router)
router.include_router(insights_router.router)
router.include_router(link_templates_router.router)
router.include_router(favourites_router.router)
router.include_router(favourites_router.router_recent)
router.include_router(scripts_router.router)
router.include_router(dashboard_widgets_router.router)
router.include_router(ops_requests_router.router)
router.include_router(internal_runner_router.router)
