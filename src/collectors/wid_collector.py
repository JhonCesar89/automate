"""
WID (Web Ingeniería) Collector using Selenium.
Scrapes service data from the PrimeFaces web interface.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseCollector, ServiceData
from ..config.settings import get_settings


class WIDCollector(BaseCollector):
    """
    Collector for WID (Web Ingeniería) system.
    Uses Selenium to scrape data from the PrimeFaces interface.
    """
    
    # CSS Selectors for WID interface
    SELECTORS = {
        # Login page
        "username_input": "input[name='username'], #username, input[type='text']",
        "password_input": "input[name='password'], #password, input[type='password']",
        "login_button": "button[type='submit'], input[type='submit'], .login-button",
        
        # Search page
        "service_number_input": "input[id*='nroServicio'], input[id*='numeroEnlace']",
        "ring_input": "input[id*='anillo'], input[id*='ring']",
        "search_button": "button[id*='buscar'], .ui-button-search, button:contains('Buscar')",
        
        # Results table
        "results_table": ".ui-datatable-data, table[role='grid'] tbody",
        "result_rows": ".ui-datatable-data tr, table[role='grid'] tbody tr",
        "detail_link": "a[href*='Detalle'], .detail-link, td a",
        
        # Detail page - attribute groups
        "attribute_groups": ".attribute-group, [class*='grupo'], table[class*='atributo']",
        "attribute_rows": "tr",
        "attribute_name": "td:first-child, .attr-name",
        "attribute_value": "td:last-child, .attr-value",
    }
    
    # Field mapping from WID labels to ServiceData fields
    FIELD_MAPPING = {
        # Grupo 1 - Cliente
        "SITIO DEL CLIENTE": "client_site",
        "RED LAN CPE - INT": "lan_network",
        "IP LAN - INT": "lan_ip",
        "MASCARA DE RED LAN IPV4": "lan_mask",
        "ANCHO DE BANDA - INT": "bandwidth",
        "TIPO DE ENRUTAMIENTO DEL CLIENTE - INT": None,
        "NRO. SIST. AUTÓNOMO / AREA - INT": None,
        "IP PEER / NETWORK - INT": None,
        
        # Grupo 2 - CPE
        "SW CPE": "cpe_name",
        "MARCA/MODELO - SW": "cpe_model",
        "IP GESTION SW - CPE": "cpe_management_ip",
        "MASCARA IP GESTION SW - CPE": None,
        "DG GESTION SW - CPE": None,
        "VLAN GESTION SW - CPE": "cpe_management_vlan",
        "VLAN INTERFACE - INT": "cpe_interface_vlan",
        "PUERTO SW CPE - INT": "cpe_port",
        "IP WAN CPE - INT": "cpe_wan_ip",
        
        # Grupo 3 - Red Claro
        "NODO CLARO B": None,
        "AGREGADOR INTERNET": "aggregator_name",
        "ANILLO METH": "ring_name",
        "P1 AGG": "aggregator_port_1",
        "P2 AGG": "aggregator_port_2",
        "VLAN BVI - INT": "bvi_vlan",
        "IP WAN AGGI - INT": "wan_aggi_ip",
        "MASCARA DE RED WAN IPV4": "wan_mask",
    }
    
    def __init__(self, headless: bool = None):
        """Initialize WID collector."""
        super().__init__()
        self.settings = get_settings().wid
        self.headless = headless if headless is not None else get_settings().headless_browser
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Configure and create Chrome WebDriver."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # Avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Remove webdriver flag
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def connect(self) -> bool:
        """Connect to WID and authenticate."""
        try:
            logger.info(f"Connecting to WID at {self.settings.base_url}")
            
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 20)
            
            # Navigate to login page
            self.driver.get(self.settings.base_url)
            time.sleep(2)  # Wait for page load
            
            # Perform login
            if not self._login():
                logger.error("Failed to login to WID")
                return False
            
            self._connected = True
            logger.info("Successfully connected to WID")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to WID: {e}")
            return False
    
    def _login(self) -> bool:
        """Perform login to WID."""
        try:
            # Find and fill username
            username_input = self._find_element_flexible(self.SELECTORS["username_input"])
            if username_input:
                username_input.clear()
                username_input.send_keys(self.settings.username)
            else:
                logger.warning("Username input not found")
                return False
            
            # Find and fill password
            password_input = self._find_element_flexible(self.SELECTORS["password_input"])
            if password_input:
                password_input.clear()
                password_input.send_keys(self.settings.password)
            else:
                logger.warning("Password input not found")
                return False
            
            # Click login button
            login_button = self._find_element_flexible(self.SELECTORS["login_button"])
            if login_button:
                login_button.click()
            else:
                # Try pressing Enter instead
                password_input.send_keys(Keys.RETURN)
            
            # Wait for page to load after login
            time.sleep(3)
            
            # Verify login success (check if we're not on login page anymore)
            if "login" in self.driver.current_url.lower():
                logger.error("Still on login page - login may have failed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _find_element_flexible(self, selector_string: str, timeout: int = 10):
        """Try multiple selectors separated by comma."""
        selectors = [s.strip() for s in selector_string.split(",")]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return element
            except TimeoutException:
                continue
        
        return None
    
    def disconnect(self) -> None:
        """Close browser and clean up."""
        if self.driver:
            logger.info("Disconnecting from WID")
            self.driver.quit()
            self.driver = None
            self.wait = None
        self._connected = False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_by_service(self, service_id: str) -> Optional[ServiceData]:
        """
        Search for a specific service by Número de Enlace.
        
        Args:
            service_id: The service identifier (Número Enlace)
            
        Returns:
            ServiceData object or None if not found
        """
        if not self.is_connected:
            logger.error("Not connected to WID")
            return None
        
        logger.info(f"Searching for service: {service_id}")
        
        try:
            # Navigate to search page
            self._navigate_to_search()
            
            # Enter service ID and search
            service_input = self._find_element_flexible(self.SELECTORS["service_number_input"])
            if service_input:
                service_input.clear()
                service_input.send_keys(service_id)
                
                # Click search or press Enter
                search_btn = self._find_element_flexible(self.SELECTORS["search_button"])
                if search_btn:
                    search_btn.click()
                else:
                    service_input.send_keys(Keys.RETURN)
                
                time.sleep(2)  # Wait for results
            
            # Check for results and navigate to detail
            if not self._click_first_result():
                logger.warning(f"No results found for service {service_id}")
                return None
            
            # Extract data from detail page
            raw_data = self._extract_detail_data()
            
            if raw_data:
                return self._map_to_service_data(service_id, raw_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for service {service_id}: {e}")
            raise
    
    def search_by_ring(self, ring_name: str) -> List[ServiceData]:
        """
        Get all services in a specific ring.
        
        Args:
            ring_name: Ring identifier (e.g., ME-BHBA_0015)
            
        Returns:
            List of ServiceData objects
        """
        if not self.is_connected:
            logger.error("Not connected to WID")
            return []
        
        logger.info(f"Searching for all services in ring: {ring_name}")
        services = []
        
        try:
            # Navigate to search and search by ring
            self._navigate_to_search()
            
            # TODO: Implement ring-based search
            # This will depend on the actual WID interface for filtering by ring
            
            # For now, return empty list - needs implementation based on actual WID UI
            logger.warning("Ring-based search not yet implemented")
            return services
            
        except Exception as e:
            logger.error(f"Error searching for ring {ring_name}: {e}")
            return services
    
    def _navigate_to_search(self):
        """Navigate to the search/Buscar Ingeniería page."""
        # Try clicking on "Buscar Ingeniería" menu item
        try:
            search_link = self.driver.find_element(By.LINK_TEXT, "Buscar Ingeniería")
            search_link.click()
            time.sleep(1)
        except NoSuchElementException:
            # Already on search page or different navigation needed
            pass
    
    def _click_first_result(self) -> bool:
        """Click on the first result to go to detail page."""
        try:
            # Wait for results table
            time.sleep(1)
            
            # Find result rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".ui-datatable-data tr")
            
            if not rows:
                return False
            
            # Click on first row or detail link
            first_row = rows[0]
            
            # Try to find a detail link in the row
            try:
                detail_link = first_row.find_element(By.CSS_SELECTOR, "a")
                detail_link.click()
            except NoSuchElementException:
                # Click on the row itself
                first_row.click()
            
            time.sleep(2)  # Wait for detail page to load
            
            # Click on "Detalle" tab if present
            try:
                detail_tab = self.driver.find_element(By.LINK_TEXT, "Detalle")
                detail_tab.click()
                time.sleep(1)
            except NoSuchElementException:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking result: {e}")
            return False
    
    def _extract_detail_data(self) -> Dict[str, Any]:
        """Extract all attribute data from detail page."""
        raw_data = {}
        
        try:
            # Find all tables with attributes (Grupo 1, Grupo 2, Grupo 3)
            # Based on screenshot, attributes are in tables under each group
            
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            
            for table in tables:
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                
                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    
                    if len(cells) >= 2:
                        attr_name = cells[0].text.strip().upper()
                        attr_value = cells[1].text.strip()
                        
                        if attr_name and attr_value and attr_value != "N/A":
                            raw_data[attr_name] = attr_value
            
            logger.debug(f"Extracted {len(raw_data)} attributes from detail page")
            
        except Exception as e:
            logger.error(f"Error extracting detail data: {e}")
        
        return raw_data
    
    def _map_to_service_data(self, service_id: str, raw_data: Dict[str, Any]) -> ServiceData:
        """Map raw WID data to standardized ServiceData."""
        
        data = ServiceData(
            service_id=service_id,
            source_system="WID",
            raw_data=raw_data
        )
        
        for wid_field, service_field in self.FIELD_MAPPING.items():
            if service_field and wid_field in raw_data:
                value = raw_data[wid_field]
                
                # Type conversion for numeric fields
                if service_field in ["bandwidth", "cpe_management_vlan", "cpe_interface_vlan", "bvi_vlan"]:
                    try:
                        value = int(re.sub(r'[^\d]', '', str(value)))
                    except ValueError:
                        value = None
                
                setattr(data, service_field, value)
        
        return data


# Convenience function for quick usage
def get_service_from_wid(service_id: str) -> Optional[ServiceData]:
    """
    Quick helper to fetch a single service from WID.
    
    Usage:
        from collectors.wid_collector import get_service_from_wid
        service = get_service_from_wid("14815103")
    """
    with WIDCollector() as collector:
        return collector.search_by_service(service_id)
