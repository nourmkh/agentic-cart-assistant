import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import logging
import threading
import random
import os

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.context = None

    def run_checkout(self, items, user_data):
        """
        Coordinates the checkout process focusing on robustness and persistent sessions.
        """
        logger.info("Starting Persistent Automation Session...")
        
        # Ensure user_data directory exists
        user_data_path = os.path.join(os.getcwd(), "browser_session")
        if not os.path.exists(user_data_path):
            os.makedirs(user_data_path)

        with sync_playwright() as p:
            try:
                # Use a persistent context to save logins/cookies
                self.context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_path,
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--start-maximized"
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                    locale="fr-FR"
                )
                
                # Execute for each item sequentially
                for item in items:
                    logger.info(f"Using Universal Intelligent Agent for item: {item.get('name')}")
                    self.automate_generic(item, user_data)
                
                logger.info("Automation task reached the payment/checkout phase. Browser staying open.")
                time.sleep(600) 
            except Exception as e:
                logger.error(f"Global automation error: {e}")
            finally:
                if self.context:
                    try:
                        logger.info("Closing session.")
                        self.context.close()
                    except: pass

    def automate_generic(self, item, user_data):
        """
        Universal Intelligent Agent that performs a structural analysis of the page
        by 'reading the console' (DOM introspection) to understand its e-commerce DNA.
        """
        page = self.context.new_page()
        Stealth().apply_stealth_sync(page)
        try:
            url = item.get("url")
            logger.info(f"--- [DEEP ANALYSIS] Mapping structure for: {item['name']} ---")
            # Using domcontentloaded + sleep is much more robust against background tracking scripts
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # 1. SETUP COLOR & SEARCH
            color = item.get("color")
            color_ready = True
            size_ready = True
            
            # Using domcontentloaded + short sleep is best for speed
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(1.5) 
            
            # 1. Structural Mapping (Deep DOM Introspection)
            # This script acts like a developer 'looking through the code'
            mapping_script = """
            (targetColor) => {
                const map = { colors: [], matches: [] };
                if (!targetColor) return map;
                
                const kws = [targetColor.toLowerCase(), 'couleur', 'color', 'swatch'];
                const lowerTarget = targetColor.toLowerCase();

                // Helper to perform a deep scan of an element's 'code'
                const deepInspect = (el) => {
                    const attrs = el.attributes;
                    const codeSnippets = [];
                    for(let i=0; i<attrs.length; i++) {
                        const val = attrs[i].value.toLowerCase();
                        if(kws.some(kw => val.includes(kw))) {
                            codeSnippets.push(`[${attrs[i].name}="${attrs[i].value}"]`);
                        }
                    }
                    if(el.innerText && kws.some(kw => el.innerText.toLowerCase().includes(kw))) {
                        codeSnippets.push(`text="${el.innerText.substring(0, 30)}"`);
                    }
                    return codeSnippets;
                };

                const allElements = document.querySelectorAll('button, a, div, span, img, label, [role]');
                allElements.forEach(el => {
                    const snippets = deepInspect(el);
                    if(snippets.length > 0) {
                        const rect = el.getBoundingClientRect();
                        if(rect.width > 2 && rect.width < 150) {
                            map.matches.push({
                                tag: el.tagName,
                                snippets: snippets,
                                rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height }
                            });
                        }
                    }
                });
                return map;
            }
            """
            page_map = page.evaluate(f"({mapping_script})('{color or ''}')")
            
            if color and page_map['matches']:
                logger.info(f"--- [CODE INSPECTOR] Found {len(page_map['matches'])} technical matches for '{color}' ---")

            # 2. DISMISS OBSTRUCTIONS (Rapid)
            try:
                page.evaluate("""() => {
                    const obstructions = document.querySelectorAll('button, a, div[id*="cookie"], [class*="cookie"], [id*="consent"], [class*="consent"]');
                    const kws = ['accept', 'accepter', 'allow', 'agree', 'd\\'accord', 'ok'];
                    obstructions.forEach(el => {
                        if(kws.some(kw => el.innerText.toLowerCase().includes(kw))) el.click();
                    });
                }""")
            except: pass
            
            time.sleep(1) # Reduced from 2s

            # 3. INTELLIGENT COLOR SELECTION (Hyper-Robust Scoring)
            if color:
                color_ready = False
                logger.info(f"Targeting color '{color}' using Hyper-Robust DNA analysis...")
                selection_result = page.evaluate(f"""
                    (targetColor) => {{
                        const kws = [targetColor.toLowerCase()];
                        if (kws[0] === 'noir') kws.push('black', 'nero', 'preto');
                        if (kws[0] === 'gris') kws.push('grey', 'gray');
                        if (kws[0] === 'blanc') kws.push('white', 'blanco');
                        if (kws[0] === 'bleu') kws.push('blue', 'azul');
                        if (kws[0] === 'beige') kws.push('ecru', 'sable', 'stone');
                        if (kws[0] === 'rouge') kws.push('red', 'rojo');

                        const candidates = [];
                        const elements = document.querySelectorAll('button, a, [role="button"], [role="radio"], label, div, span, img');
                        
                        elements.forEach(el => {{
                            const rect = el.getBoundingClientRect();
                            if (rect.width < 3 || rect.height < 3 || rect.width > 250) return;

                            let score = 0;
                            const title = (el.title || "").toLowerCase();
                            const aria = (el.getAttribute('aria-label') || "").toLowerCase();
                            const data = (el.getAttribute('data-color') || el.getAttribute('data-value') || el.getAttribute('data-name') || "").toLowerCase();
                            const classes = (el.className || "").toString().toLowerCase();
                            const text = (el.innerText || "").toLowerCase();
                            const id = el.id.toLowerCase();
                            
                            const img = el.querySelector('img') || (el.tagName === 'IMG' ? el : null);
                            const imgAlt = (img?.alt || "").toLowerCase();
                            const imgSrc = (img?.src || "").toLowerCase();

                            const fullMetadata = [title, aria, data, classes, text, imgAlt, imgSrc, id].join('|');
                            
                            const style = window.getComputedStyle(el);
                            const bg = style.backgroundImage.toLowerCase();

                            kws.forEach(kw => {{
                                // Deep 'Code' match
                                if (fullMetadata.includes(kw)) {{
                                    score += 20;
                                    // Extreme bonus for exact word in high-value attributes
                                    const exactRegex = new RegExp('\\\\b' + kw + '\\\\b', 'i');
                                    if (exactRegex.test(data) || exactRegex.test(aria) || exactRegex.test(title)) score += 40;
                                }}
                                if (bg.includes(kw)) score += 25;
                                if (text.trim() === kw) score += 50;
                            }});

                            // Shape Analysis (Stradivarius/Zara specific)
                            const isSquare = Math.abs(rect.width - rect.height) < 8;
                            const borderRadius = style.borderRadius;
                            const isCircle = borderRadius.includes('50%') || (parseInt(borderRadius) > rect.width / 2.5);
                            
                            if (isCircle) score += 30;
                            if (classes.includes('swatch') || classes.includes('selected') || classes.includes('active')) score += 15;

                            if (score > 0) {{
                                candidates.push({{ el, score, rect }});
                            }}
                        }});

                        if (candidates.length > 0) {{
                            candidates.sort((a, b) => b.score - a.score);
                            const best = candidates[0].el;
                            best.scrollIntoView({{block: 'center', behavior: 'instant'}});
                            
                            // Interaction escalation
                            let target = best;
                            if (!['BUTTON', 'A'].includes(best.tagName)) {{
                                target = best.closest('button, a, [role="button"]') || best;
                            }}
                            
                            target.click();
                            // Double fire for stubborn JS frameworks
                            setTimeout(() => {{
                                target.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                                target.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true}}));
                            }}, 100);
                            
                            return {{ success: true, score: candidates[0].score }};
                        }}
                        return {{ success: false }};
                    }}
                """, color)
                
                if selection_result['success']:
                    color_ready = True
                    if selection_result.get('alreadySelected'):
                        logger.info(f"[SKIP] Color '{color}' is already selected.")
                    else:
                        logger.info(f"[SUCCESS] Color '{color}' selected via DNA (Score: {selection_result['score']}).")
                else:
                    logger.warning(f"[FAIL] Could not locate color '{color}' in structural map.")

            time.sleep(2)

            # 4. INTELLIGENT SIZE SELECTION
            size = item.get("size")
            if size:
                size_ready = False
                logger.info(f"Targeting size '{size}' from mapped structure...")
                size_success = page.evaluate(f"""
                    (target) => {{
                        const lowerTarget = target.toLowerCase();
                        // Look for exact text match in buttons/spans first
                        const candidates = Array.from(document.querySelectorAll('button, span, a, div, label'))
                            .filter(el => el.innerText.trim().toLowerCase() === lowerTarget);
                        
                        if (candidates.length > 0) {{
                            const el = candidates[0];
                            el.scrollIntoView({{block: 'center'}});
                            el.click();
                            return true;
                        }}
                        return false;
                    }}
                """, size)
                if size_success: 
                    size_ready = True
                    logger.info(f"Size '{size}' selected strategically.")

            time.sleep(2)

            # 5. EXECUTE CART ACTION (Conditional)
            if color_ready and size_ready:
                logger.info("Prerequisites met. Executing mapped 'Add to Cart' action...")
                cart_success = page.evaluate("""() => {
                    const kws = ['add', 'ajouter', 'bag', 'basket', 'panier'];
                    const b = Array.from(document.querySelectorAll('button')).find(b => 
                        kws.some(kw => b.innerText.toLowerCase().includes(kw)) && b.getBoundingClientRect().width > 50
                    );
                    if (b) { b.click(); return true; }
                    return false;
                }""")
                if cart_success: logger.info("Item added to cart via mapped action.")
            else:
                logger.warning(f"MISSING PREVIEW DATA: Color Ready={color_ready}, Size Ready={size_ready}. Aborting cart add.")
                self._wait_for_manual_action(page, "Variant selection failed. Please select your color/size manually.")

            time.sleep(3)

            # 6. NAVIGATE TO CHECKOUT
            page.evaluate("""() => {
                const kws = ['checkout', 'payment', 'commander', 'panier'];
                const b = Array.from(document.querySelectorAll('a, button')).find(b => 
                    kws.some(kw => b.innerText.toLowerCase().includes(kw))
                );
                if (b) b.click();
                else window.location.href = window.location.origin + '/checkout';
            }""")

            # Check for redirect
            if "login" in page.url or "connexion" in page.url:
                self._wait_for_manual_action(page, "Login/Auth Detected")

        except Exception as e:
            logger.error(f"Structural Automation Error: {e}")
            self._wait_for_manual_action(page, "Structural Snag - Please assist.")

        except Exception as e:
            logger.error(f"Universal Intelligent Agent Error: {e}")
            self._wait_for_manual_action(page, "Automation Snag - Please take over.")

    def _handle_cookies(self, page, selectors):
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible(timeout=3000):
                    btn.click()
                    logger.info("Cookies accepted.")
                    return
            except: pass

    def _wait_for_manual_action(self, page, reason):
        logger.info(f"== PAUSED: {reason} ==")
        logger.info("Please complete the steps in the browser. The agent will wait for you.")
        try:
            start_time = time.time()
            while not page.is_closed() and (time.time() - start_time < 300):
                url = page.url.lower()
                # If we move to checkout steps or similar, we resume
                if any(x in url for x in ["commande", "checkout", "panier", "address", "shipping"]):
                    if "connexion" not in url and "login" not in url:
                        logger.info("Resuming automation.")
                        break
                time.sleep(2)
        except: pass
