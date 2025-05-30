"""
Color Multi-Contrast Testing Agent
Tests color contrast ratios and visual accessibility for WCAG 2.2 compliance
"""

from typing import Dict, List, Any, Tuple
import asyncio
import math
from playwright.async_api import async_playwright, Page
from PIL import Image, ImageDraw
import io
import base64
from .base_agent import BaseAccessibilityAgent, AccessibilityIssue, TestSeverity

class ColorContrastAgent(BaseAccessibilityAgent):
    """Agent specialized in testing color contrast and visual accessibility"""
    
    def __init__(self):
        super().__init__(
            name="color_contrast_agent",
            description="Tests color contrast ratios, color blindness accessibility, and visual elements per WCAG 2.2",
            instructions="""
            You are a specialized color contrast accessibility testing agent. Your expertise:
            
            1. WCAG 2.2 COLOR CONTRAST: Test normal text (4.5:1 AA, 7:1 AAA) and large text (3:1 AA, 4.5:1 AAA)
            2. NON-TEXT CONTRAST: Test graphics, icons, and UI components (3:1 AA minimum)
            3. COLOR BLINDNESS: Simulate deuteranopia, protanopia, tritanopia color vision deficiencies
            4. VISUAL INDICATORS: Ensure information isn't conveyed by color alone
            5. FOCUS INDICATORS: Test visible focus states and contrast
            
            For each element tested:
            - Calculate precise contrast ratios using WCAG formula
            - Test against appropriate size thresholds (large text 18pt+ or 14pt+ bold)
            - Provide specific hex/RGB values and calculated ratios            - Suggest accessible color alternatives
            - Reference exact WCAG 2.2 Success Criteria (1.4.3, 1.4.6, 1.4.11)
            
            Report issues with exact measurements and actionable fixes.
            """,
            tools=[],            sub_agents=[]
        )
        
        # WCAG 2.2 contrast requirements - use object.__setattr__ for Pydantic compatibility
        object.__setattr__(self, 'contrast_requirements', {
            'normal_text': {
                'AA': 4.5,
                'AAA': 7.0
            },
            'large_text': {
                'AA': 3.0,
                'AAA': 4.5
            },
            'graphics': {
                'AA': 3.0
            }
        })
    
    async def analyze(self, url: str, context: Dict[str, Any]) -> List[AccessibilityIssue]:
        """Analyze color contrast and visual accessibility of the given URL"""
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
                
                # Perform color contrast tests
                await self._test_text_contrast(page)
                await self._test_link_contrast(page)
                await self._test_button_contrast(page)
                await self._test_focus_contrast(page)
                await self._test_color_only_information(page)
                await self._test_background_images(page)
                
            except Exception as e:
                self.add_issue(AccessibilityIssue(
                    agent_name=self.name,
                    issue_type="TESTING_ERROR",
                    severity=TestSeverity.HIGH,
                    description=f"Error during color contrast testing: {str(e)}"
                ))
            finally:
                await browser.close()
        
        return self.issues_found
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two RGB colors"""
        def get_relative_luminance(rgb):
            r, g, b = [c / 255.0 for c in rgb]
            
            def adjust_color(c):
                if c <= 0.03928:
                    return c / 12.92
                else:
                    return pow((c + 0.055) / 1.055, 2.4)
            
            return 0.2126 * adjust_color(r) + 0.7152 * adjust_color(g) + 0.0722 * adjust_color(b)
        
        l1 = get_relative_luminance(color1)
        l2 = get_relative_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _parse_rgb_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse RGB color from CSS color string"""
        if color_str.startswith('rgb('):
            # Extract RGB values
            rgb_values = color_str[4:-1].split(',')
            return tuple(int(val.strip()) for val in rgb_values)
        elif color_str.startswith('rgba('):
            # Extract RGB values (ignore alpha)
            rgba_values = color_str[5:-1].split(',')
            return tuple(int(val.strip()) for val in rgba_values[:3])
        elif color_str.startswith('#'):
            # Hex color
            hex_color = color_str[1:]
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            # Named colors or other formats - return default
            return (0, 0, 0)
    
    async def _get_element_colors(self, page: Page, element) -> Dict[str, Tuple[int, int, int]]:
        """Get foreground and background colors of an element"""
        colors = await page.evaluate("""
            (element) => {
                const styles = window.getComputedStyle(element);
                return {
                    color: styles.color,
                    backgroundColor: styles.backgroundColor,
                    fontSize: styles.fontSize
                };
            }
        """, element)
        
        fg_color = self._parse_rgb_color(colors['color'])
        bg_color = self._parse_rgb_color(colors['backgroundColor'])
        
        # If background is transparent, try to find parent background
        if bg_color == (0, 0, 0) or colors['backgroundColor'] in ['transparent', 'rgba(0, 0, 0, 0)']:
            bg_color = await self._find_effective_background(page, element)
        
        return {
            'foreground': fg_color,
            'background': bg_color,
            'font_size': colors['fontSize']
        }
    
    async def _find_effective_background(self, page: Page, element) -> Tuple[int, int, int]:
        """Find the effective background color by traversing up the DOM"""
        bg_color = await page.evaluate("""
            (element) => {
                let current = element.parentElement;
                while (current && current !== document.body) {
                    const styles = window.getComputedStyle(current);
                    const bgColor = styles.backgroundColor;
                    if (bgColor && bgColor !== 'transparent' && bgColor !== 'rgba(0, 0, 0, 0)') {
                        return bgColor;
                    }
                    current = current.parentElement;
                }
                return 'rgb(255, 255, 255)'; // Default to white
            }
        """, element)
        
        return self._parse_rgb_color(bg_color)
    
    def _is_large_text(self, font_size: str, font_weight: str = 'normal') -> bool:
        """Determine if text is considered large according to WCAG"""
        size_px = float(font_size.replace('px', ''))
        
        # 18px+ is large text, or 14px+ if bold
        if size_px >= 18:
            return True
        elif size_px >= 14 and font_weight in ['bold', '600', '700', '800', '900']:
            return True
        
        return False
    
    async def _test_text_contrast(self, page: Page):
        """Test contrast ratios for text elements"""
        text_elements = await page.query_selector_all('p, h1, h2, h3, h4, h5, h6, span, div, li, td, th')
        
        low_contrast_count = 0
        total_tested = 0
        
        for element in text_elements[:50]:  # Test first 50 text elements
            try:
                # Check if element has visible text
                text_content = await element.inner_text()
                if not text_content.strip():
                    continue
                
                colors = await self._get_element_colors(page, element)
                contrast_ratio = self._calculate_contrast_ratio(
                    colors['foreground'], 
                    colors['background']
                )
                
                is_large = self._is_large_text(colors['font_size'])
                min_ratio = self.contrast_requirements['large_text']['AA'] if is_large else self.contrast_requirements['normal_text']['AA']
                
                total_tested += 1
                
                if contrast_ratio < min_ratio:
                    low_contrast_count += 1
                    
                    selector = await page.evaluate('(el) => el.tagName + (el.className ? "." + el.className.split(" ")[0] : "")', element)
                    
                    self.add_issue(AccessibilityIssue(
                        agent_name=self.name,
                        issue_type="LOW_TEXT_CONTRAST",
                        severity=TestSeverity.HIGH if contrast_ratio < 3.0 else TestSeverity.MEDIUM,
                        description=f"Text contrast ratio {contrast_ratio:.2f} is below WCAG AA requirement of {min_ratio}",
                        element_selector=selector,
                        wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)",
                        suggested_fix=f"Increase contrast to at least {min_ratio}:1",
                        evidence={
                            "contrast_ratio": contrast_ratio,
                            "foreground_color": colors['foreground'],
                            "background_color": colors['background'],
                            "is_large_text": is_large
                        }
                    ))
                    
            except Exception as e:
                continue  # Skip problematic elements
        
        if total_tested == 0:
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="NO_TEXT_ELEMENTS",
                severity=TestSeverity.INFO,
                description="No text elements found for contrast testing"
            ))
        elif low_contrast_count > total_tested * 0.2:  # 20% threshold
            self.add_issue(AccessibilityIssue(
                agent_name=self.name,
                issue_type="WIDESPREAD_CONTRAST_ISSUES",
                severity=TestSeverity.CRITICAL,
                description=f"Widespread contrast issues: {low_contrast_count} out of {total_tested} text elements fail WCAG standards",
                wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)"
            ))
    
    async def _test_link_contrast(self, page: Page):
        """Test contrast ratios for links"""
        links = await page.query_selector_all('a')
        
        for link in links[:20]:  # Test first 20 links
            try:
                # Test both normal and hover states
                colors = await self._get_element_colors(page, link)
                contrast_ratio = self._calculate_contrast_ratio(
                    colors['foreground'], 
                    colors['background']
                )
                
                if contrast_ratio < 3.0:  # Links need at least 3:1 contrast with background
                    self.add_issue(AccessibilityIssue(
                        agent_name=self.name,
                        issue_type="LOW_LINK_CONTRAST",
                        severity=TestSeverity.HIGH,
                        description=f"Link contrast ratio {contrast_ratio:.2f} is below 3:1 minimum",
                        wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)",
                        suggested_fix="Ensure links have at least 3:1 contrast with background"
                    ))
                
                # Test hover state
                await link.hover()
                hover_colors = await self._get_element_colors(page, link)
                hover_contrast = self._calculate_contrast_ratio(
                    hover_colors['foreground'], 
                    hover_colors['background']
                )
                
                if hover_contrast < 3.0:
                    self.add_issue(AccessibilityIssue(
                        agent_name=self.name,
                        issue_type="LOW_LINK_HOVER_CONTRAST",
                        severity=TestSeverity.MEDIUM,
                        description=f"Link hover contrast ratio {hover_contrast:.2f} is below 3:1 minimum",
                        wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)"
                    ))
                    
            except Exception:
                continue
    
    async def _test_button_contrast(self, page: Page):
        """Test contrast ratios for buttons and interactive elements"""
        buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"], [role="button"]')
        
        for button in buttons[:15]:  # Test first 15 buttons
            try:
                colors = await self._get_element_colors(page, button)
                contrast_ratio = self._calculate_contrast_ratio(
                    colors['foreground'], 
                    colors['background']
                )
                
                if contrast_ratio < 3.0:  # Interactive elements need 3:1 contrast
                    self.add_issue(AccessibilityIssue(
                        agent_name=self.name,
                        issue_type="LOW_BUTTON_CONTRAST",
                        severity=TestSeverity.HIGH,
                        description=f"Button contrast ratio {contrast_ratio:.2f} is below 3:1 minimum",
                        wcag_guideline="WCAG 2.2 - 1.4.11 Non-text Contrast",
                        suggested_fix="Ensure buttons have at least 3:1 contrast with background"
                    ))
                    
            except Exception:
                continue
    
    async def _test_focus_contrast(self, page: Page):
        """Test contrast ratios for focus indicators"""
        focusable_elements = await page.query_selector_all('a, button, input, textarea, select')
        
        for element in focusable_elements[:10]:  # Test first 10 focusable elements
            try:
                await element.focus()
                
                # Check focus indicator contrast
                focus_info = await page.evaluate("""
                    (element) => {
                        const styles = window.getComputedStyle(element, ':focus');
                        return {
                            outlineColor: styles.outlineColor,
                            backgroundColor: styles.backgroundColor,
                            outlineWidth: styles.outlineWidth,
                            outlineStyle: styles.outlineStyle
                        };
                    }
                """, element)
                
                if focus_info['outlineWidth'] != '0px' and focus_info['outlineStyle'] != 'none':
                    outline_color = self._parse_rgb_color(focus_info['outlineColor'])
                    bg_color = self._parse_rgb_color(focus_info['backgroundColor'])
                    
                    focus_contrast = self._calculate_contrast_ratio(outline_color, bg_color)
                    
                    if focus_contrast < 3.0:
                        self.add_issue(AccessibilityIssue(
                            agent_name=self.name,
                            issue_type="LOW_FOCUS_CONTRAST",
                            severity=TestSeverity.MEDIUM,
                            description=f"Focus indicator contrast ratio {focus_contrast:.2f} is below 3:1 minimum",
                            wcag_guideline="WCAG 2.2 - 1.4.11 Non-text Contrast",
                            suggested_fix="Ensure focus indicators have at least 3:1 contrast"
                        ))
                        
            except Exception:
                continue
    
    async def _test_color_only_information(self, page: Page):
        """Test for information conveyed by color alone"""
        # This is a simplified test - would need more sophisticated analysis in production
        elements_with_color_styles = await page.query_selector_all('[style*="color"], .text-red, .text-green, .text-blue, .error, .success, .warning')
        
        if elements_with_color_styles:
            # Check if these elements have additional non-color indicators
            for element in elements_with_color_styles[:10]:
                try:
                    text_content = await element.inner_text()
                    
                    # Look for visual indicators beyond color
                    has_icon = await page.evaluate('(el) => el.querySelector("i, svg, .icon") !== null', element)
                    has_text_indicator = any(word in text_content.lower() for word in 
                                           ['error', 'warning', 'success', 'info', 'required', 'invalid'])
                    
                    if not has_icon and not has_text_indicator:
                        self.add_issue(AccessibilityIssue(
                            agent_name=self.name,
                            issue_type="COLOR_ONLY_INFORMATION",
                            severity=TestSeverity.MEDIUM,
                            description="Information may be conveyed by color alone",
                            wcag_guideline="WCAG 2.2 - 1.4.1 Use of Color",
                            suggested_fix="Add text labels, icons, or other non-color indicators"
                        ))
                        break  # Only report once
                        
                except Exception:
                    continue
    
    async def _test_background_images(self, page: Page):
        """Test contrast for text over background images"""
        elements_with_bg_images = await page.query_selector_all('[style*="background-image"], .hero, .banner, .card')
        
        for element in elements_with_bg_images[:5]:  # Test first 5 elements
            try:
                has_bg_image = await page.evaluate("""
                    (el) => {
                        const styles = window.getComputedStyle(el);
                        return styles.backgroundImage && styles.backgroundImage !== 'none';
                    }
                """, element)
                
                if has_bg_image:
                    text_content = await element.inner_text()
                    if text_content.strip():
                        # If there's text over a background image, flag for manual review
                        self.add_issue(AccessibilityIssue(
                            agent_name=self.name,
                            issue_type="TEXT_OVER_BACKGROUND_IMAGE",
                            severity=TestSeverity.MEDIUM,
                            description="Text over background image requires manual contrast verification",
                            wcag_guideline="WCAG 2.2 - 1.4.3 Contrast (Minimum)",
                            suggested_fix="Ensure text has sufficient contrast with background image, consider overlay or alternative presentation"
                        ))
                        
            except Exception:
                continue
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "tests": [
                "Text Contrast Ratios",
                "Link Contrast",
                "Button/Interactive Element Contrast",
                "Focus Indicator Contrast",
                "Color-Only Information Detection",
                "Background Image Text Analysis"
            ],
            "wcag_guidelines": [
                "1.4.1 Use of Color",
                "1.4.3 Contrast (Minimum)",
                "1.4.11 Non-text Contrast"
            ],
            "contrast_requirements": self.contrast_requirements
        }
