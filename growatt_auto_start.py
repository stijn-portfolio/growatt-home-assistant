#!/usr/bin/env python3
"""
Growatt Auto Start Script
Automatically turns on Growatt inverters that are stuck in 'waiting' status.
"""

import requests
import json
import logging
import sys
import time as time_module
from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
import configparser
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('growatt_auto_start.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Region configuration
REGIONS = {
    'china': 'https://openapi-cn.growatt.com',
    'international': 'https://openapi.growatt.com',
    'north_america': 'https://openapi-us.growatt.com',
    'australia': 'http://openapi-au.growatt.com',
}

# Status codes
STATUS_WAITING = 0
STATUS_NORMAL = 1
STATUS_FAULT = 3


class GrowattAPI:
    """Growatt OpenAPI v4 client"""

    def __init__(self, token: str, region: str = 'international'):
        self.token = token
        self.region = region.lower()

        if self.region not in REGIONS:
            raise ValueError(f"Invalid region. Choose from: {', '.join(REGIONS.keys())}")

        self.base_url = REGIONS[self.region]
        self.headers = {
            'token': token,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    def _make_request(self, endpoint: str, data: Dict) -> Tuple[bool, Optional[Dict], Optional[int]]:
        """Make API request and return (success, response_data, error_code)"""
        url = f"{self.base_url}/v4/new-api/{endpoint}"

        try:
            response = requests.post(url, headers=self.headers, data=data, timeout=30)

            if response.status_code == 200:
                json_data = response.json()
                code = json_data.get('code', -1)

                if code == 0:  # Success
                    return True, json_data.get('data'), None
                elif code in [100, 101, 102]:  # Rate limit codes
                    logger.warning(f"Rate limit hit (code {code}): {json_data.get('message')}")
                    return False, None, code
                else:
                    logger.error(f"API error (code {code}): {json_data.get('message')}")
                    return False, None, code
            else:
                logger.error(f"HTTP error {response.status_code}: {response.reason}")
                return False, None, None

        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return False, None, None

    def get_device_list(self) -> List[Dict]:
        """Get list of all devices"""
        success, data, _ = self._make_request('queryDeviceList', {'page': '1'})

        if success and data and 'data' in data:
            devices = data['data']
            logger.info(f"Found {len(devices)} device(s)")
            return devices

        return []

    def query_last_data(self, device_sn: str, device_type: str) -> Optional[Dict]:
        """Get latest data for a device"""
        success, data, _ = self._make_request('queryLastData', {
            'deviceSn': device_sn,
            'deviceType': device_type,
        })

        if success and data:
            # API returns data wrapped in device type key (e.g., "inv": [...])
            device_data = data.get(device_type)
            if device_data and isinstance(device_data, list) and len(device_data) > 0:
                return device_data[0]

        return None

    def set_device_on(self, device_sn: str, device_type: str) -> Tuple[bool, Optional[int]]:
        """Turn device on (value=1). Returns (success, error_code)"""
        success, _, error_code = self._make_request('setOnOrOff', {
            'deviceSn': device_sn,
            'deviceType': device_type,
            'value': '1',
        })

        return success, error_code

    def set_device_on_with_retry(self, device_sn: str, device_type: str,
                                   max_retries: int = 3, retry_delay: int = 60) -> bool:
        """
        Turn device on with retry logic for timeouts.

        Args:
            device_sn: Device serial number
            device_type: Device type (inv, storage, etc)
            max_retries: Maximum number of attempts (default: 3)
            retry_delay: Seconds to wait between retries (default: 60)

        Returns:
            True if device was successfully turned on, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"     Attempt {attempt}/{max_retries}...")

            success, error_code = self.set_device_on(device_sn, device_type)

            if success:
                return True

            # Check if it was a timeout (code 16)
            if error_code == 16 and attempt < max_retries:
                logger.info(f"     Timeout - waiting {retry_delay}s before retry...")
                time_module.sleep(retry_delay)
            else:
                # Other error or last attempt failed
                return False

        return False


class AutoStartController:
    """Main controller for auto-starting inverters"""

    def __init__(self, config_path: str = 'config.ini'):
        self.config = self._load_config(config_path)
        self.api = GrowattAPI(
            token=self.config['api_token'],
            region=self.config['region']
        )

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from INI file"""
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            logger.error("Copy config.example.ini to config.ini and fill in your details")
            sys.exit(1)

        parser = configparser.ConfigParser()
        parser.read(config_path)

        config = {
            'api_token': parser.get('growatt', 'api_token'),
            'region': parser.get('growatt', 'region', fallback='international'),
            'start_hour': parser.getint('schedule', 'start_hour', fallback=7),
            'end_hour': parser.getint('schedule', 'end_hour', fallback=18),
            'exclude_noah': parser.getboolean('devices', 'exclude_noah', fallback=True),
            'max_retries': parser.getint('retry', 'max_retries', fallback=3),
            'retry_delay': parser.getint('retry', 'retry_delay', fallback=60),
        }

        # Optional: specific device serial numbers
        device_sns = parser.get('devices', 'device_serial_numbers', fallback='')
        config['device_sns'] = [sn.strip() for sn in device_sns.split(',') if sn.strip()]

        return config

    def is_active_hours(self) -> bool:
        """Check if current time is within active hours"""
        now = datetime.now().time()
        start = time(self.config['start_hour'], 0)
        end = time(self.config['end_hour'], 0)

        is_active = start <= now <= end

        if not is_active:
            logger.info(f"Outside active hours ({start} - {end}), skipping check")

        return is_active

    def check_and_start_devices(self) -> Dict[str, int]:
        """
        Check all devices and start those in waiting status.
        Returns dict with counts: {'checked': X, 'waiting': Y, 'started': Z, 'failed': W}
        """
        stats = {'checked': 0, 'waiting': 0, 'started': 0, 'failed': 0}

        if not self.is_active_hours():
            return stats

        logger.info("=" * 60)
        logger.info("Starting device check cycle")

        # Get device list
        devices = self.api.get_device_list()

        if not devices:
            logger.warning("No devices found or failed to fetch device list")
            return stats

        # Filter to specific devices if configured
        if self.config['device_sns']:
            devices = [d for d in devices if d['deviceSn'] in self.config['device_sns']]
            logger.info(f"Filtered to {len(devices)} configured device(s)")

        # Check each device
        for device in devices:
            device_sn = device['deviceSn']
            device_type = device['deviceType']
            device_name = device.get('deviceAilas') or device_sn

            # Skip Noah devices if configured
            if self.config['exclude_noah'] and device_type.lower() == 'noah':
                logger.info(f"Skipping Noah device: {device_name}")
                continue

            stats['checked'] += 1

            # Get current status
            data = self.api.query_last_data(device_sn, device_type)

            if not data:
                logger.warning(f"Failed to get data for {device_name}")
                continue

            status = data.get('status', -1)
            status_text = data.get('statusText', 'Unknown')
            pac = data.get('pac', 0)

            logger.info(f"Device: {device_name} | Status: {status_text} ({status}) | Power: {pac}W")

            # Check if waiting
            if status == STATUS_WAITING:
                stats['waiting'] += 1
                logger.info(f"  -> Device is WAITING, attempting to start...")

                # Attempt to turn on with retry logic
                if self.api.set_device_on_with_retry(
                    device_sn, device_type,
                    max_retries=self.config['max_retries'],
                    retry_delay=self.config['retry_delay']
                ):
                    stats['started'] += 1
                    logger.info(f"  [OK] Successfully sent ON command to {device_name}")
                else:
                    stats['failed'] += 1
                    logger.error(f"  [FAIL] Failed to start {device_name}")

        # Summary
        logger.info("-" * 60)
        logger.info(f"Summary: Checked {stats['checked']} device(s), "
                   f"Found {stats['waiting']} waiting, "
                   f"Started {stats['started']}, "
                   f"Failed {stats['failed']}")
        logger.info("=" * 60)

        return stats


def main():
    """Main entry point"""
    logger.info("Growatt Auto Start Script v1.0")

    try:
        controller = AutoStartController()
        stats = controller.check_and_start_devices()

        # Exit code based on results
        if stats['failed'] > 0:
            sys.exit(1)  # Some devices failed to start
        elif stats['started'] > 0:
            sys.exit(0)  # Successfully started some devices
        else:
            sys.exit(0)  # Nothing to do, but no errors

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
