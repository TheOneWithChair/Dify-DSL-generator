"""Dify API Integration"""

import requests
import logging
from typing import Dict, Optional

from app_config import LOGGERS

# Get logger for this module
logger = LOGGERS["dify.integration"]


class DifyIntegration:

    def __init__(self, api_url: str, api_key: str):
        """Initialize Dify integration"""
        logger.info("Initializing DifyIntegration")
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        logger.info(f"Dify integration initialized for URL: {self.api_url}")

    def test_connection(self) -> Dict:
        """Test connection to Dify API"""
        logger.info("Testing connection to Dify API")
        try:
            response = requests.get(
                f"{self.api_url}/console/api/apps",
                headers=self.headers,
                params={"page": 1, "limit": 1},
                timeout=10,
            )
            logger.info(f"Dify API response status: {response.status_code}")

            if response.status_code == 200:
                apps_count = response.json().get("total", 0)
                logger.info(
                    f"Successfully connected to Dify. Found {apps_count} apps"
                )
                return {
                    "success": True,
                    "message": "✅ Connected to Dify successfully",
                    "apps_count": apps_count,
                }
            else:
                logger.error(
                    f"Dify connection failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return {
                    "success": False,
                    "message": f"❌ Connection failed: {response.status_code}",
                    "error": response.text,
                }

        except Exception as e:
            logger.error(f"Dify connection error: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Connection error: {str(e)}",
            }

    def import_dsl(self, dsl_yaml: str, app_name: Optional[str] = None) -> Dict:
        """Import DSL to Dify.

        Args:
            dsl_yaml: Complete DSL YAML string
            app_name: Optional custom app name

        Returns:
            Dict with success status and app_id or error
        """
        logger.info(
            f"Starting DSL import to Dify. Length: {len(dsl_yaml)} chars"
        )
        if app_name:
            logger.info(f"Custom app name provided: {app_name}")

        try:
            logger.info("Calling Dify import API")
            response = requests.post(
                f"{self.api_url}/console/api/apps/import",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "text/yaml",
                },
                data=dsl_yaml.encode("utf-8"),
                timeout=30,
            )
            logger.info(
                f"Dify import API response status: {response.status_code}"
            )

            if response.status_code in [200, 201]:
                result = response.json()
                app_id = result.get("id") or result.get("app_id")
                logger.info(f"DSL import successful. App ID: {app_id}")
                return {
                    "success": True,
                    "app_id": app_id,
                    "message": "✅ Successfully imported to Dify!",
                    "app_url": f"{self.api_url}/app/{app_id}",
                }
            else:
                logger.error(
                    f"DSL import failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return {
                    "success": False,
                    "message": f"❌ Import failed: {response.status_code}",
                    "error": response.text,
                }

        except Exception as e:
            logger.error(f"DSL import error: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Import error: {str(e)}",
            }

    def get_apps(self, page: int = 1, limit: int = 20) -> Dict:
        """Get list of apps from Dify"""
        logger.info(f"Fetching apps list. Page: {page}, Limit: {limit}")
        try:
            response = requests.get(
                f"{self.api_url}/console/api/apps",
                headers=self.headers,
                params={"page": page, "limit": limit},
                timeout=10,
            )
            logger.info(f"Get apps API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                apps_count = len(data.get("data", []))
                total_count = data.get("total", 0)
                logger.info(
                    f"Successfully fetched {apps_count} apps (total: {total_count})"
                )
                return {
                    "success": True,
                    "apps": data.get("data", []),
                    "total": total_count,
                }
            else:
                logger.error(
                    f"Get apps failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return {
                    "success": False,
                    "error": response.text,
                }

        except Exception as e:
            logger.error(f"Get apps error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }