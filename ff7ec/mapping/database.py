"""
Octo Asset Mapping Database Builder & Loader
Queries the resource API, decodes protobuf manifests into octocacheevai.json, and provides MD5-to-path lookup tables.
"""

import os
import time
import json
import ssl
import gzip
import shutil
import socket
import urllib.request
import urllib.error
import logging
from typing import Tuple, Optional, Dict, Any, Callable

from ff7ec.constants import BASE_DIR
from ff7ec.config.manager import get_initial_mapping_path
from ff7ec.common.logger import setup_logger
from ff7ec.mapping.protobuf import ProtobufDecoder
from ff7ec.mapping.server import (
    is_nevercrisis_server_running,
    find_nevercrisis_server,
)

OCTO_REVISIONS = ["323173179", "123173179", "123173171"]
OCTO_RESOURCES_URL = "https://resources-api-c9ps53g2.app.gl.ffviiec.com/v1/"
OCTO_HEADERS = {
    "User-Agent": "FF7EC.47/25 CFNetwork/1410.0.3 Darwin/22.6.0",
    "Accept": "application/x-protobuf,x-octo-app/0",
    "X-OCTO-KEY": "10kd245cqkwhjy95okob5h8ayg59xhve",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "X-Unity-Version": "2021.3.16f1",
}


class MappingDatabaseService:
    """Provides services to fetch, decode, build, locate, and query octocacheevai.json."""

    @classmethod
    def dump_octo_database_native(
        cls,
        output_dir: Optional[str] = None,
        game_hint_dir: Optional[str] = None,
        timeout_sec: int = 8,
        logger: Optional[logging.Logger] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[Optional[str], int, int]:
        """
        Pure-Python native database generator (100% self-contained, 0 external dependencies).
        Fetches the Octo database directly via HTTPS and decodes the protobuf payload into octocacheevai.json.
        Returns (path_to_json, num_bundles, num_resources).
        """
        if logger is None:
            logger = setup_logger()

        def _log(msg: str):
            logger.info(msg)
            if log_callback:
                try:
                    log_callback(msg)
                except Exception:
                    pass

        if output_dir is None:
            output_dir = os.path.join(BASE_DIR, "data", "octo")
        os.makedirs(output_dir, exist_ok=True)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        payload = None
        used_rev = ""
        had_timeout = False

        for rev in OCTO_REVISIONS:
            url = f"{OCTO_RESOURCES_URL}list/{rev}/0"
            _log(f"[NativeDumper] Requesting revision {rev} from API...")
            req = urllib.request.Request(url, headers=OCTO_HEADERS)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=timeout_sec) as resp:
                    content_encoding = resp.headers.get("Content-Encoding")
                    raw = resp.read()
                    if content_encoding == "gzip" or raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                    if raw and len(raw) > 0:
                        payload = raw
                        used_rev = rev
                        _log(f"[NativeDumper] Successfully fetched {len(payload):,} bytes for revision {rev}!")
                        break
            except (socket.timeout, TimeoutError) as e:
                had_timeout = True
                _log(f"[NativeDumper] Revision {rev} request timed out ({timeout_sec}s): {e}")
            except urllib.error.URLError as e:
                if isinstance(e.reason, (socket.timeout, TimeoutError)):
                    had_timeout = True
                    _log(f"[NativeDumper] Revision {rev} connection timed out ({timeout_sec}s): {e}")
                else:
                    _log(f"[NativeDumper] Revision {rev} connection failed: {e}")
            except Exception as e:
                _log(f"[NativeDumper] Revision {rev} failed: {e}")

        if not payload:
            srv_running = is_nevercrisis_server_running()
            srv_path = find_nevercrisis_server(game_hint_dir)
            _log("--------------------------------------------------------------------------------")
            if had_timeout:
                _log("[TIMEOUT] Connection to asset server timed out.")
            else:
                _log("[CONNECTION FAILED] Could not reach asset database server.")

            if not srv_running:
                _log("[NOTICE] NeverCrisis offline server (FF7ECServer.exe) is NOT running.")
                _log("[NOTICE] If you are in offline mode, please open 'FF7ECServer.exe' to serve assets!")
                if srv_path:
                    _log(f"[NOTICE] Located NeverCrisis server at: {srv_path}")
            else:
                _log("[NOTICE] NeverCrisis server (FF7ECServer.exe) is currently running, but did not return data.")
            _log("--------------------------------------------------------------------------------")
            return None, 0, 0

        _log("[NativeDumper] Decoding Protobuf payload into database structures...")
        t0 = time.time()
        try:
            db = ProtobufDecoder.decode_octo_database(payload)
            t_decode = time.time() - t0
            b_cnt = len(db.get("assetBundleList", []))
            r_cnt = len(db.get("resourceList", []))
            _log(f"[NativeDumper] Parsed {b_cnt:,} asset bundles & {r_cnt:,} resources in {t_decode:.2f}s!")
        except Exception as e:
            logger.error(f"Failed to decode protobuf payload: {e}")
            return None, 0, 0

        bin_path = os.path.join(output_dir, "octocacheevai.bin")
        json_path = os.path.join(output_dir, "octocacheevai.json")

        try:
            with open(bin_path, "wb") as f:
                f.write(payload)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            _log(f"[NativeDumper] Saved: {json_path} ({os.path.getsize(json_path):,} bytes)")
            return os.path.normpath(json_path), b_cnt, r_cnt
        except Exception as e:
            logger.error(f"Failed to write output files: {e}")
            return None, 0, 0

    @classmethod
    def build_mapping_database(
        cls,
        target_copy_dir: Optional[str] = None,
        game_hint_dir: Optional[str] = None,
        timeout_sec: int = 8,
        logger: Optional[logging.Logger] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[Optional[str], int, int]:
        """
        Builds octocacheevai.json and octocacheevai.bin using pure-Python native dumper.
        Optionally copies the generated octocacheevai.json to target_copy_dir.
        Returns (path_to_json, num_bundles, num_resources).
        """
        if logger is None:
            logger = setup_logger()

        def _log(msg: str):
            logger.info(msg)
            if log_callback:
                try:
                    log_callback(msg)
                except Exception:
                    pass

        _log("================================================================================")
        _log("BUILDING OCTO ASSET DATABASE (octocacheevai.json)")
        _log("================================================================================")

        native_path, b_cnt, r_cnt = cls.dump_octo_database_native(
            output_dir=os.path.join(BASE_DIR, "data", "octo"),
            game_hint_dir=game_hint_dir,
            timeout_sec=timeout_sec,
            logger=logger,
            log_callback=log_callback,
        )
        if not (native_path and os.path.exists(native_path) and os.path.getsize(native_path) > 0):
            logger.error("Failed to build octocacheevai.json database via API.")
            return None, 0, 0

        _log("================================================================================")
        _log(f"DATABASE BUILD COMPLETE: {native_path} ({os.path.getsize(native_path):,} bytes)")
        _log(f"  - Total Asset Bundles: {b_cnt:,}")
        _log(f"  - Total Game Resources: {r_cnt:,}")
        _log("================================================================================")

        final_path = native_path
        if target_copy_dir:
            try:
                if target_copy_dir.lower().endswith(".json"):
                    dest_file = os.path.abspath(target_copy_dir)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                else:
                    os.makedirs(target_copy_dir, exist_ok=True)
                    dest_file = os.path.join(os.path.abspath(target_copy_dir), "octocacheevai.json")

                if os.path.abspath(native_path).lower() != dest_file.lower():
                    shutil.copy2(native_path, dest_file)
                    _log(f"Copied octocacheevai.json to output directory: {dest_file}")
                    final_path = dest_file
            except Exception as e:
                logger.error(f"Failed to copy octocacheevai.json to {target_copy_dir}: {e}")

        return os.path.normpath(final_path), b_cnt, r_cnt

    @classmethod
    def locate_or_fetch_mapping_database(
        cls,
        target_copy_dir: Optional[str] = None,
        auto_build_if_missing: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> Tuple[Optional[str], int, int]:
        """
        Locates, validates, and optionally exports the octocacheevai.json asset database.
        Returns (path_to_mapping, num_bundles, num_resources).
        """
        if logger is None:
            logger = setup_logger()

        found_path = get_initial_mapping_path()

        if not found_path:
            for root, _, files in os.walk(BASE_DIR):
                for f in files:
                    if f.lower() == "octocacheevai.json":
                        p = os.path.join(root, f)
                        if os.path.getsize(p) > 0:
                            found_path = os.path.normpath(p)
                            break
                if found_path:
                    break

        if not found_path:
            if auto_build_if_missing:
                logger.info("octocacheevai.json not found locally. Running native dumper to build database...")
                return cls.build_mapping_database(target_copy_dir=target_copy_dir, logger=logger)
            logger.warning("octocacheevai.json database was not found in project or game directories. Click '⚡ Build Database' to generate it.")
            return None, 0, 0

        logger.info(f"Located octocacheevai.json database at: {found_path}")
        bundles_cnt = 0
        resources_cnt = 0
        try:
            with open(found_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                bundles_cnt = len(data.get("assetBundleList", []) or data.get("asset_bundle_list", []))
                resources_cnt = len(data.get("resourceList", []) or data.get("resource_list", []))
                if bundles_cnt == 0 and resources_cnt == 0:
                    bundles_cnt = len(data)
            elif isinstance(data, list):
                bundles_cnt = len(data)
            logger.info(f"Database Stats: {bundles_cnt:,} asset bundles | {resources_cnt:,} game resources")
        except Exception as e:
            logger.warning(f"Notice: mapping file exists but error checking stats: {e}")

        if target_copy_dir:
            try:
                if target_copy_dir.lower().endswith(".json"):
                    dest_file = os.path.abspath(target_copy_dir)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                else:
                    os.makedirs(target_copy_dir, exist_ok=True)
                    dest_file = os.path.join(os.path.abspath(target_copy_dir), "octocacheevai.json")

                if os.path.abspath(found_path).lower() != dest_file.lower():
                    shutil.copy2(found_path, dest_file)
                    logger.info(f"Successfully exported octocacheevai.json to: {dest_file}")
                    return os.path.normpath(dest_file), bundles_cnt, resources_cnt
            except Exception as e:
                logger.error(f"Failed to export octocacheevai.json to {target_copy_dir}: {e}")

        return found_path, bundles_cnt, resources_cnt

    @staticmethod
    def load_mapping_file(mapping_path: str, logger: Optional[logging.Logger] = None) -> Dict[str, str]:
        """Loads and parses mapping JSON to construct an MD5 (hex) -> Logical asset path dictionary."""
        if logger is None:
            logger = setup_logger()
        mapping: Dict[str, str] = {}
        if not mapping_path or not os.path.exists(mapping_path):
            auto_path = get_initial_mapping_path()
            if auto_path:
                mapping_path = auto_path
                logger.info(f"Auto-detected asset mapping database: {mapping_path}")

        if not mapping_path or not os.path.exists(mapping_path):
            return mapping

        logger.info(f"Loading MD5-to-Asset mapping database: {mapping_path}")
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                items = []
                if "assetBundleList" in data:
                    items.extend(data["assetBundleList"])
                if "asset_bundle_list" in data:
                    items.extend(data["asset_bundle_list"])
                if "resourceList" in data:
                    items.extend(data["resourceList"])
                if "resource_list" in data:
                    items.extend(data["resource_list"])

                if items:
                    for item in items:
                        md5 = item.get("md5")
                        name = item.get("name")
                        if md5 and name:
                            mapping[md5.lower()] = name
                else:
                    for k, v in data.items():
                        if isinstance(v, str):
                            mapping[k.lower()] = v
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        md5 = item.get("md5")
                        name = item.get("name")
                        if md5 and name:
                            mapping[md5.lower()] = name

            logger.info(f"Successfully loaded {len(mapping):,} asset mapping entries.")
        except Exception as e:
            logger.error(f"Error reading mapping file: {e}")

        return mapping


# Functional aliases for backward compatibility
dump_octo_database_native = MappingDatabaseService.dump_octo_database_native
build_mapping_database = MappingDatabaseService.build_mapping_database
locate_or_fetch_mapping_database = MappingDatabaseService.locate_or_fetch_mapping_database
load_mapping_file = MappingDatabaseService.load_mapping_file
