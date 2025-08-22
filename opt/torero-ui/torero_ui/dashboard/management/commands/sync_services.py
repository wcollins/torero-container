"""Django management command to periodically sync services from torero cli."""

import logging
import time
from django.core.management.base import BaseCommand
from torero_ui.dashboard.services import DataCollectionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Periodically sync services from torero cli to detect changes."""
    
    help = 'Sync services from torero cli including those added via db import'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run sync once and exit'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Sync interval in seconds (default: 30)'
        )
    
    def handle(self, *args, **options):
        once = options['once']
        interval = options['interval']
        
        if once:
            self._sync_once()
        else:
            self._sync_continuous(interval)
    
    def _sync_once(self):
        """run sync once and exit."""
        try:
            self.stdout.write("syncing services from torero cli...")
            service = DataCollectionService()
            service.sync_services()
            self.stdout.write(self.style.SUCCESS("✅ services synchronized successfully"))
        except Exception as e:
            logger.error(f"failed to sync services: {e}")
            self.stdout.write(self.style.ERROR(f"❌ sync failed: {e}"))
    
    def _sync_continuous(self, interval: int):
        """continuously sync services at specified interval."""
        self.stdout.write(f"starting continuous sync every {interval} seconds...")
        
        while True:
            try:
                service = DataCollectionService()
                service.sync_services()
                logger.info("services synchronized successfully")
                
            except KeyboardInterrupt:
                self.stdout.write("\nstopping service sync...")
                break
            except Exception as e:
                logger.error(f"sync error: {e}")
            
            time.sleep(interval)