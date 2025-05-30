"""
Keyboard Focus Agent
Tests keyboard navigation and focus management for WCAG 2.2 compliance
"""

from typing import Dict, List, Any
import asyncio
from playwright.async_api import async_playwright, Page
from .base_agent import BaseAccessibilityAgent, AccessibilityIssue, TestSeverity

class KeyboardFocusAgent(BaseAccessibilityAgent):
    """Agent specialized in testing keyboard navigation and focus management"""
    
    def __init__(self):
        super().__init__(
            name="keyboard_focus_agent", 
            description="Tests keyboard navigation, focus management, and keyboard accessibility per WCAG 2.2",
            instructions="""
            You are a specialized keyboard accessibility testing agent. Your expertise:
            
            1. KEYBOARD NAVIGATION: Test Tab, Shift+Tab, Arrow keys, Enter, Space, Escape
            2. FOCUS MANAGEMENT: Ensure logical focus order and visible focus indicators
            3. KEYBOARD TRAPS: Detect and report focus traps that prevent keyboard navigation
            4. SKIP LINKS: Verify skip navigation links for main content access
            5. INTERACTIVE ELEMENTS: Test all buttons, links, forms, and controls
            6. ARIA SUPPORT: Test ARIA roles, states, and properties for keyboard users
            
            For each keyboard interaction:
            - Test focus visibility (WCAG 2.4.7) with sufficient contrast            - Verify logical tab order (WCAG 2.4.3) follows visual layout
            - Check keyboard shortcuts don't conflict (WCAG 2.1.4)
            - Ensure all functionality available via keyboard (WCAG 2.1.1)
            - Test custom controls have proper ARIA patterns
            
            Reference WCAG 2.2 Success Criteria: 2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.1.4
            Provide specific element selectors and keyboard sequences for testing.
            """,
            tools=[],
            sub_agents=[]
        )
    
    async def analyze(self, url: str, context: Dict[str, Any]) -> List[AccessibilityIssue]:
        """Analyze keyboard accessibility of the given URL"""
        self.clear_issues()
        
        if not await self.validate_url(url):
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="URL_VALIDATION",
                severity=TestSeverity.CRITICAL,
                description=f"Unable to access URL: {url}"
            ))
            return self.issues_found
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle')
                
                # Test keyboard navigation
                await self._test_tab_navigation(page)
                await self._test_focus_visibility(page)
                await self._test_focus_order(page)
                await self._test_skip_links(page)
                await self._test_keyboard_traps(page)
                await self._test_interactive_elements(page)
                
            except Exception as e:
                self.add_issue(AccessibilityIssue(
                    agent_name=self.name,
                    issue_type="TESTING_ERROR",
                    severity=TestSeverity.HIGH,
                    description=f"Error during keyboard testing: {str(e)}"
                ))
            finally:
                await browser.close()
        
        return self.issues_found
    
    async def _test_tab_navigation(self, page: Page):
        """Test if all interactive elements are reachable via Tab key"""
        # Get all potentially focusable elements
        focusable_elements = await page.query_selector_all(
            'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        
        if not focusable_elements:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="NO_FOCUSABLE_ELEMENTS",
                severity=TestSeverity.HIGH,
                description="No focusable elements found on the page",
                wcag_guideline="WCAG 2.2 - 2.1.1 Keyboard"
            ))
            return
        
        # Test tab navigation
        tab_reachable = 0
        for i in range(len(focusable_elements) + 5):  # Extra tabs to ensure we cycle through
            await page.keyboard.press('Tab')
            focused_element = await page.evaluate('document.activeElement')
            if focused_element:
                tab_reachable += 1
        
        if tab_reachable < len(focusable_elements) * 0.8:  # 80% threshold
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="INCOMPLETE_TAB_NAVIGATION",
                severity=TestSeverity.HIGH,
                description=f"Only {tab_reachable} out of {len(focusable_elements)} elements reachable via Tab",
                wcag_guideline="WCAG 2.2 - 2.1.1 Keyboard",
                suggested_fix="Ensure all interactive elements have proper tabindex or are naturally focusable"
            ))
    
    async def _test_focus_visibility(self, page: Page):
        """Test if focus indicators are visible"""
        # Inject CSS to detect focus indicators
        await page.add_style_tag(content="""
            .focus-test-indicator {
                outline: 2px solid red !important;
                outline-offset: 2px !important;
            }
        """)
        
        focusable_elements = await page.query_selector_all(
            'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        
        invisible_focus_count = 0
        for element in focusable_elements[:10]:  # Test first 10 elements
            await element.focus()
            
            # Check if focus is visible
            focus_styles = await page.evaluate("""
                (element) => {
                    const styles = window.getComputedStyle(element, ':focus');
                    return {
                        outline: styles.outline,
                        outlineWidth: styles.outlineWidth,
                        outlineStyle: styles.outlineStyle,
                        boxShadow: styles.boxShadow
                    };
                }
            """, element)
            
            if (focus_styles['outlineWidth'] == '0px' or focus_styles['outlineStyle'] == 'none') and not focus_styles['boxShadow']:
                invisible_focus_count += 1
        
        if invisible_focus_count > 0:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="INVISIBLE_FOCUS",
                severity=TestSeverity.HIGH,
                description=f"{invisible_focus_count} elements have no visible focus indicator",
                wcag_guideline="WCAG 2.2 - 2.4.7 Focus Visible",
                suggested_fix="Add visible focus indicators using CSS :focus pseudo-class"
            ))
    
    async def _test_focus_order(self, page: Page):
        """Test if focus order is logical"""
        # This is a simplified test - in production, you'd want more sophisticated logic
        focusable_elements = await page.query_selector_all(
            'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        )
        
        focus_order = []
        for i in range(min(len(focusable_elements), 20)):  # Test first 20 elements
            await page.keyboard.press('Tab')
            focused_element = await page.evaluate("""
                () => {
                    const el = document.activeElement;
                    if (el) {
                        const rect = el.getBoundingClientRect();
                        return {
                            tagName: el.tagName,
                            top: rect.top,
                            left: rect.left,
                            tabIndex: el.tabIndex
                        };
                    }
                    return null;
                }
            """)
            if focused_element:
                focus_order.append(focused_element)
        
        # Check for major focus order issues (e.g., jumping around the page)
        if len(focus_order) > 3:
            vertical_jumps = 0
            for i in range(1, len(focus_order)):
                if abs(focus_order[i]['top'] - focus_order[i-1]['top']) > 200:  # 200px threshold
                    vertical_jumps += 1
            
            if vertical_jumps > len(focus_order) * 0.3:  # 30% threshold
                self.add_issue(AccessibilityIssue(
                    agent_name=self.name,
                    issue_type="ILLOGICAL_FOCUS_ORDER",
                    severity=TestSeverity.MEDIUM,
                    description="Focus order appears to jump around the page illogically",
                    wcag_guideline="WCAG 2.2 - 2.4.3 Focus Order",
                    suggested_fix="Ensure focus order follows a logical sequence"
                ))
    
    async def _test_skip_links(self, page: Page):
        """Test for presence and functionality of skip links"""
        skip_links = await page.query_selector_all('a[href^="#"]')
        
        functional_skip_links = 0
        for link in skip_links:
            text = await link.inner_text()
            if any(keyword in text.lower() for keyword in ['skip', 'jump', 'main', 'content']):
                href = await link.get_attribute('href')
                target = await page.query_selector(href)
                if target:
                    functional_skip_links += 1
        
        if functional_skip_links == 0:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="NO_SKIP_LINKS",
                severity=TestSeverity.MEDIUM,
                description="No functional skip links found",
                wcag_guideline="WCAG 2.2 - 2.4.1 Bypass Blocks",
                suggested_fix="Add skip links to help users bypass repetitive content"
            ))
    
    async def _test_keyboard_traps(self, page: Page):
        """Test for keyboard traps"""
        # Simple keyboard trap detection
        initial_element = await page.evaluate('document.activeElement?.tagName')
        
        # Press Tab 50 times and check if focus gets stuck
        for _ in range(50):
            await page.keyboard.press('Tab')
        
        # Try to escape with Escape key
        await page.keyboard.press('Escape')
        await page.keyboard.press('Tab')
        
        final_element = await page.evaluate('document.activeElement?.tagName')
        
        # This is a simplified check - more sophisticated detection would be needed
        if initial_element == final_element:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="POTENTIAL_KEYBOARD_TRAP",
                severity=TestSeverity.CRITICAL,
                description="Potential keyboard trap detected",
                wcag_guideline="WCAG 2.2 - 2.1.2 No Keyboard Trap",
                suggested_fix="Ensure users can navigate away from all focusable elements"
            ))
    
    async def _test_interactive_elements(self, page: Page):
        """Test if interactive elements are keyboard accessible"""
        # Test buttons, links, and custom interactive elements
        interactive_elements = await page.query_selector_all(
            'button, [role="button"], [onclick], [role="link"]:not(a)'
        )
        
        non_accessible_count = 0
        for element in interactive_elements[:10]:  # Test first 10
            # Check if element is focusable
            is_focusable = await page.evaluate("""
                (el) => {
                    el.focus();
                    return document.activeElement === el;
                }
            """, element)
            
            if not is_focusable:
                non_accessible_count += 1
        
        if non_accessible_count > 0:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="NON_KEYBOARD_INTERACTIVE",
                severity=TestSeverity.HIGH,
                description=f"{non_accessible_count} interactive elements are not keyboard accessible",
                wcag_guideline="WCAG 2.2 - 2.1.1 Keyboard",
                suggested_fix="Add tabindex='0' or use semantic HTML elements for interactive content"
            ))
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "tests": [
                "Tab Navigation",
                "Focus Visibility", 
                "Focus Order",
                "Skip Links",
                "Keyboard Traps",
                "Interactive Element Accessibility"
            ],
            "wcag_guidelines": [
                "2.1.1 Keyboard",
                "2.1.2 No Keyboard Trap", 
                "2.4.1 Bypass Blocks",
                "2.4.3 Focus Order",
                "2.4.7 Focus Visible"
            ]
        }
